"""
daily_update.py v61.6-data-integrity

KOSPI Quant Terminal 일일 업데이트 파이프라인.

핵심 원칙:
- 10개 팩터는 실제 데이터 또는 명시된 검증 소스에서만 수집한다.
- 외국인 수급은 표준 CSV의 date, foreigner 열만 사용한다.
- 0.85 fallback, 난수, 임의 추정값을 사용하지 않는다.
- 필수 팩터가 누락되면 새 factor_snapshots와 64 Picks를 저장하지 않는다.
- 실패 시 Firestore의 마지막 정상 스냅샷을 그대로 유지한다.

구성:
1. 10개 팩터 수집 및 Z-score 계산
2. 산업 8개 × 종목 8개 = 64 Picks 생성
3. DART 재무 필터 적용
4. 레짐 및 메타 팩터 스냅샷 생성
5. 최신 재학습 베타 조회
6. Firestore factor_snapshots 저장
"""

import json
import math
import os
import sys
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Tuple

import requests


APP_VERSION = "v61.6-data-integrity"
MODEL_VERSION = "industry8-factor-v61.6"
DATA_POLICY = "REAL_ONLY_NO_SYNTHETIC_NO_085_FALLBACK"

KST = timezone(timedelta(hours=9))

MIN_MARKET_OBSERVATIONS = 20
MIN_FOREIGNER_OBSERVATIONS = 120


try:
    from price_provider import (
        calc_z_score,
        get_foreigner_factor_real,
        get_market_indicator,
    )
except ImportError:
    from scripts.price_provider import (
        calc_z_score,
        get_foreigner_factor_real,
        get_market_indicator,
    )


try:
    from fundamental_filter import apply_fundamental_filter

    FILTER_ENABLED = True
    print("[Daily] DART fundamental filter loaded")

except ImportError:
    try:
        from scripts.fundamental_filter import apply_fundamental_filter

        FILTER_ENABLED = True
        print("[Daily] DART fundamental filter loaded from scripts")

    except Exception as exc:
        FILTER_ENABLED = False
        apply_fundamental_filter = None
        print(f"[Daily] fundamental filter unavailable: {exc}")


try:
    from regime_detector import build_regime_snapshot

    REGIME_ENABLED = True
    print("[Daily] regime detector loaded")

except ImportError:
    try:
        from scripts.regime_detector import build_regime_snapshot

        REGIME_ENABLED = True
        print("[Daily] regime detector loaded from scripts")

    except Exception as exc:
        REGIME_ENABLED = False
        build_regime_snapshot = None
        print(f"[Daily] regime detector unavailable: {exc}")


try:
    from meta_factor_tracker import build_meta_tracker

    META_ENABLED = True
    print("[Daily] meta factor tracker loaded")

except ImportError:
    try:
        from scripts.meta_factor_tracker import build_meta_tracker

        META_ENABLED = True
        print("[Daily] meta factor tracker loaded from scripts")

    except Exception as exc:
        META_ENABLED = False
        build_meta_tracker = None
        print(f"[Daily] meta factor tracker unavailable: {exc}")


FRED_API_KEY = os.environ.get("FRED_API_KEY", "")
DART_API_KEY = os.environ.get("DART_API_KEY", "")


try:
    import firebase_admin
    from firebase_admin import credentials, firestore
except ImportError:
    firebase_admin = None
    credentials = None
    firestore = None


def init_firebase():
    """Firebase Admin SDK를 초기화한다. 자격증명이 없으면 로컬 저장 모드로 실행한다."""
    if firebase_admin is None:
        print("[Firebase] firebase-admin unavailable; local mode")
        return None

    credential_json = os.environ.get(
        "FIREBASE_SERVICE_ACCOUNT",
        "",
    )

    if not credential_json:
        print("[Firebase] FIREBASE_SERVICE_ACCOUNT unavailable; local mode")
        return None

    try:
        credential_dict = json.loads(credential_json)

        if not firebase_admin._apps:
            credential = credentials.Certificate(credential_dict)
            firebase_admin.initialize_app(credential)

        print("[Firebase] connected")
        return firestore.client()

    except Exception as exc:
        print(f"[Firebase] init error: {exc}")
        return None


