"""
scripts/fundamental_filter.py - v54 DART Real Data Fundamental Filter (RELAXED)
v53에서 완화된 버전 - 불황기 고려, 대장주 보호, 최신 연도 자동 탐색
"""

import os
import requests
import xml.etree.ElementTree as ET
from pathlib import Path
import json
import time
from datetime import datetime

DART_API_KEY = os.environ.get('DART_API_KEY', '')

# === 완화된 필터 기준 (v54 RELAXED) - 2023년 불황 고려 ===
# 기존 v53: elec ROE 8% / 영업 5% → 삼성전자, SK하이닉스 탈락
# v54: ROE -10% / 영업 -10% → 불황기 적자 허용, 극심한 부실만 제거
INDUSTRY_FILTERS = {
    "elec": {"ROE": -10, "debt_ratio": 400, "current_ratio": 80, "op_margin": -10, "desc": "반도체 불황 완화 - 대장주 보호"},
    "auto": {"ROE": -5, "debt_ratio": 400, "current_ratio": 80, "op_margin": -5, "desc": "부채 많은 업종 완화"},
    "chem": {"ROE": -10, "debt_ratio": 400, "op_margin": -10, "desc": "2차전지 침체 완화 - 적자 허용"},
    "fin": {"ROE": 0, "debt_ratio": 1500, "current_ratio": 70, "desc": "금융 완화 - 저PBR 허용"},
    "bio": {"debt_ratio": 250, "current_ratio": 100, "ROE": -50, "desc": "바이오 완화 - 현금 중심"},
    "steel": {"ROE": -10, "debt_ratio": 500, "op_margin": -10, "current_ratio": 70, "desc": "철강 완화"},
    "const": {"ROE": -10, "debt_ratio": 500, "current_ratio": 80, "op_margin": -10, "desc": "건설/조선 완화"},
    "retail": {"ROE": -5, "debt_ratio": 350, "op_margin": -5, "desc": "유통 완화"},
}

# 대장주 화이트리스트 - 시총 상위, 절대 탈락시키지 않음 (부채 800% 이상 등 극심한 경우만 제외)
LARGE_CAP_WHITELIST = {
    "005930",  # 삼성전자
    "000660",  # SK하이닉스
    "373220",  # LG에너지솔루션
    "005380",  # 현대차
    "000270",  # 기아
    "105560",  # KB금융
    "055550",  # 신한지주
    "006400",  # 삼성SDI
    "051910",  # LG화학
    "005490",  # POSCO홀딩스
    "035720",  # 카카오 (성장주 보호)
    "000660",  # SK하이닉스 중복이지만 명시
}

# 티커 -> DART corp_code 매핑 캐시 (8x8 주요 종목)
TICKER_TO_CORP = {
    "005930": "00126380",  # 삼성전자
    "000660": "00164742",  # SK하이닉스
    "373220": "00164779",  # LG에너지솔루션
    "005380": "00164788",  # 현대차
    "000270": "00164777",  # 기아
    "105560": "00164710",  # KB금융
    "055550": "00164708",  # 신한지주
    "207940": "00145880",  # 삼성바이오로직스
    "068270": "00143162",  # 셀트리온
    "005490": "00102018",  # POSCO홀딩스
    "009540": "00102461",  # HD한국조선해양
    "035720": "00140649",  # 카카오
    "034220": "00111821",  # LG디스플레이
    "004020": "00102101",  # 현대제철
    "042660": "00144458",  # 대우조선해양 (새로 추가)
    "006800": "00112643",  # 미래에셋증권 (새로 추가)
    "006400": "00126433",  # 삼성SDI (새로 추가)
    "051910": "00120281",  # LG화학 (새로 추가)
}

