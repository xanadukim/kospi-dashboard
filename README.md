# KOSPI Quant Terminal v61.6-stable

100% REAL 데이터 파이프라인 + DART 필터 + 64 Picks + 성과추적 + Regime + 월별 재학습.

> Stable 기준: mock/난수/합성 fallback 없음. 실제 데이터가 없으면 화면에 `N/A`/`—`/수집처를 표시한다. 상세 운영 계약은 `docs/OPERATING_BASELINE.md`를 본다.

## Architecture v61.6-stable

### 1. Daily Pipeline (평일 07:30 KST)
`.github/workflows/daily-update.yml`
1. `scripts/data_quality_check_v60.py` — 품질 게이트
2. `scripts/daily_update.py` — 10개 팩터 + DART + 64 picks + regime/retrain 첨부

10개 팩터:
1. S&P500 (`^GSPC`) — yfinance
2. US 10Y (`DGS10`) — FRED
3. 외국인 KOSPI200 — `data/foreigner_kospi200.csv`
4. SOX (`^SOX`) — yfinance
5. 원달러 (`KRW=X`) — yfinance
6. WTI (`DCOILWTICO`) — FRED
7. DXY (`DTWEXBGS`) — FRED
8. VIX (`VIXCLS`) — FRED
9. 구리 (`HG=F`) — China Proxy 1 — yfinance
10. 상해종합 (`000001.SS`) — China Proxy 2 — yfinance

산출물: `factor_snapshots/{date}`에 `zScores`, `details`, `weeklyPicks`, `regime`, `retrain`, 상태 메타데이터 저장.

### 2. Performance Pipeline (평일 16:00 KST)
`.github/workflows/performance-update.yml`
1. `scripts/regime_detector_v60.py` → `regime_snapshots`, `market_regimes`
2. `scripts/track_performance_v60.py` → `performance_tracking`, `performance_snapshots`
3. `scripts/meta_factor_tracker_v60.py` → `factor_validity`, `meta_summaries`

### 3. Monthly Retrain (매월 1일 11:00 KST)
`.github/workflows/retrain.yml` → `scripts/retrain_model.py`
- `beta_snapshots/latest`, `beta_snapshots/{date}`, `retrain_history`, `retrain_logs` 저장
- `js/data.js.new`는 수동 반영용 산출물이며 프런트 기본값이 아니다.

### 4. Dashboard
`index.html` + `js/config.js` + `js/data.js` + `js/app.jsx`(소스) → `js/app.js`(빌드 산출물)
- `js/app.jsx`를 수정한 뒤 반드시 `npm run build`(esbuild)로 `js/app.js`를 재생성하고 둘 다 커밋한다. `index.html`은 빌드된 `js/app.js`를 로드한다.
- Firebase는 읽기 전용 클라이언트만 사용한다.
- `js/regime.js`, `js/retrain.js`는 `legacy/`로 이동했으며 운영에서 로드하지 않는다.
- 프런트는 `factor_snapshots`, `performance_tracking`, `performance_snapshots`, `meta_summaries`만 표시한다.

## Data Policy

```text
APP_VERSION   = v61.6-data-integrity
MODEL_VERSION = industry8-factor-v61.6
DATA_POLICY   = REAL_ONLY_NO_SYNTHETIC_NO_085_FALLBACK
```

- 필수 데이터 부족 시 새 snapshot/picks를 생성하지 않는다.
- 마지막 정상 snapshot을 실패 결과로 덮어쓰지 않는다.
- 모든 snapshot은 `data_status`, `quality_status`, `fallback_used`, `synthetic_data_used`를 가진다.
- `daily_update.py` 내장 meta tracker는 비활성화했다. IC/HitRate는 `meta_factor_tracker_v60.py`의 실제 성과 기반 결과만 사용한다.

## Secrets

GitHub Secrets:
- `FIREBASE_SERVICE_ACCOUNT`
- `FRED_API_KEY`
- `DART_API_KEY`
- `KRX_API_KEY` (승인/필요 시)

## Verification

```bash
py -3 -m py_compile scripts/daily_update.py scripts/regime_detector.py scripts/regime_detector_v60.py scripts/track_performance_v60.py scripts/meta_factor_tracker_v60.py scripts/retrain_model.py scripts/data_quality_check_v60.py
py -3 tests/check_v616_static.py
npm run build
node --check js/app.js
git diff --check
```

## Next Step

v61.6-stable 검증 후에만 v62 factor-beta K-means 실험을 별도 브랜치에서 진행한다.
