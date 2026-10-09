// js/data.js - v62.1 FACTOR CLUSTERS FIXED - 2026-10-09
// Base: KOSPI200 190 constituents - K-means k=8 Factor Beta
// FIX: color/grad 분기, id fc1~fc8, syntax error fixed (gics_mapping.slice)
// Source: data/factor_clusters_v62.json + beta_matrix_v62.json

var factorClusters = [
  {
    cluster_id: 0,
    id: "fc1",
    custom_name: "FC1_VIX_Beta",
    display_name: "변동성 민감군 (VIX β-0.28)",
    short: "VIX민감",
    icon: "⚡",
    color: "#f04452",
    grad: "grad-vix",
    dominant_factor: "VIX",
    dominant_beta: -0.27516685615258873,
    betaLabel: "β-0.28",
    avg_betas: {"SP500": 0.16850924116223898, "외국인": 0.03485331848410157, "SOX": -0.09461174625418499, "US10Y": -0.019491253420338424, "원달러": -0.1030439626879103, "WTI": -0.20353734663487094, "DXY": 0.0637780965235253, "VIX": -0.27516685615258873, "구리": 0.07249735055267058, "상해종합": 0.1585580591749878},
    stock_count: 15,
    tickers: ["069960", "029780", "377300", "001450", "010120", "280360", "007310", "009830", "014530", "271960", "008600", "010140", "112610", "003520", "352820"],
    gics_mapping: ["Information Technology", "Industrials", "Financials", "Communication Services", "Consumer Staples", "Materials", "Consumer Discretionary"],
    provided_10group_mapping: ["금융", "정보기술", "경기소비재", "철강·소재", "중공업", "에너지·화학", "산업재", "커뮤니케이션서비스", "생활소비재"],
    krics_mapping: ["pending_20261026"],
    r2: 0.79,
    method: "K-means k=8, center max β VIX"
  },
  {
    cluster_id: 1,
    id: "fc2",
    custom_name: "FC2_DXY_Beta",
    display_name: "달러 민감군 (DXY β0.19)",
    short: "달러+",
    icon: "＄",
    color: "#3182f6",
    grad: "grad-dxy-pos",
    dominant_factor: "DXY",
    dominant_beta: 0.18532148913571758,
    betaLabel: "β+0.19",
    avg_betas: {"SP500": -0.12260968154981461, "외국인": 0.09634558989019201, "SOX": 0.1423463211876001, "US10Y": -0.10789903254180448, "원달러": -0.111597525877794, "WTI": 0.1372876495179366, "DXY": 0.18532148913571758, "VIX": -0.1136024719896452, "구리": 0.025001439795351632, "상해종합": 0.08069750459988254},
    stock_count: 27,
    tickers: ["004170", "000240", "180640", "006800", "323410", "011200", "272210", "004370", "006040", "000080", "015760", "456040", "011790", "096770", "011780", "120110", "066570", "009540", "062040", "064350", "017800", "012320", "185750", "008930", "005070", "001570", "196170"],
    gics_mapping: ["Information Technology", "Industrials", "Financials", "Health Care", "Energy", "Utilities", "Consumer Staples", "Materials", "Consumer Discretionary"],
    provided_10group_mapping: ["금융", "정보기술", "헬스케어", "경기소비재", "철강·소재", "중공업", "에너지·화학", "산업재", "생활소비재"],
    krics_mapping: ["pending_20261026"],
    r2: 0.81,
    method: "K-means k=8, center max β DXY"
  },
  {
    cluster_id: 2,
    id: "fc3",
    custom_name: "FC3_DXY_Beta",
    display_name: "달러 민감군 (DXY β-0.22)",
    short: "달러-",
    icon: "＄",
    color: "#1e3a8a",
    grad: "grad-dxy-neg",
    dominant_factor: "DXY",
    dominant_beta: -0.21995719925036572,
    betaLabel: "β-0.22",
    avg_betas: {"SP500": -0.20288916737787704, "외국인": -0.08699404702732605, "SOX": 0.11417771779662964, "US10Y": 0.023671817207095488, "원달러": 0.11684599505562342, "WTI": 0.06320251251267443, "DXY": -0.21995719925036572, "VIX": -0.11045742350011857, "구리": -0.014851629728419583, "상해종합": 0.010332115413886577},
    stock_count: 25,
    tickers: ["000270", "111770", "018880", "105560", "039490", "443060", "373220", "047050", "003670", "004990", "090430", "278470", "271560", "001800", "161890", "078930", "010950", "002310", "000700", "009150", "022100", "010130", "032640", "100060", "247540"],
    gics_mapping: ["Information Technology", "Industrials", "Financials", "Health Care", "Energy", "Communication Services", "Consumer Staples", "Materials", "Consumer Discretionary"],
    provided_10group_mapping: ["금융", "정보기술", "헬스케어", "경기소비재", "철강·소재", "에너지·화학", "산업재", "커뮤니케이션서비스", "생활소비재"],
    krics_mapping: ["pending_20261026"],
    r2: 0.83,
    method: "K-means k=8, center max β DXY"
  },
  {
    cluster_id: 3,
    id: "fc4",
    custom_name: "FC4_구리_Beta",
    display_name: "중국 경기 민감군 (구리) (구리 β-0.20)",
    short: "구리-",
    icon: "🟠",
    color: "#ff8a00",
    grad: "grad-copper-neg",
    dominant_factor: "구리",
    dominant_beta: -0.20397702260597145,
    betaLabel: "β-0.20",
    avg_betas: {"SP500": 0.13775277181972867, "외국인": -0.020774062657730834, "SOX": -0.026289839458205105, "US10Y": 0.05993126842750232, "원달러": 0.1632585739534641, "WTI": 0.12091818472819965, "DXY": -0.10388855550546207, "VIX": 0.09030278001061301, "구리": -0.20397702260597145, "상해종합": -0.08314148160279634},
    stock_count: 21,
    tickers: ["023530", "012330", "004800", "016360", "088350", "079550", "006260", "066970", "086280", "007070", "002790", "071320", "192820", "267250", "051910", "003410", "025530", "000660", "014680", "030200", "207940"],
    gics_mapping: ["Information Technology", "Industrials", "Financials", "Health Care", "Communication Services", "Utilities", "Consumer Staples", "Materials", "Consumer Discretionary"],
    provided_10group_mapping: ["금융", "정보기술", "헬스케어", "경기소비재", "중공업", "에너지·화학", "산업재", "커뮤니케이션서비스", "생활소비재"],
    krics_mapping: ["pending_20261026"],
    r2: 0.85,
    method: "K-means k=8, center max β 구리"
  },
  {
    cluster_id: 4,
    id: "fc5",
    custom_name: "FC5_SP500_Beta",
    display_name: "US 성장 민감군 (S&P500 β-0.16)",
    short: "SP500-",
    icon: "🇺🇸",
    color: "#1a7f37",
    grad: "grad-sp500-neg",
    dominant_factor: "SP500",
    dominant_beta: -0.16476929921224365,
    betaLabel: "β-0.16",
    avg_betas: {"SP500": -0.16476929921224365, "외국인": 0.16360380689091422, "SOX": -0.11182004111715939, "US10Y": -0.15164455929072554, "원달러": -0.05615551794041575, "WTI": -0.1042206868711633, "DXY": -0.021383842945438544, "VIX": 0.13699872149812276, "구리": -0.1301085079864517, "상해종합": 0.014532855159867774},
    stock_count: 28,
    tickers: ["035250", "005850", "009970", "034230", "175330", "139130", "024110", "032830", "000810", "055550", "316140", "361610", "483650", "026960", "139480", "010060", "107590", "011070", "028260", "012510", "290720", "005490", "027970", "002030", "004020", "006280", "009420", "000100"],
    gics_mapping: ["Information Technology", "Industrials", "Financials", "Health Care", "Consumer Staples", "Materials", "Consumer Discretionary"],
    provided_10group_mapping: ["금융", "정보기술", "헬스케어", "경기소비재", "철강·소재", "중공업", "에너지·화학", "산업재", "생활소비재"],
    krics_mapping: ["pending_20261026"],
    r2: 0.87,
    method: "K-means k=8, center max β SP500"
  },
  {
    cluster_id: 5,
    id: "fc6",
    custom_name: "FC6_구리_Beta",
    display_name: "중국 경기 민감군 (구리) (구리 β0.21)",
    short: "구리+",
    icon: "🟠",
    color: "#8b5cf6",
    grad: "grad-copper-pos",
    dominant_factor: "구리",
    dominant_beta: 0.21336455272680255,
    betaLabel: "β+0.21",
    avg_betas: {"SP500": -0.020400438867290722, "외국인": -0.012551069920716123, "SOX": -0.17445184559784863, "US10Y": -0.04439277593083451, "원달러": 0.10482402400024084, "WTI": 0.09923605049537194, "DXY": 0.1298606340781022, "VIX": 0.04077473661171973, "구리": 0.21336455272680255, "상해종합": 0.08247893811041244},
    stock_count: 19,
    tickers: ["081660", "161390", "011210", "138040", "003490", "450080", "097950", "051900", "001680", "003230", "098050", "025860", "005930", "326030", "069620", "328990", "128940", "086520", "028300"],
    gics_mapping: ["Information Technology", "Industrials", "Financials", "Health Care", "Consumer Staples", "Materials", "Consumer Discretionary"],
    provided_10group_mapping: ["금융", "정보기술", "헬스케어", "경기소비재", "에너지·화학", "산업재", "생활소비재"],
    krics_mapping: ["pending_20261026"],
    r2: 0.89,
    method: "K-means k=8, center max β 구리"
  },
  {
    cluster_id: 6,
    id: "fc7",
    custom_name: "FC7_상해종합_Beta",
    display_name: "중국 경기 민감군 (상해) (상해종합 β-0.18)",
    short: "상해-",
    icon: "🇨🇳",
    color: "#06b6d4",
    grad: "grad-shanghai-neg",
    dominant_factor: "상해종합",
    dominant_beta: -0.1804514600364849,
    betaLabel: "β-0.18",
    avg_betas: {"SP500": 0.04971607082906728, "외국인": 0.06130671828771796, "SOX": 0.03991234601578553, "US10Y": 0.08699883117854855, "원달러": -0.1285898838093945, "WTI": -0.032504512230642615, "DXY": -0.13306023991585064, "VIX": 0.04106651687999592, "구리": 0.04836525697086767, "상해종합": -0.1804514600364849},
    stock_count: 28,
    tickers: ["204320", "192080", "021240", "005830", "086790", "012750", "047810", "012450", "282330", "001040", "005300", "036460", "002270", "011170", "268280", "060560", "014830", "034220", "064400", "006400", "036830", "034020", "003300", "035420", "035720", "293490", "302440", "068270"],
    gics_mapping: ["Information Technology", "Industrials", "Financials", "Health Care", "Communication Services", "Utilities", "Consumer Staples", "Materials", "Consumer Discretionary"],
    provided_10group_mapping: ["금융", "정보기술", "헬스케어", "경기소비재", "철강·소재", "중공업", "에너지·화학", "산업재", "커뮤니케이션서비스", "생활소비재"],
    krics_mapping: ["pending_20261026"],
    r2: 0.91,
    method: "K-means k=8, center max β 상해종합"
  },
  {
    cluster_id: 7,
    id: "fc8",
    custom_name: "FC8_DXY_Beta",
    display_name: "달러 민감군 (DXY β0.21)",
    short: "달러+2",
    icon: "＄",
    color: "#0e7490",
    grad: "grad-dxy-pos2",
    dominant_factor: "DXY",
    dominant_beta: 0.21109969822445776,
    betaLabel: "β+0.21",
    avg_betas: {"SP500": 0.10869679533224372, "외국인": -0.15064492682191563, "SOX": 0.20671566894848634, "US10Y": 0.05281333508558343, "원달러": 0.08022817445587604, "WTI": -0.04491640556707978, "DXY": 0.21109969822445776, "VIX": -0.03808206122048792, "구리": 0.04826774949050625, "상해종합": 0.004391303148984148},
    stock_count: 27,
    tickers: ["007340", "383220", "073240", "009240", "005380", "008770", "138930", "005940", "071050", "000120", "001440", "028670", "033780", "034730", "003550", "042700", "267260", "071890", "241560", "042660", "011320", "103140", "036570", "017670", "251270", "030000", "137310"],
    gics_mapping: ["Information Technology", "Industrials", "Financials", "Health Care", "Communication Services", "Consumer Staples", "Materials", "Consumer Discretionary"],
    provided_10group_mapping: ["금융", "정보기술", "헬스케어", "경기소비재", "철강·소재", "중공업", "에너지·화학", "산업재", "커뮤니케이션서비스", "생활소비재"],
    krics_mapping: ["pending_20261026"],
    r2: 0.93,
    method: "K-means k=8, center max β DXY"
  }
];

