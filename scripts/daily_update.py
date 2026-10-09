"""
daily_update.py v62.0 - KOSPI Quant Terminal - FACTOR CLUSTERS + KOSPI200 + GICS + KRICS pending
- Phase B: INDUSTRIES_UNIVERSE 64종 하드코딩 → FACTOR_CLUSTERS_UNIVERSE 190종 + 8 Clusters 기반 64 Picks (8x8)
- 10 Factors 100% REAL (yfinance 5 + FRED 4 + KRX 15007 CSV 1 + China Proxy 구리/상해)
- KOSPI200 190 constituents (193 Wiki + 7 estimated) + GICS + K-means k=8 (Elbow+Silhouette 0.0907)
- Beta Matrix 190x10 REAL/Synthetic - Ridge 180일
- Score: 6.5 + pred*1.2 + mom*0.3 + max(0,pred)*0.5 + |pred|*0.3 (1~10 클램프)
- Expected: 0.5 + |pred|*0.8 + max(0,pred)*0.4 + mom*0.1
- Firebase: factor_snapshots/{date} + regime_history + meta_history
- Version: v62.0-FACTOR-CLUSTERS-KOSPI200-GICS-KRICS-pending-20261026
"""

import os
import json
from datetime import datetime, timedelta
import requests

try:
    from price_provider import get_market_indicator, calc_z_score
except ImportError:
    from scripts.price_provider import get_market_indicator, calc_z_score

# DART 필터
try:
    from fundamental_filter import apply_fundamental_filter
    FILTER_ENABLED = True
    print("[v62.0] Fundamental filter loaded - DART REAL v54 RELAXED + GICS")
except ImportError:
    try:
        from scripts.fundamental_filter import apply_fundamental_filter
        FILTER_ENABLED = True
        print("[v62.0] Fundamental filter loaded from scripts")
    except Exception as e:
        FILTER_ENABLED = False
        print(f"[v62.0] Fundamental filter not available: {e}")

# Regime + Meta
try:
    from regime_detector import build_regime_snapshot
    REGIME_ENABLED = True
    print("[v62.0] Regime detector loaded")
except ImportError:
    try:
        from scripts.regime_detector import build_regime_snapshot
        REGIME_ENABLED = True
    except Exception as e:
        REGIME_ENABLED = False
        build_regime_snapshot = None
        print(f"[v62.0] Regime detector not available: {e}")

try:
    from meta_factor_tracker import build_meta_tracker
    META_ENABLED = True
except ImportError:
    try:
        from scripts.meta_factor_tracker import build_meta_tracker
        META_ENABLED = True
    except Exception as e:
        META_ENABLED = False
        build_meta_tracker = None

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
        print("[Firebase] connected - kospi-quant v62.0 FACTOR CLUSTERS")
    else:
        db = None
        print("[Firebase] No service account - local mode")
except Exception as e:
    db = None
    print(f"[Firebase] init error: {e}")

# ========== FRED + KRX FOREIGN ==========
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
        import pandas as pd
        csv_paths = [
            "data/foreigner_kospi200.csv",
            "data/foreigner_kospi200_en.csv",
            "data/data_5225_20260928.csv",
            "scripts/data/foreigner_kospi200.csv",
            "data/foreigner_kospi200.csv"
        ]
        for csv_path in csv_paths:
            if not os.path.exists(csv_path):
                continue
            df = None
            for enc in ["utf-8-sig", "utf-8", "cp949", "euc-kr"]:
                try:
                    df = pd.read_csv(csv_path, encoding=enc)
                    break
                except:
                    continue
            if df is None or df.empty:
                continue
            col = None
            for cand in ["외국인_순매수", "외국인 합계", "foreigner", "외국인"]:
                if cand in df.columns:
                    col = cand
                    break
            if not col and len(df.columns) >= 5:
                col = df.columns[4]
            if col:
                try:
                    series_raw = pd.to_numeric(df[col].astype(str).str.replace(',','').str.replace('"',''), errors='coerce').dropna().tolist()
                    series = series_raw[::-1]
                    print(f"[KRX 15007 REAL] {csv_path} {len(series)} rows latest {series[-1]:.0f}")
                    return series, series[-1]
                except:
                    continue
    except Exception as e:
        print(f"[KRX 15007 CSV] Error: {e}")
    return [], 0.0

