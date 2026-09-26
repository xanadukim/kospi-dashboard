# Firestore Schema v4.0 - KOSPI Quant Terminal

## Collections

### 1. factor_snapshots/{YYYY-MM-DD} (기존, 유지)
일별 팩터 Z-Score + 64종 추천
```
{
  date: "2026-09-26",
  zScores: { SP500: 0.63, 외국인: 1.07, 반도체팩터: 1.59, US10Y: -1.13, ... },
  rawValues: { SP500: 5780, US10Y: 4.72, USD_KRW: 1382.5, WTI: 72.3 },
  weeklyPicks: [ { industryId, ticker, name, score, expectedReturn, reason, ... } x64 ],
  industryPicks: { elec: [...8], auto: [...8], ... },
  createdAt: timestamp,
  version: "v3.1-modern-8x8"
}
```

### 2. performance_tracking/{recDate}_{ticker}_{trackDate} (NEW v4.0)
추천 종목 실제 성과 추적 - 매일 16:00 KST 업데이트
```
{
  recDate: "2026-09-15",        // 추천일
  trackDate: "2026-09-26",      // 추적일 (오늘)
  ticker: "005930",
  name: "삼성전자",
  industryId: "elec",
  targetFactor: "반도체팩터",
  score: 9.2,
  expectedReturn: 2.4,
  zAtRec: 1.59,                 // 추천 당시 해당 팩터 Z
  zScoresAtRec: { ... },        // 추천 당시 전체 Z
  daysElapsed: 11,
  actual: { "1W": 3.2, "2W": 5.1, "1M": 8.4 },
  vsKOSPI: { "1W": 1.8, "1M": 4.2 },
  market: { KOSPI_1W: 1.4, KOSDAQ_1W: 1.8 },
  hit: true,                   // 1W > 0
  hitVsKOSPI: true,            // vsKOSPI > 0
  createdAt: timestamp
}
```
Index: recDate, industryId, ticker, trackDate

### 3. model_metrics/{YYYY-MM-DD} (NEW v4.0)
일별 집계 성과
```
{
  date: "2026-09-26",
  metrics: {
    elec: { count: 32, avgReturn1W: 1.84, hitRate: 0.62, ic: 0.08 },
    auto: { count: 32, avgReturn1W: 0.92, hitRate: 0.55, ic: 0.03 },
    ...
  },
  market: { KOSPI_1W: 1.2 },
  totalTracked: 256,
  createdAt: timestamp
}
```

### 4. model_versions/{YYYY-MM} (NEW v4.0)
월별 재학습된 모델 버전 관리
```
{
  yearMonth: "2026-10",
  date: "2026-10-01",
  kospiModel: {
    betas: { SP500: 0.38, 외국인: 0.32, ... },
    r2: 0.89,
    factors: [9]
  },
  industryModels: {
    elec: { betas: {...}, r2: 0.92, r2_old: 0.91, hitRate: 0.64, avgReturn1W: 2.1, sampleCount: 112, lambda: 0.32 },
    ...
  },
  meta: {
    snapshotsUsed: 26,
    perfDocsUsed: 1664,
    method: "performance-weighted Ridge + Lasso + 2-stage KOSPI",
    factorHitRates: { 반도체팩터: 0.68, 원달러: 0.55, ... }
  },
  createdAt: timestamp,
  version: "v4.0-2026-10"
}
```

### 5. config/industries (NEW v4.0)
대시보드가 로드하는 최신 β
```
{
  updated: "2026-10-01",
  version: "v4.0-2026-10",
  industries: { elec: { betas, r2, ... }, ... },
  kospiModel: { betas, r2 }
}
```

## Data Flow v4.0

```
[일요일 18:00 KST] daily_update.py
  -> factor_snapshots/{date} (64 picks)

[평일 16:00 KST] track_performance.py
  -> performance_tracking/{recDate}_{ticker}_{trackDate} (실제 수익률)
  -> model_metrics/{date} (집계)

[매월 1일 11:00 KST] retrain_model.py
  -> 최근 6개월 factor_snapshots + performance_tracking 분석
  -> factor_hit_rate, IC, 업종별 Hit Rate 계산
  -> 성과 가중 Ridge로 β 재학습 + Lasso로 불필요 팩터 제거
  -> KOSPI 2단계 모델 학습
  -> model_versions/{YYYY-MM} + config/industries 저장

[대시보드] index.html
  -> factor_snapshots (최신 Z + 64 picks)
  -> config/industries (최신 β) - onSnapshot
  -> model_metrics (성과 차트)
  -> model_versions (히스토리)
```

## 6개월 후 기대 효과

- IC (Information Coefficient) 추적: Score가 실제 수익률을 얼마나 잘 예측하는지
- Factor 유효성 검증: 반도체팩터가 전기전자에서 정말 유효한지
- β 자동 교정: 실패한 팩터는 β 축소, 성공한 팩터는 β 강화
- 전체 KOSPI 모델: 마켓 중립 알파 추출 가능
