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
                        className={`w-full text-left rounded-xl border p-3.5 flex items-center justify-between transition-all btn-modern ${isSelected ? "bg-[#1e3a8a] text-white border-[#1e3a8a]" : "bg-white border-slate-200 hover:border-slate-300 hover:bg-slate-50"}`}>
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