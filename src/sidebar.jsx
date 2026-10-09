function Sidebar({ selectedIndustry, setSelectedIndustry, industries, zScores }) {
  const inds = typeof industries !== "undefined" ? industries : (typeof window !== 'undefined' && window.industries) ? window.industries : [];
  return (
    <aside className="col-span-12 md:col-span-2 space-y-4 md:sticky md:top-[88px] md:h-[calc(100vh-6rem)] md:overflow-auto">
      <div className="rounded-2xl bg-[#e0f2fe] text-[#0c4a6e] p-4 border border-[#bae6fd]">
        <div className="flex items-center justify-between"><h3 className="text-xs font-bold tracking-widest text-[#0369a1]">FACTOR CLUSTERS • 8</h3><span className="w-2 h-2 rounded-full bg-[#0ea5e9] animate-pulse"></span></div>
        <div className="mt-1 text-xs text-[#0284c7]">클러스터 선택 • 중앙 필터 • v62</div>
        <div className="mt-4 space-y-2">
          {inds.map((ind) => {
            const isSelected = ind.id === selectedIndustry;
            const fm = (typeof factorMeta !== 'undefined' ? factorMeta : (typeof window !== 'undefined' ? window.factorMeta : {})) || {};
            const pred = Object.entries(ind.betas || ind.avg_betas || {}).reduce((s, [f, b]) => {
              const z = zScores[f] ?? fm[f]?.label ? (zScores[fm[f]?.label] ?? 0) : 0;
              const actualZ = zScores[f] ?? 0;
              return s + b * actualZ;
            }, 0);
            return (
              <button key={ind.id} onClick={() => setSelectedIndustry(ind.id)} className={`w-full flex items-center justify-between px-3 py-2.5 rounded-xl transition-all text-left border ${isSelected ? "bg-white text-[#0c4a6e] border-[#7dd3fc]" : "bg-white/70 hover:bg-white text-[#475569] border-white/50 hover:border-[#7dd3fc]"}`}>
                <div className="flex items-center gap-2.5"><div className="w-8 h-8 rounded-lg flex items-center justify-center text-sm font-bold" style={{ background: `${(ind?.color || '#3182f6')}15`, color: (ind?.color || '#3182f6') }}>{(ind?.icon || '◫')}</div><div><div className="text-xs font-bold">{(ind?.short || ind?.id || 'FC')}</div><div className="text-xs text-slate-500">R² {(ind?.r2 || 0.8)}</div></div></div>
                <div className="text-right"><div className={`text-xs font-mono font-bold ${pred>=0 ? "text-emerald-600" : "text-red-600"}`}>{pred>0 ? "+" : ""}{pred.toFixed(2)}%</div><div className={`w-2 h-2 rounded-full ml-auto mt-1 ${isSelected ? "bg-[#0ea5e9]" : "bg-slate-300"}`}></div></div>
              </button>
            );
          })}
        </div>
        <div className="mt-3 pt-3 border-t border-[#bae6fd] text-xs text-[#0284c7]">Top1이 최강 • 8개 중 선택 • Silhouette 0.0907</div>
      </div>
    </aside>
  );
}