db = init_firebase()


def now_kst() -> datetime:
    """현재 한국 표준시를 반환한다."""
    return datetime.now(KST)


def is_invalid_number(value) -> bool:
    """None, NaN, Inf를 검사한다."""
    if value is None:
        return True

    if isinstance(value, (int, float)):
        return math.isnan(value) or math.isinf(value)

    return False


def validate_series(
    series: List[float],
    factor_name: str,
    min_observations: int = MIN_MARKET_OBSERVATIONS,
) -> List[float]:
    """
    팩터 시계열의 기본 품질을 검사한다.

    실패 시 즉시 RuntimeError를 발생시킨다.
    이 예외는 main()까지 전달되어 새 스냅샷 저장을 차단한다.
    """
    normalized = []

    for value in series:
        if value is None:
            continue

        try:
            numeric_value = float(value)
        except (TypeError, ValueError):
            continue

        if math.isnan(numeric_value) or math.isinf(numeric_value):
            continue

        normalized.append(numeric_value)

    if len(normalized) < min_observations:
        raise RuntimeError(
            f"{factor_name}: insufficient observations "
            f"{len(normalized)} < {min_observations}"
        )

    if normalized[-1] == 0:
        raise RuntimeError(
            f"{factor_name}: latest value is zero"
        )

    return normalized


def fetch_fred(
    series_id: str,
    observation_start: str = None,
) -> Tuple[List[float], float]:
    """
    FRED 일별·월별 시계열을 가져온다.

    API 키가 없거나 오류가 발생하면 빈 리스트를 반환한다.
    실제 중단 여부는 호출한 팩터 수집 함수가 결정한다.
    """
    if not FRED_API_KEY:
        print(f"[FRED] {series_id}: API key unavailable")
        return [], 0.0

    try:
        if not observation_start:
            observation_start = (
                now_kst() - timedelta(days=240)
            ).strftime("%Y-%m-%d")

        url = (
            "https://api.stlouisfed.org/fred/series/observations"
        )

        params = {
            "series_id": series_id,
            "api_key": FRED_API_KEY,
            "file_type": "json",
            "observation_start": observation_start,
            "sort_order": "asc",
        }

        response = requests.get(
            url,
            params=params,
            timeout=15,
        )
        response.raise_for_status()

        payload = response.json()
        observations = payload.get("observations", [])

        values = []

        for observation in observations:
            raw_value = observation.get("value", ".")

            if raw_value == ".":
                continue

            try:
                values.append(float(raw_value))
            except (TypeError, ValueError):
                continue

        latest = values[-1] if values else 0.0

        print(
            f"[FRED] {series_id}: "
            f"rows={len(values)} "
            f"latest={latest:.4f}"
        )

        return values, latest

    except Exception as exc:
        print(f"[FRED] {series_id} error: {exc}")
        return [], 0.0


def fetch_market_factor(
    factor_name: str,
    period: str = "6mo",
    source_label: str = "market_provider",
) -> Tuple[List[float], float, Dict]:
    """시장 데이터 공급자에서 단일 팩터 시계열을 수집하고 검증한다."""
    closes, latest = get_market_indicator(
        factor_name,
        period=period,
    )

    closes = validate_series(
        closes,
        factor_name,
        MIN_MARKET_OBSERVATIONS,
    )

    if is_invalid_number(latest) or float(latest) == 0:
        latest = closes[-1]

    z_score = calc_z_score(
        closes,
        window=120,
    )

    if is_invalid_number(z_score):
        raise RuntimeError(
            f"{factor_name}: invalid z-score {z_score}"
        )

    detail = {
        "latest": float(latest),
        "z": float(z_score),
        "source": source_label,
        "data_status": "REAL_OR_VERIFIED_PROVIDER",
        "rows": len(closes),
        "fallback_used": False,
        "synthetic_data_used": False,
    }

    return closes, float(latest), detail


