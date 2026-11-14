"""
retrain_model.py v61.6-data-integrity

운영 원칙:
- 실제 데이터만 사용한다.
- 외국인 팩터 또는 산업 대표 종목 가격이 부족하면 재학습을 중단한다.
- 난수, 합성값, 0.85 fallback을 절대 사용하지 않는다.
- 실패 시 beta_snapshots/latest를 덮어쓰지 않는다.
"""

import json
import math
import os
from datetime import datetime, timedelta
from typing import Dict, List, Tuple

import numpy as np

try:
    from price_provider import (
        get_foreigner_factor_dated,
        get_stock_prices,
    )
except ImportError:
    from scripts.price_provider import (
        get_foreigner_factor_dated,
        get_stock_prices,
    )

try:
    from industry_betas import INDUSTRIES_BETAS as BASE_BETAS
except ImportError:
    from scripts.industry_betas import INDUSTRIES_BETAS as BASE_BETAS

try:
    import firebase_admin
    from firebase_admin import credentials, firestore
except ImportError:
    firebase_admin = None
    credentials = None
    firestore = None


RETRAIN_VERSION = "v61.6-data-integrity"
WINDOW_DAYS = 250
Z_WINDOW = 120
MIN_FACTOR_SAMPLES = 120
MIN_INDUSTRY_SAMPLES = 120
ALPHA_CANDIDATES = [0.1, 0.5, 1.0, 2.0]


INDUSTRY_PROXY = {
    "elec": "005930",
    "auto": "005380",
    "chem": "051910",
    "fin": "055550",
    "bio": "068270",
    "steel": "005490",
    "const": "009540",
    "retail": "035420",
}


FACTOR_CANONICAL = {
    "S&P500": "SP500",
    "외국인 수급": "외국인",
    "외국인 선물": "외국인",
    "SOX / 필라": "SOX",
    "US 10Y": "US10Y",
    "원달러": "원달러",
    "WTI": "WTI",
    "DXY": "DXY",
    "VIX": "VIX",
    "구리": "구리",
    "상해종합": "상해종합",
}


def init_firebase():
    """Firebase Admin SDK를 초기화한다. 자격증명이 없으면 로컬 모드로 실행한다."""
    if firebase_admin is None:
        print("[Firebase] firebase-admin not installed; local mode")
        return None

    credential_json = os.environ.get("FIREBASE_SERVICE_ACCOUNT", "")

    if not credential_json:
        print("[Firebase] no service account; local mode")
        return None

    try:
        credential_dict = json.loads(credential_json)

        if not firebase_admin._apps:
            credential = credentials.Certificate(credential_dict)
            firebase_admin.initialize_app(credential)

        print("[Firebase] retrain connected")
        return firestore.client()

    except Exception as exc:
        print(f"[Firebase] init error: {exc}")
        return None


db = init_firebase()


def closes_to_return_map(
    dates: List[str],
    closes: List[float],
) -> Dict[str, float]:
    """
    날짜-정렬된 종가 시계열을 {date: 일간 수익률(%)} 맵으로 변환한다.

    수익률은 당일 종가 기준 (prev -> cur)이며, 첫 관측치는 수익률이 없다.
    """
    returns: Dict[str, float] = {}

    for index in range(1, len(closes)):
        previous = float(closes[index - 1])
        current = float(closes[index])

        if (
            previous == 0
            or not math.isfinite(previous)
            or not math.isfinite(current)
        ):
            continue

        returns[dates[index]] = (current - previous) / previous * 100

    return returns


def rolling_z_map(
    dates: List[str],
    values: List[float],
    window: int = Z_WINDOW,
    negate: bool = False,
) -> Dict[str, float]:
    """
    각 날짜 시점의 trailing z-score 맵을 생성한다.

    price_provider.calc_z_score와 동일한 정의를 날짜별로 적용한다:
    - trailing window개 관측의 평균/표준편차 기준
    - 관측 20개 미만이면 해당 날짜 제외
    - [-3, 3] 클립, 소수점 2자리
    - negate=True이면 부호 반전 (VIX 위험오프 해석과 동일)
    """
    z_map: Dict[str, float] = {}
    arr = np.asarray(values, dtype=float)

    for index in range(len(arr)):
        if index + 1 < 20:
            continue

        w = min(window, index + 1)
        recent = arr[index - w + 1:index + 1]
        mean = float(np.mean(recent))
        std = float(np.std(recent))

        if std < 1e-6:
            continue

        z = (float(arr[index]) - mean) / std
        z = round(max(-3.0, min(3.0, z)), 2)

        if negate:
            z = round(-z, 2)

        z_map[str(dates[index])] = z

    return z_map


