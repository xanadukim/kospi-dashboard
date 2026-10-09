"""
data_quality_check_v60.py v61.6-data-integrity

목적:
- 10개 핵심 팩터의 최소 데이터 품질을 검사한다.
- 외국인 수급 데이터의 0.85 fallback, 난수, 임의 대체를 허용하지 않는다.
- 품질 기준 미달 시 daily_update.py 실행 전에 workflow를 실패 처리한다.
- 마지막 정상 factor_snapshots는 유지되고 새 Picks는 생성되지 않는다.
"""

import json
import math
import os
import sys
from datetime import datetime, timedelta, timezone

KST = timezone(timedelta(hours=9))
TODAY = datetime.now(KST).strftime("%Y-%m-%d")

MIN_FACTOR_OBSERVATIONS = 20
MIN_FOREIGNER_OBSERVATIONS = 120
QC_VERSION = "v61.6-data-integrity"

try:
    from price_provider import (
        FACTOR_TICKERS,
        calc_z_score,
        get_foreigner_factor_real,
        get_market_indicator,
    )
except ImportError:
    from scripts.price_provider import (
        FACTOR_TICKERS,
        calc_z_score,
        get_foreigner_factor_real,
        get_market_indicator,
    )

try:
    import firebase_admin
    from firebase_admin import credentials, firestore
except ImportError:
    firebase_admin = None
    credentials = None
    firestore = None


def init_firebase():
    """가능하면 Firestore에 QC 결과를 기록한다."""
    if firebase_admin is None:
        print("[QC] firebase-admin unavailable; local QC only")
        return None

    credential_json = os.environ.get("FIREBASE_SERVICE_ACCOUNT", "")

    if not credential_json:
        print("[QC] FIREBASE_SERVICE_ACCOUNT unavailable; local QC only")
        return None

    try:
        credential_dict = json.loads(credential_json)

        if not firebase_admin._apps:
            credential = credentials.Certificate(credential_dict)
            firebase_admin.initialize_app(credential)

        print("[QC] Firebase connected")
        return firestore.client()

    except Exception as exc:
        print(f"[QC] Firebase init failed: {exc}")
        return None


db = init_firebase()


def is_invalid_number(value) -> bool:
    """None, NaN, Inf를 검사한다."""
    if value is None:
        return True

    if isinstance(value, (int, float)):
        return math.isnan(value) or math.isinf(value)

    return False


def check_market_factor(
    factor_name: str,
    period: str = "6mo",
) -> dict:
    """시장 데이터 기반 팩터의 관측치·최신값·Z-score를 검사한다."""
    try:
        closes, latest = get_market_indicator(
            factor_name,
            period=period,
        )

        closes = [
            float(value)
            for value in closes
            if value is not None
        ]

        if len(closes) < MIN_FACTOR_OBSERVATIONS:
            return {
                "name": factor_name,
                "status": "FAIL",
                "reason": (
                    f"insufficient observations: "
                    f"{len(closes)} < {MIN_FACTOR_OBSERVATIONS}"
                ),
                "closes_len": len(closes),
                "latest": latest,
                "z": None,
            }

        if is_invalid_number(latest) or float(latest) == 0:
            return {
                "name": factor_name,
                "status": "FAIL",
                "reason": f"invalid latest value: {latest}",
                "closes_len": len(closes),
                "latest": latest,
                "z": None,
            }

        z_score = calc_z_score(closes, window=120)

        if is_invalid_number(z_score):
            return {
                "name": factor_name,
                "status": "FAIL",
                "reason": f"invalid z-score: {z_score}",
                "closes_len": len(closes),
                "latest": latest,
                "z": z_score,
            }

        return {
            "name": factor_name,
            "status": "OK",
            "reason": "",
            "closes_len": len(closes),
            "latest": float(latest),
            "z": float(z_score),
            "data_status": "REAL_OR_VERIFIED_PROVIDER",
        }

    except Exception as exc:
        return {
            "name": factor_name,
            "status": "FAIL",
            "reason": f"exception: {exc}",
            "closes_len": 0,
            "latest": None,
            "z": None,
        }


