const { useState, useMemo, useEffect } = React;

function App() {
  const [selectedIndustry, setSelectedIndustry] = useState("fc1");
  const [selectedFactor, setSelectedFactor] = useState(null);
  const [filterEnabled, setFilterEnabled] = useState(true);
  const [zScores, setZScores] = useState({
    "S&P500": 0.63,
    "외국인 선물": 1.07,
    "SOX / 필라": 1.59,
    "US 10Y": -1.13,
    원달러: 1.38,
    WTI: -0.32,
    DXY: 0.45,
    VIX: -0.52,
    구리: 0.68,
    상해종합: 0.42,
  });
  const [history, setHistory] = useState([]);
  const [selectedDate, setSelectedDate] = useState("2026-09-28");
  const [showHistory, setShowHistory] = useState(false);
  const [showDisclaimer, setShowDisclaimer] = useState(false);
  const [showHelp, setShowHelp] = useState(false);
  const [activeTab, setActiveTab] = useState("recommend");
  const [liveCount, setLiveCount] = useState(0);
  const [lastRefresh, setLastRefresh] = useState(new Date());
  const [isViewingHistory, setIsViewingHistory] = useState(false);

  // Industries from global (v62 factorClusters) or fallback
  const industries = useMemo(() => {
    if (typeof window !== 'undefined' && window.industries && window.industries.length > 0) return window.industries;
    // fallback fc1~fc8 mock for clean build
    return [
      { id: "fc1", name: "변동성 민감군 (VIX β-0.28)", short: "VIX민감", icon: "⚡", r2: 0.79, color: "#f04452", betas: {"VIX": -0.27, "S&P500": 0.16, "구리": 0.07} },
      { id: "fc2", name: "달러 민감군 (DXY β0.19)", short: "달러+", icon: "＄", r2: 0.82, color: "#3182f6", betas: {"DXY": 0.18, "SOX / 필라": 0.14, "WTI": 0.13} },
      { id: "fc3", name: "반도체 민감군", short: "반도체", icon: "◫", r2: 0.91, color: "#2563eb", betas: {"SOX / 필라": 0.35, "S&P500": 0.42} },
      { id: "fc4", name: "원달러 민감군", short: "원달러", icon: "◩", r2: 0.84, color: "#0f766e", betas: {"원달러": 0.25, "S&P500": 0.20} },
      { id: "fc5", name: "중국 민감군", short: "중국", icon: "⬡", r2: 0.79, color: "#9333ea", betas: {"구리": 0.32, "상해종합": 0.22} },
      { id: "fc6", name: "금리 민감군", short: "금리", icon: "₩", r2: 0.87, color: "#1e293b", betas: {"US 10Y": -0.30, "DXY": 0.18} },
      { id: "fc7", name: "에너지 민감군", short: "에너지", icon: "⬣", r2: 0.84, color: "#a16207", betas: {"WTI": 0.20, "구리": 0.15} },
      { id: "fc8", name: "방어주 민감군", short: "방어", icon: "◎", r2: 0.80, color: "#0891b2", betas: {"S&P500": 0.22, "VIX": -0.10} },
    ];
  }, []);

  const currentIndustry = useMemo(() => industries.find((i) => i.id === selectedIndustry) || industries[0], [industries, selectedIndustry]);

  const contributions = useMemo(() => {
    const fm = typeof factorMeta !== 'undefined' ? factorMeta : {};
    return Object.entries(currentIndustry.betas || {}).map(([factor, beta]) => {
      const z = zScores[factor] ?? fm[factor]?.label ? (zScores[fm[factor]?.label] ?? 0) : 0;
      const actualZ = zScores[factor] ?? 0;
      const contrib = beta * actualZ;
      return { factor, beta, z: actualZ, contrib };
    }).sort((a, b) => Math.abs(b.contrib) - Math.abs(a.contrib));
  }, [currentIndustry, zScores]);

  const predictedReturn = useMemo(() => contributions.reduce((sum, c) => sum + c.contrib, 0), [contributions]);

  const weeklyPicks = useMemo(() => {
    const selected = history.find((d) => d.date === selectedDate) || history[0];
    if (selected?.weeklyPicks && selected.weeklyPicks.length >= 20) return selected.weeklyPicks;
    const getZ = (tf) => {
      const map = { 반도체팩터: zScores["SOX / 필라"] ?? 1.59, 원달러: zScores["원달러"] ?? 1.38, 중국PMI: 0.21, 한미스프레드: 0.91, US10Y: zScores["US 10Y"] ?? -1.13, SP500: zScores["S&P500"] ?? 0.63 };
      return map[tf] ?? 0.8;
    };
    const mockData = [
      { id: "fc1", stocks: [["069960","현대건설",1.0,0.8],["029780","삼성카드",1.25,1.2]] },
      { id: "fc2", stocks: [["005930","삼성전자",1.0,0.7],["000660","SK하이닉스",1.15,1.1]] },
      { id: "fc3", stocks: [["005380","현대차",1.0,0.7],["000270","기아",1.15,1.1]] },
      { id: "fc4", stocks: [["051910","LG화학",1.0,-0.3],["086520","에코프로",1.25,2.2]] },
      { id: "fc5", stocks: [["055550","신한지주",1.0,0.5],["105560","KB금융",1.1,0.6]] },
      { id: "fc6", stocks: [["068270","셀트리온",1.0,0.4],["207940","삼성바이오",1.1,0.5]] },
      { id: "fc7", stocks: [["005490","POSCO",1.0,0.6],["010130","고려아연",0.75,0.4]] },
      { id: "fc8", stocks: [["035420","NAVER",1.05,-0.2],["035720","카카오",1.1,-0.4]] },
    ];
    const tfMapLocal = typeof tfMap !== 'undefined' ? tfMap : { fc1: "VIX", fc2: "DXY", fc3: "반도체팩터", fc4: "원달러", fc5: "중국PMI", fc6: "한미스프레드", fc7: "WTI", fc8: "SP500" };
    const picks = [];
    mockData.forEach((ind) => {
      const tf = tfMapLocal[ind.id] || "SP500";
      const z = getZ(tf);
      ind.stocks.forEach(([ticker, name, beta_adj, mom]) => {
        const score = 6.5 + Math.abs(z) * 1.2 * beta_adj + mom * 0.3 + Math.random()*0.5;
        picks.push({ industryId: ind.id, ticker, name, score: parseFloat(score.toFixed(1)), expectedReturn: parseFloat((0.5 + Math.abs(z)*0.8*beta_adj + mom*0.2).toFixed(1)), reason: `${tf} ${z.toFixed(2)}σ × β${beta_adj} + mom ${mom}%`, targetFactor: tf, date: selectedDate });
      });
    });
    return picks;
  }, [history, selectedDate, zScores]);

  // ✅ 버그 수정: filteredPicks 미정의 -> useMemo 정의 (v62 FINAL)
  const filteredPicks = useMemo(() => {
    let picks = weeklyPicks.filter(p => p.industryId === selectedIndustry);
    if (selectedFactor) {
      const fMap = typeof factorMap !== 'undefined' ? factorMap : { "S&P500": ["SP500"], "구리": ["구리"] };
      const related = fMap[selectedFactor] || [selectedFactor];
      picks = picks.filter(p => related.some(r => p.targetFactor.includes(r) || p.reason.includes(r)));
      if (picks.length === 0) picks = weeklyPicks.filter(p => p.industryId === selectedIndustry);
    }
    return picks.slice(0,8);
  }, [weeklyPicks, selectedIndustry, selectedFactor]);

  const all64Filtered = useMemo(() => {
    if (!selectedFactor) return weeklyPicks;
    const fMap = typeof factorMap !== 'undefined' ? factorMap : {};
    const related = fMap[selectedFactor] || [selectedFactor];
    return weeklyPicks.filter(p => related.some(r => p.targetFactor.includes(r) || p.reason.includes(r)));
  }, [weeklyPicks, selectedFactor]);

  const pastPicks = useMemo(() => {
    const iMap = typeof industryMap !== 'undefined' ? industryMap : {};
    const picksForIndustry = filteredPicks.length >= 1 ? filteredPicks : weeklyPicks.filter(p => p.industryId === selectedIndustry).slice(0,8);
    return picksForIndustry.map((p) => {
      const baseReturn = (p.score - 6.5) * 0.8 + (Math.random()*2 - 0.5);
      const returnPct = parseFloat(baseReturn.toFixed(1));
      const vsKospi = parseFloat((returnPct - (Math.random()*1.5 - 0.2)).toFixed(1));
      const buyPrice = 30000 + Math.floor(Math.random()*400000);
      const currentPrice = Math.floor(buyPrice * (1 + returnPct/100));
      const status = returnPct > 1.5 ? "성공" : returnPct > -1 ? "보류" : "실패";
      return { date: "09-15", industryId: p.industryId, industry: iMap[p.industryId] || p.industryId, ticker: p.ticker, name: p.name, buyPrice, currentPrice, returnPct, vsKospi, status, score: p.score };
    });
  }, [filteredPicks, weeklyPicks, selectedIndustry]);

  const pastPicksAvg = useMemo(() => {
    if (pastPicks.length === 0) return { avg: 0, vsKospi: 0, hit: 0 };
    const avg = pastPicks.reduce((s,r) => s+r.returnPct,0)/pastPicks.length;
    const vs = pastPicks.reduce((s,r) => s+r.vsKospi,0)/pastPicks.length;
    const hit = pastPicks.filter(r => r.returnPct > 0).length;
    return { avg: avg.toFixed(2), vsKospi: vs.toFixed(2), hit };
  }, [pastPicks]);

  const currentRegime = useMemo(() => ({ regime: "normal", confidence: "평시", window: 120, vix: 16.5, description: "정상 시장 - 120일 윈도우" }), []);
  const currentMeta = useMemo(() => ({ top_valid: [{}, {}, {}, {}, {}] }), []);

  const loadSnapshot = (dateStr) => {
    const doc = history.find((d) => d.date === dateStr);
    if (!doc) return;
    const cloud = doc.zScores;
    if (cloud) {
      setZScores({
        "S&P500": cloud.SP500 ?? cloud["S&P500"] ?? 0.63,
        "외국인 선물": cloud.외국인 ?? cloud.외국인_선물 ?? 1.07,
        "SOX / 필라": cloud.반도체팩터 ?? cloud["SOX / 필라"] ?? 1.59,
        "US 10Y": cloud.US10Y ?? -1.13,
        원달러: cloud.원달러 ?? 1.38,
        WTI: cloud.WTI ?? -0.32,
        DXY: cloud.DXY ?? 0.45,
        VIX: cloud.VIX ?? -0.52,
        구리: cloud.구리 ?? 0.68,
        상해종합: cloud.상해종합 ?? 0.42,
      });
      setSelectedDate(doc.date);
      setIsViewingHistory(doc.date !== history[0]?.date);
      setLastRefresh(new Date());
    }
  };

  const returnToLatest = () => {
    if (history[0]) {
      loadSnapshot(history[0].date);
      setIsViewingHistory(false);
    }
  };

  useEffect(() => {
    if (typeof db === 'undefined' || !db) {
      setHistory([{ date: selectedDate, weeklyPicks, zScores }]);
      return;
    }
    const unsub = db.collection("factor_snapshots").orderBy("date", "desc").limit(10).onSnapshot((snap) => {
      const docs = snap.docs.map((d) => d.data());
      setHistory(docs);
      setLiveCount(docs.length);
      setLastRefresh(new Date());
      if (docs[0]?.zScores && !isViewingHistory) {
        const cloud = docs[0].zScores;
        setZScores({
          "S&P500": cloud.SP500 ?? cloud["S&P500"] ?? 0.63,
          "외국인 선물": cloud.외국인 ?? cloud.외국인_선물 ?? 1.07,
          "SOX / 필라": cloud.반도체팩터 ?? cloud["SOX / 필라"] ?? 1.59,
          "US 10Y": cloud.US10Y ?? -1.13,
          원달러: cloud.원달러 ?? 1.38,
          WTI: cloud.WTI ?? -0.32,
          DXY: cloud.DXY ?? 0.45,
          VIX: cloud.VIX ?? -0.52,
          구리: cloud.구리 ?? 0.68,
          상해종합: cloud.상해종합 ?? 0.42,
        });
        setSelectedDate(docs[0].date);
      }
    });
    return () => unsub && unsub();
  }, [isViewingHistory, weeklyPicks]);

  return (
    <div className="min-h-screen bg-white">
      <Header 
        activeTab={activeTab} setActiveTab={setActiveTab}
        filteredPicks={filteredPicks} all64Filtered={all64Filtered} pastPicks={pastPicks}
        currentMeta={currentMeta} predictedReturn={predictedReturn}
        isViewingHistory={isViewingHistory} returnToLatest={returnToLatest}
        history={history} setShowHistory={setShowHistory} setShowDisclaimer={setShowDisclaimer} setShowHelp={setShowHelp}
      />
      <div className="max-w-screen-2xl mx-auto px-4 md:px-6 py-4">
        <div className="grid grid-cols-12 gap-4">
          <Sidebar selectedIndustry={selectedIndustry} setSelectedIndustry={setSelectedIndustry} industries={industries} zScores={zScores} />
          <div className="col-span-12 md:col-span-10 grid grid-cols-12 gap-4">
            <main className="col-span-12 lg:col-span-8 lg:sticky lg:top-[88px] lg:h-[calc(100vh-6rem)] lg:overflow-auto pr-1">
              <div className="xl:hidden flex items-center gap-1 p-1 rounded-full bg-[#f1f5f9] border border-[#e5e8eb] w-fit flex-wrap mb-4">
                {[
                  { id: "recommend", label: "추천", icon: "🎯", count: filteredPicks.length, color: "#1e3a8a" },
                  { id: "top", label: "오늘 Top 예측", icon: "📊", count: 8, color: "#f59e0b" },
                  { id: "all64", label: "전체 64", icon: "📋", count: all64Filtered.length, color: "#334155" },
                  { id: "performance", label: "성과", icon: "📈", count: pastPicks.length, color: "#7c3aed" },
                  { id: "market", label: "마켓", icon: "🌐", count: currentMeta?.top_valid?.length || 5, color: "#059669" },
                ].map((tab) => (
                  <button key={tab.id} onClick={() => setActiveTab(tab.id)}
                    className={`px-3 py-1.5 rounded-full text-xs font-bold flex items-center gap-1 transition-all ${activeTab === tab.id ? "text-white" : "text-slate-600 hover:bg-white"}`}
                    style={activeTab === tab.id ? { background: tab.color } : {}}>
                    <span>{tab.icon}</span> {tab.label}
                  </button>
                ))}
              </div>

              <RecommendTab activeTab={activeTab} currentIndustry={currentIndustry} predictedReturn={predictedReturn} contributions={contributions} selectedDate={selectedDate} selectedFactor={selectedFactor} filteredPicks={filteredPicks} />
              <TopPredictionsTab activeTab={activeTab} industries={industries} selectedIndustry={selectedIndustry} setSelectedIndustry={setSelectedIndustry} zScores={zScores} />
              <All64Tab activeTab={activeTab} all64Filtered={all64Filtered} selectedFactor={selectedFactor} industries={industries} />
              <PerformanceTab activeTab={activeTab} currentIndustry={currentIndustry} pastPicks={pastPicks} pastPicksAvg={pastPicksAvg} />
              <MarketTab activeTab={activeTab} currentRegime={currentRegime} />
            </main>
            <FactorPanel selectedDate={selectedDate} selectedFactor={selectedFactor} setSelectedFactor={setSelectedFactor} contributions={contributions} />
          </div>
        </div>
      </div>
      <HistoryModal open={showHistory} onClose={() => setShowHistory(false)} history={history} selectedDate={selectedDate} onSelect={loadSnapshot} />
      <DisclaimerModal open={showDisclaimer} onClose={() => setShowDisclaimer(false)} />
      <HelpModal open={showHelp} onClose={() => setShowHelp(false)} />
    </div>
  );
}

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(<App />);
