// constants.js - KOSPI v62.0 FINAL CLEAN - factorMap 중복 제거
const tfMap = { elec: "반도체팩터", auto: "원달러", chem: "중국PMI", fin: "한미스프레드", bio: "US10Y", steel: "중국PMI", const: "원달러", retail: "SP500" };

// v62 최신 - 10개 팩터 완전체 (github-final 기준 최신)
const factorMap = { 
  "S&P500": ["SP500","S&P500"], 
  "SOX / 필라": ["반도체팩터","SOX / 필라","SOX"], 
  "원달러": ["원달러"], 
  "US 10Y": ["US10Y","한미스프레드"], 
  "구리": ["중국PMI","구리"], 
  "상해종합": ["중국PMI","상해종합"], 
  "WTI": ["WTI"], 
  "DXY": ["DXY"], 
  "VIX": ["VIX"], 
  "외국인 선물": ["외국인"] 
};

const industryMap = { elec: "전기전자", auto: "자동차", chem: "화학·전지", fin: "금융", bio: "바이오", steel: "철강·소재", const: "건설·조선", retail: "유통·IT" };

const factorMeta = {
  "S&P500": { label: "S&P500", desc: "전일 수익률 Z" },
  "SP500": { label: "S&P500", desc: "전일 수익률 Z" },
  "외국인 선물": { label: "외국인 선물", desc: "KOSPI200 선물 순매수 - 15007 CSV REAL" },
  "외국인": { label: "외국인 선물", desc: "KOSPI200 선물 순매수" },
  "SOX / 필라": { label: "SOX / 필라", desc: "반도체 지수 모멘텀" },
  "SOX": { label: "SOX / 필라", desc: "반도체 지수 모멘텀" },
  "US 10Y": { label: "US 10Y", desc: "금리 변동 Z" },
  "US10Y": { label: "US 10Y", desc: "금리 변동 Z" },
  "원달러": { label: "원/달러", desc: "환율 변동 Z" },
  "WTI": { label: "WTI", desc: "유가 변동 Z" },
  "DXY": { label: "DXY", desc: "달러 인덱스 Z" },
  "VIX": { label: "VIX", desc: "변동성 지수 Z" },
  "구리": { label: "구리", desc: "China Proxy 1 - HG=F" },
  "상해종합": { label: "상해종합", desc: "China Proxy 2 - 000001.SS" }
};

const retrainMeta = { 
  date: "2026-09-27", 
  avg_r2: 0.84, 
  changes: 41, 
  next_retrain: "2026-10-01", 
  version: "v62.0", 
  window: 180, 
  beta_changes: {}, 
  r2_list: {elec:0.91,auto:0.84,chem:0.79,fin:0.87,bio:0.71,steel:0.84,const:0.76,retail:0.80} 
};

// global export for non-module (Babel standalone) + ESM
if (typeof window !== 'undefined') {
  window.tfMap = tfMap;
  window.factorMap = factorMap;
  window.industryMap = industryMap;
  window.factorMeta = factorMeta;
  window.retrainMeta = retrainMeta;
}