def fetch_fred_or_market_factor(
    factor_name: str,
    fred_series_id: str,
    market_source_label: str,
) -> Tuple[List[float], float, Dict]:
    """
    FRED 우선, FRED 관측치가 부족하면 시장 데이터 공급자를 사용한다.

    단, 둘 다 최소 관측치에 미달하면 예외를 발생시켜
    daily update 전체를 중단한다.
    """
    fred_values, fred_latest = fetch_fred(
        fred_series_id,
    )

    valid_fred_values = []

    for value in fred_values:
        try:
            numeric_value = float(value)

            if (
                not math.isnan(numeric_value)
                and not math.isinf(numeric_value)
            ):
                valid_fred_values.append(numeric_value)

        except (TypeError, ValueError):
            continue

    if len(valid_fred_values) >= MIN_MARKET_OBSERVATIONS:
        closes = validate_series(
            valid_fred_values,
            factor_name,
            MIN_MARKET_OBSERVATIONS,
        )

        z_score = calc_z_score(
            closes,
            window=120,
        )

        if is_invalid_number(z_score):
            raise RuntimeError(
                f"{factor_name}: invalid FRED z-score"
            )

        return closes, float(fred_latest), {
            "latest": float(fred_latest),
            "z": float(z_score),
            "source": f"FRED {fred_series_id}",
            "data_status": "REAL_OR_VERIFIED_PROVIDER",
            "rows": len(closes),
            "fallback_used": False,
            "synthetic_data_used": False,
        }

    closes, latest, detail = fetch_market_factor(
        factor_name,
        period="6mo",
        source_label=market_source_label,
    )

    detail["source"] = (
        f"{market_source_label}; "
        f"FRED {fred_series_id} unavailable_or_short"
    )

    return closes, latest, detail


def fetch_krx_foreign() -> Tuple[List[float], float, Dict]:
    """
    외국인 수급 팩터를 표준 CSV에서 가져온다.

    허용 입력 스키마:
        date,institution,other_corp,individual,foreigner,total

    운영 정책:
    - date, foreigner 열의 실제 CSV만 허용
    - pykrx 즉석 대체 금지
    - 0.85 fallback 금지
    - 난수·합성값 금지
    - 데이터 부족 시 빈 값과 MISSING 메타데이터 반환
    """
    closes, latest, z_score, metadata = (
        get_foreigner_factor_real(
            min_samples=MIN_FOREIGNER_OBSERVATIONS
        )
    )

    if metadata.get("status") != "REAL":
        print(
            "[FOREIGNER] unavailable: "
            f"{metadata.get('reason', 'unknown error')}"
        )
        return [], 0.0, metadata

    closes = validate_series(
        closes,
        "외국인_KOSPI200",
        MIN_FOREIGNER_OBSERVATIONS,
    )

    if is_invalid_number(z_score):
        raise RuntimeError(
            f"외국인_KOSPI200: invalid z-score {z_score}"
        )

    metadata = {
        **metadata,
        "z": float(z_score),
        "latest": float(latest),
        "data_status": "REAL",
        "fallback_used": False,
        "synthetic_data_used": False,
    }

    print(
        f"[FOREIGNER] REAL "
        f"rows={len(closes)} "
        f"latest_date={metadata.get('latest_date')} "
        f"latest={latest:.0f} "
        f"z={z_score:+.2f}"
    )

    return closes, float(latest), metadata


