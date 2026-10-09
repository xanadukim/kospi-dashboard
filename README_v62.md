# KOSPI200_Koptimum
## KOSPI200 기반 최적 K 팩터 클러스터링 터미널

> **기존 KOSPI Quant Terminal (v61.3 beta)은 Github에 그대로 보존됩니다.**
> 본 프로젝트는 베타 테스트를 기반으로 한 정식 개선 버전입니다.

**프로젝트명:** `KOSPI200_Koptimum` (KOSPI200 + Optimum K)
**버전:** v62.0 Phase A (2026-09-29) → v62.1 KRICS (2026-10-26 예정)
**기반:** KOSPI Quant Terminal v61.3 beta (8개 주관적 산업군, 하드코딩 64종)
**목표:** 공식 지수 + 공식 산업분류 + 통계적 최적 K + 자체 팩터 클러스터 작명

---

### 1. 왜 새로 시작하는가? (Beta vs Koptimum)

| 구분 | 기존 KOSPI Quant Terminal (Beta) | KOSPI200_Koptimum (신규) |
|---|---|---|
| **지수** | KOSPI 전체 (소형주 잡음 많음) | **KOSPI200** (외국인 선물 팩터와 정합) |
| **유니버스** | 하드코딩 64종 [티커,이름,beta_stock,momentum] | **KOSPI200 200종 동적** + 시가총액 85% + 거래대금 + 90~110% 완충 |
| **산업분류** | 전기전자/반도체 등 8개 주관적 명칭 | **GICS (현재) + KRICS 9섹터 pending_20261026** Dual-Structure |
| **클러스터 수** | 8개 고정 (주관적) | **최적 K** Elbow/Silhouette/Gap (4~12 탐색, 현재 k=8) |
| **클러스터 명칭** | 산업명 (오해) | **자체 작명 FCn_지배팩터_Beta** (예: FC1_VIX_Beta) |
| **데이터** | 193개 Wiki + 합성 | **190종 (193+7) + KRX 공식 200개 대조 예정** |
| **KRICS 대응** | 없음 | **9/23 시행, 10/26 분류 공개 대응 설계** |

**보존 전략:**
- 기존 Github repo: `kospi-quant-terminal` → `beta` 브랜치 또는 `v61.3-beta` 태그로 보존
- 신규 repo: `KOSPI200_Koptimum` → `main` 브랜치, v62부터 시작
- Firebase: `factor_snapshots`는 beta 유지, `koptimum_snapshots` 신규 컬렉션 (또는 동일 컬렉션에 version 필드로 구분)

---

### 2. 아키텍처 (v62 Phase A)

```
[KRX KOSPI200 구성종목 API + GICS 매핑 + KRICS pending]
    ↓
[Step 2: KOSPI200 규칙 필터 - 시총 85% + 거래대금 중위수 + 완충 90~110%]
    ↓ (97종 예시)
[200종 x 10팩터 베타 계산 - RidgeCV 180D]
    ↓ (200 x 10 행렬)
[Step 3: K-means 최적 K 탐색 (Elbow/Silhouette) → Factor Cluster 자체 작명]
    ↓ (k=8, FC1~FC8)
[Step 1: KOSPI200 지수 + 산업군 지수 Ridge 회귀 (매월 1일)]
    ↓
[매일 07:30: 10개 팩터 Z-Score]
    ↓
[Step 4: 각 클러스터에서 Score 계산 + GICS + 시총/거래대금 Top 8]
    ↓
[Firebase koptimum_snapshots/{date} + js/data.js v62]
    ↓
[프론트: FACTOR CLUSTERS • 8, KOSPI200 R² 0.89, GICS + KRICS pending]
```

**10개 팩터 (China Proxy 포함):**
S&P500(^GSPC), US 10Y(DGS10), 외국인 선물(KRX 15007), SOX(^SOX), 원달러(KRW=X), WTI(DCOILWTICO), DXY(DTWEXBGS), VIX(VIXCLS), 구리(HG=F), 상해종합(000001.SS)

---

### 3. 파일 구조

```
KOSPI200_Koptimum/
├── index.html                 # v62 title: KOSPI200_Koptimum
├── css/style.css              # Trader Centric v61 유지
├── js/
│   ├── data.js                # v62.0 factorClusters 8개 + kricsMeta + kospi200Meta
│   ├── app.jsx                # FACTOR CLUSTERS UI (INDUSTRIES → FACTOR CLUSTERS)
│   └── config.js              # Firebase config
├── data/
│   ├── kospi200_constituents.csv      # 190종 (193+7) + GICS + KRICS pending
│   ├── gics_mapping.csv               # GICS 매핑 전용
│   ├── kospi200_filtered_v62.json     # 85% + 거래대금 필터 → 97종
│   ├── beta_matrix_v62.json           # 190x10 베타
│   ├── optimal_k_v62.json             # k=4~12 inertia/silhouette
│   └── factor_clusters_v62.json       # 8개 클러스터
├── scripts/
│   ├── price_provider.py      # v62: KOSPI200(^KS200) + 시총/거래대금 함수 추가
│   ├── kospi200_universe.py   # NEW: KOSPI200 공식 규칙 필터
│   ├── factor_cluster.py      # NEW: 베타 행렬 + 최적 K + 자체 작명
│   ├── krics_fetcher.py       # NEW: KRICS 9섹터 크롤러 (10/26 이후)
│   ├── daily_update.py        # v61.3 → v62: 동적 유니버스 연동 예정
│   ├── retrain_model.py       # v60.2 → v62: KOSPI200 지수 기반 재학습 예정
│   └── data_quality_check_v60.py
├── .github/workflows/
│   ├── daily-update.yml       # 07:30 KST
│   └── retrain.yml            # 매월 1일
└── docs/
    ├── v62_PhaseA_Complete_Report.md
    ├── krics_transition_report.md
    └── KOSPI_Quant_Terminal_v62_Architecture.md
```

