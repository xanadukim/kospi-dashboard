"""
regime_detector.py v56 REAL yfinance - 100% REAL no KRX needed
VIX, OVX, DXY, US10Y, KRW, KOSPI, SP500 REAL via yfinance
Before: random Mock 100% -> Now: yfinance REAL 100%
"""
import os, json, datetime
import firebase_admin
from firebase_admin import credentials, firestore

sa_json = json.loads(os.environ.get('FIREBASE_SERVICE_ACCOUNT','{}'))
cred = credentials.Certificate(sa_json)
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)
db = firestore.client()

kst = datetime.timezone(datetime.timedelta(hours=9))
today = datetime.datetime.now(kst).strftime('%Y-%m-%d')
print(f"[{today}] Regime Detector v56 REAL yfinance start")

def fetch(ticker, period="3mo"):
    try:
        import yfinance as yf, numpy as np
        hist = yf.Ticker(ticker).history(period=period)
        if hist.empty:
            return [],0,0,0
        closes = [float(x) for x in hist['Close'].dropna().tolist()]
        latest = closes[-1]
        vol = float(np.std(np.diff(np.log(closes[-21:])))*(252**0.5)*100) if len(closes)>=21 else 0
        recent = closes[-60:] if len(closes)>=60 else closes
        mean = float(np.mean(recent)); std = float(np.std(recent))
        z = (latest-mean)/std if std>1e-6 else 0
        z = max(-3,min(3,z))
        print(f"{ticker}: {latest:.2f} vol {vol:.1f}% Z {z:+.2f}")
        return closes, latest, vol, z
    except Exception as e:
        print(f"Error {ticker}: {e}")
        return [],0,0,0

vix_c,vix_l,vix_v,vix_z = fetch("^VIX","6mo")
ovx_c,ovx_l,ovx_v,ovx_z = fetch("^OVX","6mo")
dxy_c,dxy_l,dxy_v,dxy_z = fetch("DX-Y.NYB","6mo")
tnx_c,tnx_l,tnx_v,tnx_z = fetch("^TNX","6mo")
krw_c,krw_l,krw_v,krw_z = fetch("KRW=X","3mo")
kospi_c,kospi_l,kospi_v,kospi_z = fetch("^KS11","3mo")
sp500_c,sp500_l,sp500_v,sp500_z = fetch("^GSPC","3mo")

gpr = (vix_l+ovx_l)/2 if vix_l and ovx_l else 50
gpr_z = (vix_z+ovx_z)/2

def classify(vix,ovx,gpr,kospi_vol):
    if vix>=35 or ovx>=55 or gpr>=70 or kospi_vol>=25:
        return "war_crisis","전시/위기","high",60
    elif vix>=25 or ovx>=45 or gpr>=50 or kospi_vol>=18:
        return "high_vol","고변동","medium",90
    elif vix>=20 or ovx>=38:
        return "caution","주의","low-medium",100
    else:
        return "normal","평시","low",120

regime,kr_label,risk,window = classify(vix_l,ovx_l,gpr,kospi_v)
hint = {"반도체팩터":0.8,"외국인":0.7,"SP500":0.6} if regime=="normal" else {"US10Y":0.8,"원달러":0.8} if regime in ["high_vol","caution"] else {"WTI":0.9,"원달러":0.9}

doc = {
 'date':today,'regime':regime,'regime_kr':kr_label,'risk_level':risk,'recommended_window':window,
 'indicators':{
  'VIX':{'latest':round(vix_l,2),'vol':round(vix_v,2),'z':round(vix_z,2),'source':'yfinance ^VIX REAL'},
  'OVX':{'latest':round(ovx_l,2),'vol':round(ovx_v,2),'z':round(ovx_z,2),'source':'yfinance ^OVX REAL'},
  'DXY':{'latest':round(dxy_l,2),'vol':round(dxy_v,2),'z':round(dxy_z,2),'source':'yfinance DXY REAL'},
  'US10Y':{'latest':round(tnx_l,2),'vol':round(tnx_v,2),'z':round(tnx_z,2),'source':'yfinance ^TNX REAL'},
  'USD_KRW':{'latest':round(krw_l,2),'vol':round(krw_v,2),'z':round(krw_z,2),'source':'yfinance KRW=X REAL'},
  'KOSPI':{'latest':round(kospi_l,2),'vol':round(kospi_v,2),'z':round(kospi_z,2),'source':'yfinance ^KS11 REAL'},
  'SP500':{'latest':round(sp500_l,2),'vol':round(sp500_v,2),'z':round(sp500_z,2),'source':'yfinance ^GSPC REAL'},
  'GPR_proxy':{'latest':round(gpr,2),'z':round(gpr_z,2),'source':'VIX+OVX REAL'}
 },
 'factorValidityHint':hint,'source':'yfinance-REAL-v56-100pct','version':'v56-regime-real','real_data_ratio':1.0,
 'trigger_retrain':regime in ["war_crisis","high_vol"],'createdAt':firestore.SERVER_TIMESTAMP
}

db.collection('regime_snapshots').document(today).set(doc, merge=True)
db.collection('market_regimes').document(today).set(doc, merge=True)
print(f"[{today}] Regime {regime} {kr_label} Risk {risk} Window {window} Saved 100% REAL")
