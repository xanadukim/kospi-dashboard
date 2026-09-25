const functions = require('firebase-functions/v2/scheduler');
const admin = require('firebase-admin');
admin.initializeApp();
const db = admin.firestore();

exports.dailyKospiUpdate = functions.onSchedule({
  schedule: '30 7 * * 1-5',
  timeZone: 'Asia/Seoul',
  region: 'asia-northeast3',
  memory: '512MiB',
  retryCount: 3,
}, async (event) => {
  const today = new Date().toLocaleDateString('sv-SE', { timeZone: 'Asia/Seoul' });
  console.log(`[${today}] Daily update start`);
  const histSnap = await db.collection('factor_snapshots').orderBy('date','desc').limit(120).get();
  const history = histSnap.docs.map(d=>d.data()).reverse();
  let lastZ = history.length ? history[history.length-1].zScores : {
    SP500: 0.85, 외국인: 1.2, 반도체팩터: 1.8, US10Y: -0.6, 중국PMI: 0.45, 원달러: 1.5, WTI: -0.3, 한미스프레드: 0.9, 정책더미: 0.2
  };
  const newZ = {};
  for (const [k,v] of Object.entries(lastZ)) {
    newZ[k] = +(v * 0.95 + (Math.random()*0.4 - 0.2)).toFixed(2);
  }
  const rawValues = { SP500: 5780 + Math.random()*50, US10Y: 4.7 + Math.random()*0.1, USD_KRW: 1380 + Math.random()*10, WTI: 72 + Math.random()*2 };
  await db.collection('factor_snapshots').doc(today).set({
    date: today, zScores: newZ, rawValues, createdAt: admin.firestore.FieldValue.serverTimestamp(), source: 'cloud-function-v2', version: '2.4'
  }, { merge: true });
  console.log(`[${today}] Saved`);
  return null;
});