def _clean_pairs(
    dates: List[str],
    closes: List[float],
    days: int,
) -> Tuple[List[str], List[float]]:
    """finite 값만 남기고 최근 days개 관측치로 자른다."""
    pairs = [
        (str(d), float(c))
        for d, c in zip(dates, closes)
        if c is not None and math.isfinite(float(c))
    ]
    pairs = pairs[-days:]
    return [p[0] for p in pairs], [p[1] for p in pairs]


def fetch_factor_history(
    days: int = WINDOW_DAYS,
) -> Tuple[Dict[str, Dict], Dict]:
    """
    재학습용 팩터 시계열을 실제 데이터에서만 가져온다.

    반환 구조: factor_series[canonical] = {"dates", "closes", "returns"}
    returns는 {date: 일간 수익률(%)} 맵으로 날짜 정보가 유지된다.

    하나라도 최소 표본 기준을 충족하지 못하면 RuntimeError를 발생시켜
    재학습 workflow가 실패하도록 만든다.
    """
    print(f"[Retrain] loading {days} days of REAL factor history (dated)")

    factor_series: Dict[str, Dict] = {}

    market_factors = [
        "SP500",
        "US10Y",
        "SOX",
        "원달러",
        "WTI",
        "DXY",
        "VIX",
        "구리",
        "상해종합",
    ]

    for factor_name in market_factors:
        closes, dates = get_stock_prices(
            factor_name,
            period="1y",
            source="yfinance",
        )
        dates, closes = _clean_pairs(dates, closes, days)

        if len(closes) < MIN_FACTOR_SAMPLES:
            raise RuntimeError(
                f"factor {factor_name} has insufficient closes: "
                f"{len(closes)} < {MIN_FACTOR_SAMPLES}"
            )

        returns = closes_to_return_map(dates, closes)

        if len(returns) < MIN_FACTOR_SAMPLES - 1:
            raise RuntimeError(
                f"factor {factor_name} has insufficient returns: "
                f"{len(returns)} < {MIN_FACTOR_SAMPLES - 1}"
            )

        factor_series[factor_name] = {
            "dates": dates,
            "closes": closes,
            "returns": returns,
            "z": rolling_z_map(
                dates,
                closes,
                negate=(factor_name == "VIX"),
            ),
        }

        print(
            f"[Retrain] factor={factor_name} "
            f"closes={len(closes)} returns={len(returns)} "
            f"latest={closes[-1]:.4f} last_date={dates[-1]}"
        )

    (
        foreigner_dates,
        foreigner_values,
        foreigner_latest,
        _,
        foreigner_meta,
    ) = get_foreigner_factor_dated(
        min_samples=MIN_FACTOR_SAMPLES
    )

    if foreigner_meta.get("status") != "REAL":
        raise RuntimeError(
            "foreigner factor unavailable: "
            f"{foreigner_meta.get('reason', 'unknown error')}"
        )

    foreigner_dates, foreigner_values = _clean_pairs(
        foreigner_dates,
        foreigner_values,
        days,
    )
    foreigner_returns = closes_to_return_map(
        foreigner_dates,
        foreigner_values,
    )

    if len(foreigner_returns) < MIN_FACTOR_SAMPLES - 1:
        raise RuntimeError(
            "foreigner factor has insufficient returns: "
            f"{len(foreigner_returns)} < {MIN_FACTOR_SAMPLES - 1}"
        )

    factor_series["외국인"] = {
        "dates": foreigner_dates,
        "closes": foreigner_values,
        "returns": foreigner_returns,
        "z": rolling_z_map(foreigner_dates, foreigner_values),
    }

    print(
        f"[Retrain] factor=외국인 "
        f"rows={len(foreigner_values)} "
        f"returns={len(foreigner_returns)} "
        f"latest={foreigner_latest:.0f} "
        f"latest_date={foreigner_meta.get('latest_date')}"
    )

    data_meta = {
        "data_status": "REAL_ONLY",
        "synthetic_data_used": False,
        "fallback_used": False,
        "foreigner": foreigner_meta,
    }

    return factor_series, data_meta


