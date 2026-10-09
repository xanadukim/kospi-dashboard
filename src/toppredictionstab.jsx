function TopPredictionsTab({ activeTab, currentIndustry, predictedReturn, contributions, selectedDate, selectedFactor, setSelectedFactor, filteredPicks, all64Filtered, pastPicks, pastPicksAvg, currentRegime, currentMeta, industries, zScores, filterEnabled }) {
  return (
    <>
                      {activeTab === "top" && (
                  <div className="mt-4 space-y-4">
                    <div className="rounded-2xl bg-white border border-slate-200 p-4">
                      <h3 className="text-sm font-bold flex items-center gap-2">📊 오늘 Top 예측 (α·β) • 8개 클러스터 랭킹</h3>
                      <div className="mt-1 text-xs text-slate-500">예측수익률 기준 정렬 • Top1이 오늘 최강 클러스터 • 클릭하면 해당 클러스터 필터</div>
                      <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-3">
                        {(typeof industries !== "undefined" ? industries : []).map((ind) => ({ ...ind, pred: Object.entries(ind.betas).reduce((s,[f,b]) => s + (zScores[f] ?? 0)*b, 0) })).sort((a,b) => b.pred - a.pred).map((item, idx) => {
                          const isSelected = item.id === selectedIndustry;
                          const isTop = idx === 0;
                          return (
                            <div key={item.id} onClick={() => setSelectedIndustry(item.id)} className={`flex items-center justify-between p-3 rounded-xl cursor-pointer transition-all border ${isSelected ? "bg-[#1e3a8a] text-white border-[#1e3a8a]" : "bg-slate-50 hover:bg-white border-slate-200"}`}>
                              <div className="flex items-center gap-3">
                                <span className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold ${isTop ? "bg-amber-400 text-[#1e3a8a]" : isSelected ? "bg-white text-[#1e3a8a]" : "bg-white border"}`}>{idx+1}</span>
                                <div className="w-8 h-8 rounded-lg flex items-center justify-center text-sm font-bold" style={{ background: isSelected ? "rgba(255,255,255,0.15)" : `${(item?.color || '#3182f6')}15`, color: isSelected ? "white" : (item?.color || '#3182f6') }}>{item.icon}</div>
                                <div><div className="text-sm font-bold">{item.short}</div><div className={`text-xs ${isSelected ? "text-white/60" : "text-slate-500"}`}>R² {item.r2} • {item.name}</div></div>
                              </div>
                              <div className="text-right">
                                <div className={`text-sm font-mono font-bold ${item.pred>=0 ? (isSelected ? "text-emerald-300" : "text-emerald-600") : (isSelected ? "text-red-300" : "text-red-600")}`}>{item.pred>0 ? "+" : ""}{item.pred.toFixed(2)}%</div>
                                <div className={`text-xs ${isSelected ? "text-white/50" : "text-slate-400"}`}>{isTop ? "👑 최강" : `${idx+1}위`}</div>
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  </div>
                )}
    </>
  );
}
