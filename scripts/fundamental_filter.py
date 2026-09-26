"""
scripts/fundamental_filter.py - 1단계 최적 필터 (v51)
개별 기업 특성 기반 부실주 제거
"""

FILTER_RULES = {
    "elec": {
        "name": "전기전자/반도체",
        "rules": [
            ("ROE", ">", 8.0, "ROE 8% 이상"),
            ("debt_ratio", "<", 200, "부채비율 200% 이하"),
            ("current_ratio", ">", 120, "유동비율 120% 이상"),
            ("operating_margin", ">", 5.0, "영업이익률 5% 이상"),
            ("PER", "range", (0, 50), "PER 0~50"),
        ],
    },
    "auto": {
        "name": "자동차/운수장비",
        "rules": [
            ("ROE", ">", 5.0, "ROE 5% 이상"),
            ("debt_ratio", "<", 250, "부채비율 250% 이하"),
            ("current_ratio", ">", 100, "유동비율 100% 이상"),
            ("operating_margin", ">", 2.0, "영업이익률 2% 이상"),
            ("sales_growth", ">", -20, "매출증가율 -20% 이상"),
        ],
    },
    "chem": {
        "name": "화학/2차전지",
        "rules": [
            ("ROE", ">", 3.0, "ROE 3% 이상"),
            ("debt_ratio", "<", 250, "부채비율 250% 이하"),
            ("operating_margin", ">", 3.0, "영업이익률 3% 이상"),
            ("sales_growth", ">", -20, "매출증가율 -20% 이상"),
            ("PER", "range", (0, 80), "PER 80 이하"),
        ],
    },
    "fin": {
        "name": "금융/증권",
        "rules": [
            ("ROE", ">", 5.0, "ROE 5% 이상"),
            ("PBR", "<", 1.5, "PBR 1.5 이하"),
            ("debt_ratio", "<", 1000, "부채비율 1000% 이하"),
            ("current_ratio", ">", 90, "유동비율 90% 이상"),
        ],
    },
    "bio": {
        "name": "바이오/의약품",
        "rules": [
            ("debt_ratio", "<", 150, "부채비율 150% 이하"),
            ("current_ratio", ">", 150, "유동비율 150% 이상"),
            ("sales_growth", ">", -30, "매출증가율 -30% 이상"),
            ("ROE", ">", -20, "ROE -20% 이상"),
        ],
    },
    "steel": {
        "name": "철강/소재/에너지",
        "rules": [
            ("ROE", ">", 3.0, "ROE 3% 이상"),
            ("debt_ratio", "<", 300, "부채비율 300% 이하"),
            ("operating_margin", ">", 2.0, "영업이익률 2% 이상"),
            ("current_ratio", ">", 90, "유동비율 90% 이상"),
        ],
    },
    "const": {
        "name": "건설/조선/기계",
        "rules": [
            ("ROE", ">", 3.0, "ROE 3% 이상"),
            ("debt_ratio", "<", 300, "부채비율 300% 이하"),
            ("current_ratio", ">", 110, "유동비율 110% 이상"),
            ("operating_margin", ">", 1.0, "영업이익률 1% 이상"),
        ],
    },
    "retail": {
        "name": "유통/IT서비스",
        "rules": [
            ("ROE", ">", 5.0, "ROE 5% 이상"),
            ("PER", "range", (0, 40), "PER 0~40"),
            ("debt_ratio", "<", 200, "부채비율 200% 이하"),
            ("operating_margin", ">", 3.0, "영업이익률 3% 이상"),
            ("PBR", "<", 5.0, "PBR 5 이하"),
        ],
    },
}

COMMON_FILTERS = [
    ("PER", "not_negative", None, "PER 음수 제외"),
    ("PBR", "<", 10, "PBR 10 이하"),
]

def check_rule(value, operator, threshold):
    if value is None:
        return True
    if operator == ">":
        return value > threshold
    elif operator == "<":
        return value < threshold
    elif operator == "range":
        low, high = threshold
        return low <= value <= high
    elif operator == "not_negative":
        return value > 0
    return True

def evaluate_candidate(candidate, industry_id):
    if industry_id not in FILTER_RULES:
        return True, [], {}
    rules = FILTER_RULES[industry_id]["rules"] + COMMON_FILTERS
    failed = []
    details = {}
    for field, op, threshold, desc in rules:
        value = candidate.get(field)
        passed = check_rule(value, op, threshold)
        details[field] = {"value": value, "passed": passed, "desc": desc}
        if not passed:
            failed.append(f"{field} {value} (기준 {op} {threshold}): {desc}")
    return len(failed)==0, failed, details

def filter_candidates(candidates, industry_id):
    passed = []
    rejected = []
    for cand in candidates:
        is_pass, reasons, details = evaluate_candidate(cand, industry_id)
        if is_pass:
            passed.append({**cand, "filter_details": details, "filter_pass": True})
        else:
            rejected.append({**cand, "filter_reasons": reasons, "filter_details": details, "filter_pass": False})
    return passed, rejected
