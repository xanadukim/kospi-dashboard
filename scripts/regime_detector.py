"""
scripts/regime_detector.py - 시장 체제 감지 (v50 준비)
매일 07:00 UTC (16:00 KST) 실행 - 평시/고변동/전시 체제 분류

목표: VIX, OVX(유가 변동성), GPR(지정학적 리스크), 원달러 변동성으로
      현재 시장이 평시인지 전시인지 분류하여 factor_validity와 모델 윈도우 결정에 사용
"""
import os, json, datetime, random, math
import firebase_admin
from firebase_admin import credentials, firestore

# Firebase init
sa_json = json.loads(os.environ.get('FIREBASE_SERVICE_ACCOUNT', '{}'))
if sa_json and not firebase_admin._apps:
    cred = credentials.Certificate(sa_json)
    firebase_admin.initialize_app(cred)
    db = firestore.client()
else:
    db = None
    print("[regime_detector] Firebase mock mode")

kst = datetime.timezone(datetime.timedelta(hours=9))
today = datetime.datetime.now(kst).strftime('%Y-%m-%d')
print(f"[{today}] Regime Detector - 체제 감지 시작")

def fetch_market_indicators():
    """
    실제 구현:
    - VIX: FRED, yfinance ^VIX
    - OVX: yfinance ^OVX (WTI 변동성)
    - GPR: https://www.matteoiacoviello.com/gpr.htm (지정학적 리스크 지수) 또는 뉴스 크롤링
    - USD_KRW vol: 20일 변동성
    Mock으로 현재는 random + 시나리오
    """
    # Mock 데이터 - 실제로는 API 호출
    vix = 18.5 + random.uniform(-2, 5)  # 평시 15-20, 고변동 25-35, 전시 35+
    ovx = 35.0 + random.uniform(-5, 15)  # 평시 30-40, 전시 50+
    gpr = 95.0 + random.uniform(-10, 80)  # 평시 80-100, 전시 150+
    usd_krw_vol = 0.8 + random.uniform(-0.2, 0.5)  # 일간 변동성 %
    
    # 6개월 후 시나리오: 미국-이란 긴장 시 GPR 급증
    # 10% 확률로 전시 시나리오 모의
    if random.random() < 0.1:
        gpr = 165 + random.uniform(0, 30)
        ovx = 52 + random.uniform(0, 10)
        vix = 32 + random.uniform(0, 8)
        print(f"[시나리오] 전시 모의: GPR {gpr:.1f}, OVX {ovx:.1f}")

    return {
        "VIX": round(vix, 1),
        "OVX": round(ovx, 1),
        "GPR": round(gpr, 1),
        "USD_KRW_vol": round(usd_krw_vol, 2),
        "SP500_vol": round(vix*0.8, 1)
    }

def classify_regime(indicators):
    """
    체제 분류 로직 (간단한 룰 기반, 추후 ML로 고도화)
    - 평시: VIX<22, OVX<40, GPR<110
    - 고변동: VIX 22-30 또는 OVX 40-50 또는 GPR 110-150
    - 전시: VIX>30 또는 OVX>50 또는 GPR>150
    """
    vix, ovx, gpr = indicators["VIX"], indicators["OVX"], indicators["GPR"]
    
    if gpr > 150 or ovx > 50 or vix > 30:
        regime = "전시"
        risk_level = "high"
        window = 60  # 120일 → 60일로 단축, 빠르게 적응
        description = f"지정학적 리스크 고조 (GPR {gpr}), 유가 변동성 급증 (OVX {ovx})"
    elif gpr > 110 or ovx > 40 or vix > 22:
        regime = "고변동"
        risk_level = "medium"
        window = 90
        description = f"변동성 확대 (VIX {vix}, OVX {ovx}), 주의 필요"
    else:
        regime = "평시"
        risk_level = "low"
        window = 120
        description = f"안정적 시장 (VIX {vix}, GPR {gpr})"

    return {
        "regime_label": regime,
        "risk_level": risk_level,
        "recommended_window": window,
        "description": description,
        "trigger_retrain": regime in ["전시", "고변동"]  # 전시/고변동이면 즉시 재학습 트리거
    }

indicators = fetch_market_indicators()
regime_info = classify_regime(indicators)

record = {
    "date": today,
    "indicators": indicators,
    "regime_label": regime_info["regime_label"],
    "risk_level": regime_info["risk_level"],
    "recommended_window": regime_info["recommended_window"],
    "description": regime_info["description"],
    "trigger_retrain": regime_info["trigger_retrain"],
    "createdAt": firestore.SERVER_TIMESTAMP if db else today
}

print(f"[{today}] 체제: {regime_info['regime_label']} (Risk: {regime_info['risk_level']})")
print(f"지표: VIX {indicators['VIX']}, OVX {indicators['OVX']}, GPR {indicators['GPR']}")
print(f"권장 윈도우: {regime_info['recommended_window']}일, 즉시 재학습: {regime_info['trigger_retrain']}")
print(f"설명: {regime_info['description']}")

if db:
    db.collection('market_regimes').document(today).set(record, merge=True)
    
    # 전시/고변동이면 이벤트 트리거 컬렉션에 저장 (GitHub Actions가 감지하여 retrain 실행)
    if regime_info["trigger_retrain"]:
        db.collection('retrain_triggers').document(today).set({
            "date": today,
            "reason": regime_info["description"],
            "regime": regime_info["regime_label"],
            "indicators": indicators,
            "createdAt": firestore.SERVER_TIMESTAMP
        }, merge=True)
        print(f"[{today}] 전시/고변동 감지 → retrain_triggers에 저장 (GitHub Actions가 즉시 재학습)")

# 로컬 백업
print(f"[{today}] Regime Detector 완료")
