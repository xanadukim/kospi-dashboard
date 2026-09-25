// firebase-config.js - Firebase 설정 파일
// 1. https://console.firebase.google.com/ 에서 프로젝트 생성
// 2. Firestore Database 생성 (테스트 모드)
// 3. Project Settings > General > Your apps > Web app 추가 후 config 복사

export const firebaseConfig = {
  apiKey: "YOUR_API_KEY",
  authDomain: "kospi-quant.firebaseapp.com",
  projectId: "kospi-quant",
  storageBucket: "kospi-quant.appspot.com",
  messagingSenderId: "123456789",
  appId: "1:123456789:web:abcdef",
};

// Firestore 보안 규칙 예시 (firestore.rules)
// rules_version = '2';
// service cloud.firestore {
//   match /databases/{database}/documents {
//     match /{document=**} {
//       allow read: if true;
//       allow write: if request.auth == null; // 데모용 - 실제로는 인증 추가
//     }
//   }
// }