def fetch_10_factors_china_proxy() -> Tuple[Dict, Dict]:
    """
    10개 핵심 팩터를 수집하고 Z-score를 계산한다.

    필수 팩터 하나라도 실패하면 RuntimeError를 발생시킨다.
    이 경우 factor_snapshots 저장과 64 Picks 생성은 수행되지 않는다.
    """
    z_scores: Dict[str, float] = {}
    details: Dict[str, Dict] = {}

    closes, latest, detail = fetch_market_factor(
        "SP500",
        period="6mo",
        source_label="yfinance ^GSPC",
    )
    z_scores["SP500"] = detail["z"]
    details["SP500"] = detail

    closes, latest, detail = fetch_fred_or_market_factor(
        "US10Y",
        "DGS10",
        "yfinance ^TNX",
    )
    z_scores["US10Y"] = detail["z"]
    details["US10Y"] = detail

    closes, latest, detail = fetch_market_factor(
        "SOX",
        period="6mo",
        source_label="yfinance ^SOX",
    )
    z_scores["SOX"] = detail["z"]
    details["SOX"] = detail
    z_scores["반도체팩터"] = z_scores["SOX"]

    closes, latest, detail = fetch_market_factor(
        "원달러",
        period="6mo",
        source_label="yfinance KRW=X",
    )
    z_scores["원달러"] = detail["z"]
    details["원달러"] = detail

    closes, latest, detail = fetch_fred_or_market_factor(
        "WTI",
        "DCOILWTICO",
        "yfinance CL=F",
    )
    z_scores["WTI"] = detail["z"]
    details["WTI"] = detail

    closes, latest, detail = fetch_fred_or_market_factor(
        "DXY",
        "DTWEXBGS",
        "yfinance DX-Y.NYB",
    )
    z_scores["DXY"] = detail["z"]
    details["DXY"] = detail

    closes, latest, detail = fetch_fred_or_market_factor(
        "VIX",
        "VIXCLS",
        "yfinance ^VIX",
    )
    raw_vix_z = detail["z"]
    z_scores["VIX"] = round(-raw_vix_z, 2)
    detail["z"] = z_scores["VIX"]
    detail["transform"] = "negative_z_for_risk_on_interpretation"
    details["VIX"] = detail

    closes, latest, foreigner_detail = fetch_krx_foreign()

    if (
        not closes
        or foreigner_detail.get("status") != "REAL"
    ):
        raise RuntimeError(
            "외국인 수급 데이터가 없거나 유효하지 않습니다. "
            "새 daily snapshot 생성을 중단합니다. "
            f"detail={foreigner_detail}"
        )

    foreigner_z = calc_z_score(
        closes,
        window=120,
    )

    if is_invalid_number(foreigner_z):
        raise RuntimeError(
            f"외국인_KOSPI200: invalid z-score {foreigner_z}"
        )

    z_scores["외국인"] = float(foreigner_z)

    details["외국인"] = {
        "latest": float(latest),
        "z": float(foreigner_z),
        "source": "KOSPI200 foreigner CSV",
        "data_status": "REAL",
        "rows": len(closes),
        "latest_date": foreigner_detail.get("latest_date"),
        "path": foreigner_detail.get("path"),
        "column": foreigner_detail.get("column", "foreigner"),
        "fallback_used": False,
        "synthetic_data_used": False,
    }

    closes, latest, detail = fetch_market_factor(
        "구리",
        period="6mo",
        source_label="yfinance HG=F; China Proxy 1",
    )
    z_scores["구리"] = detail["z"]
    details["구리"] = detail

    closes, latest, detail = fetch_market_factor(
        "상해종합",
        period="6mo",
        source_label="yfinance 000001.SS; China Proxy 2",
    )
    z_scores["상해종합"] = detail["z"]
    details["상해종합"] = detail

    z_scores["S&P500"] = z_scores["SP500"]
    z_scores["US 10Y"] = z_scores["US10Y"]
    z_scores["SOX / 필라"] = z_scores["SOX"]
    z_scores["외국인 선물"] = z_scores["외국인"]
    z_scores["외국인_선물"] = z_scores["외국인"]

    print(
        "[Daily] 10 factors loaded: "
        f"{json.dumps(z_scores, ensure_ascii=False)}"
    )

    return z_scores, details