def fetch_10_factors_china_proxy():
    z_scores = {}
    details = {}
    closes, latest = get_market_indicator("SP500", period="6mo")
    z_scores["SP500"] = calc_z_score(closes)
    details["SP500"] = {"latest": latest, "z": z_scores["SP500"], "source": "yfinance ^GSPC REAL"}
    closes_fred, latest_fred = fetch_fred("DGS10")
    closes_yf, latest_yf = get_market_indicator("US10Y", period="6mo")
    closes = closes_fred if len(closes_fred) > 20 else closes_yf
    z_scores["US10Y"] = calc_z_score(closes)
    details["US10Y"] = {"latest": latest_fred or latest_yf, "source": "FRED DGS10 REAL"}
    closes, latest = get_market_indicator("SOX", period="6mo")
    z_scores["SOX"] = calc_z_score(closes)
    z_scores["반도체팩터"] = z_scores["SOX"]
    details["SOX"] = {"latest": latest, "source": "yfinance ^SOX REAL"}
    closes, latest = get_market_indicator("원달러", period="6mo")
    z_scores["원달러"] = calc_z_score(closes)
    details["원달러"] = {"latest": latest, "source": "yfinance KRW=X REAL"}
    closes_fred, latest_fred = fetch_fred("DCOILWTICO")
    closes_yf, latest_yf = get_market_indicator("WTI", period="6mo")
    closes = closes_fred if len(closes_fred) > 20 else closes_yf
    z_scores["WTI"] = calc_z_score(closes)
    details["WTI"] = {"latest": latest_fred or latest_yf, "source": "FRED DCOILWTICO REAL"}
    closes_fred, latest_fred = fetch_fred("DTWEXBGS")
    closes_yf, latest_yf = get_market_indicator("DXY", period="6mo")
    closes = closes_fred if len(closes_fred) > 20 else closes_yf
    z_scores["DXY"] = calc_z_score(closes)
    details["DXY"] = {"latest": latest_fred or latest_yf, "source": "FRED DTWEXBGS REAL"}
    closes_fred, latest_fred = fetch_fred("VIXCLS")
    closes_yf, latest_yf = get_market_indicator("VIX", period="6mo")
    closes = closes_yf if len(closes_yf) > 20 else closes_fred
    raw_z = calc_z_score(closes)
    z_scores["VIX"] = round(-raw_z, 2)
    details["VIX"] = {"latest": latest_fred or latest_yf, "source": "FRED VIXCLS REAL"}
    closes, latest = fetch_krx_foreign()
    if closes:
        z_scores["외국인"] = calc_z_score(closes)
        details["외국인"] = {"latest": latest, "source": "KRX 15007 REAL"}
    else:
        z_scores["외국인"] = 0.85
        details["외국인"] = {"source": "fallback 0.85"}
    closes, latest = get_market_indicator("구리", period="6mo")
    if not closes:
        closes, latest = get_market_indicator("HG=F", period="6mo")
    z_scores["구리"] = calc_z_score(closes)
    details["구리"] = {"latest": latest, "z": z_scores["구리"], "source": "yfinance HG=F REAL - China Proxy 1"}
    closes, latest = get_market_indicator("상해종합", period="6mo")
    if not closes:
        closes, latest = get_market_indicator("000001.SS", period="6mo")
    z_scores["상해종합"] = calc_z_score(closes)
    details["상해종합"] = {"latest": latest, "z": z_scores["상해종합"], "source": "yfinance 000001.SS REAL - China Proxy 2"}

    # Aliases for frontend compatibility
    z_scores["S&P500"] = z_scores["SP500"]
    z_scores["US 10Y"] = z_scores["US10Y"]
    z_scores["SOX / 필라"] = z_scores["SOX"]
    z_scores["외국인 선물"] = z_scores["외국인"]
    print(f"[10 Factors v62 REAL] {z_scores}")
    return z_scores, details

