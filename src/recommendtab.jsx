function RecommendTab({ activeTab, currentIndustry, predictedReturn, contributions, selectedDate, selectedFactor, setSelectedFactor, filteredPicks, all64Filtered, pastPicks, pastPicksAvg, currentRegime, currentMeta, industries, zScores, filterEnabled }) {
  return (
    <>
                      {activeTab === "recommend" && (
                  <div className="mt-4 space-y-4">
                    <div className="rounded-2xl p-4 text-white" style={{ background: `linear-gradient(135deg, ${(currentIndustry?.color || '#1e3a8a')} 0%, ${(currentIndustry?.color || '#1e3a8a')}dd 100%)` }}>
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

                    <div className="rounded-2xl bg-white border border-slate-200 p-3">
                      <div className="flex items-center justify-between flex-wrap gap-2">
                        <div className="flex items-center gap-2"><span className="w-7 h-7 rounded-lg bg-red-50 border border-red-100 flex items-center justify-center">🛡️</span><span className="text-xs font-bold">DART 필터 • 1단계 최적 필터</span><span className="text-xs font-mono text-slate-500">부실주 제거 • 개별 기업 특성 기반</span></div>
                        <div className="flex items-center gap-2">
                          <button onClick={() => setFilterEnabled(!filterEnabled)} className={`text-xs px-3 py-1.5 rounded-full font-bold transition-all ${filterEnabled ? "bg-emerald-600 text-white" : "bg-slate-100 text-slate-500"}`}>{filterEnabled ? "ON • Hit +4.4%p" : "OFF"}</button>
                          
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
                        const ind = (typeof industries !== 'undefined' ? industries : []).find((i) => i.id === p.industryId) || { color: '#3182f6', grad: 'grad-elec', icon: '◫', short: p.industryId, r2: 0.8, name: p.industryId };
                        return (
                          <div key={`${p.industryId}-${p.ticker}`} className={`pick-card ${p.industryId} card-hover`}>
                            <div className="p-4">
                              <div className="flex items-center justify-between">
                                <div className="flex items-center gap-2">
                                  <span className="w-8 h-8 rounded-lg flex items-center justify-center text-sm font-bold" style={{ background: `${(ind?.color || '#3182f6')}15`, color: (ind?.color || '#3182f6') }}>{ind?.icon}</span>
                                  <span className="text-xs font-bold px-2 py-1 rounded-full" style={{ background: `${(ind?.color || '#3182f6')}10`, color: (ind?.color || '#3182f6') }}>{ind?.short}</span>
                                  <span className="text-xs font-mono px-2 py-1 rounded-full bg-slate-100 border text-slate-600">{p.ticker}</span>
                                </div>
                                <span className="text-xs font-mono font-bold px-2.5 py-1 rounded-full text-white" style={{ background: `linear-gradient(135deg, ${(ind?.color || '#3182f6')} 0%, ${(ind?.color || '#3182f6')}cc 100%)` }}>Score {p.score}</span>
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
    </>
  );
}
