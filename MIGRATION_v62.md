# Migration Guide: Beta → Koptimum

## 1. GitHub 보존 (Beta)

기존 KOSPI Quant Terminal은 그대로 보존됩니다.

```bash
cd kospi-quant-terminal

# 현재 main은 v61.3 beta
git tag -a v61.3-beta -m "Beta preserved: 8 industries hardcoded 64 picks, Trader Centric v61"
git push origin v61.3-beta

git branch beta
git push origin beta

# README.md에 추가
# > **Beta Preserved:** v61.3 beta is preserved in `beta` branch and `v61.3-beta` tag.
# > **New Project:** KOSPI200_Koptimum (see https://github.com/your-id/KOSPI200_Koptimum)
```

**보존되는 파일:**
- `js/data.js` v61.3 (8개 주관적 산업군)
- `js/app.jsx` Trader Centric v61
- `scripts/daily_update.py` v61.3 64 Picks
- `daily-update.yml`, `retrain.yml`
- Firebase `factor_snapshots`, `beta_snapshots`

---

## 2. 신규 프로젝트 시작 (Koptimum)

### Option A: 동일 Repo 내 orphan branch (간단)

```bash
cd kospi-quant-terminal
git checkout --orphan koptimum
git rm -rf .
cp -r /mnt/data/KOSPI200_Koptimum/* .
git add .
git commit -m "feat: KOSPI200_Koptimum v62.0 Phase A - KOSPI200 + GICS + optimal K + KRICS ready"
git push origin koptimum
```

### Option B: 신규 Repo 생성 (권장)

```bash
# GitHub 웹에서 KOSPI200_Koptimum repo 생성
mkdir KOSPI200_Koptimum
cd KOSPI200_Koptimum
cp -r /mnt/data/KOSPI200_Koptimum/* .
git init
git add .
git commit -m "init: KOSPI200_Koptimum v62.0 Phase A - KOSPI200 + optimal K + KRICS ready"
git branch -M main
git remote add origin https://github.com/your-id/KOSPI200_Koptimum.git
git push -u origin main

# beta repo 링크
echo "# Related: KOSPI Quant Terminal Beta - https://github.com/your-id/kospi-quant-terminal/tree/beta" >> README.md
```

---

## 3. Firebase 분리

### 기존 Beta
- Collection: `factor_snapshots/{date}` → 8 industries
- `beta_snapshots/latest` → latest beta
- `regime_history/{date}`

### 신규 Koptimum
- Collection: `koptimum_snapshots/{date}` → factorClusters 8개 (최적 K)
- `koptimum_beta_snapshots/latest` → optimal K beta
- `koptimum_regime_history/{date}`

**js/config.js 수정:**

```js
// Beta
var collectionPrefix = ""; // factor_snapshots

// Koptimum
var collectionPrefix = "koptimum_"; // koptimum_snapshots
```

**환경변수:**

```yaml
# .github/workflows/daily-update.yml
env:
  FIREBASE_COLLECTION_PREFIX: "koptimum_"
```

---

## 4. 파일 변경 요약

| 파일 | Beta | Koptimum v62 |
|---|---|---|
| `js/data.js` | 8 industries 하드코딩 | factorClusters 8개 + kricsMeta + kospi200Meta |
| `js/app.jsx` | INDUSTRIES 표시 | FACTOR CLUSTERS • {optimalK} + GICS/KRICS 표시 |
| `index.html` | KOSPI Quant Terminal | KOSPI200_Koptimum |
| `data/` | 외국인 CSV만 | kospi200_constituents.csv + gics_mapping.csv + factor_clusters_v62.json |
| `scripts/` | daily_update, retrain, price_provider | + kospi200_universe.py + factor_cluster.py + krics_fetcher.py |
| `price_provider.py` | KOSPI ^KS11 | + KOSPI200 ^KS200 + 시총/거래대금 함수 |
| `daily_update.py` | 64 Picks 하드코딩 | 200종 동적 + 85% + 거래대금 필터 (예정) |
| `retrain_model.py` | 8 industries proxy | KOSPI200 지수 + factorClusters 기반 (예정) |

---

## 5. 다음 단계

**Phase B (2026-09-30 ~ 2026-10-25):**
- KRX 공식 200개 대조 (data/kospi200_constituents.csv 190→200)
- yfinance REAL로 beta 재계산 (factor_cluster.py)
- daily_update.py에서 INDUSTRIES_UNIVERSE 하드코딩 제거 → kospi200_universe.py 연동
- app.jsx에서 FACTOR CLUSTERS UI

**Phase C (2026-10-26):**
- krics_fetcher.py로 KRX Index 공식 KRICS 크롤링
- KRICS 기준 재군집 → v62.1 릴리즈

---

**작성일:** 2026-09-29
**상태:** Beta preserved, Koptimum Phase A complete
