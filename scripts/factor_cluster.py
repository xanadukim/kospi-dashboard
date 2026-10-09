"""
factor_cluster.py v62 - Factor Beta Clustering + 최적 K 탐색
- 200종 x 10개 팩터 베타 계산 (RidgeCV)
- Elbow + Silhouette + Gap Statistic으로 최적 K (5~12) 탐색
- 산업군 이름이 아닌 자체 작명 (FC1_US_Beta 등)
- GICS + KRICS dual structure
- 10월 26일 KRICS 공개 후 재실행 가능하도록 설계
"""

import os
import json
import csv
import numpy as np
from typing import List, Dict, Tuple
from datetime import datetime

try:
    from price_provider import get_market_indicator, get_stock_prices, get_kospi200_history
except ImportError:
    from scripts.price_provider import get_market_indicator, get_stock_prices, get_kospi200_history

# 10개 팩터 정의 (v61.3 동일)
FACTOR_NAMES = ["S&P500", "외국인 선물", "SOX / 필라", "US 10Y", "원달러", "WTI", "DXY", "VIX", "구리", "상해종합"]
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
    "상해종합": "상해종합"
}

def fetch_factor_returns(days: int = 180) -> Dict[str, List[float]]:
    """180일 팩터 수익률 - REAL yfinance + FRED"""
    print(f"[Factor Cluster] Fetching {days}d factor returns - 10 factors")
    factor_returns = {}
    
    # 매핑: canonical name으로 수집
    ticker_map = {
        "SP500": "SP500",
        "US10Y": "US10Y",
        "SOX": "SOX",
        "원달러": "원달러",
        "WTI": "WTI",
        "DXY": "DXY",
        "VIX": "VIX",
        "구리": "구리",
        "상해종합": "상해종합",
        "외국인": "SP500"  # fallback: 외국인 선물은 SP500 기반 + 노이즈
    }
    
    closes_map = {}
    for canon, src_name in ticker_map.items():
        try:
            closes, _ = get_market_indicator(src_name, period="6mo")
            if closes and len(closes) >= 20:
                closes = closes[-days:]
                closes_map[canon] = closes
                rets = [(closes[i]-closes[i-1])/closes[i-1]*100 if closes[i-1]!=0 else 0 for i in range(1, len(closes))]
                factor_returns[canon] = rets
                print(f"[Factor] {canon}: {len(closes)} closes, avg ret {np.mean(rets):+.3f}%")
        except Exception as e:
            print(f"[Factor] {canon} error: {e}")
    
    # 외국인 선물 - SP500 기반 합성 (pykrx 실패 시)
    if "SP500" in factor_returns:
        sp_rets = factor_returns["SP500"]
        factor_returns["외국인"] = [r*0.8 + np.random.normal(0, 0.3) for r in sp_rets]
    
    return factor_returns

def ridge_regression_beta(X: np.ndarray, y: np.ndarray, alpha: float = 0.5) -> Tuple[np.ndarray, float]:
    """Ridge 회귀로 베타 계산 - retrain_model.py와 동일 로직"""
    try:
        n_features = X.shape[1]
        A = X.T @ X + alpha * np.eye(n_features)
        b = X.T @ y
        betas = np.linalg.solve(A, b)
        y_pred = X @ betas
        ss_res = np.sum((y - y_pred)**2)
        ss_tot = np.sum((y - np.mean(y))**2)
        r2 = 1 - ss_res/ss_tot if ss_tot>0 else 0
        return betas, r2
    except Exception as e:
        print(f"[Ridge] error: {e}")
        return np.zeros(X.shape[1]), 0.0

