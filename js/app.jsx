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
                <div className="text-xs font-mono text-slate-500 mb-3">Firebase • 최근 {history.length}개 • 평일 07:30 KST 자동 저장</div>
                <div className="space-y-2">
                  {history.length === 0 && <div className="text-sm text-slate-400 py-8 text-center">저장된 자료 없음 • Local Mode</div>}
                  {history.map((doc) => {
                    const isSelected = doc.date === selectedDate;
                    return (
                      <button key={doc.date} onClick={() => { onSelect(doc.date); onClose(); }}
                        className={`w-full text-left rounded-xl border p-3.5 flex items-center justify-between transition-all btn-modern ${isSelected ? "bg-[#1e3a8a] text-white border-[#1e3a8a]" : "bg-white border-slate-200 hover:border-slate-300 hover:bg-slate-50"}`}>
                        <div className="flex items-center gap-3">
                          <div className={`w-10 h-10 rounded-lg flex items-center justify-center text-sm font-bold ${isSelected ? "bg-white/15" : "bg-slate-100"}`}>📊</div>
                          <div>
                            <div className="text-sm font-bold">{doc.date} ({getDayName(doc.date)})</div>
                            <div className={`text-xs font-mono ${isSelected ? "text-slate-300" : "text-slate-500"}`}>{doc.weeklyPicks?.length || 0} picks • Z {doc.zScores ? Object.keys(doc.zScores).length : 0}</div>
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
                  <div className="text-xs font-mono text-slate-500 mt-1">데이터 출처 및 법적 고지</div>
                </div>
                <button onClick={onClose} className="w-9 h-9 rounded-full bg-[#1e3a8a] text-white hover:bg-[#23408e] btn-modern">✕</button>
              </div>
              <div className="mt-6 space-y-6 text-sm leading-relaxed">
                <div className="p-4 rounded-xl bg-red-50 border border-red-200">
                  <div className="font-extrabold text-red-900 text-sm flex items-center gap-2"><span>🚨</span> 본 서비스는 투자 조언이 아닙니다</div>
                  <div className="mt-2 text-xs text-slate-700 leading-relaxed">
                    예상 수익률, Score, 64 Picks, Factor Betas, Z-Scores는 과거 데이터 기반 통계적 예측이며 <b>투자 자문, 매수/매도 추천이 아닙니다.</b> 
                    모든 투자 결정은 본인 판단과 책임 하에 이루어져야 하며, 원금 손실이 발생할 수 있습니다. 본 모델의 과거 설명력은 미래 수익을 보장하지 않습니다.
                  </div>
                </div>

                <div className="p-4 rounded-xl bg-amber-50 border border-amber-200">
                  <div className="font-bold text-amber-900 text-xs">⚠️ 투자 위험 고지</div>
                  <div className="mt-2 text-xs text-slate-700 leading-relaxed space-y-1">
                    <div>• 주식, 선물 등 투자 상품은 가격 변동으로 원금 손실 위험이 있습니다.</div>
                    <div>• 외국인 수급, 환율, 유가 등 10개 팩터는 외부 변수이며 급변할 수 있습니다.</div>
                    <div>• DART 필터, Regime 모델은 통계적 보조 수단이며 100% 정확하지 않습니다. 성과 지표는 실제 추적 데이터 기준으로만 표시됩니다.</div>
                    <div>• 본 대시보드는 07:30 KST 자동 업데이트되며 장중 급변은 반영되지 않을 수 있습니다.</div>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
                  <div className="p-3 rounded-xl bg-blue-50 border border-blue-200"><div className="font-bold text-blue-900">FRED • US Macro</div><div className="mt-1 text-slate-700 leading-relaxed">DGS10(10Y 금리), DCOILWTICO(WTI 유가), DTWEXBGS(달러 DXY), VIXCLS(VIX) • St.Louis Fed API • 100% REAL</div></div>
                  <div className="p-3 rounded-xl bg-emerald-50 border border-emerald-200"><div className="font-bold text-emerald-900">yfinance • Global</div><div className="mt-1 text-slate-700 leading-relaxed">^GSPC(S&P500), ^SOX(필라 반도체), KRW=X(원달러), HG=F(구리), 000001.SS(상해종합) • 100% REAL</div></div>
                  <div className="p-3 rounded-xl bg-indigo-50 border border-indigo-200"><div className="font-bold text-indigo-900">KRX OPEN API • 7개 승인</div><div className="mt-1 text-slate-700 leading-relaxed">KOSPI/KOSDAQ 시세, 외국인/기관 수급(KOSPI market, pykrx) • 투자자별 거래실적 CSV(foreigner_kospi200.csv) workflow 갱신 REAL</div></div>
                  <div className="p-3 rounded-xl bg-violet-50 border border-violet-200"><div className="font-bold text-violet-900">DART • 재무 필터</div><div className="mt-1 text-slate-700 leading-relaxed">금융감독원 전자공시 • PER, PBR, ROE, 부채비율, 유동비율, 영업이익률, 매출증가율 • 부실주 15% 사전 제거 • v54 완화 기준</div></div>
                </div>

                <div className="p-3 rounded-xl bg-slate-50 border text-xs">
                  <div className="font-bold text-[#1e3a8a]">법적 고지 • 출처 명시</div>
                  <div className="mt-2 text-slate-600 leading-relaxed">
                    본 대시보드는 개인 연구용으로 제작되었습니다. FRED, yfinance, KRX, DART 데이터는 각 출처의 이용 약관을 따릅니다. 
                    Firebase Firestore는 읽기 전용(read=true, write=false)으로 설정되어 있으며 쓰기는 Admin SDK만 가능합니다. 
                    Google API Key는 Firebase 공개키이며 비밀키가 아닙니다. 비밀키는 GitHub Secrets에만 보관됩니다.<br/>
                    10 Factors China Proxy + DART + 64 Picks + Regime + Retrain • 6개월 운영 • © 2026 Quant Lab
                  </div>
                </div>
              </div>
            </div>
          </div>
        );
      }

      function HelpModal({ open, onClose }) {
        if (!open) return null;
        return (
          <div className="fixed inset-0 z-[60] help-overlay flex items-center justify-center p-4" onClick={onClose}>
            <div className="help-card bg-white rounded-2xl max-w-3xl w-full max-h-[90vh] overflow-auto p-6" onClick={(e) => e.stopPropagation()}>
              <div className="flex items-center justify-between sticky top-0 bg-white pb-4 border-b z-10">
                <div>
                  <h2 className="text-sm font-extrabold tracking-tight flex items-center gap-2">
                    <span className="w-8 h-8 rounded-xl bg-blue-100 border border-blue-200 flex items-center justify-center text-blue-700">?</span>
                    도움말 • KOSPI Quant Terminal 사용법
                  </h2>
                  <div className="text-xs font-mono text-slate-500 mt-1">v61.6-stable REAL_ONLY • 5 Tabs • Left-Right 필터 • 평일 07:30 KST 자동 업데이트</div>
                </div>
                <button onClick={onClose} className="w-9 h-9 rounded-full bg-[#1e3a8a] text-white hover:bg-[#23408e] btn-modern">✕</button>
              </div>
              <div className="mt-6 space-y-5 text-sm">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                  <div className="p-3 rounded-xl bg-[#1e3a8a] text-white"><div className="text-xs font-bold">1. 왼쪽 INDUSTRIES</div><div className="text-xs mt-1 text-slate-300">8개 업종 선택 → 중앙 필터 • R²는 재학습 스냅샷 기준</div></div>
                  <div className="p-3 rounded-xl bg-white border"><div className="text-xs font-bold">2. 중앙 5 Tabs</div><div className="text-xs mt-1 text-slate-600">추천(8) / 전체64 / 성과 / 마켓 / 시스템 • Factor Beta 바</div></div>
                  <div className="p-3 rounded-xl bg-white border"><div className="text-xs font-bold">3. 오른쪽 FACTOR</div><div className="text-xs mt-1 text-slate-600">Z-Score 클릭 → 중앙 필터링 • 구리, 상해, S&P500 등 10개</div></div>
                </div>
                <div className="p-3 rounded-xl bg-blue-50 border border-blue-200 text-xs leading-relaxed">
                  <div className="font-bold text-blue-900">💡 트레이더 사용법</div>
                  <div className="mt-1 text-slate-700">• 왼쪽 산업 클릭: 해당 산업 8종 추천 • 오른쪽 팩터 클릭: 해당 팩터에 민감한 종목만 필터 (예: 구리 클릭 → 화학·철강 위주) • DART ON/OFF: 부실주 제거 필터 • 07:30 체크리스트 4개 모두 ✓여야 신뢰도 높음</div>
                </div>
                <div className="p-3 rounded-xl bg-emerald-50 border border-emerald-200 text-xs leading-relaxed">
                  <div className="font-bold text-emerald-900">📖 읽는 법 • 지표 해석</div>
                  <div className="mt-2 space-y-1.5 text-slate-700">
                    <div><b>Z-Score</b>: 팩터가 최근 120일 평균 대비 표준편차 몇 개 위치인지. +1.0 이상 강한 우호, -1.0 이하 강한 비우호, ±3 클립. VIX는 부호 반전(높을수록 위험 → 음수로 표시).</div>
                    <div><b>β (베타)</b>: 팩터 z가 1 움직일 때 산업 수익률에 미치는 민감도. 부호 = 방향(양수 우호/음수 비우호), 크기 = 민감도.</div>
                    <div><b>기여도</b>: β × Z. 산업 예측 수익률을 만드는 각 팩터의 기여분. 합계 = 예측 산업 수익률.</div>
                    <div><b>Regime</b>: VIX/OVX/DXY/WTI 등 8개 지표 기반 시장 상태. 평시/주의/전시/위기. 전시 이상이면 리스크 관리 우선 해석.</div>
                    <div><b>Score</b>: 6.5 + 예측수익률×1.2 + 모멘텀×0.3 + 보정항. 통계적 상대 점수(1~10)이며 <b>매수 추천이 아닙니다.</b> "Score 상위"는 모델 상위권이라는 뜻입니다.</div>
                    <div><b>예상 수익률</b>: 모델 기반 추정치로 실제 수익을 보장하지 않습니다. 성과 탭의 실측 vs KOSPI가 더 신뢰할 지표입니다.</div>
                  </div>
                </div>
                <div className="p-3 rounded-xl bg-slate-50 border text-xs">
                  <div className="font-bold">DATA PIPELINE</div>
                  <div className="mt-1 font-mono text-slate-600">yfinance(4) + FRED(3) + KRX OPEN API(2) + 15007 CSV(1) → StandardScaler → RidgeCV(λ) → Dashboard • Firebase Live • 매일 07:30 KST</div>
                </div>
              </div>
            </div>
          </div>
        );
      }


      function App() {
        const [selectedIndustry, setSelectedIndustry] = useState("elec");
        const [selectedFactor, setSelectedFactor] = useState(null);
        const [zScores, setZScores] = useState({});
        const [history, setHistory] = useState([]);
        const [performanceRecords, setPerformanceRecords] = useState([]);
        const [performanceSummary, setPerformanceSummary] = useState(null);
        const [metaSummary, setMetaSummary] = useState(null);
        const [qcHealth, setQcHealth] = useState(null);
        const [selectedDate, setSelectedDate] = useState("—");
        const [showHistory, setShowHistory] = useState(false);
        const [showDisclaimer, setShowDisclaimer] = useState(false);
        const [showHelp, setShowHelp] = useState(false);
        const [activeTab, setActiveTab] = useState("recommend");
        const [liveCount, setLiveCount] = useState(0);
        const [lastRefresh, setLastRefresh] = useState(new Date());
        const [isViewingHistory, setIsViewingHistory] = useState(false);

        const normalizeZScores = (cloud = {}) => ({
          "S&P500": cloud.SP500 ?? cloud["S&P500"] ?? 0,
          "외국인 수급": cloud.외국인 ?? cloud.외국인_선물 ?? 0,
          "SOX / 필라": cloud.반도체팩터 ?? cloud.SOX ?? cloud["SOX / 필라"] ?? 0,
          "US 10Y": cloud.US10Y ?? cloud["US 10Y"] ?? 0,
          원달러: cloud.원달러 ?? 0,
          WTI: cloud.WTI ?? 0,
          DXY: cloud.DXY ?? 0,
          VIX: cloud.VIX ?? 0,
          구리: cloud.구리 ?? 0,
          상해종합: cloud.상해종합 ?? 0,
        });

        const loadSnapshot = (dateStr) => {
          const doc = history.find((d) => d.date === dateStr);
          if (!doc) return;
          const cloud = doc.zScores;
          if (cloud) {
            setZScores(normalizeZScores(cloud));
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
              setZScores(normalizeZScores(cloud));
              setSelectedDate(docs[0].date);
            }
          });
          return () => unsub();
        }, [isViewingHistory]);

        useEffect(() => {
          if (!db) {
            setPerformanceRecords([]);
            setPerformanceSummary(null);
            setMetaSummary(null);
            return;
          }

          const unsubPerformance = db.collection("performance_tracking")
            .orderBy("evalDate", "desc")
            .limit(300)
            .onSnapshot((snap) => {
              setPerformanceRecords(snap.docs.map((d) => d.data()));
            }, (error) => {
              console.warn("[performance_tracking]", error);
              setPerformanceRecords([]);
            });

          const unsubSummary = db.collection("performance_snapshots")
            .orderBy("date", "desc")
            .limit(1)
            .onSnapshot((snap) => {
              setPerformanceSummary(snap.empty ? null : snap.docs[0].data());
            }, (error) => {
              console.warn("[performance_snapshots]", error);
              setPerformanceSummary(null);
            });

          const unsubMeta = db.collection("meta_summaries")
            .orderBy("date", "desc")
            .limit(1)
            .onSnapshot((snap) => {
              setMetaSummary(snap.empty ? null : snap.docs[0].data());
            }, (error) => {
              console.warn("[meta_summaries]", error);
              setMetaSummary(null);
            });

          const unsubQc = db.collection("data_quality_logs")
            .orderBy("date", "desc")
            .limit(1)
            .onSnapshot((snap) => {
              setQcHealth(snap.empty ? null : snap.docs[0].data());
            }, (error) => {
              console.warn("[data_quality_logs]", error);
              setQcHealth(null);
            });

          return () => {
            unsubPerformance();
            unsubSummary();
            unsubMeta();
            unsubQc();
          };
        }, []);

        const currentIndustry = useMemo(() => industries.find((i) => i.id === selectedIndustry) || industries[0], [selectedIndustry]);

        const contributions = useMemo(() => {
          return Object.entries(currentIndustry.betas).map(([factor, beta]) => {
            const z = zScores[factor] ?? zScores[factorMeta[factor]?.label] ?? 0;
            const contrib = beta * z;
            return { factor, beta, z, contrib };
          }).sort((a, b) => Math.abs(b.contrib) - Math.abs(a.contrib));
        }, [currentIndustry, zScores]);

        const predictedReturn = useMemo(() => contributions.reduce((sum, c) => sum + c.contrib, 0), [contributions]);

        const activeSnapshot = useMemo(() => {
          return history.find((d) => d.date === selectedDate) || history[0] || null;
        }, [history, selectedDate]);

        const weeklyPicks = useMemo(() => {
          const picks = Array.isArray(activeSnapshot?.weeklyPicks) ? activeSnapshot.weeklyPicks : [];
          return picks.filter((p) => p && p.ticker && p.name && p.industryId);
        }, [activeSnapshot]);

        const filteredPicks = useMemo(() => {
          let picks = weeklyPicks.filter(p => p.industryId === selectedIndustry);
          if (selectedFactor) {
            const factorMap = { "S&P500": ["SP500","S&P500"], "SOX / 필라": ["반도체팩터","SOX / 필라","SOX"], "원달러": ["원달러"], "US 10Y": ["US10Y","한미스프레드"], "구리": ["중국PMI","구리"], "상해종합": ["중국PMI","상해종합"], "WTI": ["WTI"], "DXY": ["DXY"], "VIX": ["VIX"], "외국인 수급": ["외국인"] };
            const related = factorMap[selectedFactor] || [selectedFactor];
            picks = picks.filter(p => related.some(r => (p.targetFactor || "").includes(r) || (p.reason || "").includes(r)));
            if (picks.length === 0) picks = weeklyPicks.filter(p => p.industryId === selectedIndustry);
          }
          return picks.slice(0,8);
        }, [weeklyPicks, selectedIndustry, selectedFactor]);

        const all64Filtered = useMemo(() => {
          if (!selectedFactor) return weeklyPicks;
          const factorMap = { "S&P500": ["SP500","S&P500"], "SOX / 필라": ["반도체팩터","SOX"], "원달러": ["원달러"], "US 10Y": ["US10Y","한미스프레드"], "구리": ["구리","중국PMI"], "상해종합": ["상해종합","중국PMI"] };
          const related = factorMap[selectedFactor] || [selectedFactor];
          return weeklyPicks.filter(p => related.some(r => (p.targetFactor || "").includes(r) || (p.reason || "").includes(r)));
        }, [weeklyPicks, selectedFactor]);

        const pastPicks = useMemo(() => {
          const byRecDate = new Map();
          performanceRecords
            .filter((r) => r && r.industryId === selectedIndustry && typeof r.returnPct === "number")
            .forEach((r) => {
              const key = `${r.recDate || r.evalDate || `${r.ticker}-${r.date}`}-${r.ticker}`;
              const prev = byRecDate.get(key);
              if (!prev || String(r.evalDate || "") > String(prev.evalDate || "")) {
                byRecDate.set(key, r);
              }
            });

          return [...byRecDate.values()]
            .sort((a, b) => String(b.evalDate || b.recDate || "").localeCompare(String(a.evalDate || a.recDate || "")))
            .slice(0, 8)
            .map((r) => {
              const returnPct = Number(r.returnPct) || 0;
              const vsKospi = Number(r.excessReturnPct ?? r.excessReturn * 100) || 0;
              return {
                date: r.evalDate || r.recDate || "—",
                recDate: r.recDate,
                evalDate: r.evalDate,
                industryId: r.industryId,
                industry: industries.find((i) => i.id === r.industryId)?.short || r.industryId,
                ticker: r.ticker,
                name: r.name,
                returnPct,
                vsKospi,
                status: returnPct > 1.5 ? "성공" : returnPct > -1 ? "보류" : "실패",
                score: r.score,
                daysElapsed: r.daysElapsed,
              };
            });
        }, [performanceRecords, selectedIndustry]);

        const pastPicksAvg = useMemo(() => {
          if (pastPicks.length === 0) return { avg: "0.00", vsKospi: "0.00", hit: 0, total: 0, hitRate: 0 };
          const avg = pastPicks.reduce((s, r) => s + r.returnPct, 0) / pastPicks.length;
          const vs = pastPicks.reduce((s, r) => s + r.vsKospi, 0) / pastPicks.length;
          const hit = pastPicks.filter((r) => r.returnPct > 0).length;
          return { avg: avg.toFixed(2), vsKospi: vs.toFixed(2), hit, total: pastPicks.length, hitRate: hit / pastPicks.length };
        }, [pastPicks]);

        const icStats = useMemo(() => {
          const entries = metaSummary?.factors
            ? Object.entries(metaSummary.factors).map(([factor, metrics]) => ({ factor, ...(metrics || {}) }))
            : [];
          const valid = entries.filter((f) => typeof f.ic === "number");
          if (valid.length === 0) return { avgIc: null, avgHit: null, top: [], count: 0 };
          const avgIc = valid.reduce((s, f) => s + f.ic, 0) / valid.length;
          const avgHit = valid.reduce((s, f) => s + (f.hit_rate_pct ?? (f.hit_rate * 100) ?? 0), 0) / valid.length;
          const top = [...valid].sort((a, b) => Math.abs(b.ic) - Math.abs(a.ic)).slice(0, 5);
          return { avgIc, avgHit, top, count: valid.length };
        }, [metaSummary]);

        const currentRegime = useMemo(() => activeSnapshot?.regime || null, [activeSnapshot]);
        const retrainData = useMemo(() => activeSnapshot?.retrain || activeSnapshot?.beta_snapshot || null, [activeSnapshot]);

        const todaySummary = useMemo(() => {
          const zEntries = Object.entries(zScores)
            .filter(([, v]) => typeof v === "number" && Number.isFinite(v));
          const topFactorEntry = zEntries
            .sort((a, b) => Math.abs(b[1]) - Math.abs(a[1]))[0] || null;

          const industryPreds = industries
            .map((ind) => ({
              ...ind,
              pred: Object.entries(ind.betas).reduce(
                (s, [f, b]) => s + (zScores[f] ?? 0) * b, 0
              ),
            }))
            .sort((a, b) => b.pred - a.pred);

          const topPicks = [...weeklyPicks]
            .sort((a, b) => (b.score || 0) - (a.score || 0))
            .slice(0, 3);

          return {
            regime: currentRegime?.regime || null,
            regimeConf: currentRegime?.confidence,
            regimeIsRisk: ["전시", "위기", "caution", "risk_off"].includes(currentRegime?.regime),
            topFactor: topFactorEntry ? { name: topFactorEntry[0], z: topFactorEntry[1] } : null,
            topIndustries: industryPreds.slice(0, 3),
            topPicks,
          };
        }, [zScores, weeklyPicks, currentRegime]);

        const prevZScores = useMemo(() => {
          const prev = history[1];
          return prev?.zScores ? normalizeZScores(prev.zScores) : null;
        }, [history]);

        const zDelta = (factor) => {
          if (!prevZScores) return null;
          const prevV = prevZScores[factor] ?? prevZScores[factorMeta[factor]?.label];
          const curV = zScores[factor] ?? zScores[factorMeta[factor]?.label];
          if (typeof prevV !== "number" || typeof curV !== "number") return null;
          return curV - prevV;
        };
        const hasZScores = Object.values(zScores).some((v) => typeof v === "number" && v !== 0);
        const predText = hasZScores ? `${predictedReturn>0 ? "+" : ""}${predictedReturn.toFixed(2)}%` : "—";
        const fmtPred = (v) => hasZScores ? `${v>0 ? "+" : ""}${v.toFixed(2)}%` : "—";
        const dartFilterStatus = activeSnapshot?.filter_status || (activeSnapshot?.filter_applied ? "APPLIED" : "UNKNOWN");
        const snapshotDetails = activeSnapshot?.details || {};
        const foreignerDetail = snapshotDetails["외국인"] || {};
        const us10yDetail = snapshotDetails.US10Y || {};
        const dxyDetail = snapshotDetails.DXY || {};
        const regimeIndicators = currentRegime?.indicators || {};
        const regimeWindow = currentRegime?.window ?? currentRegime?.config?.window ?? "—";
        const regimeDescription = currentRegime?.config?.description || currentRegime?.reason || "레짐 데이터 없음";
        const fmtNum = (value, digits = 2) => (typeof value === "number" && Number.isFinite(value) ? value.toFixed(digits) : "—");
        const industryR2 = (industryId) => retrainData?.r2?.[industryId] ?? "—";

        return (
          <div className="min-h-screen bg-white">
            <header className="sticky top-0 z-30" style={{ background: "white", borderBottom: "1px solid #e5e8eb", height: "72px" }}>
              <div className="max-w-screen-2xl mx-auto px-4 md:px-6 h-[72px] flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-9 h-9 rounded-lg flex items-center justify-center font-extrabold text-xs" style={{ background: "#3182f6", color: "white" }}>KQ</div>
                  <div className="text-sm font-bold" style={{color: "#1e3a8a"}}>KOSPI Quant Terminal <span className="text-xs font-normal text-slate-500 ml-1">v61.6</span></div>
                </div>
                <div className="flex items-center gap-3">
                  {/* 탭을 먼저, KOSPI R²를 옆으로 - 위치 교체 */}
                  <div className="hidden xl:flex items-center gap-1 p-1 rounded-full bg-[#f1f5f9] border border-[#e5e8eb]">
                    {[
                      { id: "recommend", label: "추천", icon: "🎯", count: filteredPicks.length, color: "#1e3a8a" },
                      { id: "top", label: "오늘 Top 예측", icon: "📊", count: 8, color: "#f59e0b" },
                      { id: "all64", label: "전체 64", icon: "📋", count: all64Filtered.length, color: "#334155" },
                      { id: "performance", label: "성과", icon: "📈", count: pastPicks.length, color: "#7c3aed" },
                      { id: "market", label: "마켓", icon: "🌐", count: icStats.count, color: "#059669" },
                    ].map((tab) => (
                      <button key={tab.id} onClick={() => setActiveTab(tab.id)}
                        className={`px-3.5 py-1.5 rounded-full text-xs font-bold flex items-center gap-1.5 transition-all ${activeTab === tab.id ? "text-white" : "text-slate-600 hover:bg-white"}`}
                        style={activeTab === tab.id ? { background: tab.color } : {}}>
                        <span>{tab.icon}</span> {tab.label} <span className={`ml-1 px-1.5 py-0.5 rounded-full text-xs font-mono ${activeTab === tab.id ? "bg-white/20" : "bg-white border"}`}>{tab.count}</span>
                      </button>
                    ))}
                  </div>
                  {/* KOSPI R² 박스 - 탭 옆으로 이동 */}
                  <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-white border border-[#e5e8eb]">
                    <span className="text-xs text-slate-500">평균 R²</span>
                    <span className="text-sm font-bold">{retrainData?.avg_r2 ?? "N/A"}</span>
                    <span className={`text-xs font-mono px-2 py-0.5 rounded-full border ${hasZScores ? (predictedReturn>=0 ? "bg-emerald-50 text-emerald-700 border-emerald-100" : "bg-red-50 text-red-700 border-red-100") : "bg-slate-50 text-slate-500 border-slate-200"}`}>{predText}</span>
                  </div>
                  {isViewingHistory && <button onClick={returnToLatest} className="px-3 py-1.5 rounded-lg text-xs font-bold bg-amber-100 text-amber-800 border border-amber-200">↩ 최신으로</button>}
                  <button onClick={() => setShowHistory(true)} className={`px-3 py-1.5 rounded-lg text-xs font-bold border ${isViewingHistory ? "bg-amber-50 text-amber-700 border-amber-200" : "bg-white text-slate-600 border-[#e5e8eb] hover:bg-slate-50"}`}>📅 이전 자료 {history.length>0 ? `(${history.length})` : ""}</button>
                  <button onClick={() => setShowDisclaimer(true)} className="px-3 py-1.5 rounded-lg text-xs font-bold bg-white text-slate-600 border border-[#e5e8eb] hover:bg-slate-50">면책</button>
                  <button onClick={() => setShowHelp(true)} className="px-3.5 py-1.5 rounded-lg text-xs font-bold bg-[#3182f6] text-white hover:bg-[#2b7fff]">도움말</button>
                </div>
              </div>
            </header>

            <div className="max-w-screen-2xl mx-auto px-4 md:px-6 pt-4 pb-4 grid grid-cols-12 gap-4 items-start">

              <aside className="col-span-12 md:col-span-2 space-y-4 md:sticky md:top-[88px] md:h-[calc(100vh-6rem)] md:overflow-auto">
                <div className="rounded-2xl bg-[#e0f2fe] text-[#0c4a6e] p-4 border border-[#bae6fd]">
                  <div className="flex items-center justify-between"><h3 className="text-xs font-bold tracking-widest text-[#0369a1]">INDUSTRIES • 8</h3><span className="w-2 h-2 rounded-full bg-[#0ea5e9] animate-pulse"></span></div>
                  <div className="mt-1 text-xs text-[#0284c7]">업종 선택 • 중앙 필터</div>
                  <div className="mt-4 space-y-2">
                    {industries.map((ind) => {
                      const isSelected = ind.id === selectedIndustry;
                      const pred = contributions.filter(c => Object.keys(ind.betas).includes(c.factor)).reduce((s,c) => s + c.contrib, 0);
                      return (
                        <button key={ind.id} onClick={() => setSelectedIndustry(ind.id)} className={`w-full flex items-center justify-between px-3 py-2.5 rounded-xl transition-all text-left border ${isSelected ? "bg-white text-[#0c4a6e] border-[#7dd3fc]" : "bg-white/70 hover:bg-white text-[#475569] border-white/50 hover:border-[#7dd3fc]"}`}>
                          <div className="flex items-center gap-2.5"><div className="w-8 h-8 rounded-lg flex items-center justify-center text-sm font-bold" style={{ background: `${ind.color}15`, color: ind.color }}>{ind.icon}</div><div><div className="text-xs font-bold">{ind.short}</div><div className="text-xs text-slate-500">R² {industryR2(ind.id)}</div></div></div>
                          <div className="text-right"><div className={`text-xs font-mono font-bold ${hasZScores ? (pred>=0 ? "text-emerald-600" : "text-red-600") : "text-slate-400"}`}>{fmtPred(pred)}</div><div className={`w-2 h-2 rounded-full ml-auto mt-1 ${isSelected ? "bg-[#0ea5e9]" : "bg-slate-300"}`}></div></div>
                        </button>
                      );
                    })}
                  </div>
                  <div className="mt-3 pt-3 border-t border-[#bae6fd] text-xs text-[#0284c7]">Top1이 최강 • 8개 중 선택</div>
                </div>
              </aside>

              <div className="col-span-12 md:col-span-10 grid grid-cols-12 gap-4">
              <main className="col-span-12 lg:col-span-8 lg:sticky lg:top-[88px] lg:h-[calc(100vh-6rem)] lg:overflow-auto pr-1">
                {/* 탭은 상단 헤더로 이동 - 여기서는 모바일용 작은 탭 표시 */}
                <div className="xl:hidden flex items-center gap-1 p-1 rounded-full bg-[#f1f5f9] border border-[#e5e8eb] w-fit flex-wrap mb-4">
                  {[
                    { id: "recommend", label: "추천", icon: "🎯", count: filteredPicks.length, color: "#1e3a8a" },
                    { id: "top", label: "오늘 Top 예측", icon: "📊", count: 8, color: "#f59e0b" },
                    { id: "all64", label: "전체 64", icon: "📋", count: all64Filtered.length, color: "#334155" },
                    { id: "performance", label: "성과", icon: "📈", count: pastPicks.length, color: "#7c3aed" },
                    { id: "market", label: "마켓", icon: "🌐", count: icStats.count, color: "#059669" },
                  ].map((tab) => (
                    <button key={tab.id} onClick={() => setActiveTab(tab.id)}
                      className={`px-3 py-1.5 rounded-full text-xs font-bold flex items-center gap-1 transition-all ${activeTab === tab.id ? "text-white" : "text-slate-600 hover:bg-white"}`}
                      style={activeTab === tab.id ? { background: tab.color } : {}}>
                      <span>{tab.icon}</span> {tab.label}
                    </button>
                  ))}
                </div>

                {activeTab === "recommend" && (
                  <div className="mt-4 space-y-4">
                    <div className="rounded-2xl border border-slate-200 bg-gradient-to-br from-slate-50 to-white p-4">
                      <div className="flex items-center justify-between flex-wrap gap-2">
                        <h3 className="text-sm font-extrabold flex items-center gap-2">📌 오늘의 요약 <span className="text-xs font-normal text-slate-400">{selectedDate} 스냅샷 기준</span></h3>
                        <span className="text-xs text-slate-400">Score는 통계 점수이며 투자 권유가 아닙니다</span>
                      </div>
                      <div className="mt-3 grid grid-cols-1 md:grid-cols-3 gap-3">
                        <div className={`rounded-xl border p-3 ${todaySummary.regimeIsRisk ? "bg-red-50 border-red-200" : "bg-emerald-50 border-emerald-200"}`}>
                          <div className="text-xs text-slate-500">시장 상태 • Regime</div>
                          <div className="mt-1 text-sm font-bold">{todaySummary.regime || "N/A"}{todaySummary.regimeConf != null ? ` • conf ${Number(todaySummary.regimeConf).toFixed(2)}` : ""}</div>
                          <div className="text-xs text-slate-500 mt-0.5">{todaySummary.regimeIsRisk ? "위험 국면 — 비중·리스크 관리 우선 해석" : "정상 국면 — 팩터 신호 정상 참조"}</div>
                        </div>
                        <div className="rounded-xl bg-blue-50 border border-blue-200 p-3">
                          <div className="text-xs text-slate-500">가장 강한 팩터 신호</div>
                          <div className="mt-1 text-sm font-bold">{todaySummary.topFactor ? todaySummary.topFactor.name : "—"}</div>
                          <div className="text-xs text-slate-500 mt-0.5">{todaySummary.topFactor ? `Z ${todaySummary.topFactor.z > 0 ? "+" : ""}${todaySummary.topFactor.z.toFixed(2)}σ` : "Z 데이터 없음"}</div>
                        </div>
                        <div className="rounded-xl bg-amber-50 border border-amber-200 p-3">
                          <div className="text-xs text-slate-500">예측 강세 섹터 상위</div>
                          <div className="mt-1 text-sm font-bold">{todaySummary.topIndustries.map((i) => i.short).join(" > ") || "—"}</div>
                          <div className="text-xs text-slate-500 mt-0.5">{todaySummary.topIndustries[0] ? `Top ${fmtPred(todaySummary.topIndustries[0].pred)}` : ""}</div>
                        </div>
                      </div>
                      {todaySummary.topPicks.length > 0 && (
                        <div className="mt-3 pt-3 border-t border-slate-200 flex flex-wrap items-center gap-2">
                          <span className="text-xs font-bold text-slate-500">Score 상위:</span>
                          {todaySummary.topPicks.map((p) => {
                            const ind = industries.find((i) => i.id === p.industryId) || industries[0];
                            return (
                              <span key={`${p.industryId}-${p.ticker}-summary`} className="text-xs px-2.5 py-1 rounded-full bg-white border font-mono">
                                {p.name} <span className="font-bold" style={{ color: ind?.color }}>{p.score}</span>
                              </span>
                            );
                          })}
                        </div>
                      )}
                      <div className="mt-3 pt-2 border-t border-slate-200 flex flex-wrap items-center gap-x-4 gap-y-1 text-xs font-mono">
                        <span className="text-slate-400">Δ = 전일({history[1]?.date || "—"}) 대비 Z 변화 • 우측 표 Z 아래 배지</span>
                        {qcHealth && (
                          <span className={`px-2 py-0.5 rounded-full border font-bold ${qcHealth.is_fail ? "bg-red-50 text-red-700 border-red-200" : (qcHealth.fail_count + qcHealth.warn_count) > 0 ? "bg-amber-50 text-amber-700 border-amber-200" : "bg-emerald-50 text-emerald-700 border-emerald-200"}`}>
                            QC {qcHealth.health_score ?? "—"} • FAIL {qcHealth.fail_count ?? 0} WARN {qcHealth.warn_count ?? 0}
                            {performanceSummary?.missRatePct != null ? ` • miss ${performanceSummary.missRatePct}%` : ""}
                          </span>
                        )}
                        <span className="text-slate-400">Score는 통계 점수이며 투자 권유가 아닙니다</span>
                      </div>
                    </div>

                    <div className="rounded-2xl p-4 text-white" style={{ background: `linear-gradient(135deg, ${currentIndustry.color} 0%, ${currentIndustry.color}dd 100%)` }}>
                      <div className="flex items-center justify-between gap-2 flex-wrap">
                        <h3 className="text-sm font-extrabold tracking-tight flex items-center gap-2 flex-wrap">{currentIndustry.name} 8종목 <span className="text-xs font-mono opacity-80 bg-white/20 px-2.5 py-1 rounded-full whitespace-nowrap">전체 64종 중 {currentIndustry.short} Top 8 • KRX β·모멘텀</span></h3>
                        <span className="text-xs font-mono bg-white/20 backdrop-blur px-2.5 py-1 rounded-full whitespace-nowrap ml-auto" title={`quality_status=${activeSnapshot?.quality_status || "—"} • fallback_used=${String(Boolean(activeSnapshot?.fallback_used))} • synthetic_data_used=${String(Boolean(activeSnapshot?.synthetic_data_used))}`}>{selectedDate} • {activeSnapshot?.data_status || "NO_DATA"}</span>
                      </div>
                      <div className="mt-1.5 text-xs text-white/85">Score = 6.5 + |Z|×1.2×β_adj + mom×0.3 • 타겟팩터 {Object.entries(currentIndustry.betas).sort((a,b) => Math.abs(b[1])-Math.abs(a[1]))[0]?.[0]} {selectedFactor ? `+ ${selectedFactor} 필터` : ""}</div>
                      <div className="mt-3 grid grid-cols-3 gap-2">
                        <div className="rounded-xl bg-white/15 backdrop-blur p-2.5"><div className="text-xs text-white/70">α·β 추정</div><div className="text-sm font-bold">{hasZScores ? `${predText} α·β` : "—"}</div></div>
                        <div className="rounded-xl bg-white/15 backdrop-blur p-2.5"><div className="text-xs text-white/70">Top 기여도</div><div className="text-sm font-bold">{contributions[0] ? `${contributions[0].factor} ${fmtPred(contributions[0].contrib)}` : "—"}</div></div>
                        <div className="rounded-xl bg-white/15 backdrop-blur p-2.5"><div className="text-xs text-white/70">R² / 필터</div><div className="text-sm font-bold">{industryR2(currentIndustry.id)} • DART {dartFilterStatus}</div></div>
                      </div>
                    </div>

                    <div className="rounded-2xl bg-white border border-slate-200 p-3">
                      <div className="flex items-center justify-between flex-wrap gap-2">
                        <div className="flex items-center gap-2"><span className="w-7 h-7 rounded-lg bg-red-50 border border-red-100 flex items-center justify-center">🛡️</span><span className="text-xs font-bold">DART 필터 • 1단계 최적 필터</span><span className="text-xs font-mono text-slate-500">부실주 제거 • 개별 기업 특성 기반</span></div>
                        <div className="flex items-center gap-2">
                          <span className={`text-xs px-3 py-1.5 rounded-full font-bold ${dartFilterStatus === "APPLIED" ? "bg-emerald-600 text-white" : "bg-slate-100 text-slate-500"}`}>{dartFilterStatus}</span>
                        </div>
                      </div>
                      <div className="mt-3 flex flex-wrap gap-1.5">
                        {[
                          { label: "ROE>-10% 완화", on: true },
                          { label: "부채<400% 완화", on: true },
                          { label: "대장주 13개 보호", on: true },
                          { label: "부실주 제외 규칙", on: dartFilterStatus === "APPLIED" },
                        ].map((f,i) => (
                          <span key={i} className={`text-xs px-2.5 py-1 rounded-full border font-mono ${f.on ? "bg-emerald-50 border-emerald-200 text-emerald-700" : "bg-slate-50 border-slate-200 text-slate-400"}`}>{f.label}</span>
                        ))}
                      </div>
                    </div>

                    {filteredPicks.length === 0 ? (
                      <div className="rounded-2xl border bg-white p-6 text-center text-sm text-slate-400">{weeklyPicks.length === 0 ? "추천 데이터가 없습니다. factor_snapshots.weeklyPicks 적재 후 표시됩니다." : "선택한 산업/팩터 조건에 맞는 추천이 없습니다."}</div>
                    ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5">
                      {filteredPicks.map((p) => {
                        const ind = industries.find((i) => i.id === p.industryId) || industries[0];
                        return (
                          <div key={`${p.industryId}-${p.ticker}`} className={`pick-card ${p.industryId} card-hover`}>
                            <div className="p-4">
                              <div className="flex items-center justify-between">
                                <div className="flex items-center gap-2">
                                  <span className="w-8 h-8 rounded-lg flex items-center justify-center text-sm font-bold" style={{ background: `${ind.color}15`, color: ind.color }}>{ind?.icon}</span>
                                  <span className="text-xs font-bold px-2 py-1 rounded-full" style={{ background: `${ind.color}10`, color: ind.color }}>{ind?.short}</span>
                                  <span className="text-xs font-mono px-2 py-1 rounded-full bg-slate-100 border text-slate-600">{p.ticker}</span>
                                </div>
                                <span className="text-xs font-mono font-bold px-2.5 py-1 rounded-full text-white" style={{ background: `linear-gradient(135deg, ${ind.color} 0%, ${ind.color}cc 100%)` }}>Score {p.score}</span>
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
                    )}
                  </div>
                )}

                {activeTab === "top" && (
                  <div className="mt-4 space-y-4">
                    <div className="rounded-2xl bg-white border border-slate-200 p-4">
                      <h3 className="text-sm font-bold flex items-center gap-2">📊 오늘 Top 예측 (α·β) • 8개 업종 랭킹</h3>
                      <div className="mt-1 text-xs text-slate-500">예측수익률 기준 정렬 • Top1이 오늘 최강 업종 • 클릭하면 해당 업종 필터</div>
                      <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-3">
                        {industries.map((ind) => ({ ...ind, pred: Object.entries(ind.betas).reduce((s,[f,b]) => s + (zScores[f] ?? 0)*b, 0) })).sort((a,b) => b.pred - a.pred).map((item, idx) => {
                          const isSelected = item.id === selectedIndustry;
                          const isTop = idx === 0;
                          return (
                            <div key={item.id} onClick={() => setSelectedIndustry(item.id)} className={`flex items-center justify-between p-3 rounded-xl cursor-pointer transition-all border ${isSelected ? "bg-[#1e3a8a] text-white border-[#1e3a8a]" : "bg-slate-50 hover:bg-white border-slate-200"}`}>
                              <div className="flex items-center gap-3">
                                <span className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold ${isTop ? "bg-amber-400 text-[#1e3a8a]" : isSelected ? "bg-white text-[#1e3a8a]" : "bg-white border"}`}>{idx+1}</span>
                                <div className="w-8 h-8 rounded-lg flex items-center justify-center text-sm font-bold" style={{ background: isSelected ? "rgba(255,255,255,0.15)" : `${item.color}15`, color: isSelected ? "white" : item.color }}>{item.icon}</div>
                                <div><div className="text-sm font-bold">{item.short}</div><div className={`text-xs ${isSelected ? "text-white/60" : "text-slate-500"}`}>R² {industryR2(item.id)} • {item.name}</div></div>
                              </div>
                              <div className="text-right">
                                <div className={`text-sm font-mono font-bold ${hasZScores ? (item.pred>=0 ? (isSelected ? "text-emerald-300" : "text-emerald-600") : (isSelected ? "text-red-300" : "text-red-600")) : "text-slate-400"}`}>{fmtPred(item.pred)}</div>
                                <div className={`text-xs ${isSelected ? "text-white/50" : "text-slate-400"}`}>{isTop ? "👑 최강" : `${idx+1}위`}</div>
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  </div>
                )}

                {activeTab === "all64" && (
                  <div className="mt-4 space-y-4">
                    <div className="rounded-2xl p-5 text-white" style={{ background: "linear-gradient(135deg, #1e3a8a 0%, #1e293b 50%, #334155 100%)" }}>
                      <div className="flex items-center justify-between"><h3 className="text-base font-extrabold">📋 전체 64종 • 8×8 Industry 전체 보기</h3><span className="px-3 py-1 rounded-full bg-white/15 text-xs font-mono">{all64Filtered.length}종 {selectedFactor ? `• ${selectedFactor} 필터` : ""}</span></div>
                      <div className="mt-2 text-xs text-slate-300">왼쪽 산업 선택 + 오른쪽 팩터 선택으로 필터링 • Score 높은 순 • 트레이더 스캔용</div>
                      <div className="mt-3 grid grid-cols-4 gap-2">
                        {industries.map(ind => {
                          const cnt = all64Filtered.filter(p => p.industryId === ind.id).length;
                          return <div key={ind.id} className="rounded-xl bg-white/10 border border-white/10 p-2 text-center"><div className="text-xs font-bold" style={{ color: ind.color }}>{ind.short}</div><div className="text-xs font-mono text-white">{cnt}종</div></div>;
                        })}
                      </div>
                    </div>
                    {all64Filtered.length === 0 ? (
                      <div className="rounded-2xl border bg-white p-6 text-center text-sm text-slate-400">전체 추천 데이터가 없습니다.</div>
                    ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                      {all64Filtered.slice(0,32).map((p) => {
                        const ind = industries.find(i => i.id === p.industryId) || industries[0];
                        return (
                          <div key={`${p.industryId}-${p.ticker}-all`} className="rounded-xl border bg-white p-3 hover: transition-shadow">
                            <div className="flex items-center justify-between"><span className="text-xs font-bold px-2 py-0.5 rounded-full text-white" style={{ background: ind.color }}>{ind.short}</span><span className="text-xs font-mono">{p.ticker}</span><span className="text-xs font-bold">Score {p.score}</span></div>
                            <div className="mt-2 text-sm font-bold">{p.name}</div>
                            <div className="text-xs text-slate-500 font-mono">{p.reason}</div>
                          </div>
                        );
                      })}
                    </div>
                    )}
                    <div className="text-xs text-center text-slate-400">전체 {all64Filtered.length}종 중 32종 표시 • 전체 보기는 스크롤</div>
                  </div>
                )}

                {activeTab === "performance" && (
                  <div className="mt-4 space-y-4">
                    <div className="rounded-2xl border bg-white overflow-hidden" style={{ borderColor: "#e2e8f0" }}>
                      <div className="p-4 border-b bg-gradient-to-r from-violet-50 to-purple-50">
                        <div className="flex items-center justify-between"><h3 className="text-sm font-extrabold">📈 최근 성과 • {currentIndustry.short}</h3><span className="text-xs font-mono px-2 py-1 rounded-full bg-violet-600 text-white">Hit {pastPicksAvg.hit}/{pastPicksAvg.total} • Avg {pastPicksAvg.avg}%</span></div>
                        <div className="mt-1 text-xs text-slate-500">performance_tracking 기반 • vs KOSPI 초과 수익 • {performanceSummary?.source || "실제 종가 데이터"}</div>
                      </div>
                      <div className="p-3 grid grid-cols-3 gap-3">
                        <div className="rounded-xl bg-slate-50 border p-3 text-center"><div className="text-xs text-slate-500">평균 수익</div><div className={`text-sm font-bold ${parseFloat(pastPicksAvg.avg)>=0 ? "text-emerald-600" : "text-red-600"}`}>{pastPicksAvg.avg}%</div></div>
                        <div className="rounded-xl bg-slate-50 border p-3 text-center"><div className="text-xs text-slate-500">vs KOSPI</div><div className={`text-sm font-bold ${parseFloat(pastPicksAvg.vsKospi)>=0 ? "text-emerald-600" : "text-red-600"}`}>{pastPicksAvg.vsKospi>0 ? "+" : ""}{pastPicksAvg.vsKospi}%</div></div>
                        <div className="rounded-xl bg-slate-50 border p-3 text-center"><div className="text-xs text-slate-500">Hit Rate</div><div className="text-sm font-bold">{pastPicksAvg.total ? `${pastPicksAvg.hit}/${pastPicksAvg.total} (${(pastPicksAvg.hitRate*100).toFixed(0)}%)` : "—"}</div></div>
                      </div>
                      {pastPicks.length === 0 ? (
                        <div className="p-6 text-center text-sm text-slate-400">성과 데이터가 없습니다. performance_tracking 적재 후 표시됩니다.</div>
                      ) : (
                      <div className="p-3 grid grid-cols-1 md:grid-cols-2 gap-2">
                        {pastPicks.map((r) => (
                          <div key={`${r.recDate || r.evalDate}-${r.ticker}`} className="flex items-center justify-between p-2.5 rounded-xl border bg-white hover:bg-slate-50">
                            <div className="flex items-center gap-2"><span className="text-xs font-mono px-2 py-0.5 rounded-full bg-slate-100">{r.ticker}</span><span className="text-sm font-bold">{r.name}</span><span className={`text-xs px-1.5 py-0.5 rounded-full ${r.status==="성공" ? "bg-emerald-100 text-emerald-700" : r.status==="보류" ? "bg-amber-100 text-amber-700" : "bg-red-100 text-red-700"}`}>{r.status}</span></div>
                            <div className="flex items-center gap-3"><span className={`text-xs font-mono font-bold ${r.returnPct>=0 ? "text-emerald-600" : "text-red-600"}`}>{r.returnPct>0 ? "+" : ""}{r.returnPct}%</span><span className="text-xs text-slate-400">vs {r.vsKospi>0 ? "+" : ""}{r.vsKospi}%</span></div>
                          </div>
                        ))}
                      </div>
                      )}
                    </div>

                    <div className="rounded-2xl bg-white border border-slate-200 p-4">
                      <h4 className="text-sm font-extrabold">📊 성과 IC • Factor Validity • Hit Rate</h4>
                      <div className="mt-3 grid grid-cols-2 gap-3">
                        <div className="p-3 rounded-xl bg-violet-50 border border-violet-200"><div className="text-xs text-violet-700">평균 Hit Rate</div><div className="text-lg font-extrabold text-violet-900">{icStats.avgHit == null ? "N/A" : `${icStats.avgHit.toFixed(1)}%`}</div><div className="text-xs text-violet-600">meta_summaries/{metaSummary?.date || "—"}</div></div>
                        <div className="p-3 rounded-xl bg-emerald-50 border border-emerald-200"><div className="text-xs text-emerald-700">평균 IC</div><div className="text-lg font-extrabold text-emerald-900">{icStats.avgIc == null ? "N/A" : icStats.avgIc.toFixed(3)}</div><div className="text-xs text-emerald-600">{icStats.count} factors</div></div>
                      </div>
                      <div className="mt-3 grid grid-cols-1 md:grid-cols-2 gap-2">
                        {icStats.top.length === 0 ? (
                          <div className="col-span-2 p-4 text-center text-sm text-slate-400">factor_validity / meta_summaries 데이터가 없습니다.</div>
                        ) : icStats.top.map((f, i) => {
                          const hit = f.hit_rate_pct ?? (typeof f.hit_rate === "number" ? f.hit_rate * 100 : null);
                          return (
                            <div key={`${f.factor}-${i}`} className="flex items-center justify-between p-2 rounded-lg bg-slate-50 border">
                              <span className="text-xs font-bold flex items-center gap-1.5">
                                <span className="w-2 h-2 rounded-full bg-violet-500"></span>
                                {i+1}. {f.factor}
                              </span>
                              <span className="text-xs font-mono px-2 py-0.5 rounded-full bg-white border">IC {f.ic.toFixed(3)} • Hit {hit == null ? "N/A" : `${hit.toFixed(1)}%`}</span>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  </div>
                )}

                {activeTab === "market" && (
                  <div className="mt-4 space-y-4">
                    {!currentRegime ? (
                      <div className="rounded-2xl border bg-white p-6 text-center text-sm text-slate-400">레짐 데이터가 없습니다. regime snapshot 적재 후 표시됩니다.</div>
                    ) : (
                    <div className="rounded-2xl p-4 text-white" style={{ background: "linear-gradient(135deg, #1e3a8a 0%, #1e293b 100%)" }}>
                      <div className="flex items-center justify-between"><h3 className="text-sm font-extrabold">🌐 마켓 레짐 • Regime Dashboard</h3><span className={`px-3 py-1 rounded-full text-xs font-bold ${(currentRegime.regime==="normal" || currentRegime.regime==="평시") ? "bg-emerald-500" : (currentRegime.regime==="caution" || currentRegime.regime==="고변동") ? "bg-amber-500" : "bg-red-500"} text-white`}>{currentRegime.regime || "N/A"} • {regimeWindow}일 윈도우</span></div>
                      <div className="mt-2 text-xs text-slate-300">{currentRegime.date || selectedDate} 기준 • data_status {currentRegime.data_status || "UNKNOWN"}</div>
                      <div className="mt-4 grid grid-cols-4 gap-2">
                        {[
                          { label: "VIX", value: fmtNum(regimeIndicators.VIX ?? currentRegime.vix), threshold: 22 },
                          { label: "OVX", value: fmtNum(regimeIndicators.OVX ?? currentRegime.ovx), threshold: 50 },
                          { label: "DXY", value: fmtNum(regimeIndicators.DXY ?? currentRegime.dxy), threshold: 105 },
                          { label: "WTI vol", value: regimeIndicators.WTI_vol != null ? `${fmtNum(regimeIndicators.WTI_vol)}%` : "—", threshold: "4%" },
                        ].map((m) => (
                          <div key={m.label} className="rounded-xl bg-white/10 border border-white/10 p-2.5 text-center"><div className="text-xs text-slate-400">{m.label}</div><div className="text-sm font-bold">{m.value}</div><div className="text-xs text-slate-400">임계 {m.threshold}</div></div>
                        ))}
                      </div>
                      <div className="mt-3 text-xs text-slate-400">{regimeDescription}</div>
                    </div>
                    )}

                    <div className="rounded-2xl bg-white border border-slate-200 p-4">
                      <h4 className="text-sm font-extrabold">📈 모델 + Meta 유효 통합</h4>
                      <div className="mt-3 grid grid-cols-2 gap-3">
                        <div className="p-3 rounded-xl bg-slate-50 border"><div className="text-xs text-slate-500">KOSPI α·β 추정</div><div className="text-sm font-bold">{hasZScores ? `${predText} α·β` : "—"}</div><div className="text-xs text-slate-400">평균 R² {fmtNum(retrainData?.avg_r2, 3)} • {retrainData?.version || "retrain N/A"}</div></div>
                        <div className="p-3 rounded-xl bg-emerald-50 border border-emerald-200"><div className="text-xs text-emerald-700">Meta 유효 팩터</div><div className="text-sm font-bold">{icStats.count}개 유효</div><div className="text-xs text-emerald-600">meta {metaSummary?.date || activeSnapshot?.meta?.date || "N/A"}</div></div>
                      </div>
                      <div className="mt-3 p-2.5 rounded-xl bg-slate-50 border text-xs font-mono text-slate-500">
                        <div className="font-bold text-slate-600 mb-1">운영 메타데이터</div>
                        <div>snapshot {activeSnapshot?.date || "—"} • data_status {activeSnapshot?.data_status || "NO_DATA"} • quality_status {activeSnapshot?.quality_status || "—"}</div>
                        <div>fallback_used={String(Boolean(activeSnapshot?.fallback_used))} • synthetic_data_used={String(Boolean(activeSnapshot?.synthetic_data_used))} • filter_applied={String(Boolean(activeSnapshot?.filter_applied))}</div>
                        <div>app_version {activeSnapshot?.app_version || "—"} • model_version {activeSnapshot?.model_version || "—"} • data_policy {activeSnapshot?.data_policy || "—"}</div>
                      </div>
                      <div className="mt-3 grid grid-cols-1 md:grid-cols-2 gap-2">
                        {contributions.slice(0,5).map((c) => (
                          <div key={c.factor} className="flex items-center justify-between p-2 rounded-lg bg-slate-50 border"><span className="text-xs font-bold">{c.factor}</span><span className="text-xs font-mono">{c.z>0 ? "+" : ""}{c.z.toFixed(2)}σ × β{c.beta.toFixed(2)} = {fmtPred(c.contrib)}</span></div>
                        ))}
                      </div>
                    </div>
                  </div>
                )}

                </main>

              <aside className="col-span-12 lg:col-span-4 space-y-4 lg:sticky lg:top-[88px] lg:h-[calc(100vh-6rem)] lg:overflow-auto">
                {/* 헤더에서 이동된 외국인, US10Y */}
                <div className="grid grid-cols-2 gap-2">
                  <div className="rounded-xl bg-white border border-slate-200 p-3">
                    <div className="text-xs text-slate-500">외국인 수급</div>
                    <div className="mt-1 text-sm font-bold">{foreignerDetail.latest != null ? `${Math.round(foreignerDetail.latest/100)}억` : "—"} <span className="text-xs text-slate-500">Z {fmtNum(foreignerDetail.z)}</span></div>
                    <div className="text-xs text-slate-400">{foreignerDetail.latest_date || "KOSPI market • pykrx CSV"} • {foreignerDetail.data_status || "N/A"}</div>
                  </div>
                  <div className="rounded-xl bg-white border border-slate-200 p-3">
                    <div className="text-xs text-slate-500">US 10Y / DXY</div>
                    <div className="mt-1 text-sm font-bold">{fmtNum(us10yDetail.latest, 2)}% <span className="text-xs text-slate-500">Z {fmtNum(us10yDetail.z)}</span></div>
                    <div className="text-xs text-slate-400">DXY {fmtNum(dxyDetail.latest, 2)} • {us10yDetail.data_status || "N/A"}</div>
                  </div>
                </div>
                <div className="rounded-2xl border bg-white p-4">
                  <div className="flex items-center justify-between"><h3 className="text-sm font-bold">오늘의 팩터</h3><span className="text-xs text-slate-400">{selectedDate}</span></div>
                  {selectedFactor && <button onClick={() => setSelectedFactor(null)} className="mt-2 w-full text-xs py-1.5 rounded-full bg-[#1e3a8a] text-white hover:bg-[#23408e]">✕ {selectedFactor} 필터 해제 • 전체 보기</button>}
                  <div className="mt-4">
                    <div className="grid grid-cols-12 text-xs font-mono text-slate-400 pb-2 border-b font-bold tracking-widest"><div className="col-span-6">FACTOR</div><div className="col-span-2 text-right">Z</div><div className="col-span-2 text-right">β</div><div className="col-span-2 text-right">기여도</div></div>
                    {contributions.map((c) => {
                      const zAbs = Math.abs(c.z);
                      const zCls = zAbs > 1 ? (c.z > 0 ? "z-strong-pos" : "z-strong-neg") : c.z > 0 ? "z-pos" : c.z < 0 ? "z-neg" : "z-neutral";
                      const isSelected = selectedFactor === c.factor;
                      return (
                        <div key={c.factor} onClick={() => setSelectedFactor(isSelected ? null : c.factor)} className={`grid grid-cols-12 py-3 border-b border-slate-50 items-center hover:bg-slate-50/80 rounded-lg px-1 transition-colors cursor-pointer ${isSelected ? "bg-emerald-50 border-emerald-200" : ""}`}>
                          <div className="col-span-6"><div className="text-sm font-bold tracking-tight flex items-center gap-1.5">{c.factor} {isSelected && <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>}</div><div className="text-xs text-slate-500">{factorMeta[c.factor]?.desc || ""}</div></div>
                          <div className="col-span-2 text-right"><span className={`z-badge ${zCls}`}>{c.z>0 ? "+" : ""}{c.z.toFixed(2)}</span>{(() => { const d = zDelta(c.factor); return d != null && Math.abs(d) >= 0.05 ? <div className={`text-xs font-mono ${d>0 ? "text-emerald-600" : "text-red-600"}`}>{d>0 ? "▲" : "▼"}{Math.abs(d).toFixed(2)}</div> : null; })()}</div>
                          <div className="col-span-2 text-right font-mono text-xs font-semibold text-slate-600">{c.beta>0 ? "+" : ""}{c.beta.toFixed(2)}</div>
                          <div className={`col-span-2 text-right font-mono text-xs font-bold ${hasZScores ? (c.contrib>=0 ? "text-emerald-600" : "text-red-600") : "text-slate-400"}`}>{fmtPred(c.contrib)}</div>
                        </div>
                      );
                    })}
                  </div>
                  <div className="mt-3 p-2.5 rounded-xl bg-blue-50 border border-blue-200 text-xs text-blue-800">💡 오른쪽 팩터 클릭 → 중앙 추천 8종 필터링 • 예) 구리 클릭 → 구리 민감 종목만 표시</div>
                </div>

                </aside>
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