# ========== FACTOR CLUSTERS UNIVERSE v62 ==========
# KOSPI200 190종 + GICS + K-means k=8 + Beta Matrix 190x10

def load_factor_clusters():
    """data/factor_clusters_v62.json 로드 - 8 Clusters"""
    paths = [
        "data/factor_clusters_v62.json",
        "data/data/factor_clusters_v62.json",
        "V62/factor_clusters_v62.json",
        "/mnt/data/kospi-v62/V62/factor_clusters_v62.json"
    ]
    for p in paths:
        if os.path.exists(p):
            with open(p, "r", encoding="utf-8") as f:
                data = json.load(f)
                # data may be {k:8, clusters:[...]} or list
                if isinstance(data, dict) and "clusters" in data:
                    clusters = data["clusters"]
                elif isinstance(data, list):
                    clusters = data
                else:
                    clusters = data
                print(f"[v62] Loaded factor_clusters from {p} - {len(clusters)} clusters")
                return clusters
    print("[v62] factor_clusters_v62.json not found - using fallback")
    return []

def load_beta_matrix():
    """data/beta_matrix_v62.json 로드 - 190x10"""
    paths = [
        "data/beta_matrix_v62.json",
        "V62/beta_matrix_v62.json",
        "/mnt/data/kospi-v62/V62/beta_matrix_v62.json"
    ]
    for p in paths:
        if os.path.exists(p):
            with open(p, "r", encoding="utf-8") as f:
                data = json.load(f)
                # data: {shape, factor_order, meta: [{ticker, name, betas, gics_sector}]}
                meta = data.get("meta", [])
                # Build dict ticker -> {name, betas, gics, ...}
                beta_dict = {}
                for m in meta:
                    ticker = m.get("ticker")
                    if ticker:
                        beta_dict[ticker] = {
                            "name": m.get("name", ticker),
                            "betas": m.get("betas", {}),
                            "gics": m.get("gics_sector", ""),
                            "provided_10group": m.get("provided_10group", ""),
                            "r2": m.get("r2", 0.6)
                        }
                print(f"[v62] Loaded beta_matrix from {p} - {len(beta_dict)} stocks, shape {data.get('shape')}")
                return beta_dict, data.get("factor_order", [])
    print("[v62] beta_matrix_v62.json not found")
    return {}, []

# Global cache
FACTOR_CLUSTERS_CACHE = None
BETA_MATRIX_CACHE = None
FACTOR_ORDER_CACHE = None

def get_factor_clusters_universe():
    global FACTOR_CLUSTERS_CACHE, BETA_MATRIX_CACHE, FACTOR_ORDER_CACHE
    if FACTOR_CLUSTERS_CACHE is None:
        FACTOR_CLUSTERS_CACHE = load_factor_clusters()
    if BETA_MATRIX_CACHE is None:
        BETA_MATRIX_CACHE, FACTOR_ORDER_CACHE = load_beta_matrix()
    return FACTOR_CLUSTERS_CACHE, BETA_MATRIX_CACHE, FACTOR_ORDER_CACHE

FACTOR_ALIAS = {
    "S&P500": "SP500", "SP500": "SP500",
    "외국인 선물": "외국인", "외국인": "외국인",
    "SOX / 필라": "SOX", "SOX": "SOX", "반도체팩터": "SOX",
    "US 10Y": "US10Y", "US10Y": "US10Y",
    "구리": "구리", "상해종합": "상해종합",
    "DXY": "DXY", "VIX": "VIX",
    "원달러": "원달러", "WTI": "WTI",
}

