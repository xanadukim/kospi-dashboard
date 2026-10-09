function Header({ activeTab, setActiveTab, filteredPicks, all64Filtered, pastPicks, currentMeta, predictedReturn, isViewingHistory, returnToLatest, history, setShowHistory, setShowDisclaimer, setShowHelp }) {
  return (
    <header className="sticky top-0 z-30" style={{ background: "white", borderBottom: "1px solid #e5e8eb", height: "72px" }}>
      <div className="max-w-screen-2xl mx-auto px-4 md:px-6 h-[72px] flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg flex items-center justify-center font-extrabold text-xs" style={{ background: "#3182f6", color: "white" }}>KQ</div>
          <div className="text-sm font-bold" style={{color: "#1e3a8a"}}>KOSPI Quant Terminal <span className="text-xs font-normal text-slate-500 ml-1">v62.0 FINAL</span></div>
        </div>
        <div className="flex items-center gap-3">
          <div className="hidden xl:flex items-center gap-1 p-1 rounded-full bg-[#f1f5f9] border border-[#e5e8eb]">
            {[
              { id: "recommend", label: "추천", icon: "🎯", count: filteredPicks?.length || 8, color: "#1e3a8a" },
              { id: "top", label: "오늘 Top 예측", icon: "📊", count: 8, color: "#f59e0b" },
              { id: "all64", label: "전체 64", icon: "📋", count: all64Filtered?.length || 64, color: "#334155" },
              { id: "performance", label: "성과", icon: "📈", count: pastPicks?.length || 8, color: "#7c3aed" },
              { id: "market", label: "마켓", icon: "🌐", count: currentMeta?.top_valid?.length || 5, color: "#059669" },
            ].map((tab) => (
              <button key={tab.id} onClick={() => setActiveTab(tab.id)}
                className={`px-3.5 py-1.5 rounded-full text-xs font-bold flex items-center gap-1.5 transition-all ${activeTab === tab.id ? "text-white" : "text-slate-600 hover:bg-white"}`}
                style={activeTab === tab.id ? { background: tab.color } : {}}>
                <span>{tab.icon}</span> {tab.label} <span className={`ml-1 px-1.5 py-0.5 rounded-full text-xs font-mono ${activeTab === tab.id ? "bg-white/20" : "bg-white border"}`}>{tab.count}</span>
              </button>
            ))}
          </div>
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-white border border-[#e5e8eb]">
            <span className="text-xs text-slate-500">KOSPI R²</span>
            <span className="text-sm font-bold">0.89</span>
            <span className={`text-xs font-mono px-2 py-0.5 rounded-full border ${predictedReturn>=0 ? "bg-emerald-50 text-emerald-700 border-emerald-100" : "bg-red-50 text-red-700 border-red-100"}`}>{predictedReturn>0 ? `+${predictedReturn.toFixed(2)}%` : `${predictedReturn.toFixed(2)}%`}</span>
          </div>
          {isViewingHistory && <button onClick={returnToLatest} className="px-3 py-1.5 rounded-lg text-xs font-bold bg-amber-100 text-amber-800 border border-amber-200">↩ 최신으로</button>}
          <button onClick={() => setShowHistory(true)} className={`px-3 py-1.5 rounded-lg text-xs font-bold border ${isViewingHistory ? "bg-amber-50 text-amber-700 border-amber-200" : "bg-white text-slate-600 border-[#e5e8eb] hover:bg-slate-50"}`}>📅 이전 자료 {history?.length>0 ? `(${history.length})` : ""}</button>
          <button onClick={() => setShowDisclaimer(true)} className="px-3 py-1.5 rounded-lg text-xs font-bold bg-white text-slate-600 border border-[#e5e8eb] hover:bg-slate-50">면책</button>
          <button onClick={() => setShowHelp(true)} className="px-3.5 py-1.5 rounded-lg text-xs font-bold bg-[#3182f6] text-white hover:bg-[#2b7fff]">도움말</button>
        </div>
      </div>
    </header>
  );
}
