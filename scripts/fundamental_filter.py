"""
scripts/fundamental_filter.py - v53 DART Real Data Fundamental Filter
DART Open API를 사용한 실제 재무제표 기반 부실주 필터

API Docs: https://opendart.fss.or.kr/guide/main.do
"""

import os
import requests
import xml.etree.ElementTree as ET
from pathlib import Path
import json
import time

DART_API_KEY = os.environ.get('DART_API_KEY', '')

# Industry별 최적 필터 기준 (v51 기반, DART 실데이터로 검증)
INDUSTRY_FILTERS = {
    "elec": {"ROE": 8, "debt_ratio": 200, "current_ratio": 120, "op_margin": 5, "PER": (0, 50), "desc": "반도체는 고수익 필수"},
    "auto": {"ROE": 5, "debt_ratio": 250, "current_ratio": 100, "op_margin": 2, "sales_growth": -20, "desc": "부채 많은 업종, 유동성으로 생존"},
    "chem": {"ROE": 3, "debt_ratio": 250, "op_margin": 3, "sales_growth": -20, "PER": (0, 80), "desc": "2차전지 고PER 허용, 화학은 마진"},
    "fin": {"ROE": 5, "PBR": 1.5, "debt_ratio": 1000, "current_ratio": 90, "desc": "저PBR 고ROE가 정답"},
    "bio": {"debt_ratio": 150, "current_ratio": 150, "sales_growth": -30, "ROE": -20, "desc": "현금과 부채로 생존력 판단"},
    "steel": {"ROE": 3, "debt_ratio": 300, "op_margin": 2, "current_ratio": 90, "desc": "부채 많음, 마진으로 버티는지"},
    "const": {"ROE": 3, "debt_ratio": 300, "current_ratio": 110, "op_margin": 1, "desc": "유동성이 생명"},
    "retail": {"ROE": 5, "PER": (0, 40), "debt_ratio": 200, "op_margin": 3, "PBR": 5, "desc": "거품 제거, 효율 판단"},
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
        
        # XML 파싱 (zip 파일임)
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

def get_financial_data(corp_code, bsns_year="2023", reprt_code="11011"):
    """단일회사 주요계정 조회 - ROE, 부채비율 등 계산"""
    if not DART_API_KEY:
        return None
    
    try:
        url = "https://opendart.fss.or.kr/api/fnlttSinglAcnt.json"
        params = {
            "crtfc_key": DART_API_KEY,
            "corp_code": corp_code,
            "bsns_year": bsns_year,
            "reprt_code": reprt_code,  # 11011: 사업보고서
        }
        res = requests.get(url, params=params, timeout=15).json()
        
        if res.get('status') != '000':
            # print(f"DART API error for {corp_code}: {res.get('message')}")
            return None
        
        # 주요 계정 파싱
        data = {}
        for item in res.get('list', []):
            account_nm = item.get('account_nm', '')
            thstrm_amount = item.get('thstrm_amount', '').replace(',', '')
            
            try:
                amount = float(thstrm_amount) if thstrm_amount else 0
            except:
                continue
            
            # 필요한 계정 매핑
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
        
        # 재무비율 계산
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
        print(f"Error fetching financials for {corp_code}: {e}")
        return None

def check_filter_real(ticker, industry_id, corp_mapping=None):
    """DART 실데이터로 필터 체크"""
    if industry_id not in INDUSTRY_FILTERS:
        return True, "No filter"
    
    f = INDUSTRY_FILTERS[industry_id]
    
    # corp_code 조회
    if corp_mapping is None:
        corp_mapping = get_corp_codes()
    
    corp_code = corp_mapping.get(ticker)
    if not corp_code:
        # print(f"No corp_code for {ticker}, skipping filter (pass)")
        return True, "No corp_code"
    
    # DART 재무 데이터 조회
    financials = get_financial_data(corp_code)
    if not financials:
        # 데이터 없으면 통과 (보수적)
        return True, "No data"
    
    # 필터 체크
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
    """주간 추천에 필터 적용 - DART 실데이터 버전"""
    if not picks:
        return picks
    
    print(f"Applying fundamental filter to {len(picks)} picks (real_data={use_real_data})")
    
    if use_real_data and DART_API_KEY:
        corp_mapping = get_corp_codes()
        filtered = []
        for p in picks:
            ticker = p.get("ticker", "")
            industry_id = p.get("industryId", "")
            
            passed, reason = check_filter_real(ticker, industry_id, corp_mapping)
            
            if passed:
                filtered.append(p)
            else:
                print(f"  FILTERED OUT: {p.get('name')} {ticker} ({industry_id}) - {reason}")
            
            time.sleep(0.1)  # DART API rate limit 방지
        
        # 너무 많이 필터링되면 원본 유지 (안전장치)
        if len(filtered) < len(picks) * 0.5:
            print(f"Too many filtered ({len(picks)}->{len(filtered)}), keeping original 80%")
            return picks[:int(len(picks)*0.8)]
        
        print(f"Filter result: {len(picks)} -> {len(filtered)}")
        return filtered
    else:
        # Mock 필터 (API 키 없을 때)
        print("Using mock filter (DART_API_KEY not set)")
        return picks