def fetch_industry_returns(days: int = WINDOW_DAYS) -> Dict[str, Dict]:
    """
    8개 산업 대표주의 실제 수익률을 날짜 맵과 함께 반환한다.

    일부 종목 데이터가 부족해도 난수를 만들지 않는다.
    하나라도 실패하면 재학습 전체를 실패 처리한다.
    """
    print("[Retrain] loading REAL industry proxy returns (dated)")

    industry_series: Dict[str, Dict] = {}
    failed_industries = []

    for industry_id, ticker in INDUSTRY_PROXY.items():
        try:
            closes, dates = get_stock_prices(
                ticker,
                period="1y",
                source="yfinance",
            )
            dates, closes = _clean_pairs(dates, closes, days)

            if len(closes) < MIN_INDUSTRY_SAMPLES:
                raise ValueError(
                    f"insufficient closes: "
                    f"{len(closes)} < {MIN_INDUSTRY_SAMPLES}"
                )

            returns = closes_to_return_map(dates, closes)

            if len(returns) < MIN_INDUSTRY_SAMPLES - 1:
                raise ValueError(
                    f"insufficient returns: "
                    f"{len(returns)} < {MIN_INDUSTRY_SAMPLES - 1}"
                )

            industry_series[industry_id] = {
                "dates": dates,
                "closes": closes,
                "returns": returns,
            }

            print(
                f"[Retrain] industry={industry_id} "
                f"ticker={ticker} "
                f"returns={len(returns)} "
                f"latest={closes[-1]:.0f} last_date={dates[-1]}"
            )

        except Exception as exc:
            failed_industries.append(
                f"{industry_id}({ticker}): {exc}"
            )

    if failed_industries:
        raise RuntimeError(
            "industry proxy retrieval failed; retraining aborted: "
            + " | ".join(failed_industries)
        )

    return industry_series


def ridge_regression(
    x_matrix: np.ndarray,
    y_values: np.ndarray,
    alpha: float,
) -> Tuple[np.ndarray, float]:
    """NumPy 기반 Ridge 회귀와 학습 구간 R²를 계산한다."""
    try:
        feature_count = x_matrix.shape[1]

        matrix_a = (
            x_matrix.T @ x_matrix
            + alpha * np.eye(feature_count)
        )
        matrix_b = x_matrix.T @ y_values

        betas = np.linalg.solve(matrix_a, matrix_b)
        predictions = x_matrix @ betas

        residual_sum = np.sum((y_values - predictions) ** 2)
        total_sum = np.sum((y_values - np.mean(y_values)) ** 2)

        r_squared = (
            1 - residual_sum / total_sum
            if total_sum > 0
            else 0.0
        )

        return betas, float(r_squared)

    except Exception as exc:
        raise RuntimeError(f"ridge regression failed: {exc}") from exc


def _r_squared(predictions: np.ndarray, actual: np.ndarray) -> float:
    """결정계수 R²를 계산한다. 분산이 0이면 0.0을 반환한다."""
    total_sum = float(np.sum((actual - np.mean(actual)) ** 2))

    if total_sum <= 0:
        return 0.0

    residual_sum = float(np.sum((actual - predictions) ** 2))
    return float(1 - residual_sum / total_sum)


def fetch_previous_betas() -> Dict[str, Dict[str, float]]:
    """
    beta_snapshots/latest의 이전 재학습 β를 읽는다.

    beta_changes 비교 기준으로 사용하며, 없으면 빈 dict를 반환한다.
    """
    if db is None:
        return {}

    try:
        doc = db.collection("beta_snapshots").document("latest").get()

        if doc.exists:
            data = doc.to_dict() or {}
            betas = data.get("betas") or {}
            if betas:
                print(
                    f"[Retrain] previous betas loaded "
                    f"date={data.get('date')} industries={len(betas)}"
                )
                return betas

    except Exception as exc:
        print(f"[Retrain] previous beta_snapshots load failed: {exc}")

    return {}