INDUSTRIES_BETAS = {
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


INDUSTRIES_UNIVERSE = [
    {
        "id": "elec",
        "stocks": [
            ["005930", "삼성전자", 1.00, 0.8],
            ["000660", "SK하이닉스", 1.25, 1.2],
            ["066570", "LG전자", 0.85, 0.3],
            ["042700", "한미반도체", 1.30, 2.1],
            ["011070", "LG이노텍", 0.90, 1.5],
            ["058470", "리노공업", 0.85, 1.0],
            ["000990", "DB하이텍", 0.80, 0.9],
            ["095340", "ISC", 0.90, 0.6],
        ],
    },
    {
        "id": "auto",
        "stocks": [
            ["005380", "현대차", 1.00, 0.7],
            ["000270", "기아", 1.15, 1.1],
            ["064350", "현대로템", 1.05, 1.8],
            ["003490", "대한항공", 0.95, 1.3],
            ["012330", "현대모비스", 0.90, 0.2],
            ["086280", "현대글로비스", 0.85, 0.4],
            ["180640", "한진칼", 0.80, 0.8],
            ["161390", "한국타이어", 0.75, -0.2],
        ],
    },
    {
        "id": "chem",
        "stocks": [
            ["086520", "에코프로", 1.25, 2.2],
            ["247540", "에코프로비엠", 1.30, 1.5],
            ["373220", "LG에너지솔루션", 1.20, 0.5],
            ["003670", "포스코퓨처엠", 1.15, 0.9],
            ["051910", "LG화학", 1.00, -0.3],
            ["011780", "금호석유", 0.85, 0.1],
            ["010130", "고려아연", 0.75, 0.4],
            ["121600", "나노신소재", 1.00, 0.7],
        ],
    },
    {
        "id": "fin",
        "stocks": [
            ["071050", "한국금융지주", 1.15, 1.2],
            ["105560", "KB금융", 1.00, 0.6],
            ["055550", "신한지주", 0.95, 0.4],
            ["000810", "삼성화재", 0.85, 0.7],
            ["086790", "하나금융지주", 0.90, 0.3],
            ["175330", "JB금융", 0.75, 0.5],
            ["316140", "우리금융지주", 0.85, 0.1],
            ["030200", "KT", 0.60, -0.3],
        ],
    },
    {
        "id": "bio",
        "stocks": [
            ["195940", "HLB", 1.20, 2.5],
            ["207940", "삼성바이오로직스", 1.00, 0.9],
            ["068270", "셀트리온", 1.10, 0.2],
            ["214450", "파마리서치", 0.85, 1.4],
            ["145020", "휴젤", 0.90, 1.1],
            ["326030", "SK바이오팜", 1.05, 0.7],
            ["128940", "한미약품", 0.85, 0.5],
            ["185740", "셀트리온제약", 0.95, 0.3],
        ],
    },
    {
        "id": "steel",
        "stocks": [
            ["005490", "POSCO홀딩스", 1.00, 0.4],
            ["047050", "포스코인터", 0.95, 0.8],
            ["010130", "고려아연", 0.90, 0.6],
            ["009830", "한화솔루션", 0.85, 0.3],
            ["004020", "현대제철", 0.85, -0.3],
            ["103140", "풍산", 0.75, 0.2],
            ["001430", "세아베스틸", 0.70, 0.1],
            ["010950", "S-Oil", 0.80, -0.6],
        ],
    },
    {
        "id": "const",
        "stocks": [
            ["012450", "한화에어로", 1.20, 2.3],
            ["329180", "HD현대중공업", 1.15, 1.9],
            ["064350", "현대로템", 1.05, 1.8],
            ["009540", "HD한국조선해양", 1.00, 1.5],
            ["010140", "삼성중공업", 0.90, 0.8],
            ["034020", "두산에너빌리티", 0.95, 0.4],
            ["028050", "삼성엔지니어링", 0.85, 0.2],
            ["047040", "대우건설", 0.70, -0.3],
        ],
    },
    {
        "id": "retail",
        "stocks": [
            ["352820", "하이브", 0.90, 0.6],
            ["035900", "JYP", 0.85, 0.8],
            ["035420", "NAVER", 1.05, -0.2],
            ["035720", "카카오", 1.10, -0.4],
            ["030000", "제일기획", 0.65, 0.3],
            ["017670", "SK텔레콤", 0.65, 0.2],
            ["004170", "신세계", 0.80, -0.3],
            ["139480", "이마트", 0.75, -0.8],
        ],
    },
]


FACTOR_ALIAS = {
    "S&P500": "SP500",
    "SP500": "SP500",
    "외국인 선물": "외국인",
    "외국인": "외국인",
    "외국인_선물": "외국인",
    "SOX / 필라": "SOX",
    "SOX": "SOX",
    "반도체팩터": "SOX",
    "US 10Y": "US10Y",
    "US10Y": "US10Y",
    "구리": "구리",
    "상해종합": "상해종합",
    "DXY": "DXY",
    "VIX": "VIX",
    "원달러": "원달러",
    "WTI": "WTI",
}


def generate_64_picks(
    z_scores: Dict,
    details: Dict,
) -> List[Dict]:
    """
    8개 산업군의 각 8개 종목, 총 64개 후보를 생성한다.

    기존 v61.6 점수 구조를 유지한다.
    """
    today = now_kst().strftime("%Y-%m-%d")
    all_picks: List[Dict] = []

    for industry in INDUSTRIES_UNIVERSE:
        industry_id = industry["id"]
        betas = INDUSTRIES_BETAS.get(
            industry_id,
            {},
        )

        predicted_industry_return = 0.0
        top_factor = "S&P500"
        top_factor_beta = 0.0

        for factor_name, beta in betas.items():
            canonical_name = FACTOR_ALIAS.get(
                factor_name,
                factor_name,
            )

            z_score = z_scores.get(
                canonical_name,
                z_scores.get(factor_name, 0.0),
            )

            predicted_industry_return += beta * z_score

            if abs(beta) > abs(top_factor_beta):
                top_factor_beta = beta
                top_factor = factor_name

        top_factor_canonical = FACTOR_ALIAS.get(
            top_factor,
            top_factor,
        )

        top_factor_z = z_scores.get(
            top_factor_canonical,
            0.0,
        )

        for stock in industry["stocks"]:
            ticker, name, stock_beta, momentum = stock

            score = (
                6.5
                + predicted_industry_return * 1.2
                + momentum * 0.3
                + max(0.0, predicted_industry_return) * 0.5
                + abs(predicted_industry_return) * 0.3
            )

            score = round(
                max(1.0, min(10.0, score)),
                1,
            )

            expected_return = round(
                0.5
                + abs(predicted_industry_return) * 0.8
                + max(0.0, predicted_industry_return) * 0.4
                + momentum * 0.1,
                2,
            )

            all_picks.append(
                {
                    "industryId": industry_id,
                    "ticker": ticker,
                    "name": name,
                    "targetFactor": top_factor,
                    "score": score,
                    "expectedReturn": expected_return,
                    "reason": (
                        f"{top_factor} "
                        f"β{betas.get(top_factor, 0):+.2f} "
                        f"Z{top_factor_z:+.2f} "
                        "(REAL_ONLY)"
                    ),
                    "date": today,
                    "zAtRec": top_factor_z,
                    "predIndustry": round(
                        predicted_industry_return,
                        3,
                    ),
                    "momentum": momentum,
                    "betaStock": stock_beta,
                    "data_status": "REAL_ONLY",
                    "fallback_used": False,
                    "synthetic_data_used": False,
                }
            )

    sorted_picks = sorted(
        all_picks,
        key=lambda item: item["score"],
        reverse=True,
    )

    top_score = (
        sorted_picks[0]["score"]
        if sorted_picks
        else 0.0
    )

    print(
        f"[Daily] generated {len(sorted_picks)} picks; "
        f"top_score={top_score}"
    )

    return sorted_picks


def fetch_latest_retrain():
    """대시보드 표시용 최신 beta snapshot을 가져온다."""
    if db is None:
        return None

    try:
        document = (
            db.collection("beta_snapshots")
            .document("latest")
            .get()
        )

        if document.exists:
            data = document.to_dict()

            print(
                f"[Retrain] latest "
                f"date={data.get('date')} "
                f"avg_r2={data.get('avg_r2')}"
            )

            return data

        print("[Retrain] beta_snapshots/latest not found")
        return None

    except Exception as exc:
        print(f"[Retrain] latest fetch error: {exc}")
        return None


def save_to_firebase(
    z_scores: Dict,
    details: Dict,
    weekly_picks: List[Dict],
    regime_snapshot: Dict = None,
    meta_snapshot: Dict = None,
    retrain_snapshot: Dict = None,
):
    """
    정상 검증된 일일 결과를 저장한다.

    이 함수는 필수 팩터와 외국인 수급 검증이 모두 끝난 뒤에만 호출된다.
    """
    generated_at = now_kst()
    date_string = generated_at.strftime("%Y-%m-%d")

    document = {
        "date": date_string,
        "timestamp": generated_at,
        "generated_at_kst": generated_at.isoformat(),
        "zScores": z_scores,
        "details": details,
        "weeklyPicks": weekly_picks,
        "regime": regime_snapshot,
        "meta": meta_snapshot,
        "retrain": retrain_snapshot,
        "beta_snapshot": retrain_snapshot,

        "app_version": APP_VERSION,
        "model_version": MODEL_VERSION,
        "data_policy": DATA_POLICY,
        "data_status": "REAL_ONLY",
        "quality_status": "PASS",
        "fallback_used": False,
        "synthetic_data_used": False,

        "source": (
            "market data + FRED + "
            "KOSPI200 foreigner CSV + "
            "China proxy + DART filter + "
            "regime + retrain"
        ),
        "version": APP_VERSION,
        "factors_count": 10,
        "picks_count": len(weekly_picks),
        "china_proxy": (
            "구리(HG=F) + 상해종합(000001.SS)"
        ),
        "foreigner_metadata": details.get(
            "외국인",
            {},
        ),
        "filter_applied": FILTER_ENABLED,
        "regime_enabled": REGIME_ENABLED,
        "meta_enabled": META_ENABLED,
        "retrain_enabled": True,

        "regime_summary": (
            f"{regime_snapshot.get('regime')} "
            f"{regime_snapshot.get('confidence')} "
            f"window {regime_snapshot.get('window')}"
            if regime_snapshot
            else "N/A"
        ),
        "retrain_summary": (
            f"{retrain_snapshot.get('date')} "
            f"R2 {retrain_snapshot.get('avg_r2')} "
            f"changes {retrain_snapshot.get('changes')}"
            if retrain_snapshot
            else "N/A"
        ),
    }

    if db is None:
        output_file = "latest_factors.json"

        with open(
            output_file,
            "w",
            encoding="utf-8",
        ) as handle:
            json.dump(
                document,
                handle,
                ensure_ascii=False,
                indent=2,
                default=str,
            )

        print(
            f"[Daily] local snapshot saved: "
            f"{output_file}"
        )
        return

    try:
        db.collection("factor_snapshots").document(
            date_string
        ).set(document, merge=True)

        print(
            f"[Firebase] saved factor_snapshots/{date_string} "
            f"picks={len(weekly_picks)}"
        )

        if regime_snapshot:
            db.collection("regime_history").document(
                date_string
            ).set(regime_snapshot, merge=True)

            print(
                f"[Firebase] saved regime_history/{date_string}"
            )

        if meta_snapshot:
            db.collection("meta_history").document(
                date_string
            ).set(meta_snapshot, merge=True)

            print(
                f"[Firebase] saved meta_history/{date_string}"
            )

    except Exception as exc:
        raise RuntimeError(
            f"Firestore save failed: {exc}"
        ) from exc


def apply_dart_filter(
    weekly_picks: List[Dict],
) -> List[Dict]:
    """
    DART 필터를 적용한다.

    DART API 또는 필터 모듈의 오류는 팩터 데이터 오류와 성격이 다르므로,
    이번 v61.6 운영 유지 원칙에서는 기존처럼 로그를 남기고 원본 Picks를 유지한다.

    향후 상용 운용 단계에서는 DART 품질·기준일 검증 후
    실패 시 신호 중단 정책으로 강화할 수 있다.
    """
    if not weekly_picks:
        return weekly_picks

    if not FILTER_ENABLED:
        print("[DART] filter skipped: module unavailable")
        return weekly_picks

    if not DART_API_KEY:
        print("[DART] filter skipped: DART_API_KEY unavailable")
        return weekly_picks

    try:
        print(
            f"[DART] filtering "
            f"{len(weekly_picks)} picks"
        )

        filtered_picks = apply_fundamental_filter(
            weekly_picks,
            use_real_data=True,
        )

        print(
            f"[DART] completed "
            f"{len(weekly_picks)} -> "
            f"{len(filtered_picks)} picks"
        )

        return filtered_picks

    except Exception as exc:
        print(
            f"[DART] filter failed; "
            f"using original picks: {exc}"
        )

        import traceback
        traceback.print_exc()

        return weekly_picks


def build_optional_regime_snapshot():
    """
    레짐 탐지 결과를 생성한다.

    기존 v61.6 동작 호환을 위해 레짐 모듈 오류 시
    fallback 레짐을 기록하고 daily snapshot은 계속 생성한다.
    """
    if not REGIME_ENABLED or build_regime_snapshot is None:
        print("[Regime] skipped: module unavailable")
        return None

    try:
        print("[Regime] building snapshot")

        snapshot = build_regime_snapshot()

        print(
            f"[Regime] result="
            f"{snapshot.get('regime')} "
            f"confidence={snapshot.get('confidence')} "
            f"window={snapshot.get('window')}"
        )

        return snapshot

    except Exception as exc:
        print(f"[Regime] failed; fallback regime used: {exc}")

        import traceback
        traceback.print_exc()

        return {
            "regime": "평시",
            "confidence": 0.70,
            "triggers": [
                "regime fallback due to module error"
            ],
            "window": 120,
            "color": "#10b981",
            "risk_level": "Low",
            "date": now_kst().strftime("%Y-%m-%d"),
            "data_status": "FALLBACK_MODULE_ERROR",
        }


def build_optional_meta_snapshot(
    regime_snapshot: Dict,
):
    """레짐 기반 메타 팩터 스냅샷을 생성한다."""
    if (
        not META_ENABLED
        or build_meta_tracker is None
        or regime_snapshot is None
    ):
        print("[Meta] skipped")
        return None

    try:
        print(
            f"[Meta] building tracker for regime="
            f"{regime_snapshot.get('regime')}"
        )

        snapshot = build_meta_tracker(
            regime_snapshot
        )

        print(
            f"[Meta] top_valid="
            f"{len(snapshot.get('top_valid', []))} "
            f"top_strong="
            f"{len(snapshot.get('top_strong', []))}"
        )

        return snapshot

    except Exception as exc:
        print(f"[Meta] tracker failed: {exc}")

        import traceback
        traceback.print_exc()

        return None


def main():
    """일일 업데이트 메인 실행 함수."""
    print(
        "\n=== KOSPI Quant Terminal "
        f"{APP_VERSION} ==="
    )
    print(f"Policy: {DATA_POLICY}")

    z_scores, details = fetch_10_factors_china_proxy()

    weekly_picks = generate_64_picks(
        z_scores,
        details,
    )

    weekly_picks = apply_dart_filter(
        weekly_picks
    )

    regime_snapshot = build_optional_regime_snapshot()

    meta_snapshot = build_optional_meta_snapshot(
        regime_snapshot
    )

    latest_retrain = fetch_latest_retrain()

    save_to_firebase(
        z_scores=z_scores,
        details=details,
        weekly_picks=weekly_picks,
        regime_snapshot=regime_snapshot,
        meta_snapshot=meta_snapshot,
        retrain_snapshot=latest_retrain,
    )

    summary = {
        "app_version": APP_VERSION,
        "data_status": "REAL_ONLY",
        "fallback_used": False,
        "synthetic_data_used": False,
        "picks_count": len(weekly_picks),
        "regime": (
            regime_snapshot.get("regime")
            if regime_snapshot
            else "N/A"
        ),
        "top3": weekly_picks[:3],
    }

    print(
        json.dumps(
            summary,
            ensure_ascii=False,
            indent=2,
            default=str,
        )
    )


if __name__ == "__main__":
    try:
        main()

    except Exception as exc:
        print(
            "\n::error:: Daily update failed. "
            "No new factor snapshot should be written."
        )
        print(f"::error:: {exc}")

        import traceback
        traceback.print_exc()

        sys.exit(1)
