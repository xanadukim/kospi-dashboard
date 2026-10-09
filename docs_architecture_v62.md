# KOSPI Quant Terminal v62 Architecture 문서
## GICS 기반 + 최적 K 팩터 클러스터 전환 최종안

> **작성일:** 2026-09-29  
> **버전:** v61.6 (현재) → v62.0 (제안)  
> **결정사항:**  
> 1. GICS 선택  
> 2. 클러스터 수 8개 고정 안 함 → 최적 K로 결정  
> **첨부 이미지:** `image_165b75.png` - v61.6 대시보드 (INDUSTRIES 8, KOSPI R² 0.89)

---

## 1. Executive Summary

현재 시스템은 **KOSPI 전체 지수를 타겟으로, 팩터 민감도가 비슷한 종목끼리 묶어 산업명을 붙인 8개 클러스터(하드코딩 64종)** 구조입니다. 평가자 관점에서 `주관적 군집 + 라벨링`으로 보일 수 있습니다.

제공해 주신 코스피200 공식 기준을 적용하여 다음과 같이 전환합니다:

**Before (v61.6):**
```
KOSPI 전체 → 8개 산업(수동) → 하드코딩 64종 [티커, 이름, beta_stock, momentum] → Score
```

**After (v62.0 - 결정안):**
```
Step 1: KOSPI200 지수 회귀모델 (KOSPI 전체가 아닌 KOSPI200)
Step 2: KOSPI200 200종 안에서 GICS 산업군 분류 + 시가총액 85% + 거래대금 + 90~110% 완충 규칙으로 평가
Step 3: 200종의 10개 팩터 베타가 비슷한 것끼리 K-means 군집, 최적 K는 Elbow/Silhouette로 결정, 산업군 이름이 아닌 자체 작명 (예: FC1_US_Beta)
Step 4: 각 팩터 클러스터에서 8종 추천, 개별 종목 카드에 GICS 산업군명 + 종목코드 + 시가총액/거래대금 표시
```

이 구조는 **공식 지수(KOSPI200) → 공식 산업분류(GICS) → 자체 방법론(Factor Beta Clustering)** 3중 방어 논리가 생깁니다.

---

## 2. 전체 파일 감사 (11개 파일 최신 기준)

### 2.1 스케줄러
- **daily-update.yml:** `cron: '30 22 * * 0-4'` = UTC 22:30 = KST 07:30 평일 아침. QC Gate → daily_update.py
- **retrain.yml:** `cron: '0 2 1 * *'` = 매월 1일 02:00 UTC = 11:00 KST. RidgeCV 재학습

### 2.2 핵심 로직
- **scripts/price_provider.py:** 가격 수집 허브
  - `FACTOR_TICKERS`: S&P500(^GSPC), US10Y(^TNX), SOX(^SOX), 원달러(KRW=X), WTI(CL=F), DXY(DX-Y.NYB), VIX(^VIX), 구리(HG=F), 상해종합(000001.SS), KOSPI(^KS11)
  - KRX OPEN API: `kospi_dd_trd`만 실제 구현, KOSDAQ/개별종목은 주석 `추후 승인 시 추가`
  - `calc_z_score(series, window=120)`: (latest-mean)/std, -3~+3 클램핑, VIX만 부호 반전
  - `get_foreigner_factor_real()`: CSV 우선, 실패 시 SP500 기반 + 노이즈 합성

- **scripts/daily_update.py (v61.3):**
  - `fetch_10_factors_china_proxy()`: FRED 4개(DGS10, DCOILWTICO, DTWEXBGS, VIXCLS) + yfinance 5개 + KRX 외국인 1개 = 10개
  - `INDUSTRIES_BETAS`: 8개 산업 x 팩터 베타 하드코딩 (예: elec: S&P500 0.42, 외국인 0.28, SOX 0.35)
  - `INDUSTRIES_UNIVERSE`: 8x8=64종 하드코딩, 형식 `[티커, 이름, beta_stock, momentum]` (예: ["005930","삼성전자",1.0,0.8]) - **문제점**
  - `generate_64_picks()`: 
    ```
    pred = Σ(β_industry * Z_factor)
    Score = 6.5 + pred*1.2 + momentum*0.3 + max(0,pred)*0.5 + |pred|*0.3 (1~10 클램핑)
    expectedReturn = 0.5 + |pred|*0.8 + max(0,pred)*0.4 + momentum*0.1
    ```
  - DART 필터, Regime, Meta는 파일이 레포에 없어 import 실패 시 fallback (평시)

