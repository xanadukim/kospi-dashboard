function FactorPanel({ selectedDate, selectedFactor, setSelectedFactor, contributions }) {
  const fm = (typeof factorMeta !== 'undefined' ? factorMeta : (typeof window !== 'undefined' ? window.factorMeta : {})) || {};
  return (
    <aside className="col-span-12 lg:col-span-4 space-y-4 lg:sticky lg:top-[88px] lg:h-[calc(100vh-6rem)] lg:overflow-auto">
      <div className="grid grid-cols-2 gap-2">
        <div className="rounded-xl bg-white border border-slate-200 p-3">
          <div className="text-xs text-slate-500">외국인 선물</div>
          <div className="mt-1 text-sm font-bold">1327억 <span className="text-emerald-600">순매수</span></div>
          <div className="text-xs text-slate-400">KOSPI200 • DART • REAL</div>
        </div>
        <div className="rounded-xl bg-white border border-slate-200 p-3">
          <div className="text-xs text-slate-500">US 10Y / DXY</div>
          <div className="mt-1 text-sm font-bold">4.72% <span className="text-xs text-red-500">+0.04</span></div>
          <div className="text-xs text-slate-400">DXY 103.8 • Regime</div>
        </div>
      </div>
      <div className="rounded-2xl border bg-white p-4">
        <div className="flex items-center justify-between"><h3 className="text-sm font-bold">오늘의 팩터 • v62</h3><span className="text-xs text-slate-400">{selectedDate}</span></div>
        {selectedFactor && <button onClick={() => setSelectedFactor(null)} className="mt-2 w-full text-xs py-1.5 rounded-full bg-[#1e3a8a] text-white hover:bg-[#23408e]">✕ {selectedFactor} 필터 해제 • 전체 보기</button>}
        <div className="mt-4">
          <div className="grid grid-cols-12 text-xs font-mono text-slate-400 pb-2 border-b font-bold tracking-widest"><div className="col-span-6">FACTOR</div><div className="col-span-2 text-right">Z</div><div className="col-span-2 text-right">β</div><div className="col-span-2 text-right">기여도</div></div>
          {contributions.map((c) => {
            const zAbs = Math.abs(c.z);
            const zCls = zAbs > 1 ? (c.z > 0 ? "z-strong-pos" : "z-strong-neg") : c.z > 0 ? "z-pos" : c.z < 0 ? "z-neg" : "z-neutral";
            const isSelected = selectedFactor === c.factor;
            return (
              <div key={c.factor} onClick={() => setSelectedFactor(isSelected ? null : c.factor)} className={`grid grid-cols-12 py-3 border-b border-slate-50 items-center hover:bg-slate-50/80 rounded-lg px-1 transition-colors cursor-pointer ${isSelected ? "bg-emerald-50 border-emerald-200" : ""}`}>
                <div className="col-span-6"><div className="text-sm font-bold tracking-tight flex items-center gap-1.5">{c.factor} {isSelected && <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>}</div><div className="text-xs text-slate-500">{fm[c.factor]?.desc || ""}</div></div>
                <div className="col-span-2 text-right"><span className={`z-badge ${zCls}`}>{c.z>0 ? "+" : ""}{c.z.toFixed(2)}</span></div>
                <div className="col-span-2 text-right font-mono text-xs font-semibold text-slate-600">{c.beta>0 ? "+" : ""}{c.beta.toFixed(2)}</div>
                <div className={`col-span-2 text-right font-mono text-xs font-bold ${c.contrib>=0 ? "text-emerald-600" : "text-red-600"}`}>{c.contrib>0 ? "+" : ""}{c.contrib.toFixed(2)}%</div>
              </div>
            );
          })}
        </div>
        <div className="mt-3 p-2.5 rounded-xl bg-blue-50 border border-blue-200 text-xs text-blue-800">💡 오른쪽 팩터 클릭 → 중앙 추천 8종 필터링 • 예) 구리 클릭 → 구리 민감 종목만 표시 • v62 Factor Clusters</div>
      </div>
    </aside>
  );
}
