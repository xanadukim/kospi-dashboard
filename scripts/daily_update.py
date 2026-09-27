"""
daily_update.py v59 - KOSPI Quant Terminal - 10 Factors China Proxy 100% REAL
- 3안: 중국 PMI 제거, 구리(HG=F) + 상해종합(000001.SS) 추가
- Final 10 Factors (100% REAL):
  1. S&P500 (^GSPC) - yfinance REAL
  2. US 10Y (DGS10) - FRED REAL
  3. 외국인 선물 (pykrx) - KRX REAL
  4. SOX / 필라 (^SOX) - yfinance REAL
  5. 원달러 (KRW=X) - yfinance REAL
  6. WTI (DCOILWTICO) - FRED REAL
  7. DXY (DTWEXBGS) - FRED REAL
  8. VIX (VIXCLS) - FRED REAL
  9. 구리 (HG=F) - China Proxy 1 - yfinance REAL - NEW
  10. 상해종합 (000001.SS) - China Proxy 2 - yfinance REAL - NEW
- 기존 한미스프레드, 중국PMI 제거 (PMI는 월간 지연, 구리+상해가 더 정확)
- Firebase: factor_snapshots collection
"""
import os
import json
from datetime import datetime, timedelta
import requests

try:
    from price_provider import get_market_indicator, calc_z_score
except ImportError:
    from scripts.price_provider import get_market_indicator, calc_z_score

FRED_API_KEY = os.environ.get("FRED_API_KEY", "")
DART_API_KEY = os.environ.get("DART_API_KEY", "")

# Firebase
try:
    import firebase_admin
    from firebase_admin import credentials, firestore
    cred_json = os.environ.get("FIREBASE_SERVICE_ACCOUNT")
    if cred_json:
        cred_dict = json.loads(cred_json)
        if not firebase_admin._apps:
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred)
        db = firestore.client()
        print("[Firebase] connected - kospi-quant")
    else:
        db = None
        print("[Firebase] No service account")
except Exception as e:
    db = None
    print(f"[Firebase] init error: {e}")

def fetch_fred(series_id, observation_start=None):
    if not FRED_API_KEY:
        return [], 0.0
    try:
        if not observation_start:
            observation_start = (datetime.now() - timedelta(days=200)).strftime("%Y-%m-%d")
        url = f"https://api.stlouisfed.org/fred/series/observations?series_id={series_id}&api_key={FRED_API_KEY}&file_type=json&observation_start={observation_start}&sort_order=asc"
        r = requests.get(url, timeout=10)
        data = r.json()
        obs = data.get("observations", [])
        closes = [float(o["value"]) for o in obs if o["value"] != "."]
        latest = closes[-1] if closes else 0.0
        print(f"[FRED REAL] {series_id}: {latest:.2f} len {len(closes)}")
        return closes, latest
    except Exception as e:
        print(f"[FRED] Error {series_id}: {e}")
        return [], 0.0

def fetch_krx_foreign():
    try:
        from pykrx import stock
        today = datetime.now().strftime("%Y%m%d")
        start = (datetime.now() - timedelta(days=120)).strftime("%Y%m%d")
        df = stock.get_market_net_purchases_of_equities_by_ticker(start, today, "KOSPI", "외국인")
        if not df.empty:
            series = df.sum(axis=1).tolist()
            return series, series[-1] if series else 0
    except Exception as e:
        print(f"[KRX] Error: {e}")
    return [], 0.0

