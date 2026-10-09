function All64Tab({ activeTab, currentIndustry, predictedReturn, contributions, selectedDate, selectedFactor, setSelectedFactor, filteredPicks, all64Filtered, pastPicks, pastPicksAvg, currentRegime, currentMeta, industries, zScores, filterEnabled }) {
  return (
    <>
                      {activeTab === "all64" && (
                  <div className="mt-4 space-y-4">
                    <div className="rounded-2xl p-5 text-white" style={{ background: "linear-gradient(135deg, #1e3a8a 0%, #1e293b 50%, #334155 100%)" }}>
                      <div className="flex items-center justify-between"><h3 className="text-base font-extrabold">📋 전체 64종 • 8×8 Industry 전체 보기</h3><span className="px-3 py-1 rounded-full bg-white/15 text-xs font-mono">{all64Filtered.length}종 {selectedFactor ? `• ${selectedFactor} 필터` : ""}</span></div>
                      <div className="mt-2 text-xs text-slate-300">왼쪽 산업 선택 + 오른쪽 팩터 선택으로 필터링 • Score 높은 순 • 트레이더 스캔용</div>
                      <div className="mt-3 grid grid-cols-4 gap-2">
                        {(typeof industries !== "undefined" ? industries : []).map(ind => {
                          const cnt = all64Filtered.filter(p => p.industryId === ind.id).length;
                          return <div key={ind.id} className="rounded-xl bg-white/10 border border-white/10 p-2 text-center"><div className="text-xs font-bold" style={{ color: ind?.color || '#3182f6' }}>{(ind?.short || ind?.id || 'FC')}</div><div className="text-xs font-mono text-white">{cnt}종</div></div>;
                        })}
                      </div>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                      {all64Filtered.slice(0,32).map((p) => {
                        const ind = (typeof industries !== 'undefined' ? industries : []).find(i => i.id === p.industryId) || { color: '#3182f6', grad: 'grad-elec', icon: '◫', short: p.industryId, r2: 0.8, name: p.industryId };
                        return (
                          <div key={`${p.industryId}-${p.ticker}-all`} className="rounded-xl border bg-white p-3 hover: transition-shadow">
                            <div className="flex items-center justify-between"><span className="text-xs font-bold px-2 py-0.5 rounded-full text-white" style={{ background: ind?.color || '#3182f6' }}>{(ind?.short || ind?.id || 'FC')}</span><span className="text-xs font-mono">{p.ticker}</span><span className="text-xs font-bold">Score {p.score}</span></div>
                            <div className="mt-2 text-sm font-bold">{p.name}</div>
                            <div className="text-xs text-slate-500 font-mono">{p.reason}</div>
                          </div>
                        );
                      })}
                    </div>
                    <div className="text-xs text-center text-slate-400">전체 {all64Filtered.length}종 중 32종 표시 • 전체 보기는 스크롤</div>
                  </div>
                )}
    </>
  );
}