- **scripts/retrain_model.py (v60.2):**
  - `INDUSTRY_PROXY`: 8개 대표주 단일 종목 (삼성전자, 현대차 등) - **문제점: 단일 종목이 산업 대표**
  - `BASE_BETAS`: data.js 초기값과 동일
  - `fetch_factor_history()`: 180일 팩터 수익률, 외국인 선물은 SP500*0.8 + 노이즈 합성
  - `ridge_regression()`: numpy 직접 구현, Ridge λ 최적화 [0.1,0.5,1.0,2.0], R² 계산
  - `70% new 30% old blending`으로 베타 안정화

- **scripts/data_quality_check_v60.py:** 10개 팩터 NaN/Inf 체크, 외국인 0.85 fallback 탐지, China Proxy 이중 체크, 실패 시 `sys.exit(1)`로 GitHub Actions 실패

### 2.3 프론트엔드
- **js/data.js:** 8개 산업 정의, `id, name, short, icon, r2, color, betas, desc`만 있음. `krxMapping, gics, methodology` 없음
- **js/app.jsx:** 12컬럼 그리드 (왼쪽 2 INDUSTRIES, 중앙 8 마켓 레짐 + KOSPI 모델, 오른쪽 4 팩터 + 외국인/US10Y). 이미지의 v61.6 화면과 일치
- **js/config.js:** Firebase 공개키
- **index.html, css/style.css:** `max-w-screen-2xl px-4 md:px-6` 레이아웃

---

## 3. 코스피200 공식 선정 기준 (제공해 주신 문서 요약)

### 핵심 기준 (mofe.go)
1. 시장 대표성
2. 산업·업종 대표성
3. 시가총액
4. 유동성 (거래대금)
5. 기존 구성종목의 연속성

코스피200은 시가총액 상위 200개가 아님. **산업별 대표성을 유지하면서 시가총액이 크고 거래대금이 충분한 200개**

### 구체적 방식 (samsungpop PDF)
- **심사대상:** 유가증권시장 보통주, ETF/SPAC 제외
- **산업군:** GICS 참고한 산업군으로 나눔
- **규모:** 산업군별 일평균 시가총액 큰 순, 누적 85% 이내 1차 선정
- **유동성:** 거래대금이 일정 수준 이상, 시총 커도 거래대금 낮으면 탈락
- **완충 장치 (90~110%):** 기존 10개면 기존 종목 11위까지 잔류 가능, 신규는 9위 이내여야 편입
- **정기변경:** 매년 6월, 수시변경은 합병/분할/상폐/신규상장 시
- **201위 기업이 들어갈 수 있는 이유:** 산업군 대표성, 잔류 규칙, 균형 고려

---

## 4. v62.0 신 아키텍처 (결정사항 반영)

### 결정 1: GICS 선택
- 이유: 국제 표준, 코스피200이 GICS 참고, 평가자 납득도 높음. WICS는 한국 한정
- 구현: `data/gics_mapping.csv` 생성
```
ticker,name,gics_sector,gics_industry_group,gics_industry,gics_sub_industry,wics
005930,삼성전자,Information Technology,Semiconductors & Semiconductor Equipment,Semiconductors,Semiconductors,반도체와반도체장비
005380,현대차,Consumer Discretionary,Automobiles & Components,Automobiles,Automobiles,운수장비
...
```

### 결정 2: 클러스터 수 8개 고정 안 함, 최적 K로 결정
- 이유: 8개는 현재 산업 수에서 유래한 주관적 숫자. 통계적 근거 필요
- 방법: Elbow Method + Silhouette Score + Gap Statistic으로 k=5~12 탐색

### 4단계 상세 설계

