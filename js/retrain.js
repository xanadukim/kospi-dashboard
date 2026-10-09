// js/retrain.js - Retrain Config v60.2 REAL
var retrainConfig = {
  schedule: {
    cron: "0 2 1 * *", // 매월 1일 02:00 UTC
    kst: "매월 1일 11:00 KST",
    window: 180,
    description: "180일 롤링 RidgeCV 재학습"
  },
  method: {
    name: "RidgeCV",
    alphas: [0.1, 0.5, 1.0, 2.0],
    scaler: "StandardScaler",
    blending: "70% new 30% old",
    clipping: "[-0.6, 0.6]",
    threshold: 0.02
  },
  industries: {
    elec: { ticker: "005930", name: "삼성전자", color: "#2563eb" },
    auto: { ticker: "005380", name: "현대차", color: "#0f766e" },
    chem: { ticker: "051910", name: "LG화학", color: "#9333ea" },
    fin: { ticker: "055550", name: "신한지주", color: "#1e293b" },
    bio: { ticker: "068270", name: "셀트리온", color: "#e11d48" },
    steel: { ticker: "005490", name: "POSCO홀딩스", color: "#a16207" },
    const: { ticker: "009540", name: "HD한국조선해양", color: "#334155" },
    retail: { ticker: "035420", name: "NAVER", color: "#0891b2" }
  },
  triggers: {
    monthly: "매월 1일 정기",
    high_vol: "VIX>22 or WTI vol>4% → 90일 윈도우 즉시 재학습",
    crisis: "VIX>30 or OVX>50 → 60일 윈도우 즉시 재학습"
  },
  storage: {
    history: "retrain_history/{date}",
    latest: "beta_snapshots/latest",
    snapshots: "beta_snapshots/{date}",
    logs: "retrain_logs/{date}",
    generated: "js/data.js.new"
  },
  version: "v60.2-retrain-6mo-RidgeCV-REAL"
};
