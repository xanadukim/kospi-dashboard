// js/regime.js - Regime Dashboard Config v60.1 REAL
// Regime 감지 임계값 및 설정 - Frontend와 Backend 공유

var regimeConfig = {
  thresholds: {
    vix: { normal: 22, crisis: 30, desc: "VIX 공포지수" },
    ovx: { normal: 35, crisis: 50, desc: "OVX 원유 변동성" },
    dxy: { normal: 104, crisis: 105, desc: "달러 인덱스" },
    wti_vol: { normal: 4.0, crisis: 6.0, desc: "WTI 5일 변동성 %" },
    kospi_3d: { normal: -2.0, crisis: -3.0, desc: "KOSPI 3일 수익률 %" },
    krw_vol: { normal: 2.5, crisis: 4.0, desc: "원달러 변동성 %" }
  },
  regimes: {
    "평시": {
      window: 120,
      color: "#10b981",
      risk: "Low",
      retrain: "매월 1일",
      desc: "안정적 - 느린 적응, 긴 윈도우",
      factor_boost: [],
      factor_penalty: []
    },
    "고변동": {
      window: 90,
      color: "#f59e0b",
      risk: "Medium",
      retrain: "즉시 + 매주",
      desc: "변동성 확대 - 빠른 적응",
      factor_boost: ["WTI_vol", "정제마진"],
      factor_penalty: ["구리", "상해종합"]
    },
    "전시": {
      window: 60,
      color: "#dc2626",
      risk: "Extreme",
      retrain: "매일",
      desc: "위기 - 초단기 적응, 방어적",
      factor_boost: ["GPR", "WTI_vol", "US10Y"],
      factor_penalty: ["구리", "상해종합", "반도체팩터"]
    }
  },
  factorBase: {
    "반도체팩터": { ic: 0.18, hit: 71.2, 평시: 0.92, 고변동: 0.85, 전시: 0.60, color: "#2563eb", desc: "전기전자 핵심" },
    "원달러": { ic: 0.14, hit: 66.4, 평시: 0.88, 고변동: 0.82, 전시: 0.55, color: "#0f766e", desc: "자동차·건설" },
    "구리": { ic: 0.12, hit: 63.5, 평시: 0.78, 고변동: 0.70, 전시: 0.45, color: "#d97706", desc: "China Proxy 1" },
    "상해종합": { ic: 0.10, hit: 61.8, 평시: 0.72, 고변동: 0.65, 전시: 0.40, color: "#7c3aed", desc: "China Proxy 2" },
    "WTI_vol": { ic: 0.12, hit: 62.0, 평시: 0.45, 고변동: 0.75, 전시: 0.90, color: "#a16207", desc: "유가 변동성" },
    "GPR": { ic: -0.06, hit: 50.0, 평시: 0.35, 고변동: 0.55, 전시: 0.85, color: "#dc2626", desc: "전쟁 리스크" },
    "정제마진": { ic: 0.10, hit: 61.0, 평시: 0.50, 고변동: 0.68, 전시: 0.80, color: "#7c3aed", desc: "화학 마진" },
    "US10Y": { ic: -0.04, hit: 48.2, 평시: 0.32, 고변동: 0.48, 전시: 0.65, color: "#e11d48", desc: "금리" }
  },
  version: "v60.1-regime-dashboard-REAL"
};
