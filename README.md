# kospi-dashboard - Fixed

이전 `app.js` 분리 구조는 `Unexpected token '<'` 에러로 초기화 실패합니다.
이 버전은 `index.html` 단일 파일에 React + Babel + Firebase Compat가 모두 인라인으로 들어가 있어 GitHub Pages에서 바로 동작합니다.

## 구조
- index.html 하나만 있으면 동작 (style.css, app.js, firebase-config.js 불필요)
- data/, scripts/ 폴더는 백테스트용으로 유지해도 되지만 Pages 배포에는 영향 없음

## GitHub Pages 배포
1. 이 index.html로 기존 파일 교체
2. GitHub > Settings > Pages > Source: Deploy from a branch / Branch: main / root
3. https://xanadukim.github.io/kospi-dashboard/ 에서 확인

## Firebase 규칙
Firestore > 규칙 탭
```
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    match /{document=**} { allow read, write: if true; }
  }
}
```