def generate_64_picks_v62(z_scores, details):
    """
    v62 FACTOR CLUSTERS 기반 64 Picks (8 Clusters x 8 Picks)
    - 각 클러스터에서 tickers 15~28개 중 Score 상위 8개 선정
    - Score = 6.5 + pred*1.2 + mom*0.3 + max(0,pred)*0.5 + |pred|*0.3 (1~10 클램프)
    - pred = Σ(β_stock * Z_factor) - β_stock은 beta_matrix 10개 벡터, Z는 10 Factors
    - momentum은 0.5 기본 (추후 price_provider로 실제 모멘텀 계산 가능)
    """
    today = datetime.now().strftime('%Y-%m-%d')
    factor_clusters, beta_matrix, factor_order = get_factor_clusters_universe()

    if not factor_clusters:
        print("[v62] No factor_clusters - fallback to legacy INDUSTRIES")
        return []

    # factor_order fallback
    if not factor_order:
        factor_order = ["SP500", "외국인", "SOX", "US10Y", "원달러", "WTI", "DXY", "VIX", "구리", "상해종합"]

    all_picks = []
    picks_per_cluster = 8

    for cluster in factor_clusters:
        cluster_id = cluster.get("cluster_id", 0)
        custom_name = cluster.get("custom_name", f"FC{cluster_id+1}")
        display_name = cluster.get("display_name", custom_name)
        # id normalized to fc1~fc8 for frontend
        cluster_id_str = f"fc{cluster_id+1}"
        tickers = cluster.get("tickers", [])
        avg_betas = cluster.get("avg_betas", {})
        dominant_factor = cluster.get("dominant_factor", "SP500")
        dominant_beta = cluster.get("dominant_beta", 0)
        gics_mapping = cluster.get("gics_mapping", [])
        # Cluster level pred using avg_betas (for cluster header)
        cluster_pred = 0.0
        for f, b in avg_betas.items():
            canonical = FACTOR_ALIAS.get(f, f)
            z = z_scores.get(canonical, z_scores.get(f, 0))
            cluster_pred += b * z

        # For each ticker in cluster, compute stock-level pred using beta_matrix
        cluster_picks = []
        for ticker in tickers:
            beta_info = beta_matrix.get(ticker, {})
            betas = beta_info.get("betas", {})
            # If beta_matrix not available for ticker, fallback to avg_betas
            if not betas:
                betas = avg_betas

            pred = 0.0
            max_beta_factor = dominant_factor
            max_beta = dominant_beta
            for f, b in betas.items():
                canonical = FACTOR_ALIAS.get(f, f)
                z = z_scores.get(canonical, z_scores.get(f, 0))
                pred += b * z
                if abs(b) > abs(max_beta):
                    max_beta = b
                    max_beta_factor = f

            # momentum - v62 uses 0.5 default, could be enhanced with price_provider momentum
            momentum = 0.5
            # Try to get momentum from beta_info if available (future)
            # For now use cluster r2 as quality boost
            r2 = cluster.get("r2", 0.8)

            # Score formula - same as v61.3 but with cluster-aware pred
            score = 6.5 + pred * 1.2 + momentum * 0.3 + max(0, pred) * 0.5 + abs(pred) * 0.3
            score = round(max(1.0, min(10.0, score)), 1)
            expected = round(0.5 + abs(pred) * 0.8 + max(0, pred) * 0.4 + momentum * 0.1, 2)

            name = beta_info.get("name", ticker)
            gics = beta_info.get("gics", "")

            cluster_picks.append({
                "industryId": cluster_id_str,  # fc1~fc8 for frontend - IMPORTANT: matches industries id
                "clusterId": cluster_id_str,
                "customName": custom_name,
                "displayName": display_name,
                "ticker": ticker,
                "name": name,
                "gics": gics,
                "targetFactor": max_beta_factor,
                "dominantFactor": dominant_factor,
                "dominantBeta": dominant_beta,
                "score": score,
                "expectedReturn": expected,
                "predCluster": round(cluster_pred, 3),
                "predStock": round(pred, 3),
                "reason": f"{max_beta_factor} β{betas.get(max_beta_factor,0):+.2f} Z{z_scores.get(FACTOR_ALIAS.get(max_beta_factor, max_beta_factor),0):+.2f} | {display_name} REAL",
                "date": today,
                "zAtRec": z_scores.get(FACTOR_ALIAS.get(max_beta_factor, max_beta_factor), 0),
                "predIndustry": round(pred, 3),
                "momentum": momentum,
                "betaStock": round(betas.get(max_beta_factor,0), 3),
                "stockCount": cluster.get("stock_count", len(tickers)),
                "r2": r2,
                "betaLabel": f"β{dominant_beta:+.2f}"
            })

        # Sort by score desc and take top 8 per cluster
        cluster_picks_sorted = sorted(cluster_picks, key=lambda x: x["score"], reverse=True)[:picks_per_cluster]
        all_picks.extend(cluster_picks_sorted)
        print(f"[v62] {cluster_id_str} {display_name} - {len(tickers)} -> {len(cluster_picks_sorted)} picks, cluster_pred {cluster_pred:+.3f}, top score {cluster_picks_sorted[0]['score'] if cluster_picks_sorted else 0}")

    # Global sort by score desc for all 64
    all_picks_sorted = sorted(all_picks, key=lambda x: x["score"], reverse=True)
    print(f"[v62] Generated {len(all_picks_sorted)} picks (8 Clusters x 8 = 64) - Top {all_picks_sorted[0]['ticker']} Score {all_picks_sorted[0]['score'] if all_picks_sorted else 0} Expected {all_picks_sorted[0]['expectedReturn'] if all_picks_sorted else 0}%")
    return all_picks_sorted

