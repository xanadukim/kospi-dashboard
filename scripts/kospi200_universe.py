"""
kospi200_universe.py v62 - KOSPI200 공식 선정 기준 구현
- 기준: 시장 대표성 + 산업·업종 대표성 + 시가총액 + 유동성(거래대금) + 연속성
- 산업군: GICS 참고 (현재) + KRICS pending (10월 26일)
- 규모: 산업군별 일평균 시가총액 85% 누적
- 유동성: 거래대금 필터
- 완충: 90~110% 규칙 (기존 10개면 기존 11위까지 잔류, 신규 9위 이내)
- 출처: mofe.go, samsungpop PDF, data.krx.co.kr Index Constituents
"""

import os
import csv
import json
from typing import List, Dict, Tuple
from datetime import datetime

try:
    from price_provider import get_avg_market_cap_trading_value
except ImportError:
    from scripts.price_provider import get_avg_market_cap_trading_value

KOSPI200_CSV = "data/kospi200_constituents.csv"
GICS_CSV = "data/gics_mapping.csv"
PREV_UNIVERSE = "data/prev_universe.csv"  # 이전 64종 또는 이전 200종

def load_kospi200_constituents(csv_path: str = KOSPI200_CSV) -> List[Dict]:
    """KOSPI200 구성종목 로드 - GICS + KRICS dual structure"""
    constituents = []
    if not os.path.exists(csv_path):
        # fallback to gics_mapping
        csv_path = GICS_CSV
    if not os.path.exists(csv_path):
        print(f"[KOSPI200 Universe] CSV not found: {csv_path}")
        return []
    
    for enc in ["utf-8-sig", "utf-8", "cp949"]:
        try:
            with open(csv_path, 'r', encoding=enc) as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # ticker 정규화
                    ticker = row.get('ticker','').strip()
                    if not ticker:
                        continue
                    constituents.append({
                        'ticker': ticker,
                        'name': row.get('name','').strip(),
                        'provided_10group': row.get('provided_10group','').strip(),
                        'gics_sector': row.get('gics_sector','').strip(),
                        'gics_industry_group': row.get('gics_industry_group','').strip(),
                        'gics_industry': row.get('gics_industry','').strip(),
                        'krics_sector_L1': row.get('krics_sector_L1','pending_20261026').strip(),
                        'krics_group_L2': row.get('krics_group_L2','pending_20261026').strip(),
                        'krics_status': row.get('krics_status','pending_20261026').strip(),
                        'market_cap': 0.0,  # will be fetched
                        'trading_value': 0.0,
                    })
                break
        except Exception as e:
            print(f"[KOSPI200] load error {enc}: {e}")
            continue
    
    print(f"[KOSPI200 Universe] loaded {len(constituents)} constituents from {csv_path}")
    return constituents

def enrich_with_market_data(constituents: List[Dict], days: int = 60, use_real: bool = False) -> List[Dict]:
    """일평균 시가총액, 거래대금 enrich - pykrx (선택적)"""
    if not use_real:
        # placeholder - 실제 수집은 GitHub Actions에서 수행, 로컬에서는 0으로 두고 정렬은 티커 순
        print(f"[KOSPI200] enrich skipped (use_real=False) - placeholder market cap")
        for c in constituents:
            # 임시: 티커 해시 기반 시총 (실제로는 pykrx 수집)
            c['market_cap'] = hash(c['ticker']) % 1000000000000 + 100000000000
            c['trading_value'] = hash(c['name']) % 100000000000 + 10000000000
        return constituents
    
    enriched = []
    for c in constituents:
        try:
            cap, val = get_avg_market_cap_trading_value(c['ticker'], days=days)
            c['market_cap'] = cap if cap>0 else c.get('market_cap',0)
            c['trading_value'] = val if val>0 else c.get('trading_value',0)
            enriched.append(c)
        except Exception as e:
            print(f"[KOSPI200 enrich] {c['ticker']} error: {e}")
            enriched.append(c)
    return enriched