def train_industry_model(
    factor_series: Dict[str, Dict],
    industry_series: Dict[str, Dict],
    industry_id: str,
) -> Dict:
    """
    산업별 대표 종목 수익률로 Ridge 모델을 학습한다.

    피처 공간: daily_update와 동일한 팩터 레벨 z-score
    (rolling 120일, VIX 부호 반전). BASE_BETAS와 β 단위가 일치하므로
    OOS 게이트 비교가 유효하다.

    - 모든 시계열을 공통 거래일로 inner join해 날짜 정렬한다.
    - α는 시간순 holdout(최근 25%) validation R²로 선택한다.
    - retrained 모델의 OOS R²가 BASE_BETAS의 OOS R²보다 낮으면
      재학습 β를 채택하지 않고 base β를 유지한다 (retrain_gate=REJECTED).
    """
    factor_names = list(BASE_BETAS[industry_id].keys())
    industry_returns_map = industry_series[industry_id]["returns"]

    factor_z_maps = {}

    for factor_name in factor_names:
        canonical_name = FACTOR_CANONICAL[factor_name]

        if canonical_name not in factor_series:
            raise RuntimeError(
                f"{industry_id}: factor data missing for {factor_name}"
            )

        factor_z_maps[factor_name] = (
            factor_series[canonical_name]["z"]
        )

    # 날짜 inner join: 산업 수익률 + 해당 산업 팩터 z 전부에 존재하는 공통일
    common_dates = sorted(
        set(industry_returns_map.keys())
        & set.intersection(
            *[
                set(factor_z_maps[f].keys())
                for f in factor_names
            ]
        )
    )

    sample_count = len(common_dates)

    if sample_count < MIN_INDUSTRY_SAMPLES - 1:
        raise RuntimeError(
            f"{industry_id}: insufficient common sample count: "
            f"{sample_count}"
        )

    x_raw = np.array(
        [
            [factor_z_maps[f][d] for f in factor_names]
            for d in common_dates
        ],
        dtype=float,
    )
    y_values = np.array(
        [industry_returns_map[d] for d in common_dates],
        dtype=float,
    )

    # 시간순 holdout: 최근 25%를 validation으로 사용
    val_count = max(15, int(round(sample_count * 0.25)))
    train_count = sample_count - val_count

    if train_count < 40:
        raise RuntimeError(
            f"{industry_id}: train split too small: {train_count}"
        )

    x_train = x_raw[:train_count]
    y_train = y_values[:train_count]
    x_val = x_raw[train_count:]
    y_val = y_values[train_count:]

    x_mean = np.mean(x_train, axis=0)
    x_std = np.std(x_train, axis=0)

    if np.any(x_std < 1e-8):
        raise RuntimeError(
            f"{industry_id}: at least one factor has near-zero variance"
        )

    x_train_norm = (x_train - x_mean) / x_std
    x_val_norm = (x_val - x_mean) / x_std

    # α 선택: validation R² 기준 (in-sample R²는 과적합으로 α=0.1에 편향)
    best_alpha = None
    best_val_r2 = -np.inf

    for alpha in ALPHA_CANDIDATES:
        candidate_betas, _ = ridge_regression(
            x_train_norm,
            y_train,
            alpha,
        )
        candidate_pred = x_val_norm @ candidate_betas
        candidate_r2 = _r_squared(candidate_pred, y_val)

        if candidate_r2 > best_val_r2:
            best_alpha = alpha
            best_val_r2 = float(candidate_r2)

    if best_alpha is None:
        raise RuntimeError(
            f"{industry_id}: no valid ridge model produced"
        )

    # BASE_BETAS의 validation 성능 (게이트 비교 기준)
    base_vector = np.array(
        [BASE_BETAS[industry_id][f] for f in factor_names],
        dtype=float,
    )
    base_val_pred = x_val @ base_vector
    base_val_r2 = _r_squared(base_val_pred, y_val)

    retrain_gate = (
        "PASSED" if best_val_r2 > base_val_r2 else "REJECTED"
    )

    # 최종 β 결정
    if retrain_gate == "PASSED":
        # 전체 공통 표본으로 재적합 후 70/30 블렌딩
        x_all_mean = np.mean(x_raw, axis=0)
        x_all_std = np.std(x_raw, axis=0)

        if np.any(x_all_std < 1e-8):
            raise RuntimeError(
                f"{industry_id}: near-zero variance on full sample"
            )

        x_all_norm = (x_raw - x_all_mean) / x_all_std
        final_betas_norm, final_insample_r2 = ridge_regression(
            x_all_norm,
            y_values,
            best_alpha,
        )
        original_scale_betas = final_betas_norm / x_all_std

        blended_betas = {}
        for index, factor_name in enumerate(factor_names):
            new_beta = float(
                np.clip(original_scale_betas[index], -0.6, 0.6)
            )
            base_beta = BASE_BETAS[industry_id][factor_name]
            blended_betas[factor_name] = round(
                float(0.7 * new_beta + 0.3 * base_beta),
                3,
            )

        final_r2 = float(final_insample_r2)
    else:
        # OOS에서 base보다 못하면 재학습 β를 채택하지 않는다
        blended_betas = {
            factor_name: round(
                float(BASE_BETAS[industry_id][factor_name]),
                3,
            )
            for factor_name in factor_names
        }
        base_insample_pred = x_raw @ base_vector
        final_r2 = _r_squared(base_insample_pred, y_values)

    print(
        f"[Retrain] industry={industry_id} "
        f"alpha={best_alpha} gate={retrain_gate} "
        f"oos_r2={best_val_r2:.3f} base_oos_r2={base_val_r2:.3f} "
        f"r2={final_r2:.3f} samples={sample_count} "
        f"common={common_dates[0]}..{common_dates[-1]}"
    )

    return {
        "betas": blended_betas,
        "r2": round(final_r2, 3),
        "alpha": best_alpha,
        "samples": sample_count,
        "common_start": common_dates[0],
        "common_end": common_dates[-1],
        "oos_r2": round(best_val_r2, 3),
        "base_oos_r2": round(base_val_r2, 3),
        "retrain_gate": retrain_gate,
        "validation": "last 25% chronological holdout",
        "method": (
            "Ridge alpha by holdout R2 + factor-level z features "
            "(same space as INDUSTRIES_BETAS) + date inner-join "
            "alignment + OOS gate vs BASE_BETAS; REAL_ONLY inputs"
        ),
        "factor_names": factor_names,
        "data_status": "REAL_ONLY",
        "synthetic_data_used": False,
        "fallback_used": False,
    }