#### Step 1: 코스피200 지수 회귀모델 (KOSPI 전체가 아닌 KOSPI200)
**Why:** 외국인 선물 팩터가 KOSPI200 선물이므로 타겟도 KOSPI200이 정합성 맞음. KOSPI 전체는 소형주 잡음 많음.

**구현:**
- `price_provider.py`: `KOSPI200 = ^KS200` (yfinance) + KRX OPEN API `idx/kospi200_dd_trd` 추가
- `retrain_model.py`:
  - Before: `y = 삼성전자 수익률` (단일 종목)
  - After: `y = KOSPI200 지수 수익률` (지수 자체) + 8개 산업은 KOSPI200 산업군 지수 수익률로 변경
  - `INDUSTRY_PROXY`를 업종지수로: `elec: KRX 전기전자 업종지수` 또는 `GICS Information Technology 지수`

**검증:** KOSPI200 vs KOSPI 전체 R² 비교, 외국인 선물과의 상관관계 개선 확인

#### Step 2: KOSPI200 안에서 GICS 산업군에서 개별 종목 평가
**Why:** 공식 기준을 그대로 따름. 시가총액+거래대금+연속성

**구현: `scripts/kospi200_universe.py` 신규**

```python
def fetch_kospi200_constituents(date):
    # KRX API 또는 data/kospi200_constituents_202406.csv (6월 정기변경 반영)
    # 컬럼: ticker, name, gics_sector, avg_market_cap, avg_trading_value

def filter_by_kospi200_rule(candidates, industry_group):
    # 1. 산업군별 일평균 시가총액 큰 순 정렬
    # 2. 누적 시가총액 85% 이내 1차 컷
    # 3. 거래대금 필터: 산업군 내 거래대금 중위수 이상 또는 상위 70%
    # 4. 90~110% 완충: data/prev_constituents.csv와 비교
    #    - 기존 종목이면 순위 110%까지 허용 (10개→11위까지)
    #    - 신규 종목이면 90% 이내 (10개→9위 이내)여야 편입
    # 5. 결과: 산업군별 후보군 (예: IT 30개 → 25개로 압축)
```

**데이터 필요:**
- `pykrx`로 일평균 시가총액, 일평균 거래대금 3개월치 수집
- `data/kospi200_202406.csv`: 2024년 6월 정기변경 기준 200종
- `data/prev_universe.csv`: 이전 64종 (완충 규칙용)

#### Step 3: 팩터 베타가 비슷한 것끼리 묶은 팩터 클러스터, 산업군 이름이 아닌 자체 작명, 최적 K

**Why:** 현재 `전기전자/반도체` 같은 이름이 공식 업종으로 오해받음. 자체 작명으로 정직하게 `팩터 클러스터`임을 명시.

**구현: `scripts/factor_cluster.py` 신규**

```python
# 1. 200종의 10개 팩터 베타 계산
for ticker in kospi200_200:
    closes = get_stock_prices(ticker, period="6mo")
    rets = calc_returns(closes)
    betas = ridge_regression(factor_returns, rets) # 10개 베타 벡터

# 2. 베타 행렬: 200 x 10
beta_matrix = np.array([betas for ticker in 200])

# 3. 최적 K 탐색 (k=5~12)
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

inertias = []
silhouettes = []
for k in range(5,13):
    kmeans = KMeans(n_clusters=k, random_state=42).fit(beta_matrix)
    inertias.append(kmeans.inertia_)
    silhouettes.append(silhouette_score(beta_matrix, kmeans.labels_))

# Elbow: inertia 급감 지점, Silhouette 최대 지점
optimal_k = argmax(silhouettes) # 예: k=7이 최적이면 7개

# 4. 최종 클러스터링
final_kmeans = KMeans(n_clusters=optimal_k).fit(beta_matrix)

# 5. 자체 작명: 클러스터별 평균 베타 중 절대값 가장 큰 팩터로 네이밍
cluster_names = {
  0: "FC1_US_Growth: S&P500/SOX 민감군 (β 0.42)",
  1: "FC2_Rate_Sensitive: US10Y/DXY 민감군 (β -0.30)",
  2: "FC3_China_Beta: 구리/상해 민감군 (β 0.35)",
  3: "FC4_FX_Commodity: 원달러/WTI 민감군",
  ...
}
```