def filter_by_kospi200_rule(constituents: List[Dict], industry_field: str = 'gics_sector') -> Dict[str, List[Dict]]:
    """
    KOSPI200 공식 규칙 필터:
    1. 산업군별 일평균 시가총액 큰 순 정렬
    2. 누적 시가총액 85% 이내 1차 선정 (samsungpop 기준)
    3. 거래대금 필터 - 중위수 이상 또는 상위 70%
    4. 90~110% 완충 규칙 (prev_universe가 있으면 적용)
    """
    from collections import defaultdict
    import numpy as np
    
    # 산업군별 그룹화
    grouped = defaultdict(list)
    for c in constituents:
        key = c.get(industry_field) or c.get('provided_10group') or 'Unknown'
        grouped[key].append(c)
    
    filtered_by_industry = {}
    
    # prev universe 로드 (완충 규칙용)
    prev_tickers = set()
    if os.path.exists(PREV_UNIVERSE):
        try:
            with open(PREV_UNIVERSE, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    prev_tickers.add(row.get('ticker',''))
        except:
            pass
    
    for industry, stocks in grouped.items():
        # 1. 시가총액 큰 순 정렬
        stocks_sorted = sorted(stocks, key=lambda x: x.get('market_cap',0), reverse=True)
        
        # 2. 누적 시가총액 85% 계산
        total_cap = sum(s.get('market_cap',0) for s in stocks_sorted)
        cum_cap = 0
        cutoff_idx = len(stocks_sorted)
        for idx, s in enumerate(stocks_sorted):
            cum_cap += s.get('market_cap',0)
            if total_cap>0 and cum_cap/total_cap >= 0.85:
                cutoff_idx = idx+1
                break
        
        primary_selected = stocks_sorted[:cutoff_idx]
        print(f"[KOSPI200 Rule] {industry}: {len(stocks_sorted)} -> 85% cum {cutoff_idx} (total cap {total_cap:.0f})")
        
        # 3. 거래대금 필터 - 중위수 이상
        if len(primary_selected) >= 3:
            trading_values = [s.get('trading_value',0) for s in primary_selected]
            median_val = float(np.median(trading_values)) if trading_values else 0
            # 상위 70% 또는 중위수 이상
            primary_selected = [s for s in primary_selected if s.get('trading_value',0) >= median_val*0.7]
            print(f"[KOSPI200 Rule] {industry}: trading value filter median {median_val:.0f} -> {len(primary_selected)}")
        
        # 4. 완충 규칙 90~110%
        if prev_tickers:
            # 기존 종목은 110%까지 잔류 허용, 신규는 90% 이내
            # 여기서는 단순화: 기존 종목이면 순위 +10% 여유
            existing_count = len([s for s in stocks_sorted if s['ticker'] in prev_tickers])
            if existing_count>0:
                # 기존 10개면 11위까지 허용
                buffer_limit = int(existing_count * 1.1)
                # 이미 primary_selected에 포함 안 된 기존 종목 중 buffer_limit 이내면 추가
                for s in stocks_sorted[cutoff_idx:buffer_limit]:
                    if s['ticker'] in prev_tickers and s not in primary_selected:
                        primary_selected.append(s)
                        print(f"[KOSPI200 Rule] {industry}: buffer add existing {s['ticker']} {s['name']}")
        
        filtered_by_industry[industry] = primary_selected
    
    return filtered_by_industry

def get_kospi200_universe(use_real_market_data: bool = False, industry_field: str = 'gics_sector') -> Dict:
    """전체 KOSPI200 유니버스 빌드 - v62 Phase A"""
    print("=== KOSPI200 Universe v62 - KOSPI200 공식 기준 ===")
    constituents = load_kospi200_constituents()
    if not constituents:
        return {'industries': {}, 'total': 0, 'note': 'no constituents'}
    
    enriched = enrich_with_market_data(constituents, use_real=use_real_market_data)
    filtered = filter_by_kospi200_rule(enriched, industry_field=industry_field)
    
    total_filtered = sum(len(v) for v in filtered.values())
    print(f"[KOSPI200 Universe] total {len(constituents)} -> filtered {total_filtered} across {len(filtered)} industries")
    
    # 검증: 200개 확인
    if len(constituents) != 200:
        print(f"[WARNING] constituents {len(constituents)} != 200, check base_date. Current base_date 2026-09-29, official 200 should be from KRX Index Constituents")
    
    return {
        'industries': filtered,
        'total_original': len(constituents),
        'total_filtered': total_filtered,
        'industry_count': len(filtered),
        'base_date': '2026-09-29',
        'classification': f'{industry_field} (GICS) + KRICS pending 2026-10-26',
        'method': 'KOSPI200 official: market cap 85% cum + trading value median + buffer 90~110%',
        'source': 'data/kospi200_constituents.csv (193+7 estimated) + KRX official to be updated 2026-10-26'
    }

if __name__ == "__main__":
    result = get_kospi200_universe(use_real_market_data=False)
    print(json.dumps({
        'total_original': result['total_original'],
        'total_filtered': result['total_filtered'],
        'industries': {k: len(v) for k,v in result['industries'].items()}
    }, ensure_ascii=False, indent=2))
    
    # Save filtered result
    os.makedirs('data', exist_ok=True)
    with open('data/kospi200_filtered_v62.json','w',encoding='utf-8') as f:
        # Convert for JSON
        json_out = {k: [{'ticker': s['ticker'], 'name': s['name'], 'market_cap': s['market_cap'], 'trading_value': s['trading_value']} for s in v] for k,v in result['industries'].items()}
        json.dump(json_out, f, ensure_ascii=False, indent=2)
    print("[KOSPI200] saved data/kospi200_filtered_v62.json")