def build_retrain_snapshot():
    """전체 산업 재학습 결과 스냅샷을 생성한다."""
    print("=== Retrain v61.6 data-integrity: REAL_ONLY ===")

    date_string = datetime.now().strftime("%Y-%m-%d")

    factor_series, data_meta = fetch_factor_history(WINDOW_DAYS)

    industry_series = fetch_industry_returns(WINDOW_DAYS)

    previous_betas = fetch_previous_betas()

    retrained = {}
    r_squared_values = []

    for industry_id in INDUSTRY_PROXY:
        result = train_industry_model(
            factor_series,
            industry_series,
            industry_id,
        )

        retrained[industry_id] = result
        r_squared_values.append(result["r2"])

    average_r_squared = (
        float(np.mean(r_squared_values))
        if r_squared_values
        else 0.0
    )

    beta_changes = {}

    for industry_id, result in retrained.items():
        # 비교 기준: 이전 재학습 β (없으면 BASE_BETAS)
        previous = previous_betas.get(industry_id) or BASE_BETAS[industry_id]
        new_betas = result["betas"]

        changes = {}

        for factor_name, new_beta in new_betas.items():
            old_beta = previous.get(factor_name, 0.0)
            difference = round(new_beta - old_beta, 3)

            if abs(difference) > 0.02:
                changes[factor_name] = {
                    "old": old_beta,
                    "new": new_beta,
                    "diff": difference,
                }

        if changes:
            beta_changes[industry_id] = changes

    passed_count = sum(
        1
        for result in retrained.values()
        if result.get("retrain_gate") == "PASSED"
    )
    total_count = len(retrained)

    retrain_gate = (
        "PASSED"
        if passed_count == total_count
        else (
            "PARTIAL"
            if passed_count > 0
            else "REJECTED"
        )
    )

    snapshot = {
        "date": date_string,
        "timestamp": datetime.now().isoformat(),
        "version": RETRAIN_VERSION,
        "window": WINDOW_DAYS,
        "method": (
            "Ridge alpha by holdout R2 + factor-level z features "
            "(same space as INDUSTRIES_BETAS) + date inner-join "
            "alignment + OOS gate vs BASE_BETAS + "
            "70% new / 30% base blending; REAL_ONLY inputs; "
            "no synthetic fallback"
        ),
        "industries": retrained,
        "avg_r2": round(average_r_squared, 3),
        "r2_list": {
            industry_id: result["r2"]
            for industry_id, result in retrained.items()
        },
        "beta_changes": beta_changes,
        "beta_changes_count": sum(
            len(changes)
            for changes in beta_changes.values()
        ),
        "factor_closes_count": {
            factor_name: len(series["dates"])
            for factor_name, series in factor_series.items()
        },
        "proxy_tickers": INDUSTRY_PROXY,
        "next_retrain": (
            datetime.now() + timedelta(days=30)
        ).strftime("%Y-%m-%d"),
        "retrain_type": (
            "monthly"
            if datetime.now().day == 1
            else "manual"
        ),
        "data_status": "REAL_ONLY",
        "synthetic_data_used": False,
        "fallback_used": False,
        "retrain_gate": retrain_gate,
        "retrain_gate_detail": {
            "passed": passed_count,
            "total": total_count,
        },
        "foreigner_metadata": data_meta["foreigner"],
        "china_proxy": (
            "구리(HG=F) + 상해종합(000001.SS); "
            "source status validated before training"
        ),
    }

    print(
        f"[Retrain] completed "
        f"avg_r2={snapshot['avg_r2']:.3f} "
        f"changes={snapshot['beta_changes_count']}"
    )

    return snapshot


