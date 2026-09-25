# KOSPI 산업별 회귀 대시보드

GitHub Pages로 배포되는 퀀트 대시보드입니다.

## 웹에서 보기
Settings > Pages > Source: `main` branch / `root` 선택
→ https://{username}.github.io/{repo}/

## 폴더 구조
```
/
├── index.html          # 대시보드 진입점
├── style.css           # 스타일 (분리됨)
├── app.js              # 로직 (분리됨)
├── data/               # 회귀모델 데이터 저장소 ⭐
│   ├── model.json      # 산업별 β 계수, R²
│   ├── factors.json    # 매일 갱신되는 Z-score
│   └── history.json    # 지난주 추천 성과
├── scripts/
│   └── daily_update.py # 매일 데이터 수집 스크립트
└── .github/workflows/
    └── daily_update.yml # 매일 07:30 KST 자동 실행
```

## 데이터는 어디에 저장되나요?
1. **model.json**: 회귀모델 β (8개 산업 x 9개 팩터) - 수동으로 월 1회 재학습 후 업데이트
2. **factors.json**: 매일 갱신되는 팩터 Z-score - GitHub Actions가 자동 커밋
3. **history.json**: 추천 종목 성과 - app.js에서 localStorage + data 파일에 이중 저장
4. **브라우저 localStorage**: 사용자 개인 설정 (선택 산업 등)

## 매일 갱신은 어떻게?
1. GitHub Actions cron `30 22 * * *` (07:30 KST) 자동 실행
2. `daily_update.py`가 yfinance(FRED, KRX)에서 데이터 수집
3. Z-score 계산 후 `data/factors.json` 덮어쓰기
4. 변경사항 자동 커밋 & 푸시 → GitHub Pages 자동 재배포 (1분 내 반영)

수동 실행: Actions 탭 > Daily KOSPI Update > Run workflow
