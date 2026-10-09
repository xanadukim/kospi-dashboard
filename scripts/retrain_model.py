"""
retrain_model.py v61.6-data-integrity

운영 원칙:
- 실제 데이터만 사용한다.
- 외국인 팩터 또는 산업 대표 종목 가격이 부족하면 재학습을 중단한다.
- 난수, 합성값, 0.85 fallback을 절대 사용하지 않는다.
- 실패 시 beta_snapshots/latest를 덮어쓰지 않는다.
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Tuple

import numpy as np

try:
    from price_provider import (
        get_foreigner_factor_real,
        get_market_indicator,
        get_stock_prices,
    )
except ImportError:
    from scripts.price_provider import (
        get_foreigner_factor_real,
        get_market_indicator,
        get_stock_prices,
    )

try:
    import firebase_admin
    from firebase_admin import credentials, firestore
except ImportError:
    firebase_admin = None
    credentials = None
    firestore = None


RETRAIN_VERSION = "v61.6-data-integrity"
WINDOW_DAYS = 180
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


BASE_BETAS = {
    "elec": {
        "S&P500": 0.42,
        "외국인 선물": 0.28,
        "SOX / 필라": 0.35,
        "US 10Y": -0.18,
        "구리": 0.15,
        "상해종합": 0.10,
        "DXY": -0.08,
        "VIX": -0.06,
    },
    "auto": {
        "원달러": 0.25,
        "WTI": -0.15,
        "S&P500": 0.20,
        "구리": 0.12,
        "상해종합": 0.14,
        "DXY": 0.10,
    },
    "chem": {
        "구리": 0.32,
        "상해종합": 0.22,
        "WTI": -0.18,
        "원달러": -0.10,
        "S&P500": 0.12,
    },
    "fin": {
        "US 10Y": -0.30,
        "DXY": 0.18,
        "외국인 선물": 0.15,
        "VIX": -0.15,
        "S&P500": 0.10,
    },
    "bio": {
        "US 10Y": -0.22,
        "S&P500": 0.18,
        "VIX": -0.18,
        "DXY": -0.06,
    },
    "steel": {
        "구리": 0.35,
        "상해종합": 0.28,
        "원달러": 0.15,
        "WTI": 0.14,
        "S&P500": 0.08,
        "DXY": 0.10,
    },
    "const": {
        "구리": 0.22,
        "상해종합": 0.18,
        "원달러": 0.15,
        "WTI": 0.08,
        "DXY": 0.08,
    },
    "retail": {
        "S&P500": 0.22,
        "외국인 선물": 0.18,
        "상해종합": 0.12,
        "구리": 0.08,
        "VIX": -0.10,
    },
}


FACTOR_CANONICAL = {
    "S&P500": "SP500",
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


def to_returns(closes: List[float]) -> List[float]:
    """가격 시계열을 일간 단순 수익률(%)로 변환한다."""
    if len(closes) < 2:
        return []

    returns = []

    for index in range(1, len(closes)):
        previous = float(closes[index - 1])
        current = float(closes[index])

        if previous == 0:
            continue

        returns.append((current - previous) / previous * 100)

    return returns


def fetch_factor_history(
    days: int = WINDOW_DAYS,
) -> Tuple[Dict[str, List[float]], Dict[str, List[float]], Dict]:
    """
    재학습용 팩터 시계열을 실제 데이터에서만 가져온다.

    하나라도 최소 표본 기준을 충족하지 못하면 RuntimeError를 발생시켜
    재학습 workflow가 실패하도록 만든다.
    """
    print(f"[Retrain] loading {days} days of REAL factor history")

    factor_closes: Dict[str, List[float]] = {}
    factor_returns: Dict[str, List[float]] = {}

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
        closes, _ = get_market_indicator(factor_name, period="1y")
        closes = [
            float(value)
            for value in closes
            if value is not None
        ][-days:]

        if len(closes) < MIN_FACTOR_SAMPLES:
            raise RuntimeError(
                f"factor {factor_name} has insufficient closes: "
                f"{len(closes)} < {MIN_FACTOR_SAMPLES}"
            )

        returns = to_returns(closes)

        if len(returns) < MIN_FACTOR_SAMPLES - 1:
            raise RuntimeError(
                f"factor {factor_name} has insufficient returns: "
                f"{len(returns)} < {MIN_FACTOR_SAMPLES - 1}"
            )

        factor_closes[factor_name] = closes
        factor_returns[factor_name] = returns

        print(
            f"[Retrain] factor={factor_name} "
            f"closes={len(closes)} returns={len(returns)} "
            f"latest={closes[-1]:.4f}"
        )

    foreigner_values, foreigner_latest, _, foreigner_meta = (
        get_foreigner_factor_real(
            min_samples=MIN_FACTOR_SAMPLES
        )
    )

    if foreigner_meta.get("status") != "REAL":
        raise RuntimeError(
            "foreigner factor unavailable: "
            f"{foreigner_meta.get('reason', 'unknown error')}"
        )

    foreigner_values = [
        float(value)
        for value in foreigner_values
        if value is not None
    ][-days:]

    foreigner_returns = to_returns(foreigner_values)

    if len(foreigner_returns) < MIN_FACTOR_SAMPLES - 1:
        raise RuntimeError(
            "foreigner factor has insufficient returns: "
            f"{len(foreigner_returns)} < {MIN_FACTOR_SAMPLES - 1}"
        )

    factor_closes["외국인"] = foreigner_values
    factor_returns["외국인"] = foreigner_returns

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

    return factor_closes, factor_returns, data_meta


def fetch_industry_returns(days: int = WINDOW_DAYS) -> Dict[str, List[float]]:
    """
    8개 산업 대표주의 실제 수익률만 반환한다.

    일부 종목 데이터가 부족해도 난수를 만들지 않는다.
    하나라도 실패하면 재학습 전체를 실패 처리한다.
    """
    print("[Retrain] loading REAL industry proxy returns")

    industry_returns: Dict[str, List[float]] = {}
    failed_industries = []

    for industry_id, ticker in INDUSTRY_PROXY.items():
        try:
            closes, _ = get_stock_prices(ticker, period="1y")

            closes = [
                float(value)
                for value in closes
                if value is not None
            ][-days:]

            if len(closes) < MIN_INDUSTRY_SAMPLES:
                raise ValueError(
                    f"insufficient closes: "
                    f"{len(closes)} < {MIN_INDUSTRY_SAMPLES}"
                )

            returns = to_returns(closes)

            if len(returns) < MIN_INDUSTRY_SAMPLES - 1:
                raise ValueError(
                    f"insufficient returns: "
                    f"{len(returns)} < {MIN_INDUSTRY_SAMPLES - 1}"
                )

            industry_returns[industry_id] = returns

            print(
                f"[Retrain] industry={industry_id} "
                f"ticker={ticker} "
                f"returns={len(returns)} "
                f"latest={closes[-1]:.0f}"
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

    return industry_returns


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


def train_industry_model(
    factor_returns: Dict[str, List[float]],
    industry_returns: List[float],
    industry_id: str,
) -> Dict:
    """
    산업별 대표 종목 수익률로 Ridge 모델을 학습한다.

    주의:
    - 이 단계에서는 날짜 기반 정렬이 아직 구현되지 않았다.
    - 다음 단계에서 모든 시계열을 기준일로 inner join해야 한다.
    """
    factor_names = list(BASE_BETAS[industry_id].keys())

    required_factor_returns = []

    for factor_name in factor_names:
        canonical_name = FACTOR_CANONICAL[factor_name]
        values = factor_returns.get(canonical_name, [])

        if not values:
            raise RuntimeError(
                f"{industry_id}: factor data missing for {factor_name}"
            )

        required_factor_returns.append(values)

    sample_count = min(
        len(industry_returns),
        *[len(values) for values in required_factor_returns],
    )

    if sample_count < MIN_INDUSTRY_SAMPLES - 1:
        raise RuntimeError(
            f"{industry_id}: insufficient common sample count: "
            f"{sample_count}"
        )

    x_columns = [
        values[-sample_count:]
        for values in required_factor_returns
    ]

    x_matrix = np.array(x_columns, dtype=float).T
    y_values = np.array(
        industry_returns[-sample_count:],
        dtype=float,
    )

    x_mean = np.mean(x_matrix, axis=0)
    x_std = np.std(x_matrix, axis=0)

    if np.any(x_std < 1e-8):
        raise RuntimeError(
            f"{industry_id}: at least one factor has near-zero variance"
        )

    x_normalized = (x_matrix - x_mean) / x_std

    best_alpha = None
    best_r_squared = -np.inf
    best_betas = None

    for alpha in ALPHA_CANDIDATES:
        candidate_betas, candidate_r_squared = ridge_regression(
            x_normalized,
            y_values,
            alpha,
        )

        if candidate_r_squared > best_r_squared:
            best_alpha = alpha
            best_r_squared = candidate_r_squared
            best_betas = candidate_betas

    if best_betas is None:
        raise RuntimeError(
            f"{industry_id}: no valid ridge model produced"
        )

    original_scale_betas = best_betas / x_std
    blended_betas = {}

    for index, factor_name in enumerate(factor_names):
        new_beta = float(
            np.clip(original_scale_betas[index], -0.6, 0.6)
        )
        base_beta = BASE_BETAS[industry_id][factor_name]

        blended_beta = (
            0.7 * new_beta
            + 0.3 * base_beta
        )

        blended_betas[factor_name] = round(
            float(blended_beta),
            3,
        )

    print(
        f"[Retrain] industry={industry_id} "
        f"alpha={best_alpha} "
        f"r2={best_r_squared:.3f} "
        f"samples={sample_count}"
    )

    return {
        "betas": blended_betas,
        "r2": round(float(best_r_squared), 3),
        "alpha": best_alpha,
        "samples": sample_count,
        "method": "Ridge real-only inputs; no synthetic fallback",
        "factor_names": factor_names,
        "data_status": "REAL_ONLY",
        "synthetic_data_used": False,
        "fallback_used": False,
    }


def build_retrain_snapshot():
    """전체 산업 재학습 결과 스냅샷을 생성한다."""
    print("=== Retrain v61.6 data-integrity: REAL_ONLY ===")

    date_string = datetime.now().strftime("%Y-%m-%d")

    factor_closes, factor_returns, data_meta = (
        fetch_factor_history(WINDOW_DAYS)
    )

    industry_returns = fetch_industry_returns(WINDOW_DAYS)

    retrained = {}
    r_squared_values = []

    for industry_id in INDUSTRY_PROXY:
        result = train_industry_model(
            factor_returns,
            industry_returns[industry_id],
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
        previous_betas = BASE_BETAS[industry_id]
        new_betas = result["betas"]

        changes = {}

        for factor_name, new_beta in new_betas.items():
            old_beta = previous_betas.get(factor_name, 0.0)
            difference = round(new_beta - old_beta, 3)

            if abs(difference) > 0.02:
                changes[factor_name] = {
                    "old": old_beta,
                    "new": new_beta,
                    "diff": difference,
                }

        if changes:
            beta_changes[industry_id] = changes

    snapshot = {
        "date": date_string,
        "timestamp": datetime.now().isoformat(),
        "version": RETRAIN_VERSION,
        "window": WINDOW_DAYS,
        "method": (
            "Ridge alpha selection [0.1,0.5,1.0,2.0] + "
            "StandardScaler + 70% new / 30% base blending; "
            "REAL_ONLY inputs; no synthetic fallback"
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
            factor_name: len(values)
            for factor_name, values in factor_closes.items()
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
        "retrain_gate": "PASSED",
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
        "retrain_gate": "PASSED",
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
        "retrain_gate": "PASSED",
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