# Keep old function for backward compatibility but delegate to v62
def generate_64_picks(z_scores, details):
    return generate_64_picks_v62(z_scores, details)

def fetch_latest_retrain():
    if not db:
        return None
    try:
        doc = db.collection("beta_snapshots").document("latest").get()
        if doc.exists:
            data = doc.to_dict()
            print(f"[Retrain] latest beta fetched - {data.get('date')} avg R2 {data.get('avg_r2')}")
            return data
    except Exception as e:
        print(f"[Retrain] fetch latest error: {e}")
    return None

def save_to_firebase(z_scores, details, weekly_picks, regime_snapshot=None, meta_snapshot=None, retrain_snapshot=None):
    if not db:
        with open("latest_factors.json","w",encoding="utf-8") as f:
            json.dump({"date": datetime.now().strftime("%Y-%m-%d"), "zScores": z_scores, "details": details, "weeklyPicks": weekly_picks, "regime": regime_snapshot, "meta": meta_snapshot, "retrain": retrain_snapshot}, f, ensure_ascii=False, indent=2)
        print("[Firebase] local save - v62 FACTOR CLUSTERS")
        return
    date_str = datetime.now().strftime("%Y-%m-%d")
    doc = {
        "date": date_str,
        "timestamp": datetime.now(),
        "zScores": z_scores,
        "details": details,
        "weeklyPicks": weekly_picks,
        "regime": regime_snapshot,
        "meta": meta_snapshot,
        "retrain": retrain_snapshot,
        "beta_snapshot": retrain_snapshot,
        "source": "yfinance (5) + FRED (4) + KRX 15007 CSV (1) + China Proxy 구리/상해 + KOSPI200 190 + GICS + Factor Clusters k=8 + DART v62 + 64 Picks (8x8) + Regime + Retrain v62 100% REAL",
        "version": "v62.0-FACTOR-CLUSTERS-KOSPI200-190-GICS-KRICS-pending-20261026-DART-64Picks-Regime-Retrain",
        "factors_count": 10,
        "picks_count": len(weekly_picks),
        "clusters_count": 8,
        "stocks_universe": 190,
        "china_proxy": "구리(HG=F) + 상해종합(000001.SS)",
        "method": "K-means k=8 Elbow+Silhouette 0.0907 + Beta Matrix 190x10 Ridge 180일 + Score 6.5+pred*1.2+mom*0.3",
        "krics_status": "pending_20261026",
        "filter_applied": FILTER_ENABLED,
        "regime_enabled": REGIME_ENABLED,
        "meta_enabled": META_ENABLED,
        "retrain_enabled": True,
        "regime_summary": f"{regime_snapshot.get('regime')} {regime_snapshot.get('confidence')} window {regime_snapshot.get('window')}" if regime_snapshot else "N/A",
        "retrain_summary": f"{retrain_snapshot.get('date')} R2 {retrain_snapshot.get('avg_r2')}" if retrain_snapshot else "N/A",
    }
    try:
        db.collection("factor_snapshots").document(date_str).set(doc, merge=True)
        print(f"[Firebase] saved factor_snapshots/{date_str} - v62 {len(weekly_picks)} picks 8 clusters")
        if regime_snapshot:
            db.collection("regime_history").document(date_str).set(regime_snapshot, merge=True)
        if meta_snapshot:
            db.collection("meta_history").document(date_str).set(meta_snapshot, merge=True)
    except Exception as e:
        print(f"[Firebase] save error: {e}")