def get_corp_codes():
    """DART 전체 corp_code XML 다운로드 및 파싱"""
    if not DART_API_KEY:
        print("DART_API_KEY not set, using cached mapping")
        return TICKER_TO_CORP
    
    try:
        url = "https://opendart.fss.or.kr/api/corpCode.xml"
        params = {"crtfc_key": DART_API_KEY}
        res = requests.get(url, params=params, timeout=30)
        
        import zipfile, io
        with zipfile.ZipFile(io.BytesIO(res.content)) as z:
            xml_content = z.read(z.namelist()[0])
        
        root = ET.fromstring(xml_content)
        mapping = {}
        for corp in root.findall('list'):
            stock_code = corp.findtext('stock_code', '').strip()
            corp_code = corp.findtext('corp_code', '').strip()
            if stock_code and corp_code:
                mapping[stock_code] = corp_code
        
        print(f"Loaded {len(mapping)} corp codes from DART")
        return mapping
    except Exception as e:
        print(f"Failed to load corp codes: {e}, using cache")
        return TICKER_TO_CORP

def get_financial_data_single(corp_code, bsns_year, reprt_code="11011"):
    """단일 연도 재무 데이터 조회"""
    if not DART_API_KEY:
        return None
    
    try:
        url = "https://opendart.fss.or.kr/api/fnlttSinglAcnt.json"
        params = {
            "crtfc_key": DART_API_KEY,
            "corp_code": corp_code,
            "bsns_year": bsns_year,
            "reprt_code": reprt_code,
        }
        res = requests.get(url, params=params, timeout=15).json()
        
        if res.get('status') != '000':
            return None
        
        data = {}
        for item in res.get('list', []):
            account_nm = item.get('account_nm', '')
            thstrm_amount = item.get('thstrm_amount', '').replace(',', '')
            
            try:
                amount = float(thstrm_amount) if thstrm_amount else 0
            except:
                continue
            
            if '당기순이익' in account_nm:
                data['net_income'] = amount
            elif '자본총계' in account_nm or '자기자본' in account_nm:
                data['equity'] = amount
            elif '부채총계' in account_nm:
                data['liability'] = amount
            elif '유동자산' in account_nm:
                data['current_asset'] = amount
            elif '유동부채' in account_nm:
                data['current_liability'] = amount
            elif '영업이익' in account_nm:
                data['op_income'] = amount
            elif '매출액' in account_nm or '영업수익' in account_nm:
                data['sales'] = amount
        
        result = {}
        if 'net_income' in data and 'equity' in data and data['equity'] != 0:
            result['ROE'] = (data['net_income'] / data['equity']) * 100
        
        if 'liability' in data and 'equity' in data and data['equity'] != 0:
            result['debt_ratio'] = (data['liability'] / data['equity']) * 100
        
        if 'current_asset' in data and 'current_liability' in data and data['current_liability'] != 0:
            result['current_ratio'] = (data['current_asset'] / data['current_liability']) * 100
        
        if 'op_income' in data and 'sales' in data and data['sales'] != 0:
            result['op_margin'] = (data['op_income'] / data['sales']) * 100
        
        return result if result else None
        
    except Exception as e:
        return None

def get_financial_data(corp_code, bsns_year=None, reprt_code="11011"):
    """최신 연도 자동 탐색 - 2024 → 2023 → 2022 순으로 fallback"""
    if not DART_API_KEY:
        return None
    
    # 현재 연도 기준으로 최신 사업보고서 탐색
    current_year = datetime.now().year
    # 2026년 9월이면 2024년 사업보고서가 최신 (2025년은 아직 미확정)
    years_to_try = []
    if bsns_year:
        years_to_try = [bsns_year]
    else:
        # 2024, 2023, 2022 순으로 시도
        for y in [str(current_year-1), str(current_year-2), "2024", "2023", "2022"]:
            if y not in years_to_try:
                years_to_try.append(y)
    
    for year in years_to_try:
        result = get_financial_data_single(corp_code, year, reprt_code)
        if result:
            # print(f"Found data for {corp_code} year {year}: {result}")
            return result
    
    return None