def save_to_firebase(snapshot: Dict):
    """
    정상 재학습 결과만 Firestore에 저장한다.

    build_retrain_snapshot()에서 오류가 나면 이 함수까지 도달하지 않으므로,
    beta_snapshots/latest는 기존 정상값을 유지한다.
    """
    if db is None:
        output_name = f"retrain_{snapshot['date']}.json"

        with open(
            output_name,
            "w",
            encoding="utf-8",
        ) as output_file:
            json.dump(
                snapshot,
                output_file,
                ensure_ascii=False,
                indent=2,
            )

        print(f"[Retrain] local snapshot saved: {output_name}")
        return

    date_string = snapshot["date"]

    db.collection("retrain_history").document(
        date_string
    ).set(snapshot, merge=True)

    beta_only = {
        industry_id: result["betas"]
        for industry_id, result in snapshot["industries"].items()
    }

    beta_document = {
        "date": date_string,
        "timestamp": datetime.now(),
        "betas": beta_only,
        "r2": snapshot["r2_list"],
        "avg_r2": snapshot["avg_r2"],
        "version": snapshot["version"],
        "changes": snapshot["beta_changes_count"],
        "data_status": snapshot["data_status"],
        "synthetic_data_used": False,
        "fallback_used": False,
        "retrain_gate": snapshot.get("retrain_gate", "PASSED"),
        "foreigner_metadata": snapshot["foreigner_metadata"],
    }

    db.collection("beta_snapshots").document(
        date_string
    ).set(beta_document, merge=True)

    db.collection("beta_snapshots").document(
        "latest"
    ).set(beta_document, merge=True)

    log_document = {
        "date": date_string,
        "avg_r2": snapshot["avg_r2"],
        "changes": snapshot["beta_changes_count"],
        "industries": list(snapshot["industries"].keys()),
        "next_retrain": snapshot["next_retrain"],
        "version": snapshot["version"],
        "data_status": snapshot["data_status"],
        "synthetic_data_used": False,
        "fallback_used": False,
        "retrain_gate": snapshot.get("retrain_gate", "PASSED"),
        "createdAt": firestore.SERVER_TIMESTAMP,
    }

    db.collection("retrain_logs").document(
        date_string
    ).set(log_document, merge=True)

    print(
        f"[Firebase] retrain saved: "
        f"beta_snapshots/latest "
        f"avg_r2={snapshot['avg_r2']:.3f}"
    )


