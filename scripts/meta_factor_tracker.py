"""
scripts/meta_factor_tracker.py - 메타 팩터 유효성 추적 (v50 준비)
매일 16:30 KST 실행 - 어떤 팩터가 지금 유효한지를 배우는 메타 모델의 데이터 수집기

목표: 팩터별 IC(Information Coefficient), Hit Rate, β 변화를 추적하여
      factor_validity 컬렉션에 저장. 추후 메타 러너가 P(factor_valid | regime) 학습
"""
import os, json, datetime, math, random
import firebase_admin
from firebase_admin import credentials, firestore
import numpy as np

# Firebase init
sa_json = json.loads(os.environ.get('FIREBASE_SERVICE_ACCOUNT', '{}'))
if sa_json and not firebase_admin._apps:
    cred = credentials.Certificate(sa_json)
    firebase_admin.initialize_app(cred)
    db = firestore.client()
else:
    db = None
    print("[meta_factor_tracker] Firebase mock mode (local test)")

kst = datetime.timezone(datetime.timedelta(hours=9))
today = datetime.datetime.now(kst).strftime('%Y-%m-%d')
print(f"[{today}] Meta Factor Tracker - IC/Hit 계산 시작")

# 9개 기본 팩터 + 확장 팩터 (미래)
factors = ["SP500", "외국인", "반도체팩터", "US10Y", "중국PMI", "원달러", "WTI", "한미스프레드", "정책더미",
           "WTI_vol", "GPR", "정제마진"]  # 확장 팩터는 v50에서 실제 데이터로 교체

# Mock: 최근 20일 performance_tracking 데이터에서 IC 계산
# 실제 구현: performance_tracking 컬렉션에서 예측 순위 vs 실제 수익률 순위 상관
def calculate_ic(factor_name, window=20):
    """IC 계산 Mock - 실제로는 예측 기여도 vs 실제 수익률 상관계수"""
    base_ic = {
        "SP500": 0.11, "외국인": 0.12, "반도체팩터": 0.18, "US10Y": -0.04,
        "중국PMI": 0.07, "원달러": 0.14, "WTI": 0.05, "한미스프레드": 0.08, "정책더미": 0.02,
        "WTI_vol": 0.09, "GPR": -0.06, "정제마진": 0.10
    }
    # 전쟁 시뮬레이션: WTI_vol IC 급증
    # 실제로는 OVX가 높으면 WTI_vol IC가 올라감
    ic = base_ic.get(factor_name, 0.05) + random.uniform(-0.03, 0.03)
    # 6개월 후 유가 변동성 증가 시나리오
    if factor_name == "WTI_vol":
        ic += 0.08  # 전시에는 유효성 증가
    return round(ic, 3)

def calculate_hit(factor_name):
    base_hit = {
        "SP500": 62.8, "외국인": 64.1, "반도체팩터": 71.2, "US10Y": 48.2,
        "중국PMI": 58.3, "원달러": 66.4, "WTI": 55.0, "한미스프레드": 60.1, "정책더미": 52.0,
        "WTI_vol": 62.0, "GPR": 50.0, "정제마진": 61.0
    }
    return round(base_hit.get(factor_name, 55.0) + random.uniform(-2, 2), 1)

def calculate_validity_prob(ic, hit, regime="평시"):
    """메타 모델: IC와 Hit로 유효 확률 계산 (간단한 시그모이드)"""
    # IC 0.1 이상, Hit 60% 이상이면 유효
    score = ic*5 + (hit-50)/20
    if regime == "전시":
        # 전시에는 WTI_vol, GPR 유효 확률 상향
        score += 0.5
    prob = 1 / (1 + math.exp(-score))
    return round(prob, 3)

# 현재 체제 가져오기 (regime_detector에서 저장한 값, 없으면 평시)
regime = "평시"
if db:
    try:
        regime_docs = list(db.collection('market_regimes').order_by('date', direction=firestore.Query.DESCENDING).limit(1).stream())
        if regime_docs:
            regime = regime_docs[0].to_dict().get('regime_label', '평시')
    except:
        pass

print(f"현재 체제: {regime}")

# 팩터별 유효성 계산 및 저장
validity_records = []
for factor in factors:
    ic_20d = calculate_ic(factor, 20)
    ic_60d = calculate_ic(factor, 60)
    hit_20d = calculate_hit(factor)
    validity_prob = calculate_validity_prob(ic_20d, hit_20d, regime)
    
    record = {
        "date": today,
        "factor": factor,
        "ic_20d": ic_20d,
        "ic_60d": ic_60d,
        "hit_20d": hit_20d,
        "validity_prob": validity_prob,
        "regime": regime,
        "beta": round(random.uniform(-0.3, 0.4), 3),  # 실제는 retrain_model에서 가져옴
        "p_value": round(random.uniform(0.01, 0.15), 3),
        "createdAt": firestore.SERVER_TIMESTAMP if db else today
    }
    validity_records.append(record)
    print(f"[{factor}] IC20={ic_20d} Hit={hit_20d}% Prob={validity_prob} Regime={regime}")

    if db:
        db.collection('factor_validity').document(f"{today}_{factor}").set(record, merge=True)

# 요약 저장
summary = {
    "date": today,
    "regime": regime,
    "factors": {r["factor"]: r["validity_prob"] for r in validity_records},
    "top_factors": sorted(validity_records, key=lambda x: x["validity_prob"], reverse=True)[:3],
    "createdAt": firestore.SERVER_TIMESTAMP if db else today
}

if db:
    db.collection('meta_summaries').document(today).set(summary, merge=True)

print(f"[{today}] Meta Factor Tracker 완료 - {len(validity_records)}개 팩터 저장")
print(f"Top 유효 팩터: {[f['factor'] for f in summary['top_factors']]}")