def check_foreigner_factor() -> dict:
    """
    외국인 수급은 표준 CSV의 date, foreigner 열에서만 읽는다.

    다음 상태는 모두 FAIL:
    - CSV 없음
    - foreigner 열 없음
    - 관측치 120개 미만
    - 최신값 0
    - 0.85 fallback 또는 임의 대체
    """
    try:
        closes, latest, z_score, metadata = (
            get_foreigner_factor_real(
                min_samples=MIN_FOREIGNER_OBSERVATIONS
            )
        )

        if metadata.get("status") != "REAL":
            return {
                "name": "외국인_KOSPI200",
                "status": "FAIL",
                "reason": metadata.get(
                    "reason",
                    "foreigner source is unavailable",
                ),
                "closes_len": len(closes),
                "latest": latest,
                "z": z_score,
                "data_status": metadata.get(
                    "status",
                    "MISSING",
                ),
                "source": metadata.get("source"),
                "is_fallback": False,
                "synthetic_data_used": False,
            }

        if len(closes) < MIN_FOREIGNER_OBSERVATIONS:
            return {
                "name": "외국인_KOSPI200",
                "status": "FAIL",
                "reason": (
                    f"insufficient foreigner observations: "
                    f"{len(closes)} < "
                    f"{MIN_FOREIGNER_OBSERVATIONS}"
                ),
                "closes_len": len(closes),
                "latest": latest,
                "z": z_score,
                "data_status": "MISSING",
                "source": metadata.get("source"),
                "is_fallback": False,
                "synthetic_data_used": False,
            }

        if is_invalid_number(latest) or float(latest) == 0:
            return {
                "name": "외국인_KOSPI200",
                "status": "FAIL",
                "reason": f"invalid latest foreigner value: {latest}",
                "closes_len": len(closes),
                "latest": latest,
                "z": z_score,
                "data_status": "INVALID",
                "source": metadata.get("source"),
                "is_fallback": False,
                "synthetic_data_used": False,
            }

        return {
            "name": "외국인_KOSPI200",
            "status": "OK",
            "reason": "",
            "closes_len": len(closes),
            "latest": float(latest),
            "z": float(z_score),
            "data_status": "REAL",
            "source": metadata.get("source"),
            "path": metadata.get("path"),
            "column": metadata.get("column"),
            "latest_date": metadata.get("latest_date"),
            "is_fallback": False,
            "synthetic_data_used": False,
        }

    except Exception as exc:
        return {
            "name": "외국인_KOSPI200",
            "status": "FAIL",
            "reason": f"exception: {exc}",
            "closes_len": 0,
            "latest": None,
            "z": None,
            "data_status": "MISSING",
            "is_fallback": False,
            "synthetic_data_used": False,
        }


def check_latest_firestore_snapshot() -> list:
    """최근 factor_snapshots에 NaN, fallback 메타데이터가 있는지 점검한다."""
    if db is None:
        return [
            {
                "name": "firebase_latest_snapshot",
                "status": "SKIP",
                "reason": "Firestore unavailable in local QC",
            }
        ]

    checks = []

    try:
        documents = list(
            db.collection("factor_snapshots")
            .order_by(
                "date",
                direction=firestore.Query.DESCENDING,
            )
            .limit(1)
            .stream()
        )

        if not documents:
            return [
                {
                    "name": "firebase_latest_snapshot",
                    "status": "WARN",
                    "reason": "no factor_snapshots found",
                }
            ]

        latest_snapshot = documents[0].to_dict()
        z_scores = latest_snapshot.get("zScores", {})

        for factor_name, z_score in z_scores.items():
            if is_invalid_number(z_score):
                checks.append(
                    {
                        "name": f"firebase_z_{factor_name}",
                        "status": "FAIL",
                        "reason": f"invalid z-score: {z_score}",
                    }
                )

        if latest_snapshot.get("synthetic_data_used") is True:
            checks.append(
                {
                    "name": "firebase_synthetic_data",
                    "status": "FAIL",
                    "reason": "latest snapshot indicates synthetic data",
                }
            )

        if latest_snapshot.get("fallback_used") is True:
            checks.append(
                {
                    "name": "firebase_fallback_data",
                    "status": "FAIL",
                    "reason": "latest snapshot indicates fallback data",
                }
            )

        if not checks:
            checks.append(
                {
                    "name": "firebase_latest_snapshot",
                    "status": "OK",
                    "reason": "",
                    "date": latest_snapshot.get("date"),
                }
            )

        return checks

    except Exception as exc:
        return [
            {
                "name": "firebase_latest_snapshot",
                "status": "WARN",
                "reason": f"Firestore read failed: {exc}",
            }
        ]