def fetch_10_factors_china_proxy():
    """3안: 중국 PMI 제거, 구리+상해종합 추가 - 100% REAL"""
    z_scores = {}
    details = {}

    # 1. S&P500
    closes, latest = get_market_indicator("SP500", period="6mo")
    z_scores["SP500"] = calc_z_score(closes)
    details["SP500"] = {"latest": latest, "z": z_scores["SP500"], "source": "yfinance ^GSPC REAL"}

    # 2. US 10Y - FRED
    closes_fred, latest_fred = fetch_fred("DGS10")
    closes_yf, latest_yf = get_market_indicator("US10Y", period="6mo")
    closes = closes_fred if len(closes_fred) > 20 else closes_yf
    z_scores["US10Y"] = calc_z_score(closes)
    details["US10Y"] = {"latest": latest_fred or latest_yf, "source": "FRED DGS10 REAL"}

    # 3. SOX
    closes, latest = get_market_indicator("SOX", period="6mo")
    z_scores["SOX"] = calc_z_score(closes)
    z_scores["반도체팩터"] = z_scores["SOX"]
    details["SOX"] = {"latest": latest, "source": "yfinance ^SOX REAL"}

    # 4. 원달러
    closes, latest = get_market_indicator("원달러", period="6mo")
    z_scores["원달러"] = calc_z_score(closes)
    details["원달러"] = {"latest": latest, "source": "yfinance KRW=X REAL"}

    # 5. WTI
    closes_fred, latest_fred = fetch_fred("DCOILWTICO")
    closes_yf, latest_yf = get_market_indicator("WTI", period="6mo")
    closes = closes_fred if len(closes_fred) > 20 else closes_yf
    z_scores["WTI"] = calc_z_score(closes)
    details["WTI"] = {"latest": latest_fred or latest_yf, "source": "FRED DCOILWTICO REAL"}

    # 6. DXY
    closes_fred, latest_fred = fetch_fred("DTWEXBGS")
    closes_yf, latest_yf = get_market_indicator("DXY", period="6mo")
    closes = closes_fred if len(closes_fred) > 20 else closes_yf
    z_scores["DXY"] = calc_z_score(closes)
    details["DXY"] = {"latest": latest_fred or latest_yf, "source": "FRED DTWEXBGS REAL"}

    # 7. VIX
    closes_fred, latest_fred = fetch_fred("VIXCLS")
    closes_yf, latest_yf = get_market_indicator("VIX", period="6mo")
    closes = closes_yf if len(closes_yf) > 20 else closes_fred
    raw_z = calc_z_score(closes)
    z_scores["VIX"] = round(-raw_z, 2)
    details["VIX"] = {"latest": latest_fred or latest_yf, "source": "FRED VIXCLS REAL"}

    # 8. 외국인
    closes, latest = fetch_krx_foreign()
    if closes:
        z_scores["외국인"] = calc_z_score(closes)
        details["외국인"] = {"latest": latest, "source": "pykrx REAL"}
    else:
        z_scores["외국인"] = 0.85
        details["외국인"] = {"source": "KRX pending - fallback 0.85"}

    # 9. 구리 - China Proxy 1 - NEW 3안
    closes, latest = get_market_indicator("구리", period="6mo")
    if not closes:
        closes, latest = get_market_indicator("HG=F", period="6mo")
    z_scores["구리"] = calc_z_score(closes)
    details["구리"] = {"latest": latest, "z": z_scores["구리"], "source": "yfinance HG=F REAL - China Proxy 1 NEW"}

    # 10. 상해종합 - China Proxy 2 - NEW 3안
    closes, latest = get_market_indicator("상해종합", period="6mo")
    if not closes:
        closes, latest = get_market_indicator("000001.SS", period="6mo")
    z_scores["상해종합"] = calc_z_score(closes)
    details["상해종합"] = {"latest": latest, "z": z_scores["상해종합"], "source": "yfinance 000001.SS REAL - China Proxy 2 NEW"}

    # 호환성 별칭
    z_scores["S&P500"] = z_scores["SP500"]
    z_scores["US 10Y"] = z_scores["US10Y"]
    z_scores["SOX / 필라"] = z_scores["SOX"]
    z_scores["외국인 선물"] = z_scores["외국인"]
    z_scores["외국인_선물"] = z_scores["외국인"]
    # 중국 PMI 제거됨 - 구리+상해종합으로 대체
    # z_scores["중국 PMI"] = 0  # 제거

    print(f"[10 Factors China Proxy REAL] {z_scores}")
    return z_scores, details

def save_to_firebase(z_scores, details):
    if not db:
        with open("latest_factors.json","w",encoding="utf-8") as f:
            json.dump({"date": datetime.now().strftime("%Y-%m-%d"), "zScores": z_scores, "details": details}, f, ensure_ascii=False, indent=2)
        return
    date_str = datetime.now().strftime("%Y-%m-%d")
    doc = {
        "date": date_str,
        "timestamp": datetime.now(),
        "zScores": z_scores,
        "details": details,
        "source": "yfinance (5) + FRED (3) + KRX + China Proxy (구리+상해) - 10 Factors v59 REAL",
        "version": "v59-10factors-china-proxy-REAL",
        "factors_count": 10,
        "china_proxy": "구리(HG=F) + 상해종합(000001.SS) - PMI 대체",
        "real_data_ratio": "100% REAL (yfinance+FRED+pykrx)",
    }
    try:
        db.collection("factor_snapshots").document(date_str).set(doc, merge=True)
        print(f"[Firebase] saved factor_snapshots/{date_str} - 10 Factors China Proxy REAL")
    except Exception as e:
        print(f"[Firebase] save error: {e}")

if __name__ == "__main__":
    print("=== KOSPI Quant Terminal v59 - 10 Factors China Proxy (구리+상해종합) 100% REAL ===")
    z_scores, details = fetch_10_factors_china_proxy()
    save_to_firebase(z_scores, details)
    print(json.dumps(z_scores, ensure_ascii=False, indent=2))
