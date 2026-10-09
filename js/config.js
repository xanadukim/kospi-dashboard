// js/config.js - Firebase & App Config - v61.3 100% REAL KRX - SECURITY PATCH v61.3 - apiKey public
// 분리된 설정 파일 - 수정 시 여기만 수정
// SECURITY: apiKey는 Firebase 공식 문서상 공개 키입니다 (https://firebase.google.com/docs/projects/api-keys)
//          비밀키가 아닙니다. 진짜 비밀은 FIREBASE_SERVICE_ACCOUNT이며 GitHub Secrets에만 보관됩니다.
//          Firestore Rules에서 write:false로 차단했으므로 클라이언트에서 쓰기 불가능합니다.

var firebaseConfig = {
  apiKey: "AIzaSyDg4-fL22BCdCIJPX4tGFmidGCUwAJ4P_Y",
  authDomain: "kospi-quant.firebaseapp.com",
  projectId: "kospi-quant",
  storageBucket: "kospi-quant.firebasestorage.app",
  messagingSenderId: "194454549722",
  appId: "1:194454549722:web:fef6a227d517e31d5b61e3",
  measurementId: "G-TJNBECPW24",
};

// 환경변수 오버라이드 지원 (Vite 전환 후 import.meta.env로 이전 예정)
if (typeof window !== 'undefined' && window._env && window._env.FIREBASE_API_KEY) {
  firebaseConfig.apiKey = window._env.FIREBASE_API_KEY;
}

var db = null;
try {
  firebase.initializeApp(firebaseConfig);
  db = firebase.firestore();
  // SECURITY: 오프라인 캐시 활성화로 불필요한 읽기 감소
  // db.enablePersistence()는 선택 사항 - 혼자 사용 시 생략 가능
  console.log("[SECURITY] Firestore Rules: read=true, write=false - Admin SDK만 쓰기 가능");
} catch (e) {
  console.log("Firebase init", e);
}
