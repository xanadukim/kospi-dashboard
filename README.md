# KOSPI Quant Terminal v4.2 - Modern + KOSPI Market Model + Performance Learning

## 🚀 v4.2 배포 버전 (최종)

### 프론트엔드 (5개 탭)
1. **산업 회귀모델** - Factor Betas, DAILY MORNING CHECKLIST
2. **월요일 추천** - 업종별 Top8, 64선 KRX β·모멘텀 스크리닝
3. **지난주 성과** - 8종목 수익률, vs KOSPI
4. **📊 성과 분석 (NEW v4.1)** - IC, Hit Rate, Factor 유효성, 12주 추이
5. **🌐 KOSPI 마켓 (NEW v4.2)** - 전체 KOSPI 2-Stage 모델, β_market, 마켓 중립 알파

모던 디자인: 영역별 그라데이션, 글래스모피즘, 모던 버튼 (btn-modern)

### 백엔드 v4.0 (3개 Job)
- **weekly-picks**: 일요일 18:00 KST - 64선 생성 (`scripts/daily_update.py`)
- **performance-track**: 평일 16:00 KST - 실제 수익률 추적 (`scripts/track_performance.py`)
- **model-retrain**: 매월 1일 11:00 KST - 6개월 성과 기반 재학습 (`scripts/retrain_model.py`)

### Firestore Collections (v4.0)
- `factor_snapshots/{YYYY-MM-DD}` - Z-Scores + 64 picks (기존)
- `performance_tracking/{recDate}_{ticker}_{trackDate}` - 실제 1W/1M 수익률 (NEW)
- `model_metrics/{YYYY-MM-DD}` - Hit Rate, IC 일별 집계 (NEW)
- `model_versions/{YYYY-MM}` - 월별 재학습 β 버전 관리 (NEW)
- `config/industries` - 최신 β (대시보드 로드)

## 📦 GitHub 배포 방법

### 1. GitHub Secrets 설정
Repository Settings → Secrets and variables → Actions → New repository secret

- `FIREBASE_SERVICE_ACCOUNT`: Firebase 서비스 계정 JSON 전체
  ```bash
  # 로컬에서
  cat serviceAccount.json | base64 -w 0
  # GitHub Secret에 붙여넣기 (JSON 그대로)
  ```
- `KRX_API_KEY`: KRX Open API 키 (선택, pykrx로 대체 가능)

### 2. GitHub Pages 활성화
Settings → Pages → Source: Deploy from a branch → Branch: main, / (root)

### 3. 워크플로우 실행
Actions → KOSPI Quant Terminal v4.0 → Run workflow → job: all

수동 실행:
- `picks`: 64선 생성만
- `track`: 성과 추적만
- `retrain`: 모델 재학습만
- `all`: 전체 실행

### 4. Firebase Hosting (선택)
```bash
npm install -g firebase-tools
firebase login
firebase deploy --only hosting
```

### 5. Firestore Indexes 배포
```bash
firebase deploy --only firestore:indexes
firebase deploy --only firestore:rules
```

## 🔄 데이터 플로우 v4.2

```
[일요일 18:00] daily_update.py
  → factor_snapshots/{date}

[평일 16:00] track_performance.py
  → performance_tracking + model_metrics

[매월 1일 11:00] retrain_model.py
  → 6개월 분석 → model_versions + config/industries

[대시보드] index.html
  → factor_snapshots + config/industries + model_metrics (onSnapshot)
  → 5개 탭: 모델, 추천, 성과, 분석, KOSPI 마켓
```

## 📈 6개월 로드맵

- **0-1개월**: 성과 데이터 1,664개 샘플 적재 시작
- **3개월**: IC 0.08 → 0.12 목표, Hit Rate 62% → 68%
- **6개월**: 첫 재학습 v4.0, R² 0.71~0.91 → 0.78~0.94, KOSPI R² 0.89 → 0.92

## 🛠️ 로컬 테스트

```bash
pip install firebase-admin pykrx pandas numpy scikit-learn

# 64선 생성
export FIREBASE_SERVICE_ACCOUNT='$(cat serviceAccount.json)'
python scripts/daily_update.py

# 성과 추적
python scripts/track_performance.py

# 재학습 (6개월 데이터 필요)
python scripts/retrain_model.py
```

## 📄 라이선스
© 2026 Quant Lab • 교육용 시뮬레이션

## 🔗 링크
- Dashboard: https://kospi-quant.web.app (Firebase Hosting)
- GitHub: https://github.com/your-username/kospi-quant-terminal