**작명 규칙 (예시):**
- FC = Factor Cluster
- 뒤에 지배 팩터 표시: `FC1_S&P500_SOX`, `FC2_US10Y_DXY`
- 평가자용 설명: `중국 경기 프록시(구리+상해)에 가장 민감한 군집`

**검증 문서화:**
- `docs/clustering_validation.png`: Elbow chart, Silhouette chart
- `docs/beta_heatmap.png`: 200종 x 10팩터 베타 히트맵
- `methodology.md`에 `Silhouette 0.68, 최적 K=7` 같은 수치 기재

#### Step 4: 8개 팩터 클러스터에 포함되는 개별 종목 8개 추천, GICS 표시

**Why:** 8x8=64 구조 유지하되, 각 종목 카드에 GICS 정보 표시로 투명성 확보

**구현: `daily_update.py` `generate_64_picks()` 전면 교체**

```python
def generate_picks_v62(z_scores, optimal_k=7):
    # optimal_k는 Step 3 결과, 예: 7이면 7개 클러스터
    # 클러스터별 종목 수 비례 또는 균등 8개씩 (현재는 균등 유지하되 근거 문서화)
    
    all_picks = []
    for cluster_id in range(optimal_k):
        cluster_tickers = get_tickers_in_cluster(cluster_id) # 예: 30개
        # 1차: KOSPI200 규칙 (시총 85% + 거래대금)
        filtered = filter_by_kospi200_rule(cluster_tickers, cluster_id)
        # 2차: 팩터 Score로 정렬
        for ticker in filtered:
            pred = Σ(β_stock * Z) # β_stock은 해당 종목의 팩터 베타
            score = 6.5 + pred*1.2 + momentum*0.3 ... # 기존 공식 유지 가능
            # GICS 정보 추가
            gics = gics_mapping[ticker]
            all_picks.append({
                "clusterId": cluster_id,
                "clusterName": cluster_names[cluster_id],
                "ticker": ticker,
                "name": name,
                "gicsSector": gics["gics_sector"],
                "gicsIndustry": gics["gics_industry"],
                "marketCap": avg_market_cap,
                "tradingValue": avg_trading_value,
                "score": score,
                "reason": f"{dominant_factor} β{beta:.2f} Z{Z:.2f} (REAL) | GICS: {gics_sector}"
            })
        # 클러스터별 Top 8
        top8 = sorted(filtered, key=lambda x: x["score"], reverse=True)[:8]
        all_picks.extend(top8)
    
    # optimal_k=7이면 56종, 8이면 64종. 이미지의 전체 64와 맞추려면 k=8이거나, k=7이면 8개씩이 아닌 비례 배분
    return all_picks
```

**프론트엔드 변경 (js/app.jsx):**
- 왼쪽 INDUSTRIES → `FACTOR CLUSTERS • {optimal_k}`로 명칭 변경
- 카드: `전기전자` → `FC1_US_Growth` + `R² 0.91` + `+0.07%`
- 중앙 추천 카드: `GICS: Information Technology / 005930.KS / 시총 12조 / 거래대금 300억` 추가
- 오른쪽 팩터: 그대로 유지

**데이터 구조 (js/data.js v62):**
```javascript
var factorClusters = [
  {
    id: "FC1",
    customName: "FC1_US_Growth",
    displayName: "US 성장 민감군 (S&P500/SOX)",
    gicsMapping: ["Information Technology", "Communication Services"],
    dominantFactor: "S&P500",
    avgBetas: {"S&P500":0.42, "SOX":0.35, ...},
    method: "K-means k=7, Silhouette 0.68, Elbow 7",
    r2: 0.89,
    stockCount: 32,
    selectionRule: "시총 85% + 거래대금 + 완충 90~110%",
    desc: "나스닥/외국인 + 중국 프록시 민감"
  }
]
```

---

## 5. GICS 구조 (선택 결정)

GICS 11개 섹터:
1. Energy
2. Materials
3. Industrials
4. Consumer Discretionary
5. Consumer Staples
6. Health Care
7. Financials
8. Information Technology
9. Communication Services
10. Utilities
11. Real Estate

