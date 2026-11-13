"""
update_foreigner_csv.py - Refresh data/foreigner_kospi200.csv from KRX via pykrx.

The daily pipeline only reads the standard CSV. This script is the ETL step that
keeps that CSV real and current; it does not feed pykrx output directly into
daily_update.py.

The foreigner series is the KOSPI whole-market investor trading aggregate
(institution / other corp / individual / foreigner), converted from KRW to
million KRW to keep the existing CSV scale.
"""

import os
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

WON_PER_MILLION = 1_000_000
LOOKBACK_DAYS = 450
MIN_ROWS = 120
LATEST_TOLERANCE_DAYS = 10


def _pick_column(df: pd.DataFrame, candidates):
    for name in candidates:
        if name in df.columns:
            return name
    for col in df.columns:
        if any(cand in str(col) for cand in candidates):
            return col
    return None


def _fetch_pykrx(start: str, end: str) -> pd.DataFrame:
    if not os.environ.get("KRX_ID") or not os.environ.get("KRX_PW"):
        raise RuntimeError("KRX_ID/KRX_PW not set; KRX investor trading requires login")

    from pykrx import stock

    df = stock.get_market_trading_value_by_date(
        start,
        end,
        "KOSPI",
        etf=True,
        etn=True,
        elw=True,
    )
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

    out = out.dropna(subset=VALUE_COLUMNS)
    if out.empty:
        raise RuntimeError("pykrx frame has no usable investor rows")
    out = out.sort_index()
    print(f"[FOREIGNER UPDATE] pykrx shape={out.shape} range={out.index.min().date()}..{out.index.max().date()}")
    return out


def _validate(df: pd.DataFrame, today) -> None:
    if df.empty:
        raise RuntimeError("empty foreigner frame")
    if len(df) < MIN_ROWS:
        raise RuntimeError(f"insufficient rows: {len(df)} < {MIN_ROWS}")

    latest = df.index.max().date()
    if (today - latest).days > LATEST_TOLERANCE_DAYS:
        raise RuntimeError(f"stale foreigner data: latest={latest} today={today}")

    for col in VALUE_COLUMNS:
        if not bool(np.isfinite(df[col].to_numpy(dtype=float)).all()):
            raise RuntimeError(f"non-finite values in {col}")

    component_sum = df["institution"] + df["other_corp"] + df["individual"] + df["foreigner"]
    diff = (component_sum - df["total"]).abs()
    max_diff = float(diff.max())
    if max_diff > 1.0:
        raise RuntimeError(f"investor column sum mismatch max={max_diff:.4f} (million KRW)")


def main() -> int:
    today = datetime.now().date()
    end = today.strftime("%Y%m%d")
    start_date = today - timedelta(days=LOOKBACK_DAYS)
    start = start_date.strftime("%Y%m%d")

    print(f"[FOREIGNER UPDATE] fetch KOSPI market {start}..{end}")
    fetched = _fetch_pykrx(start, end)

    for col in VALUE_COLUMNS:
        fetched[col] = fetched[col] / WON_PER_MILLION

    _validate(fetched, today)

    out = fetched.reset_index()
    out = out.rename(columns={"index": "date"})
    out["date"] = pd.to_datetime(out["date"], errors="coerce")
    out = out.dropna(subset=["date"]).drop_duplicates(subset=["date"], keep="last")
    out = out.sort_values("date", ascending=False).reset_index(drop=True)

    CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(CSV_PATH, index=False, columns=OUT_COLUMNS, float_format="%.1f")

    latest = out["date"].max().strftime("%Y-%m-%d")
    latest_row = out.loc[out["date"].idxmax()]
    print(
        f"[FOREIGNER UPDATE] wrote {CSV_PATH} rows={len(out)} "
        f"latest_date={latest} foreigner={latest_row['foreigner']:.1f} (million KRW)"
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"[FOREIGNER UPDATE] failed: {exc}")
        raise