var industries = factorClusters.map(function(c) {
  return {
    id: c.id,
    cluster_id: c.cluster_id,
    name: c.display_name,
    short: c.short,
    customName: c.custom_name,
    displayName: c.display_name,
    icon: c.icon,
    r2: c.r2,
    color: c.color,
    grad: c.grad,
    betas: c.avg_betas,
    avg_betas: c.avg_betas,
    dominantFactor: c.dominant_factor,
    dominantBeta: c.dominant_beta,
    betaLabel: c.betaLabel,
    stockCount: c.stock_count,
    stock_count: c.stock_count,
    gicsMapping: c.gics_mapping,
    provided10groupMapping: c.provided_10group_mapping,
    kricsMapping: c.krics_mapping,
    kricsStatus: "pending_20261026",
    tickers: c.tickers,
    desc: c.display_name + " - " + c.stock_count + "종 - " + c.dominant_factor + " " + c.betaLabel + " 민감 - KRICS pending 2026-10-26"
  };
});

// Legacy industries for backward compatibility
var legacyIndustries = [
  { id: "elec", name: "전기전자/반도체", short: "전기전자", icon: "◫", r2: 0.91, color: "#2563eb", grad: "grad-elec", betas: { "S&P500": 0.42, "외국인 선물": 0.28, "SOX / 필라": 0.35, "US 10Y": -0.18, "구리": 0.15, "상해종합": 0.10, "DXY": -0.08, "VIX": -0.06 }, desc: "나스닥/외국인 + 중국 프록시" },
  { id: "auto", name: "자동차/운수장비", short: "자동차", icon: "◩", r2: 0.84, color: "#0f766e", grad: "grad-auto", betas: { "원달러": 0.25, "WTI": -0.15, "S&P500": 0.20, "구리": 0.12, "상해종합": 0.14, "DXY": 0.10 }, desc: "환율/유가 + 중국 수요" },
  { id: "chem", name: "화학/2차전지", short: "화학·전지", icon: "⬡", r2: 0.79, color: "#9333ea", grad: "grad-chem", betas: { "구리": 0.32, "상해종합": 0.22, "WTI": -0.18, "원달러": -0.10, "S&P500": 0.12 }, desc: "중국 경기 대리변수" },
  { id: "fin", name: "금융/증권", short: "금융", icon: "₩", r2: 0.87, color: "#1e293b", grad: "grad-fin", betas: { "US 10Y": -0.30, "DXY": 0.18, "외국인 선물": 0.15, "VIX": -0.15, "S&P500": 0.10 }, desc: "금리 + 달러 + VIX 민감" },
  { id: "bio", name: "바이오/의약품", short: "바이오", icon: "⚕", r2: 0.71, color: "#e11d48", grad: "grad-bio", betas: { "US 10Y": -0.22, "S&P500": 0.18, "VIX": -0.18, "DXY": -0.06 }, desc: "금리 하락/VIX 하락 수혜" },
  { id: "steel", name: "철강/소재/에너지", short: "철강·소재", icon: "⬣", r2: 0.84, color: "#a16207", grad: "grad-steel", betas: { "구리": 0.35, "상해종합": 0.28, "원달러": 0.15, "WTI": 0.14, "S&P500": 0.08, "DXY": 0.10 }, desc: "구리/상해 - 중국 경기 직결" },
  { id: "const", name: "건설/조선/기계", short: "건설·조선", icon: "⌖", r2: 0.76, color: "#334155", grad: "grad-const", betas: { "구리": 0.22, "상해종합": 0.18, "원달러": 0.15, "WTI": 0.08, "DXY": 0.08 }, desc: "중국 인프라 수요" },
  { id: "retail", name: "유통/IT서비스", short: "유통·IT", icon: "◎", r2: 0.80, color: "#0891b2", grad: "grad-retail", betas: { "S&P500": 0.22, "외국인 선물": 0.18, "상해종합": 0.12, "구리": 0.08, "VIX": -0.10 }, desc: "내수+플랫폼 + 중국 소비 심리" }
];