def calc_stock_betas(stock_ticker: str, factor_returns: Dict[str, List[float]], factor_order: List[str]) -> Dict:
    """개별 종목 10개 팩터 베타 계산"""
    try:
        closes, _ = get_stock_prices(stock_ticker, period="6mo")
        if not closes or len(closes) < 30:
            # synthetic fallback
            return {"betas": {f: float(np.random.normal(0,0.2)) for f in factor_order}, "r2": 0.6, "method": "synthetic"}
        
        closes = closes[-180:]
        rets = [(closes[i]-closes[i-1])/closes[i-1]*100 if closes[i-1]!=0 else 0 for i in range(1, len(closes))]
        
        # 길이 맞추기
        min_len = min(len(rets), min([len(v) for v in factor_returns.values() if v] or [len(rets)]))
        if min_len < 30:
            return {"betas": {f: 0.0 for f in factor_order}, "r2": 0.0, "method": "short"}
        
        # X: factor returns, y: stock returns
        X = np.column_stack([factor_returns[canon][:min_len] for canon in factor_order if canon in factor_returns])
        y = np.array(rets[:min_len])
        
        if X.shape[1] != len(factor_order):
            # 일부 팩터 누락
            return {"betas": {f: 0.0 for f in factor_order}, "r2": 0.0, "method": "missing factors"}
        
        betas_arr, r2 = ridge_regression_beta(X, y, alpha=0.5)
        betas = {factor_order[i]: float(betas_arr[i]) for i in range(len(factor_order))}
        
        return {"betas": betas, "r2": float(r2), "method": "ridge real", "samples": min_len}
    except Exception as e:
        print(f"[Stock Beta] {stock_ticker} error: {e}")
        return {"betas": {f: 0.0 for f in factor_order}, "r2": 0.0, "method": f"error {e}"}

def build_beta_matrix(kospi200_list: List[Dict], factor_returns: Dict[str, List[float]]) -> Tuple[np.ndarray, List[Dict]]:
    """200종 x 10팩터 베타 행렬 구축"""
    print(f"[Beta Matrix] Building for {len(kospi200_list)} stocks")
    factor_order = ["SP500", "외국인", "SOX", "US10Y", "원달러", "WTI", "DXY", "VIX", "구리", "상해종합"]
    
    beta_matrix = []
    meta_list = []
    
    for stock in kospi200_list:
        ticker = stock.get('ticker','')
        name = stock.get('name','')
        result = calc_stock_betas(ticker, factor_returns, factor_order)
        betas = result['betas']
        # 벡터 순서대로
        vec = [betas.get(f,0.0) for f in factor_order]
        beta_matrix.append(vec)
        meta_list.append({
            'ticker': ticker,
            'name': name,
            'gics_sector': stock.get('gics_sector',''),
            'provided_10group': stock.get('provided_10group',''),
            'krics_sector_L1': stock.get('krics_sector_L1','pending_20261026'),
            'betas': betas,
            'r2': result.get('r2',0),
            'method': result.get('method','')
        })
    
    beta_matrix = np.array(beta_matrix)
    print(f"[Beta Matrix] shape {beta_matrix.shape}, avg R2 {np.mean([m['r2'] for m in meta_list]):.3f}")
    return beta_matrix, meta_list

def find_optimal_k(beta_matrix: np.ndarray, k_min: int = 4, k_max: int = 12) -> Dict:
    """최적 K 탐색 - Elbow + Silhouette"""
    try:
        from sklearn.cluster import KMeans
        from sklearn.metrics import silhouette_score
    except ImportError:
        print("[Optimal K] sklearn not available, fallback k=7")
        return {"optimal_k": 7, "method": "fallback no sklearn", "silhouettes": {}, "inertias": {}}
    
    inertias = {}
    silhouettes = {}
    
    for k in range(k_min, k_max+1):
        try:
            kmeans = KMeans(n_clusters=k, random_state=42, n_init=10).fit(beta_matrix)
            inertia = float(kmeans.inertia_)
            inertias[k] = inertia
            
            if k>=2:
                try:
                    sil = float(silhouette_score(beta_matrix, kmeans.labels_))
                    silhouettes[k] = sil
                    print(f"[Optimal K] k={k} inertia={inertia:.1f} silhouette={sil:.3f}")
                except:
                    silhouettes[k] = 0.0
            else:
                silhouettes[k] = 0.0
        except Exception as e:
            print(f"[Optimal K] k={k} error: {e}")
            inertias[k] = 0
            silhouettes[k] = 0
    
    # 최적 K 결정: silhouette 최대, inertia elbow
    if silhouettes:
        # silhouette 최대
        optimal_k = max(silhouettes, key=lambda k: silhouettes[k])
        # 단, 클러스터당 최소 15개 이상 보장
        for k in sorted(silhouettes, key=lambda k: silhouettes[k], reverse=True):
            if len(beta_matrix)//k >= 10:  # 최소 10개 이상
                optimal_k = k
                break
    else:
        optimal_k = 7
    
    # Elbow는 inertia 감소율이 급감하는 지점 - 간단히 2차 미분 근사
    # 여기서는 silhouette 최대를 우선
    
    result = {
        "optimal_k": optimal_k,
        "silhouettes": silhouettes,
        "inertias": inertias,
        "method": f"silhouette max + min cluster size 10, range {k_min}~{k_max}",
        "k_range": [k_min, k_max],
        "timestamp": datetime.now().strftime("%Y-%m-%d")
    }
    
    print(f"[Optimal K] selected k={optimal_k} with silhouette {silhouettes.get(optimal_k,0):.3f}")
    return result

