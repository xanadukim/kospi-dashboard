# GitHub 배포 체크리스트 v4.2

## ✅ 배포 전 확인

### 파일 구조
```
.
├── index.html (대시보드 v4.2 - 5개 탭)
├── daily-update.yml (루트 - GitHub Actions가 인식)
├── .github/workflows/daily-update.yml (실제 워크플로우)
├── scripts/
│   ├── daily_update.py (64선 생성)
│   ├── track_performance.py (성과 추적 NEW)
│   └── retrain_model.py (재학습 NEW)
├── firebase.json
├── firestore.rules
├── firestore.indexes.json
├── firestore_schema_v4.md
└── README.md
```

### 1. GitHub Repository 생성
```bash
git init
git add .
git commit -m "v4.2 - KOSPI Market Model + Performance Analytics"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/kospi-quant-terminal.git
git push -u origin main
```

### 2. Secrets 설정 (중요!)
GitHub → Settings → Secrets and variables → Actions

**FIREBASE_SERVICE_ACCOUNT**
- Firebase Console → Project Settings → Service accounts → Generate new private key
- 다운로드한 JSON 파일 내용 전체를 Secret 값으로 붙여넣기
- 예: {"type": "service_account", "project_id": "kospi-quant", ...}

**KRX_API_KEY (선택)**
- KRX Open API 키, 없으면 pykrx로 대체됨

### 3. GitHub Actions 활성화
- Actions 탭 → "I understand my workflows, go ahead and enable them" 클릭
- KOSPI Quant Terminal v4.0 워크플로우 → Run workflow → job: all → Run workflow

### 4. GitHub Pages 활성화
- Settings → Pages → Build and deployment → Source: Deploy from a branch → Branch: main, /(root)
- Save 후 1-2분 뒤 https://YOUR_USERNAME.github.io/kospi-quant-terminal/ 접속

### 5. Firebase (선택, 더 빠른 호스팅)
```bash
npm install -g firebase-tools
firebase login
firebase use --add (kospi-quant 선택)
firebase deploy --only hosting,firestore
```

### 6. 첫 실행 확인
- Actions → 실행 로그 확인
- Firebase Console → Firestore → factor_snapshots 컬렉션에 오늘 날짜 문서 생성 확인
- 대시보드에서 Firebase Live 표시 확인

### 7. 스케줄 확인
- Weekly Picks: 일요일 18:00 KST 자동 실행 (09:00 UTC)
- Performance Track: 평일 16:00 KST 자동 실행 (07:00 UTC)
- Model Retrain: 매월 1일 11:00 KST 자동 실행 (02:00 UTC)

## 🚨 트러블슈팅

**Firebase 권한 오류**
- serviceAccount.json의 type 필드가 있는지 확인 (전체 JSON이어야 함, client_email만 있으면 안 됨)
- firestore.rules에서 allow write: if true로 임시 설정

**pykrx 설치 실패**
- requirements에 pykrx 추가, 또는 track_performance.py에서 pykrx 부분 주석 처리 (시뮬레이션 모드로 동작)

**GitHub Pages 404**
- index.html이 루트에 있는지 확인
- Settings → Pages → Branch가 main인지 확인

## 📊 배포 후 6개월

- 매일: performance_tracking에 64개씩 쌓임 (월 ~1,300개)
- 3개월: 4,000개 샘플, IC/Hit Rate 분석 가능
- 6개월: 8,000개 샘플, 첫 재학습으로 β 개선

## 다음 작업

1. GitHub에 푸시
2. Actions에서 수동 실행 (job: all)
3. 대시보드 5개 탭 확인 (특히 성과 분석, KOSPI 마켓 탭)
4. 내일부터 매일 16:00 자동 성과 추적 시작됨
