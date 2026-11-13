# KOSPI Quant Terminal v61.6-stable 운영 기준

이 문서는 v61.6-stable의 실제 운영 파일, 데이터 계약, 검증 기준을 정리한다. v62 실험은 이 기준판 이후 별도 브랜치에서만 진행한다.

## 1. 운영 파일

| 영역 | 파일 | 역할 |
|---|---|---|
| 프런트엔드 | `index.html`, `js/config.js`, `js/data.js`, `js/app.jsx` | Firebase 읽기 전용 대시보드 |
| 일일 스냅샷 | `scripts/daily_update.py` | 10개 팩터, 64 picks, regime/retrain 첨부 |
| 데이터 품질 게이트 | `scripts/data_quality_check_v60.py` | daily 실행 전 NaN/fallback/신선도 검사 |
| 성과 추적 | `scripts/track_performance_v60.py` | `performance_tracking`, `performance_snapshots` 생성 |
| 메타 팩터 | `scripts/meta_factor_tracker_v60.py` | `factor_validity`, `meta_summaries` 생성 |
| 재학습 | `scripts/retrain_model.py` | 월별 beta/R² 재학습, `beta_snapshots/latest` 저장 |
| 공통 데이터 | `scripts/price_provider.py`, `scripts/fundamental_filter.py` | yfinance/KRX/FRED/DART 접근 계층 |

`js/app.js`, `js/regime.js`, `js/retrain.js`는 `legacy/`로 이동했으며 운영에서 로드하지 않는다. `scripts/legacy/`에는 v56 계열과 regime-aware `meta_factor_tracker.py`가 있으며 워크플로에서 사용하지 않는다.

## 2. 워크플로

| 워크플로 | 스케줄 | 실행 스크립트 |
|---|---|---|
| `.github/workflows/daily-update.yml` | 평일 07:30 KST | `data_quality_check_v60.py` → `daily_update.py` |
| `.github/workflows/performance-update.yml` | 평일 16:00 KST | `regime_detector_v60.py` → `track_performance_v60.py` → `meta_factor_tracker_v60.py` |
| `.github/workflows/retrain.yml` | 매월 1일 11:00 KST | `retrain_model.py` |

## 3. 데이터 계약

### `factor_snapshots/{date}`

프런트엔드가 직접 읽는 핵심 필드:

- `date`, `timestamp`, `generated_at_kst`
- `zScores`: canonical key + 호환 alias
- `details`: 팩터별 `latest`, `z`, `source`, `data_status`, `rows`, `fallback_used`, `synthetic_data_used`
- `weeklyPicks[]`: `industryId`, `ticker`, `name`, `targetFactor`, `score`, `expectedReturn`, `reason`, `date`, `zAtRec`, `predIndustry`, `momentum`, `betaStock`, `data_status`, `fallback_used`, `synthetic_data_used`
- `regime`: `regime`, `confidence`, `window`, `indicators`, `data_status`, `fallback_used`, `synthetic_data_used`
- `retrain` / `beta_snapshot`: `avg_r2`, `r2`, `version`
- 최상위 상태: `app_version`, `model_version`, `data_policy`, `data_status`, `quality_status`, `fallback_used`, `synthetic_data_used`, `filter_applied`, `regime_enabled`, `meta_enabled`, `retrain_enabled`

### `performance_tracking/{recDate}_{ticker}_{evalDate}`

- `recDate`, `evalDate`, `ticker`, `name`, `industryId`, `targetFactor`
- `zAtRec`, `score`, `predIndustry`, `daysElapsed`
- `return`, `returnPct`, `kospiReturn`, `kospiReturnPct`
- `excessReturn`, `excessReturnPct`
- `source`, `priceSource`, `chinaProxy`, `version`

### `performance_snapshots/{date}`

- `totalPicks`, `avgReturnPct`, `avgExcessReturnPct`
- `hitRate`, `hitRatePct`, `winRate`, `winRatePct`, `excessWinRate`, `excessWinRatePct`
- `ok`, `fail`, `source`, `version`, `period`

### `factor_validity/{factor}_{date}`, `meta_summaries/{date}`

- `factor_validity`: `ic`, `hit_rate`, `hit_rate_pct`, `avg_excess_pct`, `avg_return_pct`, `t_stat`, `n_samples`, `score_ic`, `is_china_proxy`
- `meta_summaries`: `factors`, `topIC`, `total_samples`, `unique_factors`, `china_proxy`

## 4. v61.6 데이터 정책

- `APP_VERSION = "v61.6-data-integrity"`
- `MODEL_VERSION = "industry8-factor-v61.6"`
- `DATA_POLICY = "REAL_ONLY_NO_SYNTHETIC_NO_085_FALLBACK"`
- 필수 팩터/외국인 수급 검증 실패 시 새 snapshot과 picks를 만들지 않는다.
- 실패 시 마지막 정상 `factor_snapshots` 문서를 덮어쓰지 않는다.
- 프런트엔드는 `Math.random`, `mockData`, 고정 성과/지수/확률을 사용하지 않는다.
- 데이터가 없으면 `N/A`, `—`, 또는 수집처/컬렉션명을 표시한다.
- `daily_update.py`의 내장 meta tracker는 비활성화했다. IC/HitRate는 `meta_factor_tracker_v60.py`가 실제 `performance_tracking`으로 생성한 `meta_summaries`/`factor_validity`만 사용한다.
- `meta_factor_tracker_v60.py`는 같은 `recDate+ticker`의 여러 `evalDate` 중 최신 1건만 사용해 look-ahead/중복 표본을 줄인다.
- `regime_detector.py`는 필수 지표 누락 시 예외를 발생시킨다. daily pipeline은 이를 `REGIME_MODULE_ERROR`로 명시 기록하며 정상 regime처럼 표시하지 않는다.

## 5. 검증 명령

```bash
py -3 -m py_compile scripts/daily_update.py scripts/regime_detector.py scripts/regime_detector_v60.py scripts/track_performance_v60.py scripts/meta_factor_tracker_v60.py scripts/retrain_model.py scripts/data_quality_check_v60.py
py -3 tests/check_v616_static.py
npx --yes esbuild js/app.jsx --loader:.jsx=jsx --outfile=/tmp/app.jsx.js
node --check /tmp/app.jsx.js
```

추가 수동 확인:

- `git diff --check`
- `js/app.jsx`에서 `Math.random`, `mockData`, 고정 `66.8`, `1327`, `103.8`, `4.72`, `16.5` 부재
- GitHub Actions 수동 실행 후 `factor_snapshots`, `performance_tracking`, `meta_summaries` 실제 문서 확인