코스피200은 이 중 10개 정도를 사용 (Utilities, Real Estate 비중 작음). 이를 8개가 아닌 최적 K(예: 7개) 팩터 클러스터로 재군집.

예시 매핑:
- IT(반도체) + Communication → FC1 US Growth
- Financials + Real Estate → FC2 Rate Sensitive
- Materials(화학/철강) + Energy → FC3 China Beta
- Industrials(조선/건설) + Materials → FC4 Infra

---

## 6. 최적 K 결정 방법론 (고정 안 함)

**Why 8개 고정이 문제인가:**
- 8개는 현재 산업 수에서 유래한 주관적 숫자
- 200종 베타 행렬에 대해 통계적으로 8개가 최적인지 검증 없음

**최적 K 탐색 절차:**

1. **데이터:** 200종 x 10팩터 베타 행렬 (180일 Ridge)
2. **범위:** k=4~12 탐색 (4개 미만은 너무 큼, 12개 초과는 너무 세분화)
3. **지표:**
   - Inertia (Elbow): k 증가 시 inertia 급감 지점
   - Silhouette Score: -1~1, 높을수록 잘 분리됨, 0.5 이상 양호
   - Gap Statistic: 랜덤 분포 대비 개선도
   - R² 안정성: 클러스터별 평균 R²가 0.7 이상 유지되는 k
   - 실무: 클러스터당 최소 15종 이상 (너무 작으면 8종 추천 의미 없음)

4. **결정 예시:**
```
k=5: Silhouette 0.62, Inertia 120
k=6: 0.65, 105
k=7: 0.68 (최대), 92 (Elbow)
k=8: 0.64, 85
k=9: 0.60, 80
→ 최적 k=7 선택
```

5. **문서화:** `docs/k_selection_report.md`에 차트 3개 + 결정 근거 작성

**고정 안 함의 장점:** 평가자가 `왜 8개인가?` 물으면 `통계적 검증 결과 7개가 최적이었다`고 답변 가능

---

## 7. 전체 파이프라인 변경 (v62)

```
[KRX KOSPI200 구성종목 API + GICS 매핑 CSV + 시가총액/거래대금 (pykrx)]
    ↓
[Step 2: KOSPI200 규칙 필터 - 시총 85% + 거래대금 + 완충 90~110%]
    ↓
[200종 x 10팩터 베타 계산 (RidgeCV, 180일)]
    ↓
[Step 3: K-means 최적 K 탐색 (Elbow/Silhouette) → Factor Cluster (예: 7개) 자체 작명]
    ↓
[Step 1: KOSPI200 지수 + 산업군 지수 Ridge 회귀 (매월 1일) → 베타 갱신 → beta_snapshots/latest]
    ↓
[매일 07:30: 10개 팩터 Z-Score 계산]
    ↓
[Step 4: 각 클러스터에서 Score = 6.5 + pred*1.2 + momentum*0.3 ... 계산, GICS 정보 포함 Top 8]
    ↓
[Firebase factor_snapshots/{date} + data.js v62 생성]
    ↓
[프론트: FACTOR CLUSTERS • 7, KOSPI200 R² 0.89, GICS 표시]
```

---

## 8. 파일별 변경 목록

| 파일 | 현재 | v62 변경 |
|---|---|---|
| `price_provider.py` | KOSPI(^KS11)만 | KOSPI200(^KS200) 추가, 업종지수 API, 시총/거래대금 함수 추가 |
| `retrain_model.py` | INDUSTRY_PROXY 단일 종목 8개 | KOSPI200 지수 + GICS 산업군 지수 기반, BASE_BETAS는 클러스터 베타로 |
| `daily_update.py` | INDUSTRIES_UNIVERSE 하드코딩 64종 | `kospi200_universe.py`에서 동적 생성, 85%/거래대금/완충 규칙, GICS 정보 포함 |
| `js/data.js` | industries 8개, betas만 | factorClusters {optimal_k}개, gicsMapping, selectionRule, method, Silhouette 포함 |
| `js/app.jsx` | INDUSTRIES • 8 | FACTOR CLUSTERS • {optimal_k}, 카드에 GICS/시총/거래대금 표시 |
| **신규** `data/gics_mapping.csv` | 없음 | 티커-GICS 매핑 200종 |
| **신규** `data/kospi200_constituents.csv` | 없음 | 2024년 6월 기준 200종 + 시총/거래대금 |
| **신규** `scripts/kospi200_universe.py` | 없음 | KOSPI200 규칙 필터 구현 |
| **신규** `scripts/factor_cluster.py` | 없음 | 200종 베타 계산 + 최적 K 탐색 + 자체 작명 |
| **신규** `docs/methodology.md` | 없음 | GICS 선택 이유, 최적 K 검증 차트, KOSPI200 규칙 설명 |
| **신규** `docs/k_selection_report.md` | 없음 | Elbow/Silhouette 차트 + k=7 결정 근거 |