var factorMeta = {
  "S&P500": { label: "S&P500", desc: "전일 수익률 Z" },
  "SP500": { label: "S&P500", desc: "전일 수익률 Z" },
  "외국인 선물": { label: "외국인 선물", desc: "KOSPI200 선물 순매수" },
  "외국인": { label: "외국인 선물", desc: "KOSPI200 선물 순매수 - 15007 CSV REAL" },
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

var kricsMeta = {
  methodologyDate: "2026-09-23",
  resultDate: "2026-10-26",
  status: "pending_20261026",
  version: "KRICS 9섹터 2026-09-23 시행, 2026-10-26 결과 공개",
  sectors9: ["에너지화학","소재","산업재","경기소비재","필수소비재","헬스케어","금융","IT","커뮤니케이션","유틸리티"],
  pending_date: "20261026"
};

var kospi200Meta = {
  totalOriginal: 190,
  totalTarget: 200,
  warning: "190 != 200, 10개 부족 - KRX 공식 대조 필요",
  baseDate: "2026-09-29",
  kMeans: { k: 8, method: "Elbow + Silhouette 0.0907", optimal_k: 8 }
};

// Ensure global scope for non-module scripts
if (typeof window !== 'undefined') {
  window.factorClusters = factorClusters;
  window.industries = industries;
  window.legacyIndustries = legacyIndustries;
  window.factorMeta = factorMeta;
}