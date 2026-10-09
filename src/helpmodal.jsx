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
                  <div className="text-xs font-mono text-slate-500 mt-1">v62.0 Factor Clusters • 5 Tabs • Left-Right 필터 • 07:30 KST 자동 업데이트</div>
                </div>
                <button onClick={onClose} className="w-9 h-9 rounded-full bg-[#1e3a8a] text-white hover:bg-[#23408e] btn-modern">✕</button>
              </div>
              <div className="mt-6 space-y-5 text-sm">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                  <div className="p-3 rounded-xl bg-[#1e3a8a] text-white"><div className="text-xs font-bold">1. 왼쪽 FACTOR CLUSTERS</div><div className="text-xs mt-1 text-slate-300">8개 클러스터 선택 → 중앙 필터 • R² 0.79~0.93 • 달러+2 0.93 최고 • K-means k=8 (Silhouette 0.0907)</div></div>
                  <div className="p-3 rounded-xl bg-white border"><div className="text-xs font-bold">2. 중앙 5 Tabs</div><div className="text-xs mt-1 text-slate-600">추천(8) / 전체64 / 성과 / 마켓 / 시스템 • Factor Beta 바 • 190종 KOSPI200</div></div>
                  <div className="p-3 rounded-xl bg-white border"><div className="text-xs font-bold">3. 오른쪽 FACTOR</div><div className="text-xs mt-1 text-slate-600">Z-Score 클릭 → 중앙 필터링 • 10 Factors (SP500, 외국인, SOX, US10Y, 원달러, WTI, DXY, VIX, 구리, 상해)</div></div>
                </div>
                <div className="p-3 rounded-xl bg-blue-50 border border-blue-200 text-xs leading-relaxed">
                  <div className="font-bold text-blue-900">💡 트레이더 사용법</div>
                  <div className="mt-1 text-slate-700">• 왼쪽 클러스터 클릭: 해당 클러스터 8종 추천 (예: VIX민감 → 변동성 민감 15종 중 Top 8) • 오른쪽 팩터 클릭: 해당 팩터에 민감한 종목만 필터 (예: 구리 클릭 → 구리 β 높은 클러스터 위주) • DART ON/OFF: 부실주 제거 필터 • 07:30 체크리스트 4개 모두 ✓여야 신뢰도 높음 • KOSPI200 190종 + GICS + KRICS pending 2026-10-26</div>
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
