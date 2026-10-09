"""
krics_fetcher.py v62 - KRICS 공식 분류 결과 크롤러 (2026-10-26 이후)
- KRX 인덱스 홈페이지에서 종목별 KRICS 1·2단계 분류 결과 공개 예정
- URL: KRX 인덱스 홈페이지 (예정)
- 현재는 pending, 10월 26일 이후 구현
- etoday: https://www.etoday.co.kr/news/view/2628472
"""

import os
import csv
import json
import requests
from datetime import datetime
from typing import List, Dict

KRICS_OFFICIAL_URL = "https://index.krx.co.kr"  # 예상 URL, 10월 26일 이후 확정
KRICS_METHODOLOGY_DATE = "2026-09-23"
KRICS_RESULT_DATE = "2026-10-26"

# KRICS 9개 섹터 (공식)
KRICS_SECTORS = [
    "에너지화학",
    "소재",
    "산업재",
    "모빌리티",
    "정보기술",
    "금융 및 부동산",
    "소비재",
    "헬스케어",
    "미디어 및 콘텐츠"
]

def fetch_krics_classification_official() -> List[Dict]:
    """
    10월 26일 이후 KRX 인덱스 홈페이지에서 KRICS 분류 크롤링
    현재는 pending이므로 샘플 구조만 반환
    """
    print(f"[KRICS Fetcher] Official KRICS results expected from {KRICS_RESULT_DATE}")
    print(f"[KRICS Fetcher] Methodology effective from {KRICS_METHODOLOGY_DATE}")
    print(f"[KRICS Fetcher] Sectors: {KRICS_SECTORS}")
    
    # TODO: 10월 26일 이후 구현
    # 예상 API: https://data.krx.co.kr/svc/apis/idx/krics_classification?basDd=20261026
    # 또는 https://index.krx.co.kr/MKD/IDX/...
    
    # 현재는 기존 mapping 파일의 krics 컬럼을 pending으로 유지
    existing_csv = "data/kospi200_constituents.csv"
    if not os.path.exists(existing_csv):
        print(f"[KRICS] {existing_csv} not found")
        return []
    
    results = []
    try:
        with open(existing_csv, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                results.append({
                    'ticker': row.get('ticker',''),
                    'name': row.get('name',''),
                    'krics_sector_L1': 'pending_20261026',
                    'krics_group_L2': 'pending_20261026',
                    'krics_industry_L3': 'pending_20261026',
                    'krics_sub_industry_L4': 'pending_20261026',
                    'krics_status': 'pending_20261026',
                    'fetch_date': datetime.now().strftime('%Y-%m-%d'),
                    'source': 'KRICS pending - to be updated 2026-10-26'
                })
    except Exception as e:
        print(f"[KRICS] error reading existing: {e}")
    
    return results

def update_krics_mapping(krics_results: List[Dict], output_csv: str = "data/kospi200_constituents.csv"):
    """KRICS 결과를 기존 CSV에 업데이트"""
    if not krics_results:
        print("[KRICS] no results to update")
        return
    
    # 기존 CSV 읽기
    existing = {}
    if os.path.exists(output_csv):
        try:
            with open(output_csv, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    existing[row.get('ticker','')] = row
        except Exception as e:
            print(f"[KRICS update] read error: {e}")
    
    # 업데이트
    for res in krics_results:
        ticker = res.get('ticker','')
        if ticker in existing:
            existing[ticker]['krics_sector_L1'] = res.get('krics_sector_L1','')
            existing[ticker]['krics_group_L2'] = res.get('krics_group_L2','')
            existing[ticker]['krics_status'] = res.get('krics_status','updated')
    
    # 저장
    if existing:
        fieldnames = list(list(existing.values())[0].keys())
        with open(output_csv, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for ticker, row in existing.items():
                writer.writerow(row)
        print(f"[KRICS] updated {output_csv} with {len(krics_results)} results")

def generate_krics_report():
    """KRICS 전환 보고서 생성"""
    report = {
        "title": "KRICS Transition Report",
        "methodology_date": KRICS_METHODOLOGY_DATE,
        "result_date": KRICS_RESULT_DATE,
        "sectors": KRICS_SECTORS,
        "status": "pending_20261026",
        "current_classification": "GICS based (2026-09-29) + KRICS pending",
        "future_classification": "KRICS 9 sectors after 2026-10-26",
        "expected_changes": [
            "배터리 기업: 산업재·화학·IT → 별도 배터리 산업",
            "자동차 및 부품: 모빌리티 섹터 통합",
            "조선·선박: 독립 산업군",
            "반도체/디스플레이: 세분화",
            "플랫폼·콘텐츠: 미디어 및 콘텐츠 재분류",
            "지주회사: 산업 배정 변경"
        ],
        "action_plan": [
            "2026-10-26: KRX 인덱스 홈페이지에서 KRICS 분류 결과 크롤링",
            "2026-10-26: data/kospi200_constituents.csv krics_* 컬럼 업데이트",
            "2026-10-26: factor_cluster.py 재실행 (KRICS 기준 재군집)",
            "2026-10-26: js/data.js v62 KRICS 버전 생성",
            "2026년 하반기: KOSPI200 등 대표지수 KRICS 단계적 적용 모니터링"
        ],
        "references": [
            "https://www.etoday.co.kr/news/view/2628472?trc=sub_list_news",
            "https://www.dailian.co.kr/news/view/1693610/",
            "https://data.krx.co.kr/contents/MDC/MAIN/main/index.cmd?locale=en"
        ],
        "generated": datetime.now().strftime("%Y-%m-%d")
    }
    
    os.makedirs('docs', exist_ok=True)
    with open('docs/krics_transition_report.json','w',encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    with open('docs/krics_transition_report.md','w',encoding='utf-8') as f:
        f.write(f"""# KRICS 전환 보고서
## {report['title']}

- 방법론 시행: {report['methodology_date']}
- 분류 결과 공개: {report['result_date']}
- 현재 상태: {report['status']}

### 9개 섹터
{chr(10).join([f"- {s}" for s in report['sectors']])}

### 예상 변화
{chr(10).join([f"- {c}" for c in report['expected_changes']])}

### 액션 플랜
{chr(10).join([f"{i+1}. {a}" for i,a in enumerate(report['action_plan'])])}

### 참고
{chr(10).join([f"- {r}" for r in report['references']])}
""")
    
    print("[KRICS] generated docs/krics_transition_report.json/md")

if __name__ == "__main__":
    print("=== KRICS Fetcher v62 - Pending until 2026-10-26 ===")
    results = fetch_krics_classification_official()
    print(f"[KRICS] fetched {len(results)} pending entries")
    generate_krics_report()
    # update는 10월 26일 이후에만 실행
    # update_krics_mapping(results)
