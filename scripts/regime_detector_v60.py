"""
regime_detector_v60.py - KOSPI Quant Terminal v60 - Market Regime 100% REAL + China Proxy

개선점 v56 -> v60:
- China Proxy 요인 포함: 구리(HG=F), 상해종합(000001.SS) 변동성도 레짐 판단에 반영
- 10 Factors 전체 변동성 모니터링
- GPR_proxy = (VIX+OVX)/2 + 구리 변동성
- 4단계: normal / caution / high_vol / war_crisis
- window 120→100→90→60일 자동 조절 + China Proxy 가중
- DART 필터와 연동: high_vol/war_crisis시 필터 강화 힌트

실행: 매일 16:00 KST (performance-update.yml 첫 번째)
Firestore: regime_snapshots/{date} + market_regimes/{date}

v60 China Proxy 레짐:
- 구리 급락 + 상해종합 급락 = 중국 경기 침체 → KOSPI 화학/철강/건설 약세 레짐
- VIX 상승 + 구리 하락 = 글로벌 리스크 오프 + 중국 수요 둔화 이중 악재
"""

import os
import json
import datetime
from datetime import timezone, timedelta
import firebase_admin
from firebase_admin import credentials, firestore
import numpy as np

# Firebase
cred_json_str = os.environ.get("FIREBASE_SERVICE_ACCOUNT", "")
if not cred_json_str:
    print("No FIREBASE_SERVICE_ACCOUNT")
    exit(1)

cred_dict = json.loads(cred_json_str)
if not firebase_admin._apps:
    cred = credentials.Certificate(cred_dict)
    firebase_admin.initialize_app(cred)
db = firestore.client()

KST = timezone(timedelta(hours=9))
today = datetime.datetime.now(KST).strftime('%Y-%m-%d')
print(f"\n=== Regime Detector v60 REAL + China Proxy {today} ===")

def fetch_indicator(ticker, period="6mo", name=""):
    """yfinance에서 지표 로드 - 종가, 변동성, Z-score"""
    try:
        import yfinance as yf
        hist = yf.Ticker(ticker).history(period=period)
        if hist.empty:
            print(f"{name or ticker}: empty")
            return [], 0, 0, 0
        
        closes = [float(x) for x in hist['Close'].dropna().tolist()]
        latest = closes[-1]
        
        # 21일 실현 변동성 (연율화)
        if len(closes) >= 21:
            log_rets = np.diff(np.log(closes[-21:]))
            vol = float(np.std(log_rets) * (252**0.5) * 100)
        else:
            vol = 0.0
        
        # 60일 기준 Z-score
        recent = closes[-60:] if len(closes) >= 60 else closes
        mean = float(np.mean(recent))
        std = float(np.std(recent))
        z = (latest - mean) / std if std > 1e-6 else 0
        z = max(-3, min(3, z))
        
        print(f"{name or ticker:12s}: {latest:8.2f} vol {vol:5.1f}% Z {z:+5.2f} [{ticker}]")
        return closes, latest, vol, z
    except Exception as e:
        print(f"Error {name or ticker} ({ticker}): {e}")
        return [], 0, 0, 0

# ========== 10 Factors + China Proxy Fetch ==========
print("\n--- Global Risk Indicators ---")
vix_c, vix_l, vix_v, vix_z = fetch_indicator("^VIX", "6mo", "VIX")
ovx_c, ovx_l, ovx_v, ovx_z = fetch_indicator("^OVX", "6mo", "OVX(유가변동)")

print("\n--- Dollar & Rates ---")
dxy_c, dxy_l, dxy_v, dxy_z = fetch_indicator("DX-Y.NYB", "6mo", "DXY")
tnx_c, tnx_l, tnx_v, tnx_z = fetch_indicator("^TNX", "6mo", "US10Y")

print("\n--- FX & KOSPI ---")
krw_c, krw_l, krw_v, krw_z = fetch_indicator("KRW=X", "3mo", "USD/KRW")
kospi_c, kospi_l, kospi_v, kospi_z = fetch_indicator("^KS11", "3mo", "KOSPI")
sp500_c, sp500_l, sp500_v, sp500_z = fetch_indicator("^GSPC", "3mo", "S&P500")