def save_qc_log(
    results: list,
    firebase_checks: list,
    fail_count: int,
    warn_count: int,
):
    """QC 결과를 Firestore에 저장한다."""
    if db is None:
        return

    health_score = max(
        0,
        min(
            100,
            100 - fail_count * 20 - warn_count * 5,
        ),
    )

    log_document = {
        "date": TODAY,
        "timestamp": datetime.now(KST),
        "version": QC_VERSION,
        "fail_count": fail_count,
        "warn_count": warn_count,
        "health_score": health_score,
        "is_fail": fail_count > 0,
        "results": results + firebase_checks,
        "data_policy": (
            "REAL_ONLY_NO_SYNTHETIC_NO_085_FALLBACK"
        ),
        "synthetic_data_allowed": False,
        "foreigner_status": next(
            (
                result.get("data_status")
                for result in results
                if result["name"] == "외국인_KOSPI200"
            ),
            "UNKNOWN",
        ),
        "createdAt": firestore.SERVER_TIMESTAMP,
    }

    db.collection("data_quality_logs").document(
        TODAY
    ).set(log_document, merge=True)

    print(
        f"[QC] saved data_quality_logs/{TODAY} "
        f"health={health_score}"
    )


def main():
    print(
        f"\n=== KOSPI Quant QC "
        f"{QC_VERSION} "
        f"{TODAY} ==="
    )
    print(
        "Policy: REAL ONLY; "
        "no synthetic data; "
        "no 0.85 foreigner fallback"
    )

    factor_definitions = [
        ("SP500", "6mo"),
        ("US10Y", "6mo"),
        ("SOX", "6mo"),
        ("원달러", "6mo"),
        ("WTI", "6mo"),
        ("DXY", "6mo"),
        ("VIX", "6mo"),
        ("구리", "6mo"),
        ("상해종합", "6mo"),
    ]

    results = []

    for factor_name, period in factor_definitions:
        result = check_market_factor(
            factor_name,
            period,
        )
        results.append(result)

    results.append(check_foreigner_factor())

    fail_count = sum(
        1
        for result in results
        if result["status"] == "FAIL"
    )

    warn_count = sum(
        1
        for result in results
        if result["status"] == "WARN"
    )

    for result in results:
        status = result["status"]
        name = result["name"]

        if status == "FAIL":
            print(
                f"::error:: [FAIL] {name}: "
                f"{result.get('reason', '')}"
            )
        elif status == "WARN":
            print(
                f"::warning:: [WARN] {name}: "
                f"{result.get('reason', '')}"
            )
        else:
            print(
                f"[OK] {name}: "
                f"rows={result.get('closes_len', '')} "
                f"latest={result.get('latest', '')} "
                f"z={result.get('z', '')}"
            )

    firebase_checks = check_latest_firestore_snapshot()

    for check in firebase_checks:
        if check["status"] == "FAIL":
            fail_count += 1
            print(
                f"::error:: [FAIL] {check['name']}: "
                f"{check.get('reason', '')}"
            )
        elif check["status"] == "WARN":
            warn_count += 1
            print(
                f"::warning:: [WARN] {check['name']}: "
                f"{check.get('reason', '')}"
            )

    save_qc_log(
        results,
        firebase_checks,
        fail_count,
        warn_count,
    )

    print("\n=== QC Summary ===")
    print(
        f"FAIL={fail_count} "
        f"WARN={warn_count} "
        f"Policy=REAL_ONLY"
    )

    if fail_count > 0:
        print(
            "::error:: QC failed. "
            "Daily update must not create a new snapshot."
        )
        sys.exit(1)

    print("[QC] PASS")
    sys.exit(0)


if __name__ == "__main__":
    main()