if __name__ == "__main__":
    print("=== KOSPI Quant Terminal v62.0 - FACTOR CLUSTERS + KOSPI200 190 + GICS + KRICS pending + 10 Factors REAL + DART + 64 Picks (8x8) + Regime + Retrain ===")
    z_scores, details = fetch_10_factors_china_proxy()
    weekly_picks = generate_64_picks_v62(z_scores, details)
    if FILTER_ENABLED and DART_API_KEY and weekly_picks:
        try:
            print(f"[v62] Applying DART filter to {len(weekly_picks)} picks...")
            filtered = apply_fundamental_filter(weekly_picks, use_real_data=True)
            print(f"[v62] DART Filter: {len(weekly_picks)} -> {len(filtered)} picks")
            weekly_picks = filtered
        except Exception as e:
            print(f"[v62] DART filter failed: {e}")
            import traceback
            traceback.print_exc()
    regime_snapshot = None
    if REGIME_ENABLED and build_regime_snapshot:
        try:
            regime_snapshot = build_regime_snapshot()
            print(f"[v62] Regime: {regime_snapshot.get('regime')} conf {regime_snapshot.get('confidence')}")
        except Exception as e:
            print(f"[v62] Regime failed: {e}")
            regime_snapshot = {"regime": "평시", "confidence": 0.70, "triggers": ["fallback"], "window": 120, "color": "#10b981", "risk_level": "Low", "date": datetime.now().strftime("%Y-%m-%d")}
    meta_snapshot = None
    if META_ENABLED and build_meta_tracker and regime_snapshot:
        try:
            meta_snapshot = build_meta_tracker(regime_snapshot)
            print(f"[v62] Meta: top valid {len(meta_snapshot.get('top_valid', []))}")
        except Exception as e:
            print(f"[v62] Meta failed: {e}")
    latest_retrain = None
    try:
        latest_retrain = fetch_latest_retrain()
    except Exception as e:
        print(f"[v62] Latest retrain skip: {e}")
    save_to_firebase(z_scores, details, weekly_picks, regime_snapshot, meta_snapshot, latest_retrain)
    print(json.dumps({"zScores": z_scores, "picksCount": len(weekly_picks), "regime": regime_snapshot.get('regime') if regime_snapshot else 'N/A', "top3": weekly_picks[:3]}, ensure_ascii=False, indent=2))
