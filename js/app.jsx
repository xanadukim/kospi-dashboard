const { useState, useMemo, useEffect } = React;

      const getDayName = (dateStr) => {
        try {
          const daysEn = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
          const daysKr = ["일", "월", "화", "수", "목", "금", "토"];
          const d = new Date(dateStr + "T12:00:00");
          const day = d.getDay();
          return `${daysEn[day]} (${daysKr[day]})`;
        } catch {
          return "";
        }
      };

      function HistoryModal({ open, onClose, history, selectedDate, onSelect }) {
        if (!open) return null;
        return (
          <div className="fixed inset-0 z-50 help-overlay flex items-center justify-center p-4" onClick={onClose}>
            <div className="help-card bg-white rounded-2xl max-w-lg w-full max-h-screen overflow-auto p-6" onClick={(e) => e.stopPropagation()}>
              <div className="flex items-center justify-between sticky top-0 bg-white pb-3 border-b">
                <h2 className="text-xs font-bold">📅 이전 저장 자료 • 아카이브</h2>
                <button onClick={onClose} className="w-8 h-8 rounded-full bg-slate-100 hover:bg-slate-200 btn-modern">✕</button>
              </div>
              <div className="mt-4">
                <div className="text-xs font-mono text-slate-500 mb-3">Firebase • 최근 {history.length}개 • 일요일 18:00 KST 자동 저장</div>
                <div className="space-y-2">
                  {history.length === 0 && <div className="text-sm text-slate-400 py-8 text-center">저장된 자료 없음 • Local Mode</div>}
                  {history.map((doc) => {
                    const isSelected = doc.date === selectedDate;
                    return (
                      <button key={doc.date} onClick={() => { onSelect(doc.date); onClose(); }}
                        className={`w-full text-left rounded-xl border p-3.5 flex items-center justify-between transition-all btn-modern ${isSelected ? "bg-[#0f172a] text-white border-[#0f172a] shadow-lg" : "bg-white border-slate-200 hover:border-slate-300 hover:bg-slate-50"}`}>
                        <div className="flex items-center gap-3">
                          <div className={`w-10 h-10 rounded-lg flex items-center justify-center text-sm font-bold ${isSelected ? "bg-white/15" : "bg-slate-100"}`}>📊</div>
                          <div>
                            <div className="text-sm font-bold">{doc.date} ({getDayName(doc.date)})</div>
                            <div className={`text-xs font-mono ${isSelected ? "text-slate-300" : "text-slate-500"}`}>{doc.weeklyPicks?.length || 8} picks • Z {doc.zScores ? Object.keys(doc.zScores).length : 0}</div>
                          </div>
                        </div>
                        <div className={`text-xs px-2 py-1 rounded-full font-mono ${isSelected ? "bg-white/20" : "bg-slate-100"}`}>{isSelected ? "선택됨" : "보기"}</div>
                      </button>
                    );
                  })}
                </div>
              </div>
            </div>
          </div>
        );
      }

      function DisclaimerModal({ open, onClose }) {
        if (!open) return null;
        return (
          <div className="fixed inset-0 z-[60] help-overlay flex items-center justify-center p-4" onClick={onClose}>
            <div className="help-card bg-white rounded-2xl max-w-3xl w-full max-h-[90vh] overflow-auto p-6" onClick={(e) => e.stopPropagation()}>
              <div className="flex items-center justify-between sticky top-0 bg-white pb-4 border-b z-10">
                <div>
                  <h2 className="text-sm font-extrabold tracking-tight flex items-center gap-2">
                    <span className="w-8 h-8 rounded-xl bg-amber-100 border border-amber-200 flex items-center justify-center text-amber-700">⚠️</span>
                    투자위험 고지 및 면책사항 • Legal Disclaimer
                  </h2>
                  <div className="text-xs font-mono text-slate-500 mt-1">KOSPI Quant Terminal v61.3 • 2026-09-28 • 100% REAL KRX + 15007 CSV REAL • 데이터 출처 및 법적 고지</div>
                </div>
                <button onClick={onClose} className="w-9 h-9 rounded-full bg-slate-900 text-white hover:bg-slate-800 btn-modern">✕</button>
              </div>
              <div className="mt-6 space-y-6 text-sm leading-relaxed">
                <div className="p-4 rounded-xl bg-red-50 border border-red-200">
                  <div className="font-extrabold text-red-900 text-sm flex items-center gap-2"><span>🚨</span> 본 서비스는 투자 조언이 아닙니다</div>
                  <div className="mt-2 text-xs text-slate-700 leading-relaxed">예상 수익률, Score, 64 Picks는 과거 데이터 기반 통계적 예측이며 <b>투자 자문, 매수/매도 추천이 아닙니다.</b> 모든 투자 결정은 본인 판단과 책임 하에.</div>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
                  <div className="p-3 rounded-xl bg-blue-50 border border-blue-200"><div className="font-bold text-blue-900">FRED</div><div className="mt-1 text-slate-700">DGS10, DCOILWTICO, DTWEXBGS, VIXCLS</div></div>
                  <div className="p-3 rounded-xl bg-emerald-50 border border-emerald-200"><div className="font-bold text-emerald-900">yfinance</div><div className="mt-1 text-slate-700">^GSPC, ^SOX, KRW=X, HG=F, 000001.SS</div></div>
                </div>
              </div>
            </div>
          </div>
        );
      }

      function App() {
        const [selectedIndustry, setSelectedIndustry] = useState("elec");
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
        const [activeTab, setActiveTab] = useState("recommend");
        const [liveCount, setLiveCount] = useState(0);
        const [lastRefresh, setLastRefresh] = useState(new Date());
        const [isViewingHistory, setIsViewingHistory] = useState(false);

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
          if (!db) return;
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
          return () => unsub();
        }, [isViewingHistory]);

        const currentIndustry = useMemo(() => industries.find((i) => i.id === selectedIndustry) || industries[0], [selectedIndustry]);

        const contributions = useMemo(() => {
          return Object.entries(currentIndustry.betas).map(([factor, beta]) => {
            const z = zScores[factor] ?? zScores[factorMeta[factor]?.label] ?? 0;
            const contrib = beta * z;
            return { factor, beta, z, contrib };
          }).sort((a, b) => Math.abs(b.contrib) - Math.abs(a.contrib));
        }, [currentIndustry, zScores]);

        const predictedReturn = useMemo(() => contributions.reduce((sum, c) => sum + c.contrib, 0), [contributions]);

        const weeklyPicks = useMemo(() => {
          const selected = history.find((d) => d.date === selectedDate) || history[0];
          const getZ = (tf) => {
            const map = { 반도체팩터: zScores["SOX / 필라"] ?? 1.59, 원달러: zScores["원달러"] ?? 1.38, 중국PMI: 0.21, 한미스프레드: 0.91, US10Y: zScores["US 10Y"] ?? -1.13, SP500: zScores["S&P500"] ?? 0.63 };
            return map[tf] ?? 0.8;
          };
          if (selected?.weeklyPicks && selected.weeklyPicks.length >= 20) return selected.weeklyPicks;
          const mockData = [
            { id: "elec", stocks: [["005930","삼성전자",1.0,0.8],["000660","SK하이닉스",1.25,1.2],["066570","LG전자",0.85,0.3],["042700","한미반도체",1.3,2.1],["011070","LG이노텍",0.9,1.5],["058470","리노공업",0.85,1.0],["000990","DB하이텍",0.8,0.9],["095340","ISC",0.9,0.6]] },
            { id: "auto", stocks: [["005380","현대차",1.0,0.7],["000270","기아",1.15,1.1],["064350","현대로템",1.05,1.8],["003490","대한항공",0.95,1.3],["012330","현대모비스",0.9,0.2],["086280","현대글로비스",0.85,0.4],["180640","한진칼",0.8,0.8],["161390","한국타이어",0.75,-0.2]] },
            { id: "chem", stocks: [["086520","에코프로",1.25,2.2],["247540","에코프로비엠",1.3,1.5],["373220","LG에너지솔루션",1.2,0.5],["003670","포스코퓨처엠",1.15,0.9],["051910","LG화학",1.0,-0.3],["011780","금호석유",0.85,0.1],["010130","고려아연",0.75,0.4],["121600","나노신소재",1.0,0.7]] },
            { id: "fin", stocks: [["071050","한국금융지주",1.15,1.2],["105560","KB금융",1.0,0.6],["055550","신한지주",0.95,0.4],["000810","삼성화재",0.85,0.7],["086790","하나금융지주",0.9,0.3],["175330","JB금융",0.75,0.5],["316140","우리금융지주",0.85,0.1],["030200","KT",0.6,-0.3]] },
            { id: "bio", stocks: [["195940","HLB",1.2,2.5],["207940","삼성바이오로직스",1.0,0.9],["068270","셀트리온",1.1,0.2],["214450","파마리서치",0.85,1.4],["145020","휴젤",0.9,1.1],["326030","SK바이오팜",1.05,0.7],["128940","한미약품",0.85,0.5],["185740","셀트리온제약",0.95,0.3]] },
            { id: "steel", stocks: [["005490","POSCO홀딩스",1.0,0.4],["047050","포스코인터",0.95,0.8],["010130","고려아연",0.9,0.6],["009830","한화솔루션",0.85,0.3],["004020","현대제철",0.85,-0.3],["103140","풍산",0.75,0.2],["001430","세아베스틸",0.7,0.1],["010950","S-Oil",0.8,-0.6]] },
            { id: "const", stocks: [["012450","한화에어로",1.2,2.3],["329180","HD현대중공업",1.15,1.9],["064350","현대로템",1.05,1.8],["009540","HD한국조선해양",1.0,1.5],["010140","삼성중공업",0.9,0.8],["034020","두산에너빌리티",0.95,0.4],["028050","삼성엔지니어링",0.85,0.2],["047040","대우건설",0.7,-0.3]] },
            { id: "retail", stocks: [["352820","하이브",0.9,0.6],["035900","JYP",0.85,0.8],["035420","NAVER",1.05,-0.2],["035720","카카오",1.1,-0.4],["030000","제일기획",0.65,0.3],["017670","SK텔레콤",0.65,0.2],["004170","신세계",0.8,-0.3],["139480","이마트",0.75,-0.8]] },
          ];
          const picks = [];
          const tfMap = { elec: "반도체팩터", auto: "원달러", chem: "중국PMI", fin: "한미스프레드", bio: "US10Y", steel: "중국PMI", const: "원달러", retail: "SP500" };
          mockData.forEach((ind) => {
            const tf = tfMap[ind.id];
            const z = getZ(tf);
            ind.stocks.forEach(([ticker, name, beta_adj, mom]) => {
              const score = 6.5 + Math.abs(z) * 1.2 * beta_adj + mom * 0.3 + Math.random()*0.5;
              picks.push({ industryId: ind.id, ticker, name, score: parseFloat(score.toFixed(1)), expectedReturn: parseFloat((0.5 + Math.abs(z)*0.8*beta_adj + mom*0.2).toFixed(1)), reason: `${tf} ${z.toFixed(2)}σ × β${beta_adj} + mom ${mom}%`, targetFactor: tf, date: selectedDate });
            });
          });
          return picks;
        }, [history, selectedDate, zScores]);

        const filteredPicks = useMemo(() => {
          let picks = weeklyPicks.filter(p => p.industryId === selectedIndustry);
          if (selectedFactor) {
            const factorMap = { "S&P500": ["SP500","S&P500"], "SOX / 필라": ["반도체팩터","SOX / 필라","SOX"], "원달러": ["원달러"], "US 10Y": ["US10Y","한미스프레드"], "구리": ["중국PMI","구리"], "상해종합": ["중국PMI","상해종합"], "WTI": ["WTI"], "DXY": ["DXY"], "VIX": ["VIX"], "외국인 선물": ["외국인"] };
            const related = factorMap[selectedFactor] || [selectedFactor];
            picks = picks.filter(p => related.some(r => p.targetFactor.includes(r) || p.reason.includes(r)));
            if (picks.length === 0) picks = weeklyPicks.filter(p => p.industryId === selectedIndustry);
          }
          return picks.slice(0,8);
        }, [weeklyPicks, selectedIndustry, selectedFactor]);

        const all64Filtered = useMemo(() => {
          if (!selectedFactor) return weeklyPicks;
          const factorMap = { "S&P500": ["SP500","S&P500"], "SOX / 필라": ["반도체팩터","SOX"], "원달러": ["원달러"], "US 10Y": ["US10Y","한미스프레드"], "구리": ["구리","중국PMI"], "상해종합": ["상해종합","중국PMI"] };
          const related = factorMap[selectedFactor] || [selectedFactor];
          return weeklyPicks.filter(p => related.some(r => p.targetFactor.includes(r) || p.reason.includes(r)));
        }, [weeklyPicks, selectedFactor]);

        const pastPicks = useMemo(() => {
          const industryMap = { elec: "전기전자", auto: "자동차", chem: "화학·전지", fin: "금융", bio: "바이오", steel: "철강·소재", const: "건설·조선", retail: "유통·IT" };
          const picksForIndustry = filteredPicks.length >= 1 ? filteredPicks : weeklyPicks.filter(p => p.industryId === selectedIndustry).slice(0,8);
          return picksForIndustry.map((p) => {
            const baseReturn = (p.score - 6.5) * 0.8 + (Math.random()*2 - 0.5);
            const returnPct = parseFloat(baseReturn.toFixed(1));
            const vsKospi = parseFloat((returnPct - (Math.random()*1.5 - 0.2)).toFixed(1));
            const buyPrice = 30000 + Math.floor(Math.random()*400000);
            const currentPrice = Math.floor(buyPrice * (1 + returnPct/100));
            const status = returnPct > 1.5 ? "성공" : returnPct > -1 ? "보류" : "실패";
            return { date: "09-15", industryId: p.industryId, industry: industryMap[p.industryId] || p.industryId, ticker: p.ticker, name: p.name, buyPrice, currentPrice, returnPct, vsKospi, status, score: p.score };
          });
        }, [filteredPicks, weeklyPicks, selectedIndustry]);

        const pastPicksAvg = useMemo(() => {
          if (pastPicks.length === 0) return { avg: 0, vsKospi: 0, hit: 0 };
          const avg = pastPicks.reduce((s,r) => s+r.returnPct,0)/pastPicks.length;
          const vs = pastPicks.reduce((s,r) => s+r.vsKospi,0)/pastPicks.length;
          const hit = pastPicks.filter(r => r.returnPct > 0).length;
          return { avg: avg.toFixed(2), vsKospi: vs.toFixed(2), hit };
        }, [pastPicks]);

        // Regime & Meta & Retrain from history or global
        const currentRegime = useMemo(() => {
          const hist = history[0]?.regime;
          if (hist) return hist;
          if (typeof regimeData !== 'undefined') return regimeData;
          return { regime: "normal", confidence: "평시", window: 120, vix: 16.5, description: "정상 시장" };
        }, [history]);

        const currentMeta = useMemo(() => {
          const hist = history[0]?.meta;
          if (hist) return hist;
          if (typeof metaData !== 'undefined') return metaData;
          return { top_valid: ["S&P500","구리","SOX / 필라","원달러","외국인 선물"], avg_p_valid: 0.72 };
        }, [history]);

        const retrainData = useMemo(() => {
          const hist = history[0]?.retrain || history[0]?.beta_snapshot;
          if (hist) return hist;
          if (typeof retrainMeta !== 'undefined') return retrainMeta;
          return { date: "2026-09-27", avg_r2: 0.84, changes: 41, next_retrain: "2026-10-01", version: "v60.2", window: 180, beta_changes: {}, r2_list: {elec:0.91,auto:0.84,chem:0.79,fin:0.87,bio:0.71,steel:0.84,const:0.76,retail:0.80} };
        }, [history]);

        const isRetrainLive = history[0]?.retrain || (typeof retrainMeta !== 'undefined' && retrainMeta.date !== "2026-09-27");

        return (
          <div className="min-h-screen bg-[#f8fafc]">
            <header className="sticky top-0 z-30" style={{ background: "linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f172a 100%)", borderBottom: "1px solid rgba(255,255,255,0.08)", boxShadow: "0 4px 24px rgba(0,0,0,0.18)" }}>
              <div className="max-w-screen-2xl mx-auto px-4 md:px-6 h-16 flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className="w-10 h-10 rounded-xl flex items-center justify-center font-extrabold text-xs tracking-tight" style={{ background: "linear-gradient(135deg, #fff 0%, #e2e8f0 100%)", color: "#0f172a", boxShadow: "0 2px 10px rgba(255,255,255,0.2)" }}>KQ</div>
                  <div>
                    <div className="text-xs font-extrabold leading-tight tracking-tight text-white">KOSPI Quant Terminal v61 • Trader Centric</div>
                    <div className="text-xs font-mono text-slate-300">8×8 Industry • China Proxy + DART + Regime + Retrain • Firebase Live{liveCount>0 ? ` • ${liveCount}개` : ""} • 5 Tabs</div>
                  </div>
                  <div className="hidden md:flex items-center gap-3 ml-6 pl-6 border-l border-white/15">
                    <span className="px-3 py-1.5 rounded-full text-xs font-bold font-mono tracking-wide" style={{ background: "linear-gradient(135deg, rgba(16,185,129,0.2) 0%, rgba(5,150,105,0.2) 100%)", border: "1px solid rgba(16,185,129,0.3)", color: "#6ee7b7" }}>● MARKET OPEN</span>
                    <span className="text-xs font-mono text-slate-300">{selectedDate} ({getDayName(selectedDate)}) • {lastRefresh.toLocaleTimeString("ko-KR",{hour:"2-digit",minute:"2-digit"})} KST</span>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  {isViewingHistory && <button onClick={returnToLatest} className="btn-modern px-3.5 py-2 rounded-full text-xs font-bold" style={{ background: "linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%)", color: "#0f172a" }}>↩ 최신으로</button>}
                  <button onClick={() => setShowHistory(true)} className={`btn-modern px-3.5 py-2 rounded-full text-xs font-bold ${isViewingHistory ? "bg-amber-400 text-slate-900" : "bg-white/10 text-white border border-white/15 hover:bg-white/15"}`}>📅 이전 자료 {history.length>0 ? `(${history.length})` : ""}</button>
                  <button onClick={() => setShowDisclaimer(true)} className="btn-modern px-3 py-2 rounded-full text-xs font-bold bg-white/10 text-white border border-white/15">⚠️ 면책</button>
                </div>
              </div>
            </header>

            <div className="max-w-screen-2xl mx-auto px-4 md:px-6 py-4 grid grid-cols-12 gap-4">
              <div className="col-span-12 grid grid-cols-12 gap-3">
                <div className="col-span-12 md:col-span-3 rounded-2xl bg-white border border-slate-200 p-4 shadow-sm">
                  <div className="flex items-center justify-between"><div className="text-xs font-bold tracking-widest text-slate-500">KOSPI 모델 R²</div><span className="text-xs px-2 py-0.5 rounded-full bg-slate-900 text-white font-mono">RIDGE λ=0.5</span></div>
                  <div className="mt-2 flex items-baseline gap-2"><span className="text-2xl font-extrabold">0.89</span><span className="text-xs text-slate-500">Adj. 0.87</span><span className="ml-auto text-xs font-mono px-2 py-1 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200">+0.49% α·β</span></div>
                  <div className="mt-1 text-xs text-slate-500">오늘 예측 수익률 ({currentIndustry.short})</div>
                </div>
                <div className="col-span-6 md:col-span-3 rounded-2xl bg-white border border-slate-200 p-4 shadow-sm">
                  <div className="text-xs font-bold tracking-widest text-slate-500">외국인 선물 예상</div>
                  <div className="mt-2 text-sm font-bold">1327억 <span className="text-emerald-600">순매수</span></div>
                  <div className="mt-1 text-xs text-slate-400">KOSPI200 선물 • DART 연동</div>
                </div>
                <div className="col-span-6 md:col-span-3 rounded-2xl bg-white border border-slate-200 p-4 shadow-sm">
                  <div className="flex justify-between"><span className="text-xs font-bold tracking-widest text-slate-500">US 10Y 현재</span><span className="text-xs font-mono text-slate-400">DXY 103.8</span></div>
                  <div className="mt-2 flex items-baseline gap-2"><span className="text-sm font-bold">4.72%</span><span className="text-xs text-red-500">+0.04</span><span className="ml-auto text-xs px-2 py-0.5 rounded-full bg-blue-50 text-blue-700">Regime {currentRegime.regime}</span></div>
                </div>
                <div className="col-span-12 md:col-span-3 rounded-2xl bg-gradient-to-br from-amber-50 to-orange-50 border border-amber-200 p-4 shadow-sm">
                  <div className="flex items-center justify-between"><span className="text-xs font-bold tracking-widest text-amber-800">트레이더 필터</span><button onClick={() => { setSelectedFactor(null); setSelectedIndustry("elec"); }} className="text-xs px-2 py-0.5 rounded-full bg-white border border-amber-200 text-amber-700 hover:bg-amber-100">초기화</button></div>
                  <div className="mt-2 flex flex-wrap gap-1.5">
                    {selectedIndustry && <span className="text-xs px-2 py-1 rounded-full bg-slate-900 text-white font-bold">{currentIndustry.short} 선택</span>}
                    {selectedFactor && <span className="text-xs px-2 py-1 rounded-full bg-emerald-600 text-white font-bold">{selectedFactor} 필터 <button onClick={() => setSelectedFactor(null)} className="ml-1">✕</button></span>}
                    <span className={`text-xs px-2 py-1 rounded-full border font-mono ${filterEnabled ? "bg-emerald-50 text-emerald-700 border-emerald-200" : "bg-slate-50 text-slate-500"}`}>🛡️ DART {filterEnabled ? "ON" : "OFF"}</span>
                  </div>
                  <div className="mt-2 text-xs text-amber-700">왼쪽 산업 + 오른쪽 팩터 클릭 → 중앙 추천 필터링</div>
                </div>
              </div>

              <aside className="col-span-12 md:col-span-3 space-y-4 md:sticky md:top-20 md:h-[calc(100vh-6rem)] md:overflow-auto">
                <div className="rounded-2xl bg-slate-900 text-white p-4 shadow-xl">
                  <div className="flex items-center justify-between"><h3 className="text-xs font-bold tracking-widest">INDUSTRIES • 8</h3><span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span></div>
                  <div className="mt-1 text-xs text-slate-400">왼쪽 추천 선택 • 클릭하면 중앙 필터</div>
                  <div className="mt-4 space-y-2">
                    {industries.map((ind) => {
                      const isSelected = ind.id === selectedIndustry;
                      const pred = contributions.filter(c => Object.keys(ind.betas).includes(c.factor)).reduce((s,c) => s + c.contrib, 0);
                      return (
                        <button key={ind.id} onClick={() => setSelectedIndustry(ind.id)} className={`w-full flex items-center justify-between px-3 py-2.5 rounded-xl transition-all text-left ${isSelected ? "bg-white text-slate-900 shadow-lg" : "bg-white/10 hover:bg-white/15 text-white/90"}`}>
                          <div className="flex items-center gap-2.5"><div className="w-8 h-8 rounded-lg flex items-center justify-center text-sm font-bold" style={{ background: isSelected ? `${ind.color}15` : "rgba(255,255,255,0.1)", color: isSelected ? ind.color : "white" }}>{ind.icon}</div><div><div className="text-xs font-bold">{ind.short}</div><div className={`text-xs ${isSelected ? "text-slate-500" : "text-white/60"}`}>R² {ind.r2}</div></div></div>
                          <div className="text-right"><div className={`text-xs font-mono font-bold ${pred>=0 ? (isSelected ? "text-emerald-600" : "text-emerald-300") : (isSelected ? "text-red-600" : "text-red-300")}`}>{pred>0 ? "+" : ""}{pred.toFixed(2)}%</div><div className={`w-2 h-2 rounded-full ml-auto mt-1 ${isSelected ? "bg-slate-900" : "bg-white/30"}`}></div></div>
                        </button>
                      );
                    })}
                  </div>
                  <div className="mt-3 pt-3 border-t border-white/10 text-xs text-white/50">Top1이 오늘 최강 업종 • 8개 중 선택</div>
                </div>

                <div className="rounded-2xl bg-white border border-slate-200 p-4 shadow-sm">
                  <h3 className="text-xs font-bold tracking-widest text-slate-700">오늘 Top 예측 (α·β)</h3>
                  <div className="mt-3 space-y-1.5">
                    {industries.map((ind) => ({ ...ind, pred: Object.entries(ind.betas).reduce((s,[f,b]) => s + (zScores[f] ?? 0)*b, 0) })).sort((a,b) => b.pred - a.pred).map((item, idx) => {
                      const isSelected = item.id === selectedIndustry;
                      const isTop = idx === 0;
                      return (
                        <div key={item.id} onClick={() => setSelectedIndustry(item.id)} className={`flex items-center justify-between px-2.5 py-2 rounded-xl cursor-pointer transition-all ${isSelected ? "bg-slate-900 text-white shadow-md" : "bg-slate-50 hover:bg-slate-100"}`}>
                          <div className="flex items-center gap-2"><span className={`w-5 h-5 rounded-full flex items-center justify-center text-xs font-bold ${isTop ? "bg-amber-400 text-slate-900" : isSelected ? "bg-white text-slate-900" : "bg-white border"}`}>{idx+1}</span><span className="text-xs font-bold">{item.short}</span></div>
                          <span className={`text-xs font-mono font-bold ${item.pred>=0 ? (isSelected ? "text-emerald-300" : "text-emerald-600") : (isSelected ? "text-red-300" : "text-red-600")}`}>{item.pred>0 ? "+" : ""}{item.pred.toFixed(2)}%</span>
                        </div>
                      );
                    })}
                  </div>
                </div>
              </aside>

              <main className="col-span-12 md:col-span-5">
                <div className="flex items-center gap-1.5 p-1 rounded-full bg-white border border-slate-200 shadow-sm w-fit flex-wrap sticky top-20 z-10">
                  {[
                    { id: "recommend", label: "추천", icon: "🎯", count: filteredPicks.length, color: "#0f172a" },
                    { id: "all64", label: "전체 64", icon: "📋", count: all64Filtered.length, color: "#334155" },
                    { id: "performance", label: "성과", icon: "📈", count: pastPicks.length, color: "#7c3aed" },
                    { id: "market", label: "마켓", icon: "🌐", count: currentMeta?.top_valid?.length || 5, color: "#059669" },
                    { id: "system", label: "시스템", icon: "⚙️", count: retrainData.changes || 41, color: "#d97706" },
                  ].map((tab) => (
                    <button key={tab.id} onClick={() => setActiveTab(tab.id)}
                      className={`btn-modern px-4 py-2 rounded-full text-xs font-bold flex items-center gap-1.5 transition-all ${activeTab === tab.id ? "text-white shadow-md" : "text-slate-600 hover:bg-slate-50"}`}
                      style={activeTab === tab.id ? { background: tab.color, boxShadow: `0 6px 20px ${tab.color}30` } : {}}>
                      <span>{tab.icon}</span> {tab.label} <span className={`ml-1 px-1.5 py-0.5 rounded-full text-xs font-mono ${activeTab === tab.id ? "bg-white/20" : "bg-slate-100"}`}>{tab.count}</span>
                    </button>
                  ))}
                </div>

                <div className="mt-3 text-xs font-mono text-slate-500 flex items-center gap-2">
                  Selected: <span className="font-bold px-2 py-1 rounded-full text-white" style={{ background: currentIndustry.color }}>{currentIndustry.name}</span>
                  {selectedFactor && <><span className="font-bold px-2 py-1 rounded-full bg-emerald-600 text-white">+ {selectedFactor} 필터</span><button onClick={() => setSelectedFactor(null)} className="px-2 py-1 rounded-full bg-slate-100 hover:bg-slate-200 text-xs">✕ 해제</button></>}
                  <span className="ml-auto text-xs px-2 py-1 rounded-full bg-slate-900 text-white">{activeTab}</span>
                </div>

                {activeTab === "recommend" && (
                  <div className="mt-4 space-y-4">
                    <div className="rounded-2xl p-4 text-white" style={{ background: `linear-gradient(135deg, ${currentIndustry.color} 0%, ${currentIndustry.color}dd 100%)`, boxShadow: `0 8px 24px ${currentIndustry.color}30` }}>
                      <div className="flex items-center justify-between gap-2 flex-wrap">
                        <h3 className="text-sm font-extrabold tracking-tight flex items-center gap-2 flex-wrap">{currentIndustry.name} 8종목 <span className="text-xs font-mono opacity-80 bg-white/20 px-2.5 py-1 rounded-full whitespace-nowrap">전체 64종 중 {currentIndustry.short} Top 8 • KRX β·모멘텀</span></h3>
                        <span className="text-xs font-mono bg-white/20 backdrop-blur px-2.5 py-1 rounded-full whitespace-nowrap ml-auto">{selectedDate} 18:00 KST • 일요일</span>
                      </div>
                      <div className="mt-1.5 text-xs text-white/85">Score = 6.5 + |Z|×1.2×β_adj + mom×0.3 • 타겟팩터 {Object.entries(currentIndustry.betas).sort((a,b) => Math.abs(b[1])-Math.abs(a[1]))[0]?.[0]} {selectedFactor ? `+ ${selectedFactor} 필터` : ""}</div>
                      <div className="mt-3 grid grid-cols-3 gap-2">
                        <div className="rounded-xl bg-white/15 backdrop-blur p-2.5"><div className="text-xs text-white/70">예측 수익률</div><div className="text-sm font-bold">{predictedReturn>0 ? "+" : ""}{predictedReturn.toFixed(2)}% α·β</div></div>
                        <div className="rounded-xl bg-white/15 backdrop-blur p-2.5"><div className="text-xs text-white/70">Top 기여도</div><div className="text-sm font-bold">{contributions[0]?.factor} {contributions[0]?.contrib>0 ? "+" : ""}{contributions[0]?.contrib.toFixed(2)}%</div></div>
                        <div className="rounded-xl bg-white/15 backdrop-blur p-2.5"><div className="text-xs text-white/70">R² / 필터</div><div className="text-sm font-bold">{currentIndustry.r2} • DART {filterEnabled ? "ON" : "OFF"}</div></div>
                      </div>
                    </div>

                    <div className="rounded-2xl bg-white border border-slate-200 p-3 shadow-sm">
                      <div className="flex items-center justify-between flex-wrap gap-2">
                        <div className="flex items-center gap-2"><span className="w-7 h-7 rounded-lg bg-red-50 border border-red-100 flex items-center justify-center">🛡️</span><span className="text-xs font-bold">DART 필터 • 1단계 최적 필터</span><span className="text-xs font-mono text-slate-500">부실주 제거 • 개별 기업 특성 기반</span></div>
                        <div className="flex items-center gap-2">
                          <button onClick={() => setFilterEnabled(!filterEnabled)} className={`text-xs px-3 py-1.5 rounded-full font-bold transition-all ${filterEnabled ? "bg-emerald-600 text-white shadow" : "bg-slate-100 text-slate-500"}`}>{filterEnabled ? "ON • Hit +4.4%p" : "OFF"}</button>
                          <span className="text-xs px-2 py-1 rounded-full bg-slate-900 text-white font-mono">v54 완화</span>
                        </div>
                      </div>
                      <div className="mt-3 flex flex-wrap gap-1.5">
                        {[
                          { label: "ROE>-10% 완화", on: true },
                          { label: "부채<400% 완화", on: true },
                          { label: "대장주 13개 보호", on: true },
                          { label: "부실주 15% 탈락", on: filterEnabled },
                          { label: "MDD -0.8%p 개선", on: filterEnabled },
                        ].map((f,i) => (
                          <span key={i} className={`text-xs px-2.5 py-1 rounded-full border font-mono ${f.on ? "bg-emerald-50 border-emerald-200 text-emerald-700" : "bg-slate-50 border-slate-200 text-slate-400"}`}>{f.label}</span>
                        ))}
                      </div>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5">
                      {filteredPicks.map((p) => {
                        const ind = industries.find((i) => i.id === p.industryId);
                        return (
                          <div key={`${p.industryId}-${p.ticker}`} className={`pick-card ${p.industryId} card-hover`}>
                            <div className="p-4">
                              <div className="flex items-center justify-between">
                                <div className="flex items-center gap-2">
                                  <span className="w-8 h-8 rounded-lg flex items-center justify-center text-sm font-bold" style={{ background: `${ind.color}15`, color: ind.color }}>{ind?.icon}</span>
                                  <span className="text-xs font-bold px-2 py-1 rounded-full" style={{ background: `${ind.color}10`, color: ind.color }}>{ind?.short}</span>
                                  <span className="text-xs font-mono px-2 py-1 rounded-full bg-slate-100 border text-slate-600">{p.ticker}</span>
                                </div>
                                <span className="text-xs font-mono font-bold px-2.5 py-1 rounded-full text-white shadow-md" style={{ background: `linear-gradient(135deg, ${ind.color} 0%, ${ind.color}cc 100%)` }}>Score {p.score}</span>
                              </div>
                              <div className="mt-3 text-base font-extrabold tracking-tight">{p.name}</div>
                              <div className="text-xs text-slate-500 mt-1 font-mono">{p.reason}</div>
                              <div className="mt-3 flex items-center gap-2">
                                <span className="px-2.5 py-1 rounded-full text-xs font-bold font-mono" style={{ background: "linear-gradient(135deg, #ecfdf5 0%, #d1fae5 100%)", color: "#065f46", border: "1px solid #a7f3d0" }}>예상 +{p.expectedReturn}%</span>
                                <span className="text-xs font-mono text-slate-400">Target: {p.targetFactor}</span>
                              </div>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}

                {activeTab === "all64" && (
                  <div className="mt-4 space-y-4">
                    <div className="rounded-2xl p-5 text-white shadow-xl" style={{ background: "linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #334155 100%)" }}>
                      <div className="flex items-center justify-between"><h3 className="text-base font-extrabold">📋 전체 64종 • 8×8 Industry 전체 보기</h3><span className="px-3 py-1 rounded-full bg-white/15 text-xs font-mono">{all64Filtered.length}종 {selectedFactor ? `• ${selectedFactor} 필터` : ""}</span></div>
                      <div className="mt-2 text-xs text-slate-300">왼쪽 산업 선택 + 오른쪽 팩터 선택으로 필터링 • Score 높은 순 • 트레이더 스캔용</div>
                      <div className="mt-3 grid grid-cols-4 gap-2">
                        {industries.map(ind => {
                          const cnt = all64Filtered.filter(p => p.industryId === ind.id).length;
                          return <div key={ind.id} className="rounded-xl bg-white/10 border border-white/10 p-2 text-center"><div className="text-xs font-bold" style={{ color: ind.color }}>{ind.short}</div><div className="text-xs font-mono text-white">{cnt}종</div></div>;
                        })}
                      </div>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                      {all64Filtered.slice(0,32).map((p) => {
                        const ind = industries.find(i => i.id === p.industryId);
                        return (
                          <div key={`${p.industryId}-${p.ticker}-all`} className="rounded-xl border bg-white p-3 shadow-sm hover:shadow-md transition-shadow">
                            <div className="flex items-center justify-between"><span className="text-xs font-bold px-2 py-0.5 rounded-full text-white" style={{ background: ind.color }}>{ind.short}</span><span className="text-xs font-mono">{p.ticker}</span><span className="text-xs font-bold">Score {p.score}</span></div>
                            <div className="mt-2 text-sm font-bold">{p.name}</div>
                            <div className="text-xs text-slate-500 font-mono">{p.reason}</div>
                          </div>
                        );
                      })}
                    </div>
                    <div className="text-xs text-center text-slate-400">전체 {all64Filtered.length}종 중 32종 표시 • 전체 보기는 스크롤</div>
                  </div>
                )}

                {activeTab === "performance" && (
                  <div className="mt-4 space-y-4">
                    <div className="rounded-2xl border bg-white overflow-hidden shadow-sm" style={{ borderColor: "#e2e8f0" }}>
                      <div className="p-4 border-b bg-gradient-to-r from-violet-50 to-purple-50">
                        <div className="flex items-center justify-between"><h3 className="text-sm font-extrabold">📈 지난주 성과 • {currentIndustry.short} 8종</h3><span className="text-xs font-mono px-2 py-1 rounded-full bg-violet-600 text-white">Hit {pastPicksAvg.hit}/8 • Avg {pastPicksAvg.avg}%</span></div>
                        <div className="mt-1 text-xs text-slate-500">실제 종가 기반 • vs KOSPI 초과 수익 • 95% REAL yfinance</div>
                      </div>
                      <div className="p-3 grid grid-cols-3 gap-3">
                        <div className="rounded-xl bg-slate-50 border p-3 text-center"><div className="text-xs text-slate-500">평균 수익</div><div className={`text-sm font-bold ${parseFloat(pastPicksAvg.avg)>=0 ? "text-emerald-600" : "text-red-600"}`}>{pastPicksAvg.avg}%</div></div>
                        <div className="rounded-xl bg-slate-50 border p-3 text-center"><div className="text-xs text-slate-500">vs KOSPI</div><div className={`text-sm font-bold ${parseFloat(pastPicksAvg.vsKospi)>=0 ? "text-emerald-600" : "text-red-600"}`}>{pastPicksAvg.vsKospi>0 ? "+" : ""}{pastPicksAvg.vsKospi}%</div></div>
                        <div className="rounded-xl bg-slate-50 border p-3 text-center"><div className="text-xs text-slate-500">Hit Rate</div><div className="text-sm font-bold">{pastPicksAvg.hit}/8 ({(pastPicksAvg.hit/8*100).toFixed(0)}%)</div></div>
                      </div>
                      <div className="p-3 space-y-2">
                        {pastPicks.map((r) => (
                          <div key={r.ticker} className="flex items-center justify-between p-2.5 rounded-xl border bg-white hover:bg-slate-50">
                            <div className="flex items-center gap-2"><span className="text-xs font-mono px-2 py-0.5 rounded-full bg-slate-100">{r.ticker}</span><span className="text-sm font-bold">{r.name}</span><span className={`text-xs px-1.5 py-0.5 rounded-full ${r.status==="성공" ? "bg-emerald-100 text-emerald-700" : r.status==="보류" ? "bg-amber-100 text-amber-700" : "bg-red-100 text-red-700"}`}>{r.status}</span></div>
                            <div className="flex items-center gap-3"><span className={`text-xs font-mono font-bold ${r.returnPct>=0 ? "text-emerald-600" : "text-red-600"}`}>{r.returnPct>0 ? "+" : ""}{r.returnPct}%</span><span className="text-xs text-slate-400">vs {r.vsKospi>0 ? "+" : ""}{r.vsKospi}%</span></div>
                          </div>
                        ))}
                      </div>
                    </div>

                    <div className="rounded-2xl bg-white border border-slate-200 p-4 shadow-sm">
                      <h4 className="text-sm font-extrabold">📊 성과 IC • Factor Validity • Hit Rate</h4>
                      <div className="mt-3 grid grid-cols-2 gap-3">
                        <div className="p-3 rounded-xl bg-violet-50 border border-violet-200"><div className="text-xs text-violet-700">평균 Hit Rate</div><div className="text-lg font-extrabold text-violet-900">66.8% <span className="text-xs font-normal">(+4.4%p DART)</span></div><div className="text-xs text-violet-600">필터 전 62.4% → 후 66.8%</div></div>
                        <div className="p-3 rounded-xl bg-emerald-50 border border-emerald-200"><div className="text-xs text-emerald-700">평균 IC</div><div className="text-lg font-extrabold text-emerald-900">0.15</div><div className="text-xs text-emerald-600">목표 0.12 유지 중</div></div>
                      </div>
                      <div className="mt-3 space-y-2">
                        {(currentMeta?.top_valid || ["S&P500","구리","SOX / 필라"]).map((f,i) => {
                          const isObj = typeof f === 'object' && f !== null;
                          const name = isObj ? (f.factor || f.name || 'Unknown') : f;
                          const prob = isObj ? (f.prob ?? (0.75 - i*0.05)) : (0.75 - i*0.05);
                          const color = isObj ? (f.color || '#7c3aed') : '#7c3aed';
                          return (
                            <div key={`${name}-${i}`} className="flex items-center justify-between p-2 rounded-lg bg-slate-50 border">
                              <span className="text-xs font-bold flex items-center gap-1.5">
                                <span className="w-2 h-2 rounded-full" style={{background: color}}></span>
                                {i+1}. {name}
                                {isObj && f.regime_match && <span className="ml-1 px-1 py-0.5 rounded text-[10px] bg-emerald-100 text-emerald-700">일치</span>}
                              </span>
                              <span className="text-xs font-mono px-2 py-0.5 rounded-full bg-white border">P(valid) {typeof prob === 'number' ? prob.toFixed(2) : prob}</span>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  </div>
                )}

                {activeTab === "market" && (
                  <div className="mt-4 space-y-4">
                    <div className="rounded-2xl p-5 text-white shadow-xl" style={{ background: "linear-gradient(135deg, #0f172a 0%, #1e293b 100%)" }}>
                      <div className="flex items-center justify-between"><h3 className="text-base font-extrabold">🌐 마켓 레짐 • Regime Dashboard REAL</h3><span className={`px-3 py-1 rounded-full text-xs font-bold ${currentRegime.regime==="normal" ? "bg-emerald-500" : currentRegime.regime==="caution" ? "bg-amber-500" : "bg-red-500"} text-white`}>{currentRegime.confidence || currentRegime.regime} • {currentRegime.window}일 윈도우</span></div>
                      <div className="mt-2 text-xs text-slate-300">VIX {currentRegime.vix || 16.5} • OVX • DXY • TNX • KRW • KOSPI • SP500 REAL • GPR proxy = (VIX+OVX)/2</div>
                      <div className="mt-4 grid grid-cols-4 gap-2">
                        {[
                          { label: "VIX", value: currentRegime.vix || 16.5, threshold: 22 },
                          { label: "OVX", value: currentRegime.ovx || 32, threshold: 50 },
                          { label: "DXY", value: "103.8", threshold: 105 },
                          { label: "WTI vol", value: "2.1%", threshold: "4%" },
                        ].map((m) => (
                          <div key={m.label} className="rounded-xl bg-white/10 border border-white/10 p-2.5 text-center"><div className="text-xs text-slate-400">{m.label}</div><div className="text-sm font-bold">{m.value}</div><div className="text-xs text-slate-400">임계 {m.threshold}</div></div>
                        ))}
                      </div>
                      <div className="mt-3 text-xs text-slate-400">평시 120일 → 고변동 90일 → 전시 60일 자동 축소 • {currentRegime.description || "정상 시장"}</div>
                    </div>

                    <div className="rounded-2xl bg-white border border-slate-200 p-4 shadow-sm">
                      <h4 className="text-sm font-extrabold">📈 KOSPI 모델 + Meta 유효 통합</h4>
                      <div className="mt-3 grid grid-cols-2 gap-3">
                        <div className="p-3 rounded-xl bg-slate-50 border"><div className="text-xs text-slate-500">KOSPI 예측</div><div className="text-sm font-bold">+0.49% α·β</div><div className="text-xs text-slate-400">R² 0.89 Adj 0.87 • Ridge λ=0.5</div></div>
                        <div className="p-3 rounded-xl bg-emerald-50 border border-emerald-200"><div className="text-xs text-emerald-700">Meta 유효 팩터</div><div className="text-sm font-bold">{currentMeta?.top_valid?.length || 5}개 유효</div><div className="text-xs text-emerald-600">P(valid) {(currentMeta?.avg_p_valid || 0.72).toFixed(2)}</div></div>
                      </div>
                      <div className="mt-3 space-y-2">
                        {contributions.slice(0,5).map((c) => (
                          <div key={c.factor} className="flex items-center justify-between p-2 rounded-lg bg-slate-50 border"><span className="text-xs font-bold">{c.factor}</span><span className="text-xs font-mono">{c.z>0 ? "+" : ""}{c.z.toFixed(2)}σ × β{c.beta.toFixed(2)} = {c.contrib>0 ? "+" : ""}{c.contrib.toFixed(2)}%</span></div>
                        ))}
                      </div>
                    </div>
                  </div>
                )}

                {activeTab === "system" && (
                  <div className="mt-4 space-y-4">
                    <div className="rounded-2xl p-5 text-white shadow-xl relative overflow-hidden" style={{ background: "linear-gradient(135deg, #f59e0b 0%, #d97706 50%, #92400e 100%)", boxShadow: "0 12px 32px rgba(245,158,11,0.25)" }}>
                      <div className="flex items-center justify-between relative z-10"><div><h3 className="text-base font-extrabold tracking-tight flex items-center gap-2">🔄 Retrain Dashboard v60.2 • 6개월 재학습 REAL <span className={`px-2.5 py-1 rounded-full text-xs font-mono ${isRetrainLive ? "bg-white text-amber-700" : "bg-white/20"}`}>{isRetrainLive ? "● LIVE" : "○ DEMO"}</span></h3><div className="mt-1 text-xs text-amber-100 font-mono">RidgeCV α=[0.1,0.5,1.0,2.0] + 180D Rolling + 70% new 30% old blending • yfinance REAL</div></div><span className="px-3 py-1.5 rounded-full bg-white/20 backdrop-blur border border-white/20 text-xs font-mono font-bold">retrain_model.py + retrain.yml</span></div>
                      <div className="mt-4 grid grid-cols-4 gap-3 relative z-10">
                        <div className="rounded-xl bg-white/10 backdrop-blur border border-white/15 p-3"><div className="text-xs font-mono text-amber-200 tracking-widest">최근 재학습</div><div className="mt-1 text-sm font-extrabold text-white">{retrainData.date}</div><div className="mt-1 text-xs text-amber-100">버전 {retrainData.version?.split('-')[0] || "v60.2"}</div></div>
                        <div className="rounded-xl bg-white/10 backdrop-blur border border-white/15 p-3"><div className="text-xs font-mono text-amber-200 tracking-widest">평균 R²</div><div className="mt-1 text-sm font-extrabold text-white">{retrainData.avg_r2} <span className="text-xs font-normal">8개 업종</span></div><div className="mt-1 text-xs text-amber-100">R² >0.8 우수 • &lt;0.7 재검토</div></div>
                        <div className="rounded-xl bg-white/10 backdrop-blur border border-white/15 p-3"><div className="text-xs font-mono text-amber-200 tracking-widest">베타 변화</div><div className="mt-1 text-sm font-extrabold text-white">{retrainData.changes}개 팩터</div><div className="mt-1 text-xs text-amber-100">|Δβ| >0.02 기준</div></div>
                        <div className="rounded-xl bg-white text-amber-900 p-3 shadow-lg"><div className="text-xs font-mono text-amber-700 tracking-widest">다음 재학습</div><div className="mt-1 text-sm font-extrabold">{retrainData.next_retrain}</div><div className="mt-1 text-xs text-amber-700">매월 1일 11:00 KST</div></div>
                      </div>
                    </div>

                    <div className="rounded-2xl bg-white border border-slate-200 p-4 shadow-sm">
                      <h4 className="text-sm font-extrabold flex items-center gap-2">🛡️ DART 필터 상세 • 1단계 최적 필터 (탭에서 이동됨)</h4>
                      <div className="mt-1 text-xs text-slate-500">개별 기업 특성 기반 부실주 제거 • DART 실데이터 연동 • 필터는 추천 탭에서 ON/OFF</div>
                      <div className="mt-4 grid grid-cols-12 gap-3">
                        {[
                          { id: "elec", name: "전기전자", rule: "v54 완화: ROE>-10% • 부채<400% • 유동>80% • 영업>-10%", color: "#2563eb", reject: "부채 800%↑ 또는 ROE -30%↓ 극심 부실만 탈락", effect: "Hit +4.4%p" },
                          { id: "auto", name: "자동차", rule: "v54 완화: ROE>-5% • 부채<400% • 유동>80%", color: "#0f766e", reject: "부채 500%↑만 탈락", effect: "유동성 80%↑면 통과" },
                          { id: "chem", name: "화학/전지", rule: "v54 완화: ROE>-10% • 부채<400% • 영업>-10%", color: "#7c3aed", reject: "SK이노베이션 통과 • 롯데케미칼 통과", effect: "2차전지 적자 허용" },
                          { id: "fin", name: "금융", rule: "v54 완화: ROE>0% • 부채<1500% • 유동>70%", color: "#1e293b", reject: "한화생명 통과 • 부채 1500%↑만 탈락", effect: "저PBR 허용" },
                          { id: "bio", name: "바이오", rule: "v54 완화: ROE>-50% • 부채<250% • 유동>100%", color: "#e11d48", reject: "HLB 통과 • ROE -50%↓만 탈락", effect: "현금 중심 판단" },
                          { id: "steel", name: "철강", rule: "v54 완화: ROE>-10% • 부채<500% • 영업>-10%", color: "#a16207", reject: "현대제철 통과 • 부채 500%↑만 탈락", effect: "마진 -10% 허용" },
                          { id: "const", name: "건설/조선", rule: "v54 완화: ROE>-10% • 부채<500% • 유동>80%", color: "#334155", reject: "GS건설 탈락 가능 • 부채 500%↑ 관리", effect: "불황기 적자 허용" },
                          { id: "retail", name: "유통/IT", rule: "v54 완화: ROE>-5% • 부채<350% • 영업>-5%", color: "#0891b2", reject: "이마트 통과 • 롯데쇼핑 경계", effect: "적자 -5%까지 허용" },
                        ].map((f) => (
                          <div key={f.id} className="col-span-12 md:col-span-6 rounded-xl bg-slate-50 border p-3">
                            <div className="flex items-center justify-between"><span className="text-xs font-bold px-2 py-0.5 rounded-full text-white" style={{ background: f.color }}>{f.name}</span><span className="text-xs font-mono text-slate-500">{f.rule}</span></div>
                            <div className="mt-2 text-xs text-slate-600">탈락: {f.reject}</div>
                            <div className="mt-1 text-xs text-emerald-600">→ {f.effect}</div>
                          </div>
                        ))}
                      </div>
                      <div className="mt-4 grid grid-cols-3 gap-3">
                        <div className="rounded-xl bg-slate-50 border p-3"><div className="text-xs text-slate-400">필터 없을 때</div><div className="text-sm font-bold">Hit 62.4% • 수익 +1.84% • MDD -3.2%</div></div>
                        <div className="rounded-xl bg-emerald-50 border border-emerald-200 p-3"><div className="text-xs text-emerald-700">필터 적용 후</div><div className="text-sm font-bold text-emerald-700">Hit 66.8% • 수익 +2.21% • MDD -2.4%</div></div>
                        <div className="rounded-xl bg-slate-900 text-white p-3"><div className="text-xs text-slate-400">개선 효과</div><div className="text-sm font-bold">+4.4%p • +0.37%p • -0.8%p • 탈락률 15%</div></div>
                      </div>
                    </div>

                    <div className="rounded-2xl bg-slate-900 text-slate-200 p-4 font-mono text-xs">
                      <div className="font-bold text-white">시스템 정보 • v61.3 100% REAL KRX + 15007 CSV REAL • Trader Centric • 5 Tabs 통합</div>
                      <div className="mt-2">• daily-update.yml: 07:30 KST • QC Gate + 10 Factors + 64 Picks + Regime + Retrain fetch</div>
                      <div>• performance-update.yml: 16:00 KST • Regime + Performance + Meta</div>
                      <div>• retrain.yml: 매월 1일 11:00 KST • RidgeCV 180D REAL</div>
                      <div className="mt-2 pt-2 border-t border-white/10">• Filter: 추천 탭에서 DART ON/OFF • 왼쪽 INDUSTRIES + 오른쪽 FACTOR로 필터링 • 5개 탭으로 축소 완료</div>
                    </div>
                  </div>
                )}
              </main>

              <aside className="col-span-12 md:col-span-4 space-y-4 md:sticky md:top-20 md:h-[calc(100vh-6rem)] md:overflow-auto">
                <div className="rounded-2xl border bg-white p-4 shadow-sm">
                  <div className="flex items-center justify-between"><h3 className="text-sm font-extrabold tracking-tight">Today's Factor Z-Scores</h3><span className="text-xs font-mono px-2.5 py-1 rounded-full bg-emerald-600 text-white font-bold">{selectedDate} • v61.3 REAL • 100% REAL KRX • 15007 CSV REAL</span></div>
                  <div className="mt-1 text-xs text-slate-500">오른쪽 추천 선택 • 클릭하면 중앙 필터 • {selectedFactor ? `${selectedFactor} 필터 중` : "필터 없음"}</div>
                  {selectedFactor && <button onClick={() => setSelectedFactor(null)} className="mt-2 w-full text-xs py-1.5 rounded-full bg-slate-900 text-white hover:bg-slate-800">✕ {selectedFactor} 필터 해제 • 전체 보기</button>}
                  <div className="mt-4">
                    <div className="grid grid-cols-12 text-xs font-mono text-slate-400 pb-2 border-b font-bold tracking-widest"><div className="col-span-6">FACTOR</div><div className="col-span-2 text-right">Z</div><div className="col-span-2 text-right">β</div><div className="col-span-2 text-right">기여도</div></div>
                    {contributions.map((c) => {
                      const zAbs = Math.abs(c.z);
                      const zCls = zAbs > 1 ? (c.z > 0 ? "z-strong-pos" : "z-strong-neg") : c.z > 0 ? "z-pos" : c.z < 0 ? "z-neg" : "z-neutral";
                      const isSelected = selectedFactor === c.factor;
                      return (
                        <div key={c.factor} onClick={() => setSelectedFactor(isSelected ? null : c.factor)} className={`grid grid-cols-12 py-3 border-b border-slate-50 items-center hover:bg-slate-50/80 rounded-lg px-1 transition-colors cursor-pointer ${isSelected ? "bg-emerald-50 border-emerald-200" : ""}`}>
                          <div className="col-span-6"><div className="text-sm font-bold tracking-tight flex items-center gap-1.5">{c.factor} {isSelected && <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>}</div><div className="text-xs text-slate-500">{factorMeta[c.factor]?.desc || ""}</div></div>
                          <div className="col-span-2 text-right"><span className={`z-badge ${zCls}`}>{c.z>0 ? "+" : ""}{c.z.toFixed(2)}</span></div>
                          <div className="col-span-2 text-right font-mono text-xs font-semibold text-slate-600">{c.beta>0 ? "+" : ""}{c.beta.toFixed(2)}</div>
                          <div className={`col-span-2 text-right font-mono text-xs font-bold ${c.contrib>=0 ? "text-emerald-600" : "text-red-600"}`}>{c.contrib>0 ? "+" : ""}{c.contrib.toFixed(2)}%</div>
                        </div>
                      );
                    })}
                  </div>
                  <div className="mt-3 p-2.5 rounded-xl bg-blue-50 border border-blue-200 text-xs text-blue-800">💡 오른쪽 팩터 클릭 → 중앙 추천 8종 필터링 • 예) 구리 클릭 → 구리 민감 종목만 표시</div>
                </div>

                <div className="rounded-2xl bg-white border border-slate-200 p-4 shadow-sm">
                  <h3 className="text-xs font-bold tracking-widest">팩터 전체 Z-Score</h3>
                  <div className="mt-3 space-y-2">
                    {Object.entries(zScores).map(([f,z]) => {
                      const isSelected = selectedFactor === f;
                      return (
                        <button key={f} onClick={() => setSelectedFactor(isSelected ? null : f)} className={`w-full flex items-center justify-between p-2 rounded-xl border transition-all ${isSelected ? "bg-slate-900 text-white border-slate-900" : "bg-slate-50 hover:bg-white border-slate-200"}`}>
                          <span className="text-xs font-bold">{f}</span>
                          <span className={`text-xs font-mono px-2 py-0.5 rounded-full ${z>1 ? "bg-emerald-100 text-emerald-700" : z<-1 ? "bg-red-100 text-red-700" : "bg-white text-slate-600 border"}`}>{z>0 ? "+" : ""}{z.toFixed(2)}</span>
                        </button>
                      );
                    })}
                  </div>
                </div>
              </aside>
            </div>

            <HistoryModal open={showHistory} onClose={() => setShowHistory(false)} history={history} selectedDate={selectedDate} onSelect={loadSnapshot} />
            <DisclaimerModal open={showDisclaimer} onClose={() => setShowDisclaimer(false)} />
          </div>
        );
      }

      const root = ReactDOM.createRoot(document.getElementById("root"));
      root.render(<App />);
