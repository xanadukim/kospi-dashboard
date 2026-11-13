"""
update_foreigner_csv.py - Refresh data/foreigner_kospi200.csv from KRX via pykrx.

The daily pipeline only reads the standard CSV. This script is the ETL step that
keeps that CSV real and current; it does not feed pykrx output directly into
daily_update.py.
"""

import math
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

CSV_PATH = Path("data/foreigner_kospi200.csv")
OUT_COLUMNS = [
    "date",
    "institution",
    "other_corp",
    "individual",
    "foreigner",
    "total",
]
VALUE_COLUMNS = OUT_COLUMNS[1:]

COLUMN_CANDIDATES = {
    "institution": ["기관합계", "기관", "기관계"],
    "other_corp": ["기타법인", "기타법인합계"],
    "individual": ["개인", "개인합계"],
    "foreigner": ["외국인합계", "외국인"],
    "total": ["전체", "합계"],
}


def _read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame(columns=OUT_COLUMNS)

    df = None
    for encoding in ("utf-8-sig", "utf-8", "cp949", "euc-kr"):
        try:
            df = pd.read_csv(path, encoding=encoding)
            break
        except UnicodeDecodeError:
            continue
    if df is None:
        raise RuntimeError(f"cannot decode {path}")

    if "date" not in df.columns:
        raise RuntimeError(f"{path}: missing date column")

    out = pd.DataFrame()
    out["date"] = pd.to_datetime(df["date"], errors="coerce")
    for col in VALUE_COLUMNS:
        if col not in df.columns:
            out[col] = np.nan
            continue
        out[col] = pd.to_numeric(
            df[col].astype(str).str.replace(",", "", regex=False).str.replace('"', "", regex=False),
            errors="coerce",
        )

    out = out.dropna(subset=["date"]).drop_duplicates(subset=["date"], keep="last").sort_values("date")
    return out.reset_index(drop=True)


def _pick_column(df: pd.DataFrame, candidates):
    for name in candidates:
        if name in df.columns:
            return name
    for col in df.columns:
        if any(cand in str(col) for cand in candidates):
            return col
    return None


def _fetch_pykrx(start: str, end: str) -> pd.DataFrame:
    from pykrx import stock

    df = stock.get_market_trading_value_by_date(start, end, "KOSPI")
    if df is None or getattr(df, "empty", True):
        raise RuntimeError("pykrx returned empty KOSPI investor trading frame")

    work = df.copy()
    if "date" in work.columns:
        work["date"] = pd.to_datetime(work["date"], errors="coerce")
        work = work.set_index("date")
    else:
        work.index = pd.to_datetime(work.index, errors="coerce")
        work.index.name = "date"

    work = work[~work.index.isna()]
    if work.empty:
        raise RuntimeError("pykrx frame has no valid dates")

    out = pd.DataFrame(index=work.index)
    out.index.name = "date"
    for target, candidates in COLUMN_CANDIDATES.items():
        src = _pick_column(work, candidates)
        if src is None:
            raise RuntimeError(f"pykrx columns missing {target}: {list(work.columns)}")
        out[target] = pd.to_numeric(
            work[src].astype(str).str.replace(",", "", regex=False).str.replace('"', "", regex=False),
            errors="coerce",
        )

    out = out.dropna(subset=["foreigner", "institution", "individual", "total"])
    if out.empty:
        raise RuntimeError("pykrx frame has no usable investor rows")
    return out.sort_index()


def _calibrate_scale(existing: pd.DataFrame, fetched: pd.DataFrame):
    if existing.empty:
        return 1.0, 0

    ex = existing.set_index("date")["foreigner"]
    fe = fetched.set_index("date")["foreigner"]
    common = ex.index.intersection(fe.index)
    if len(common) < 3:
        raise RuntimeError(f"insufficient overlap for unit calibration: {len(common)}")

    ratios = []
    for day in common:
        e_val = float(ex.loc[day])
        f_val = float(fe.loc[day])
        if math.isfinite(e_val) and math.isfinite(f_val) and e_val != 0 and f_val != 0:
            ratios.append(e_val / f_val)
    if len(ratios) < 3:
        raise RuntimeError("insufficient non-zero overlap for unit calibration")

    scale = float(np.median(ratios))
    if not math.isfinite(scale) or scale <= 0:
        raise RuntimeError(f"invalid calibration scale {scale}")

    rel_errors = []
    for day in common:
        e_val = float(ex.loc[day])
        f_val = float(fe.loc[day]) * scale
        if math.isfinite(e_val) and math.isfinite(f_val) and e_val != 0:
            rel_errors.append(abs((f_val - e_val) / e_val))
    if rel_errors and float(np.median(rel_errors)) > 0.10:
        raise RuntimeError(f"unit calibration failed: median rel err {np.median(rel_errors):.4f}")

    return scale, len(common)


def main() -> int:
    existing = _read_csv(CSV_PATH)
    today = datetime.now().date()
    end = today.strftime("%Y%m%d")

    if existing.empty:
        start_date = today - timedelta(days=370)
    else:
        latest_existing = existing["date"].max().date()
        start_date = latest_existing - timedelta(days=21)

    start = start_date.strftime("%Y%m%d")
    print(f"[FOREIGNER UPDATE] fetch KOSPI {start}..{end}")
    fetched = _fetch_pykrx(start, end)

    fetched = fetched.reset_index()
    fetched["date"] = pd.to_datetime(fetched["date"], errors="coerce")
    fetched = fetched.dropna(subset=["date"]).drop_duplicates(subset=["date"], keep="last").sort_values("date")

    if existing.empty:
        existing_max = None
    else:
        existing_max = existing["date"].max()
    new_mask = fetched["date"] > existing_max if existing_max is not None else pd.Series(True, index=fetched.index)
    if not bool(new_mask.any()):
        print("[FOREIGNER UPDATE] already up to date")
        return 0

    scale, overlap = _calibrate_scale(existing, fetched)
    if scale != 1.0:
        for col in VALUE_COLUMNS:
            fetched[col] = fetched[col] * scale
        print(f"[FOREIGNER UPDATE] calibrated scale={scale:.8g} overlap={overlap}")
    else:
        print(f"[FOREIGNER UPDATE] unit ok overlap={overlap}")

    merged = pd.concat([existing, fetched[OUT_COLUMNS]], ignore_index=True)
    merged = (
        merged.dropna(subset=["date"])
        .drop_duplicates(subset=["date"], keep="last")
        .sort_values("date", ascending=False)
        .reset_index(drop=True)
    )

    CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    merged.to_csv(CSV_PATH, index=False, columns=OUT_COLUMNS, float_format="%.1f")

    latest = merged["date"].max().strftime("%Y-%m-%d")
    latest_row = merged.loc[merged["date"].idxmax()]
    print(
        f"[FOREIGNER UPDATE] wrote {CSV_PATH} rows={len(merged)} "
        f"latest_date={latest} foreigner={latest_row['foreigner']:.1f}"
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"[FOREIGNER UPDATE] failed: {exc}")
        raise