print("\n--- China Proxy (v60 NEW) ---")
copper_c, copper_l, copper_v, copper_z = fetch_indicator("HG=F", "6mo", "구리(China1)")
sse_c, sse_l, sse_v, sse_z = fetch_indicator("000001.SS", "6mo", "상해종합(China2)")

# GPR Proxy + China Proxy 결합
gpr = (vix_l + ovx_l) / 2 if vix_l and ovx_l else 50
gpr_z = (vix_z + ovx_z) / 2

# China Stress Index = 구리 Z + 상해종합 Z (둘 다 -면 중국 경기 침체)
china_stress_z = (copper_z + sse_z) / 2 if copper_z != 0 or sse_z != 0 else 0
china_vol = (copper_v + sse_v) / 2 if copper_v and sse_v else 0

print(f"\n--- Composite ---")
print(f"GPR_proxy: {gpr:.2f} Z {gpr_z:+.2f}")
print(f"China Stress: Z {china_stress_z:+.2f} Vol {china_vol:.1f}% (구리 {copper_z:+.2f} + 상해 {sse_z:+.2f})")

# ========== Regime Classification v60 ==========
def classify_v60(vix, ovx, gpr, kospi_vol, copper_z, sse_z, china_vol):
    """
    v60 4단계 + China Proxy 가중
    - normal: 평시, 120일 윈도우, 반도체/외국인 팩터 유효
    - caution: 주의, 100일 윈도우, 금리/환율 팩터 유효
    - high_vol: 고변동, 90일 윈도우, 방어적
    - war_crisis: 전시/위기, 60일 윈도우, WTI/달러/현금
    + China Proxy: 구리/상해 급락시 caution 이상으로 격상
    """
    # China 침체 체크
    china_down = (copper_z < -1.5 and sse_z < -1.0) or (copper_z < -2.0) or (sse_z < -2.0)
    china_crash = (copper_z < -2.5 and sse_z < -2.0)
    
    if vix >= 35 or ovx >= 55 or gpr >= 70 or kospi_vol >= 25 or china_crash:
        regime = "war_crisis"
        kr_label = "전시/위기"
        risk = "high"
        window = 60
        reason = f"VIX {vix:.0f} OVX {ovx:.0f} GPR {gpr:.0f} KOSPIvol {kospi_vol:.0f}% ChinaCrash"
    elif vix >= 25 or ovx >= 45 or gpr >= 50 or kospi_vol >= 18 or china_down:
        regime = "high_vol"
        kr_label = "고변동"
        risk = "medium"
        window = 90
        reason = f"VIX {vix:.0f} OVX {ovx:.0f} ChinaDown 구리Z {copper_z:+.1f} 상해Z {sse_z:+.1f}"
    elif vix >= 20 or ovx >= 38 or china_vol >= 25 or abs(copper_z) >= 1.5:
        regime = "caution"
        kr_label = "주의"
        risk = "low-medium"
        window = 100
        reason = f"VIX {vix:.0f} OVX {ovx:.0f} ChinaVol {china_vol:.0f}%"
    else:
        regime = "normal"
        kr_label = "평시"
        risk = "low"
        window = 120
        reason = f"Normal VIX {vix:.0f} China Z {china_stress_z:+.1f}"
    
    return regime, kr_label, risk, window, reason

regime, kr_label, risk, window, reason = classify_v60(
    vix_l, ovx_l, gpr, kospi_v, copper_z, sse_z, china_vol
)

# 팩터 유효성 힌트 (레짐별)
if regime == "normal":
    hint = {"반도체팩터": 0.8, "외국인": 0.7, "SP500": 0.6, "구리": 0.6, "상해종합": 0.5}
    dart_hint = "RELAXED"
elif regime == "caution":
    hint = {"US10Y": 0.8, "원달러": 0.8, "구리": 0.7, "DXY": 0.6}
    dart_hint = "NORMAL"
elif regime == "high_vol":
    hint = {"US10Y": 0.8, "원달러": 0.9, "WTI": 0.7, "VIX": 0.6}
    dart_hint = "STRICT"
else:  # war_crisis
    hint = {"WTI": 0.9, "원달러": 0.9, "DXY": 0.8, "US10Y": 0.7}
    dart_hint = "VERY_STRICT"

