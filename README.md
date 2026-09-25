# KOSPI Quant - Cloud Auto Fix for Pages Build Failure

## 왜 Pages 빌드가 실패했나요?
GitHub Pages는 기본적으로 Jekyll로 빌드합니다.
.github/workflows 폴더와 functions 폴더가 있으면 Jekyll이 오해해서 실패합니다.
해결: 루트에 .nojekyll 파일 추가 (빈 파일)

## 이 패키지로 해결
1. .nojekyll 파일을 루트에 추가
2. daily-update.yml 문법 수정 (들여쓰기, 따옴표)

## 설치
1. 이 zip 압축 해제 후 모든 파일을 xanadukim/kospi-dashboard repo에 업로드 (덮어쓰기)
2. Actions 탭에서 pages build and deployment가 초록색으로 돌아오는지 확인
3. Daily KOSPI Auto Update 워크플로우가 보이는지 확인
4. Run workflow로 테스트
