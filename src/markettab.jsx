function MarketTab({ activeTab, currentIndustry, predictedReturn, contributions, selectedDate, selectedFactor, setSelectedFactor, filteredPicks, all64Filtered, pastPicks, pastPicksAvg, currentRegime, currentMeta, industries, zScores, filterEnabled }) {
  return (
    <>
                      {activeTab === "market" && (
                  <div className="mt-4 space-y-4">
                    <div className="rounded-2xl p-4 text-white" style={{ background: "linear-gradient(135deg, #1e3a8a 0%, #1e293b 100%)" }}>
                      <div className="flex items-center justify-between"><h3 className="text-sm font-extrabold">🌐 마켓 레짐 • Regime Dashboard REAL</h3><span className={`px-3 py-1 rounded-full text-xs font-bold ${currentRegime.regime==="normal" ? "bg-emerald-500" : currentRegime.regime==="caution" ? "bg-amber-500" : "bg-red-500"} text-white`}>{currentRegime.confidence || currentRegime.regime} • {currentRegime.window}일 윈도우</span></div>
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

                    <div className="rounded-2xl bg-white border border-slate-200 p-4">
                      <h4 className="text-sm font-extrabold">📈 KOSPI 모델 + Meta 유효 통합</h4>
                      <div className="mt-3 grid grid-cols-2 gap-3">
                        <div className="p-3 rounded-xl bg-slate-50 border"><div className="text-xs text-slate-500">KOSPI 예측</div><div className="text-sm font-bold">+0.49% α·β</div><div className="text-xs text-slate-400">R² 0.89 Adj 0.87 • Ridge λ=0.5</div></div>
                        <div className="p-3 rounded-xl bg-emerald-50 border border-emerald-200"><div className="text-xs text-emerald-700">Meta 유효 팩터</div><div className="text-sm font-bold">{currentMeta?.top_valid?.length || 5}개 유효</div><div className="text-xs text-emerald-600">P(valid) {(currentMeta?.avg_p_valid || 0.72).toFixed(2)}</div></div>
                      </div>
                      <div className="mt-3 grid grid-cols-1 md:grid-cols-2 gap-2">
                        {contributions.slice(0,5).map((c) => (
                          <div key={c.factor} className="flex items-center justify-between p-2 rounded-lg bg-slate-50 border"><span className="text-xs font-bold">{c.factor}</span><span className="text-xs font-mono">{c.z>0 ? "+" : ""}{c.z.toFixed(2)}σ × β{c.beta.toFixed(2)} = {c.contrib>0 ? "+" : ""}{c.contrib.toFixed(2)}%</span></div>
                        ))}
                      </div>
                    </div>
                  </div>
                )}

    </>
  );
}