def generate_data_js(
    snapshot: Dict,
    output_path: str = "js/data.js.new",
):
    """
    기존 프런트엔드 호환을 위한 data.js.new를 생성한다.

    이 파일은 자동 배포하지 않는다.
    생성 결과는 검토 후 별도 커밋으로 js/data.js에 반영한다.
    """
    base_meta = {
        "elec": {
            "name": "전기전자/반도체",
            "short": "전기전자",
            "icon": "◫",
            "color": "#2563eb",
            "grad": "grad-elec",
            "desc": "나스닥/외국인 + 중국 프록시 민감",
        },
        "auto": {
            "name": "자동차/운수장비",
            "short": "자동차",
            "icon": "◩",
            "color": "#0f766e",
            "grad": "grad-auto",
            "desc": "환율/유가 + 중국 수요 민감 수출주",
        },
        "chem": {
            "name": "화학/2차전지",
            "short": "화학·전지",
            "icon": "⬡",
            "color": "#9333ea",
            "grad": "grad-chem",
            "desc": "구리/상해종합 중국 경기 프록시 민감",
        },
        "fin": {
            "name": "금융/증권",
            "short": "금융",
            "icon": "₩",
            "color": "#1e293b",
            "grad": "grad-fin",
            "desc": "금리·달러·VIX 민감",
        },
        "bio": {
            "name": "바이오/의약품",
            "short": "바이오",
            "icon": "⚕",
            "color": "#e11d48",
            "grad": "grad-bio",
            "desc": "금리 하락·VIX 하락 민감",
        },
        "steel": {
            "name": "철강/소재/에너지",
            "short": "철강·소재",
            "icon": "⬣",
            "color": "#a16207",
            "grad": "grad-steel",
            "desc": "구리·상해종합 중국 경기 민감",
        },
        "const": {
            "name": "건설/조선/기계",
            "short": "건설·조선",
            "icon": "⌖",
            "color": "#334155",
            "grad": "grad-const",
            "desc": "중국 인프라 수요 민감",
        },
        "retail": {
            "name": "유통/IT서비스",
            "short": "유통·IT",
            "icon": "◎",
            "color": "#0891b2",
            "grad": "grad-retail",
            "desc": "내수·플랫폼·중국 소비 심리",
        },
    }

    industries = []

    for industry_id in INDUSTRY_PROXY:
        model_result = snapshot["industries"][industry_id]
        meta = base_meta[industry_id]

        industries.append(
            {
                "id": industry_id,
                "name": meta["name"],
                "short": meta["short"],
                "icon": meta["icon"],
                "r2": model_result["r2"],
                "color": meta["color"],
                "grad": meta["grad"],
                "betas": model_result["betas"],
                "desc": meta["desc"],
            }
        )

    js_content = f"""// AUTO GENERATED: {snapshot["version"]}
// Date: {snapshot["date"]}
// Data policy: REAL_ONLY, no synthetic fallback
// Review this file before replacing js/data.js.

var industries = {json.dumps(industries, ensure_ascii=False, indent=2)};

var retrainMeta = {{
  date: "{snapshot["date"]}",
  avg_r2: {snapshot["avg_r2"]},
  changes: {snapshot["beta_changes_count"]},
  version: "{snapshot["version"]}",
  data_status: "{snapshot["data_status"]}",
  synthetic_data_used: false,
  fallback_used: false
}};
"""

    output_directory = os.path.dirname(output_path)

    if output_directory:
        os.makedirs(output_directory, exist_ok=True)

    with open(
        output_path,
        "w",
        encoding="utf-8",
    ) as output_file:
        output_file.write(js_content)

    print(
        f"[Retrain] generated candidate JS: "
        f"{output_path}"
    )


if __name__ == "__main__":
    snapshot = build_retrain_snapshot()
    save_to_firebase(snapshot)
    generate_data_js(snapshot)

    print(
        json.dumps(
            {
                "date": snapshot["date"],
                "version": snapshot["version"],
                "avg_r2": snapshot["avg_r2"],
                "changes": snapshot["beta_changes_count"],
                "data_status": snapshot["data_status"],
                "synthetic_data_used": False,
                "fallback_used": False,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
