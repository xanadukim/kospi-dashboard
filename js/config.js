// js/config.js - Firebase & App Config - v59 China Proxy
// 분리된 설정 파일 - 수정 시 여기만 수정

var firebaseConfig = {
  apiKey: "AIzaSyDg4-fL22BCdCIJPX4tGFmidGCUwAJ4P_Y",
  authDomain: "kospi-quant.firebaseapp.com",
  projectId: "kospi-quant",
  storageBucket: "kospi-quant.firebasestorage.app",
  messagingSenderId: "194454549722",
  appId: "1:194454549722:web:fef6a227d517e31d5b61e3",
  measurementId: "G-TJNBECPW24",
};

var db = null;
try {
  firebase.initializeApp(firebaseConfig);
  db = firebase.firestore();
} catch (e) {
  console.log("Firebase init", e);
}