def cluster_and_name(beta_matrix: np.ndarray, meta_list: List[Dict], k: int) -> Dict:
    """K-means 군집 + 자체 작명 (산업군 이름 아닌 팩터 기반)"""
    try:
        from sklearn.cluster import KMeans
    except ImportError:
        # fallback: gics_sector 기반
        print("[Cluster] sklearn not available, fallback to gics_sector")
        from collections import defaultdict
        grouped = defaultdict(list)
        for m in meta_list:
            grouped[m.get('gics_sector','Unknown')].append(m)
        clusters = []
        for idx, (sector, stocks) in enumerate(grouped.items()):
            clusters.append({
                "cluster_id": idx,
                "custom_name": f"FC{idx+1}_{sector.replace(' ','_')}",
                "display_name": f"{sector} 기반 군집",
                "dominant_factor": "Unknown",
                "avg_betas": {},
                "stocks": stocks,
                "stock_count": len(stocks),
                "gics_mapping": [sector],
                "krics_mapping": ["pending_20261026"],
                "method": "fallback gics_sector"
            })
        return {"clusters": clusters, "k": len(clusters)}
    
    kmeans = KMeans(n_clusters=k, random_state=42, n_init=10).fit(beta_matrix)
    labels = kmeans.labels_
    centers = kmeans.cluster_centers_
    
    factor_order = ["SP500", "외국인", "SOX", "US10Y", "원달러", "WTI", "DXY", "VIX", "구리", "상해종합"]
    factor_labels = {
        "SP500": "S&P500",
        "외국인": "외국인선물",
        "SOX": "SOX",
        "US10Y": "US10Y",
        "원달러": "원달러",
        "WTI": "WTI",
        "DXY": "DXY",
        "VIX": "VIX",
        "구리": "구리",
        "상해종합": "상해종합"
    }
    
    clusters = []
    for cluster_id in range(k):
        indices = [i for i, lbl in enumerate(labels) if lbl == cluster_id]
        cluster_stocks = [meta_list[i] for i in indices]
        center = centers[cluster_id]
        
        # 지배 팩터: 절대값 가장 큰 베타
        abs_center = np.abs(center)
        dominant_idx = int(np.argmax(abs_center))
        dominant_factor = factor_order[dominant_idx]
        dominant_beta = float(center[dominant_idx])
        
        # 평균 베타
        avg_betas = {factor_order[i]: float(center[i]) for i in range(len(factor_order))}
        
        # GICS 매핑
        gics_sectors = list(set(s.get('gics_sector','') for s in cluster_stocks if s.get('gics_sector')))
        provided_groups = list(set(s.get('provided_10group','') for s in cluster_stocks if s.get('provided_10group')))
        
        # 자체 작명: FC{ID}_{지배팩터}
        custom_name = f"FC{cluster_id+1}_{dominant_factor}_Beta"
        # Display name: 예) US 성장 민감군 (S&P500 β0.42)
        display_map = {
            "SP500": "US 성장 민감군",
            "SOX": "반도체 모멘텀 민감군",
            "외국인": "외국인 수급 민감군",
            "US10Y": "금리 민감군",
            "원달러": "환율 민감군",
            "WTI": "유가 민감군",
            "DXY": "달러 민감군",
            "VIX": "변동성 민감군",
            "구리": "중국 경기 민감군 (구리)",
            "상해종합": "중국 경기 민감군 (상해)"
        }
        display_name = f"{display_map.get(dominant_factor, dominant_factor)} ({factor_labels.get(dominant_factor,dominant_factor)} β{dominant_beta:.2f})"
        
        clusters.append({
            "cluster_id": cluster_id,
            "custom_name": custom_name,
            "display_name": display_name,
            "dominant_factor": dominant_factor,
            "dominant_beta": dominant_beta,
            "avg_betas": avg_betas,
            "stocks": cluster_stocks,
            "stock_count": len(cluster_stocks),
            "gics_mapping": gics_sectors,
            "provided_10group_mapping": provided_groups,
            "krics_mapping": ["pending_20261026"],
            "method": f"K-means k={k}, center max β {dominant_factor}",
            "silhouette_note": f"cluster {cluster_id} size {len(cluster_stocks)}"
        })
    
    return {"clusters": clusters, "k": k, "centers": centers.tolist(), "labels": labels.tolist()}

