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
                    모든 투자 결정은 본인 판단과 책임 하에 이루어져야 하며, 원금 손실이 발생할 수 있습니다. 본 모델의 R² 0.89는 과거 설명력이며 미래 수익을 보장하지 않습니다.
                  </div>
                </div>

                <div className="p-4 rounded-xl bg-amber-50 border border-amber-200">
                  <div className="font-bold text-amber-900 text-xs">⚠️ 투자 위험 고지</div>
                  <div className="mt-2 text-xs text-slate-700 leading-relaxed space-y-1">
                    <div>• 주식, 선물 등 투자 상품은 가격 변동으로 원금 손실 위험이 있습니다.</div>
                    <div>• 외국인 선물 수급, 환율, 유가 등 10개 팩터는 외부 변수이며 급변할 수 있습니다.</div>
                    <div>• DART 필터, Regime 모델은 통계적 보조 수단이며 100% 정확하지 않습니다. Hit Rate 66.8%는 과거 백테스트 결과입니다.</div>
                    <div>• 본 대시보드는 07:30 KST 자동 업데이트되며 장중 급변은 반영되지 않을 수 있습니다.</div>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
                  <div className="p-3 rounded-xl bg-blue-50 border border-blue-200"><div className="font-bold text-blue-900">FRED • US Macro</div><div className="mt-1 text-slate-700 leading-relaxed">DGS10(10Y 금리), DCOILWTICO(WTI 유가), DTWEXBGS(달러 DXY), VIXCLS(VIX) • St.Louis Fed API • 100% REAL</div></div>
                  <div className="p-3 rounded-xl bg-emerald-50 border border-emerald-200"><div className="font-bold text-emerald-900">yfinance • Global</div><div className="mt-1 text-slate-700 leading-relaxed">^GSPC(S&P500), ^SOX(필라 반도체), KRW=X(원달러), HG=F(구리), 000001.SS(상해종합) • 100% REAL</div></div>
                  <div className="p-3 rounded-xl bg-indigo-50 border border-indigo-200"><div className="font-bold text-indigo-900">KRX OPEN API • 7개 승인</div><div className="mt-1 text-slate-700 leading-relaxed">KOSPI/KOSDAQ 시세, 외국인/기관 수급, KOSPI200 선물 • 15007 투자자별 거래실적 CSV(foreigner_kospi200.csv) 244일 REAL</div></div>
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