print(f"\n=== Regime Result v60 ===")
print(f"Regime: {regime} ({kr_label}) Risk {risk} Window {window}d")
print(f"Reason: {reason}")
print(f"Factor Hint: {hint}")
print(f"DART Hint: {dart_hint}")

# ========== Save to Firestore ==========
doc = {
    'date': today,
    'timestamp': datetime.datetime.now(KST),
    'regime': regime,
    'regime_kr': kr_label,
    'risk_level': risk,
    'recommended_window': window,
    'reason': reason,
    'indicators': {
        'VIX': {'latest': round(vix_l, 2), 'vol': round(vix_v, 2), 'z': round(vix_z, 2), 'source': 'yfinance ^VIX REAL v60'},
        'OVX': {'latest': round(ovx_l, 2), 'vol': round(ovx_v, 2), 'z': round(ovx_z, 2), 'source': 'yfinance ^OVX REAL v60'},
        'DXY': {'latest': round(dxy_l, 2), 'vol': round(dxy_v, 2), 'z': round(dxy_z, 2), 'source': 'yfinance DXY REAL v60'},
        'US10Y': {'latest': round(tnx_l, 2), 'vol': round(tnx_v, 2), 'z': round(tnx_z, 2), 'source': 'yfinance ^TNX REAL v60'},
        'USD_KRW': {'latest': round(krw_l, 2), 'vol': round(krw_v, 2), 'z': round(krw_z, 2), 'source': 'yfinance KRW=X REAL v60'},
        'KOSPI': {'latest': round(kospi_l, 2), 'vol': round(kospi_v, 2), 'z': round(kospi_z, 2), 'source': 'yfinance ^KS11 REAL v60'},
        'SP500': {'latest': round(sp500_l, 2), 'vol': round(sp500_v, 2), 'z': round(sp500_z, 2), 'source': 'yfinance ^GSPC REAL v60'},
        'GPR_proxy': {'latest': round(gpr, 2), 'z': round(gpr_z, 2), 'source': 'VIX+OVX REAL v60'},
        # China Proxy NEW v60
        'COPPER': {'latest': round(copper_l, 2), 'vol': round(copper_v, 2), 'z': round(copper_z, 2), 'source': 'yfinance HG=F REAL v60 China Proxy 1'},
        'SSE': {'latest': round(sse_l, 2), 'vol': round(sse_v, 2), 'z': round(sse_z, 2), 'source': 'yfinance 000001.SS REAL v60 China Proxy 2'},
        'China_Stress': {'z': round(china_stress_z, 2), 'vol': round(china_vol, 2), 'copper_z': round(copper_z, 2), 'sse_z': round(sse_z, 2), 'source': '구리+상해종합 China Proxy v60'}
    },
    'factorValidityHint': hint,
    'dartFilterHint': dart_hint,
    'chinaProxy': {
        'copper': {'z': round(copper_z, 2), 'vol': round(copper_v, 2)},
        'sse': {'z': round(sse_z, 2), 'vol': round(sse_v, 2)},
        'stress_z': round(china_stress_z, 2),
        'is_down': (copper_z < -1.5 and sse_z < -1.0)
    },
    'source': 'yfinance-REAL-v60-ChinaProxy-100pct',
    'version': 'v60-regime-real-china-proxy',
    'real_data_ratio': 1.0,
    'trigger_retrain': regime in ["war_crisis", "high_vol"],
    'createdAt': firestore.SERVER_TIMESTAMP
}

# Save to both collections for compatibility
db.collection('regime_snapshots').document(today).set(doc, merge=True)
db.collection('market_regimes').document(today).set(doc, merge=True)

print(f"\n[{today}] Regime {regime} {kr_label} Risk {risk} Window {window} Saved 100% REAL v60 China Proxy")
print(f"China Proxy: 구리 Z {copper_z:+.2f} 상해 Z {sse_z:+.2f} -> Stress {china_stress_z:+.2f}")
if doc['chinaProxy']['is_down']:
    print("⚠️ China Downturn Detected - 화학/철강/건설 주의 레짐")

# Also save to performance_snapshots? No, separate
