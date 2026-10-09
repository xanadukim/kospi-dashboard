# KOSPI v62 FINAL CLEAN

## 구조 비교 결과
- split.zip (17개): 모듈화된 src 파일 17개, v61.6 기반, 버그 3개 포함
- github-final.zip: 모놀리식 app.jsx 57KB + Python 백엔드 + data v62.1, 최신

## 병합 전략
- 최신 로직 기준: github-final의 data.js (factorClusters v62.1, industries, factorMeta) + factorMap 10개 완전체
- 구조 기준: split.zip의 17개 모듈 구조 유지
- 버그 수정:
  1. constants.js factorMap 중복 (2개) -> 1개로 통합 (10개 팩터)
  2. Header.jsx, Sidebar.jsx, FactorPanel.jsx return으로 시작 -> function Header(){} / Sidebar() / FactorPanel()로 감싸기
  3. App.jsx filteredPicks 미정의 -> useMemo로 정의 (github 로직 기준)

## 최종 17개 파일 (src/)
- constants.js (FIXED)
- format.js
- calculations.js
- usehistory.js
- usemarketdata.js
- Header.jsx (FIXED)
- Sidebar.jsx (FIXED)
- FactorPanel.jsx (FIXED)
- RecommendTab.jsx
- TopPredictionsTab.jsx
- All64Tab.jsx
- PerformanceTab.jsx
- MarketTab.jsx
- HistoryModal.jsx
- DisclaimerModal.jsx
- HelpModal.jsx
- App.jsx (FIXED: filteredPicks useMemo)

## 실행
- index.html 열기 (Babel standalone, React 18 CDN)
- Firebase config는 js/config.js에 포함 (공개키)
- data/ 폴더 v62 데이터 포함
