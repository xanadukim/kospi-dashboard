"""
daily_update.py - 매일 07:30 KST 실행
1. yfinance, KRX, FRED에서 데이터 수집
2. Z-score 계산 (최근 120일 평균/표준편차)
3. data/factors.json 업데이트
4. 산업별 예측 Score 재계산 -> data/picks.json
"""
import yfinance as yf
import json
from pathlib import Path
from datetime import datetime
import random

# 실제 구현시 아래 주석 해제
# import FinanceDataReader as fdr

def fetch_factors():
    # TODO: 실제 API 연결
    # sp500 = yf.download('^GSPC')['Close'].pct_change().iloc[-1]
    # us10y = yf.download('^TNX')['Close'].diff().iloc[-1]
    # usdkrw = fdr.DataReader('USD/KRW')['Close'].iloc[-1]
    
    # 지금은 시뮬레이션
    return {
        "SP500": round(random.uniform(-1.5, 1.5), 2),
        "외국인": round(random.uniform(-2, 2), 2),
        "반도체팩터": round(random.uniform(-1, 2), 2),
        "US10Y": round(random.uniform(-1.5, 1), 2),
        "중국PMI": round(random.uniform(-1, 1), 2),
        "원달러": round(random.uniform(-1.5, 1.5), 2),
        "WTI": round(random.uniform(-1, 1), 2),
        "한미스프레드": round(random.uniform(-1, 1), 2),
        "정책더미": 0
    }

if __name__ == "__main__":
    z_scores = fetch_factors()
    data = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "z_scores": z_scores,
        "updated_at": datetime.now().isoformat()
    }
    Path("data/factors.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f"Updated {data}")