def check_filter_real(ticker, industry_id, corp_mapping=None):
    """DART 실데이터로 필터 체크 - 완화된 버전"""
    if industry_id not in INDUSTRY_FILTERS:
        return True, "No filter"
    
    # 대장주 화이트리스트 - 극심한 부실(부채 800% 이상 등) 아니면 통과
    if ticker in LARGE_CAP_WHITELIST:
        # 화이트리스트는 매우 완화된 기준으로만 체크
        if corp_mapping is None:
            corp_mapping = get_corp_codes()
        corp_code = corp_mapping.get(ticker)
        if corp_code:
            financials = get_financial_data(corp_code)
            if financials:
                # 부채 800% 이상 또는 ROE -30% 이하 등 극심한 경우만 탈락
                if financials.get('debt_ratio', 0) > 800:
                    return False, f"대장주지만 부채 {financials['debt_ratio']:.0f}% > 800% (극심)"
                if financials.get('ROE', 0) < -30:
                    return False, f"대장주지만 ROE {financials['ROE']:.1f}% < -30% (극심)"
        return True, "대장주 화이트리스트 - 보호"
    
    f = INDUSTRY_FILTERS[industry_id]
    
    if corp_mapping is None:
        corp_mapping = get_corp_codes()
    
    corp_code = corp_mapping.get(ticker)
    if not corp_code:
        return True, "No corp_code"
    
    financials = get_financial_data(corp_code)
    if not financials:
        return True, "No data"
    
    reasons = []
    
    if "ROE" in f and "ROE" in financials:
        if financials["ROE"] < f["ROE"]:
            reasons.append(f"ROE {financials['ROE']:.1f}% < {f['ROE']}%")
    
    if "debt_ratio" in f and "debt_ratio" in financials:
        if financials["debt_ratio"] > f["debt_ratio"]:
            reasons.append(f"부채 {financials['debt_ratio']:.0f}% > {f['debt_ratio']}%")
    
    if "current_ratio" in f and "current_ratio" in financials:
        if financials["current_ratio"] < f["current_ratio"]:
            reasons.append(f"유동 {financials['current_ratio']:.0f}% < {f['current_ratio']}%")
    
    if "op_margin" in f and "op_margin" in financials:
        if financials["op_margin"] < f["op_margin"]:
            reasons.append(f"영업 {financials['op_margin']:.1f}% < {f['op_margin']}%")
    
    if reasons:
        return False, " • ".join(reasons)
    else:
        return True, f"ROE {financials.get('ROE', 0):.1f}%"

def apply_fundamental_filter(picks, use_real_data=True):
    """주간 추천에 필터 적용 - DART 실데이터 완화된 버전 v54"""
    if not picks:
        return picks
    
    print(f"Applying fundamental filter to {len(picks)} picks (real_data={use_real_data}) - v54 RELAXED")
    
    if use_real_data and DART_API_KEY:
        corp_mapping = get_corp_codes()
        filtered = []
        filtered_out_count = 0
        for p in picks:
            ticker = p.get("ticker", "")
            industry_id = p.get("industryId", "")
            
            passed, reason = check_filter_real(ticker, industry_id, corp_mapping)
            
            if passed:
                filtered.append(p)
            else:
                print(f"  FILTERED OUT: {p.get('name')} {ticker} ({industry_id}) - {reason}")
                filtered_out_count += 1
            
            time.sleep(0.08)  # DART API rate limit 방지 (0.1 → 0.08로 단축)
        
        # 안전장치 강화: 70% 이상 유지 (기존 50% → 60% → 70%)
        if len(filtered) < len(picks) * 0.7:
            keep_count = int(len(picks) * 0.85)
            print(f"Too many filtered ({len(picks)}->{len(filtered)}), keeping top {keep_count} (85% safety) - RELAXED")
            return picks[:keep_count]
        
        print(f"Filter result: {len(picks)} -> {len(filtered)} (filtered {filtered_out_count} - RELAXED v54)")
        return filtered
    else:
        print("Using mock filter (DART_API_KEY not set)")
        return picks