---

### 4. KRICS 대응 (핵심)

**타임라인:**
- 2026-09-22: KRICS 구축 완료 발표
- 2026-09-23: 방법론 시행
- 2026-10-26: 종목별 분류 결과 공개 예정 (KRX 인덱스 홈페이지)
- 2026년 하반기: KOSPI200 등 대표지수 순차 적용

**9개 섹터:**
에너지화학, 소재, 산업재, 모빌리티, 정보기술, 금융 및 부동산, 소비재, 헬스케어, 미디어 및 콘텐츠

**Dual-Structure:**
```csv
ticker,name,gics_sector,krics_sector_L1,krics_status
005930,삼성전자,Information Technology,정보기술,pending_20261026
373220,LG에너지솔루션,Industrials,에너지화학(배터리),pending_20261026
005380,현대차,Consumer Discretionary,모빌리티,pending_20261026
```

10월 26일 이후 `krics_fetcher.py`로 크롤링 → 컬럼 업데이트 → `factor_cluster.py` 재실행 (1시간)

---

### 5. 로드맵

**Phase A - 완료 (2026-09-29):**
- [x] KOSPI200 190종 구성 (193 Wiki + 7 추정)
- [x] KOSPI200 공식 필터 구현 (85% + 거래대금 + 90~110%)
- [x] 베타 행렬 + 최적 K 탐색 (k=8)
- [x] 팩터 클러스터 자체 작명 (FCn_Beta)
- [x] KRICS pending 구조
- [x] price_provider.py v62

**Phase B - 진행 중:**
- [ ] KRX 공식 200개 대조 (10개 추가)
- [ ] yfinance REAL 데이터로 베타 재계산 (GitHub Actions)
- [ ] daily_update.py 동적 유니버스 연동
- [ ] app.jsx FACTOR CLUSTERS UI
- [ ] docs/methodology.md, k_selection_report.md

**Phase C - 2026-10-26 이후:**
- [ ] KRICS 공식 분류 크롤링
- [ ] KRICS 기준 재군집
- [ ] KOSPI200_Koptimum v62.1 릴리즈

---

### 6. GitHub 보존 가이드

```bash
# 기존 프로젝트 보존
git tag v61.3-beta
git branch beta
git push origin v61.3-beta
git push origin beta

# 신규 프로젝트 시작
# Option 1: 동일 repo에서 orphan branch
git checkout --orphan koptimum
git rm -rf .
cp -r /path/to/KOSPI200_Koptimum/* .
git add .
git commit -m "feat: KOSPI200_Koptimum v62.0 Phase A - KOSPI200 + GICS + optimal K + KRICS ready"
git push origin koptimum

# Option 2: 신규 repo 생성 (권장)
# Github에서 KOSPI200_Koptimum 신규 repo 생성 후
git init
git add .
git commit -m "init: KOSPI200_Koptimum v62.0"
git remote add origin https://github.com/your-id/KOSPI200_Koptimum.git
git push -u origin main
```

**Firebase:**
- 기존: `factor_snapshots/{date}` (beta)
- 신규: `koptimum_snapshots/{date}` 또는 `factor_snapshots`에 `version: "koptimum_v62"` 필드 추가

---

### 7. 실행 방법

```bash
# 1. KOSPI200 유니버스
python scripts/kospi200_universe.py

# 2. Factor Cluster + 최적 K (합성 데이터 - yfinance 설치 시 REAL)
python scripts/factor_cluster.py

# 3. KRICS (현재 pending, 10/26 이후)
python scripts/krics_fetcher.py

# 4. Daily Update (기존 + 신규)
python scripts/daily_update.py

# 5. Frontend
# index.html을 브라우저로 열거나
python -m http.server 8000
```

---

### 8. 평가자용 한 줄 정리

> **KOSPI200_Koptimum은 KOSPI200(공식 지수, 시장 대표성·유동성·연속성) 200종을 1차 유니버스로 두고, GICS(국제 표준) + KRICS(국내 신규 9섹터, 10월 26일 공개 예정) Dual-Structure로 분류한 뒤, 10개 팩터 베타가 비슷한 종목끼리 K-means 최적 K(Elbow/Silhouette 검증)로 군집하여 자체 작명한 팩터 클러스터(예: FC1_US_Beta)에서 시가총액 85%·거래대금·완충 규칙을 적용해 8종씩 추천하는 모델입니다. 기존 KOSPI Quant Terminal beta는 Github에 보존됩니다.**

---

### 9. 참고 자료

- KRX Data Marketplace: https://data.krx.co.kr/contents/MDC/MAIN/main/index.cmd?locale=en
- KRICS 도입 기사: https://www.etoday.co.kr/news/view/2628472
- KRICS 구축 기사: https://www.dailian.co.kr/news/view/1693610/
- KOSPI200 선정 기준: mofe.go, samsungpop PDF
- GICS: MSCI & S&P
- WICS: KRX 기존 분류

---

**작성일:** 2026-09-29
**작성자:** KOSPI200_Koptimum Team (Beta → Koptimum)
**상태:** Phase A 완료, Phase B 진행, 10/26 KRICS v62.1 예정