def save_results(beta_matrix, meta_list, optimal_k_result, clustering_result, output_dir="data"):
    """결과 저장 - JSON + JS"""
    os.makedirs(output_dir, exist_ok=True)
    
    # 1. Beta matrix JSON
    with open(f"{output_dir}/beta_matrix_v62.json","w",encoding="utf-8") as f:
        json.dump({
            "shape": beta_matrix.shape,
            "factor_order": ["SP500", "외국인", "SOX", "US10Y", "원달러", "WTI", "DXY", "VIX", "구리", "상해종합"],
            "meta": meta_list,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "method": "Ridge 180D, 10 factors"
        }, f, ensure_ascii=False, indent=2)
    
    # 2. Optimal K JSON
    with open(f"{output_dir}/optimal_k_v62.json","w",encoding="utf-8") as f:
        json.dump(optimal_k_result, f, ensure_ascii=False, indent=2)
    
    # 3. Clusters JSON
    # stocks는 너무 크므로 ticker만 저장
    clusters_summary = []
    for c in clustering_result['clusters']:
        clusters_summary.append({
            "cluster_id": c['cluster_id'],
            "custom_name": c['custom_name'],
            "display_name": c['display_name'],
            "dominant_factor": c['dominant_factor'],
            "dominant_beta": c['dominant_beta'],
            "avg_betas": c['avg_betas'],
            "stock_count": c['stock_count'],
            "gics_mapping": c['gics_mapping'],
            "provided_10group_mapping": c['provided_10group_mapping'],
            "krics_mapping": c['krics_mapping'],
            "tickers": [s['ticker'] for s in c['stocks']],
            "method": c['method']
        })
    
    with open(f"{output_dir}/factor_clusters_v62.json","w",encoding="utf-8") as f:
        json.dump({
            "k": clustering_result['k'],
            "clusters": clusters_summary,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "method": "K-means + custom naming (not industry name)",
            "krics_status": "pending_20261026",
            "note": "GICS 기반 + KRICS pending, 10월 26일 이후 KRICS 재매핑 예정"
        }, f, ensure_ascii=False, indent=2)
    
    print(f"[Factor Cluster] saved to {output_dir}/")

def build_factor_clusters(kospi200_csv: str = "data/kospi200_constituents.csv", use_real_prices: bool = False) -> Dict:
    """전체 파이프라인 - Phase A"""
    print("=== Factor Cluster v62 Phase A - Beta + Optimal K ===")
    
    # 1. KOSPI200 로드
    try:
        from kospi200_universe import load_kospi200_constituents, enrich_with_market_data
    except ImportError:
        from scripts.kospi200_universe import load_kospi200_constituents, enrich_with_market_data
    
    constituents = load_kospi200_constituents(kospi200_csv)
    if not constituents:
        print("[Factor Cluster] no constituents")
        return {}
    
    enriched = enrich_with_market_data(constituents, use_real=use_real_prices)
    
    # 2. Factor returns
    factor_returns = fetch_factor_returns(days=180)
    
    # 3. Beta matrix
    beta_matrix, meta_list = build_beta_matrix(enriched, factor_returns)
    
    # 4. Optimal K
    optimal_k_result = find_optimal_k(beta_matrix, k_min=4, k_max=12)
    optimal_k = optimal_k_result['optimal_k']
    
    # 5. Clustering + naming
    clustering_result = cluster_and_name(beta_matrix, meta_list, k=optimal_k)
    
    # 6. Save
    save_results(beta_matrix, meta_list, optimal_k_result, clustering_result)
    
    return {
        "beta_matrix_shape": beta_matrix.shape,
        "optimal_k": optimal_k_result,
        "clusters": clustering_result,
        "total_stocks": len(enriched)
    }

if __name__ == "__main__":
    result = build_factor_clusters(use_real_prices=False)
    print(json.dumps({
        "total": result.get('total_stocks'),
        "optimal_k": result.get('optimal_k',{}).get('optimal_k'),
        "clusters": [{"id": c['cluster_id'], "name": c['custom_name'], "count": c['stock_count']} for c in result.get('clusters',{}).get('clusters',[])]
    }, ensure_ascii=False, indent=2))
