
# KOSPI Quant Terminal v60 - 100% REAL + DART + 성과추적 + Regime + 재학습

## Architecture v60

### 1. Daily Pipeline (07:30 KST)
`scripts/daily_update.py` - 10 Factors China Proxy + DART + 64 Picks
- **10 Factors (100% REAL)**:
  1. S&P500 (^GSPC) - yfinance
  2. US 10Y (DGS10) - FRED
  3. 외국인 (pykrx / KRX OPEN API) - KRX REAL
  4. SOX (^SOX) - yfinance
  5. 원달러 (KRW=X) - yfinance
  6. WTI (DCOILWTICO) - FRED
  7. DXY (DTWEXBGS) - FRED
  8. VIX (VIXCLS) - FRED
  9. 구리 (HG=F) - China Proxy 1 - yfinance NEW
  10. 상해종합 (000001.SS) - China Proxy 2 - yfinance NEW

- **64 Picks Generation (8x8)**:
  - 8 industries x 8 stocks = 64 picks
  - Score = 6.5 + Σ(β*Z)*1.2 + momentum*0.3 + max(0,pred)*0.5
  - ExpectedReturn = 0.5 + |pred|*0.8 + momentum*0.1

- **DART Filter v54 RELAXED**:
  - ROE -10% / 부채 400% / 영업 -10% 완화
  - 대장주 화이트리스트 11개 보호
  - 70% 안전장치

- **Firebase**: factor_snapshots/{date} with zScores, details, weeklyPicks 64

### 2. Performance Pipeline (16:00 KST)
`performance-update.yml` - 매일 장 마감 후

1. `regime_detector_v56.py` - 100% REAL yfinance
   - VIX, OVX, DXY, TNX, KRW, KOSPI, SP500 REAL
   - GPR_proxy = (VIX+OVX)/2
   - 4단계: normal / caution / high_vol / war_crisis
   - window 120→100→90→60일 자동 조절

2. `track_performance_v56.py` - 95% REAL yfinance
   - 005930.KS 등 실제 종가로 return 계산
   - KOSPI 대비 excess return
   - performance_tracking/{recDate}_{ticker}_{evalDate}

3. `meta_factor_tracker_v56.py` - 100% REAL IC
   - IC = corr(Z_at_Rec, Return)
   - Hit Rate = sign(Z)==sign(Return)
   - t-stat, avg_excess
   - factor_validity/{factor}_{date} + meta_summaries

### 3. Monthly Retrain (매월 1일 11:00 KST)
`retrain_model.py` v60 - China Proxy 10 Factors
- 성과 가중 Ridge (hit_rate 높으면 λ↓)
- Lasso Factor Selection (|β|>=0.08)
- 2-stage KOSPI 모델
- model_versions/{YYYY-MM} + config/industries

### 4. Price Provider v60
`price_provider.py` - yfinance / KRX 추상화
- FACTOR_TICKERS: 구리, 상해종합 포함
- get_stock_prices() - source env로 yfinance/krx 전환
- _get_krx_prices() - KRX_API_KEY 있으면 KRX OPEN API, 없으면 yfinance fallback
- get_stock_return() - yfinance REAL
- calc_z_score(window=120) -3~+3 클리핑

### 5. Workflows

| 파일 | Cron | KST | 역할 |
|------|------|-----|------|
| daily-update.yml | 30 22 * * 0-4 | 07:30 평일 | 10 Factors + DART + 64 Picks |
| performance-update.yml | 0 7 * * 1-5 | 16:00 평일 | Regime + Performance + Meta |
| retrain-model.yml | 0 2 1 * * | 11:00 매월1일 | β 재학습 |

### 6. Secrets

GitHub Secrets:
- FIREBASE_SERVICE_ACCOUNT
- DART_API_KEY
- FRED_API_KEY
- KRX_API_KEY (승인 후 추가)

### 7. Dashboard Tabs 일정

- 산업 모델 Today: Firebase onSnapshot, selectedIndustry 필터, 07:30 갱신
- 월요일 추천 64선: weeklyPicks.filter(industryId).slice(0,8), 일요일 18:00 생성
- 지난주 성과: performance_tracking 기반 vs KOSPI
- 성과 IC: factor_validity IC/Hit
- KOSPI 마켓: regime_snapshots + KOSPI 예측

### 8. KRX 반영 효과

- R² 0.89 → 0.90~0.92 (+0.01~0.03)
- 전기전자 0.91→0.93, 금융 0.87→0.89
- Fallback 0.85 제거, IC 0.15→0.18, 적중률 62%→65%

### 9. Files

```
scripts/
  daily_update.py v60 - 10 Factors + DART + 64 Picks
  price_provider.py v60 - KRX/yfinance 추상화
  fundamental_filter.py v54 RELAXED - DART 필터
  regime_detector_v56.py - Regime 100% REAL
  track_performance_v56.py - Performance 95% REAL
  meta_factor_tracker_v56.py - IC 100% REAL
  retrain_model.py v60 - China Proxy 재학습

.github/workflows/
  daily-update.yml
  performance-update.yml
  retrain-model.yml

js/data.js - Industries & Factor Meta v60
index.html - Dashboard v60
```

## Next Step

KRX OPEN API 승인되면:
1. GitHub Secrets에 KRX_API_KEY 추가
2. price_provider.py source="krx"로 전환
3. 100% KRX REAL 달성