---

## 9. 구현 로드맵 (단계별 결정 후)

**Phase 1 - 데이터 준비 (1~2일):**
- GICS 매핑 200종 수작업 또는 외부 API로 확보
- KOSPI200 구성종목 최신 CSV 확보 (KRX INFO-DATA)
- pykrx로 시총/거래대금 수집 테스트

**Phase 2 - 클러스터링 검증 (2~3일):**
- `factor_cluster.py`로 200종 베타 계산
- k=5~12 탐색, Elbow/Silhouette 차트 생성
- 최적 K 결정 (예: 7), 자체 작명

**Phase 3 - 파이프라인 교체 (3~4일):**
- `price_provider.py`에 KOSPI200 지수 추가
- `daily_update.py` 하드코딩 제거, 동적 유니버스 적용
- `js/data.js` v62 구조로 재생성

**Phase 4 - 프론트엔드 + 문서화 (1~2일):**
- `app.jsx` INDUSTRIES → FACTOR CLUSTERS 변경, GICS 표시
- `methodology.md`, `k_selection_report.md` 작성
- 이미지 v61.6과 비교 스크린샷

**총 예상:** 7~11일, 평가자 문서 포함

---

## 10. 리스크 및 대응

| 리스크 | 대응 |
|---|---|
| GICS 매핑 데이터 없음 | WICS로 대체 가능, KRX WICS는 API 제공. GICS는 수동 매핑하되 출처 명시 |
| KOSPI200 구성종목 API 불안정 | CSV로 관리, 6월 정기변경 때 수동 갱신, Git에 커밋 |
| 200종 베타 계산 시 합성 데이터 (현재 외국인 선물 합성) | KRX API 완성까지는 현재 방식 유지하되 문서에 `합성 데이터 사용 구간` 명시 |
| 최적 K가 8이 아니면 64종 구조 깨짐 (7*8=56) | 균등 8개 고집 안 함, 클러스터 크기 비례 (예: 32개 군집은 10개, 15개 군집은 5개) 또는 64개 고정하되 가중치 조정 |
| 평가자가 `왜 자체 작명인가` 질문 | `산업명이 아닌 팩터 노출도 기반 군집임을 정직하게 표현하기 위함`이라고 답변, 방법론 문서에 명시 |

---

## 11. 한 줄 정리 (평가자용)

> **v62는 KOSPI200(공식 지수, 시장 대표성·유동성·연속성) 200종을 1차 유니버스로 두고, GICS(국제 표준 산업분류)로 1차 분류한 뒤, 10개 팩터 베타가 비슷한 종목끼리 K-means 최적 K(Elbow/Silhouette 검증)로 군집하여 자체 작명한 팩터 클러스터에서 시가총액 85%·거래대금·완충 규칙을 적용해 8종씩 추천하는 모델입니다.**

---

## 12. 다음 액션 (결정 필요)

1. GICS 매핑 파일 200종을 제가 크롤링해서 만들까요, 아니면 보유하신 파일이 있나요?
2. 최적 K 탐색을 바로 시작할까요? (200종 베타 계산부터)
3. 이 문서를 `docs/` 폴더에 넣고, `README.md`로도 사용할까요?

문서를 읽어보시고, Phase 1 데이터 준비부터 시작할지 말씀해 주세요.
