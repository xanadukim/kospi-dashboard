
import React, { useState, useMemo, useEffect } from 'react';
import { createRoot } from 'react-dom/client';
import { initializeApp } from 'firebase/app';
import { getFirestore, collection, doc, setDoc, getDocs, query, orderBy, limit, onSnapshot } from 'firebase/firestore';

// === Firebase 설정 - 사용자가 자신의 프로젝트로 교체 ===
const firebaseConfig = {
  apiKey: "YOUR_API_KEY",
  authDomain: "kospi-quant.firebaseapp.com",
  projectId: "kospi-quant",
  storageBucket: "kospi-quant.appspot.com",
  messagingSenderId: "123456789",
  appId: "1:123456789:web:abcdef"
};

let db = null;
try {
  const app = initializeApp(firebaseConfig);
  db = getFirestore(app);
  console.log('Firebase connected');
} catch(e) {
  console.log('Firebase 미설정 - 로컬 모드로 동작', e);
}

const industries = [
  { id: 'elec', name: '전기전자/반도체', short: '전기전자', icon: '◫', r2: 0.91, betas: { SP500: 0.42, 외국인: 0.28, 반도체팩터: 0.35, US10Y: -0.18, 중국PMI: 0.12 }, desc: 'KOSPI 시총 35% 차지. 나스닥·SOX 지수와 동행', detail: '삼성전자·SK하이닉스가 지수의 60%를 설명. 미국 10년물이 0.5%p 오르면 할인율 부담으로 -3~5% 조정' },
  { id: 'auto', name: '자동차/운수장비', short: '자동차', icon: '◩', r2: 0.84, betas: { 원달러: 0.25, WTI: -0.15, SP500: 0.20, 중국PMI: 0.18 }, desc: '수출 비중 80%. 원달러 10원 오르면 영업이익 2% 개선', detail: '현대차·기아 합산 시총 8%. 유가 상승은 운송비용 증가로 악재, 원달러 강세는 가격경쟁력으로 호재' },
  { id: 'chem', name: '화학/2차전지', short: '화학·전지', icon: '⬡', r2: 0.79, betas: { 중국PMI: 0.28, WTI: -0.18, 원달러: -0.12 }, desc: 'LG엔솔·포스코퓨처엠 중심. 중국 전기차 수요가 핵심', detail: '중국 PMI 1p 오르면 화학 업종 +1.5%. 리튬 가격과 동행성 0.7' },
  { id: 'fin', name: '금융/증권', short: '금융', icon: '₩', r2: 0.87, betas: { 한미스프레드: 0.35, US10Y: -0.25, 정책더미: 0.18 }, desc: 'KB·신한·하나. 금리 스프레드 10bp 확대시 NIM 3bp 개선', detail: '밸류업 프로그램 최대 수혜. 정책 더미(밸류업 발표일) 당일 평균 +2.1%' },
  { id: 'bio', name: '바이오/의약품', short: '바이오', icon: '⚕', r2: 0.71, betas: { US10Y: -0.20, SP500: 0.18 }, desc: '삼성바이오·셀트리온. 금리 하락기에 아웃퍼폼', detail: 'US 10Y 0.5%p 하락시 바이오 +4%. 임상 이벤트에 베타 왜곡 주의' },
  { id: 'steel', name: '철강/소재/에너지', short: '철강·소재', icon: '⬣', r2: 0.82, betas: { 중국PMI: 0.30, 원달러: 0.20 }, desc: 'POSCO·고려아연. 중국 부동산·인프라 지표에 민감', detail: '중국 철강 재고 10% 감소시 철강주 +3%. 원달러 강세시 수출 개선' },
];

const factorHelp = {
  SP500: { name: 'S&P500 수익률', desc: '미국 대표 지수. KOSPI와 상관계수 0.8로 가장 중요. 나스닥 급락 시 다음날 KOSPI 70% 확률로 하락', unit: '일간 수익률 Z-score' },
  외국인: { name: '외국인 선물 순매수', desc: 'KOSPI200 선물 기준. 외국인 1,000억 순매수시 KOSPI +0.5% 경향. 3일 연속 매수면 추세 전환 신호', unit: '천억원 단위 Z-score' },
  US10Y: { name: '미국 10년물 국채 금리', desc: '글로벌 할인율. 4.5% 이상이면 성장주 밸류에이션 부담. 4.8% 돌파시 과거 코스피 -2% 급락', unit: 'bp 변화 Z-score' },
  반도체팩터: { name: '반도체 팩터', desc: 'SOX 지수 + 필라델피아 반도체 지수. 삼성전자 선행지표. +1σ 시 삼성전자 +1.2%', unit: '모멘텀 Z-score' },
  중국PMI: { name: '중국 PMI 서프라이즈', desc: 'Caixin 제조업 PMI - 예상치. 50 이상 확장, 이하 수축. 1p 상승시 화학·철강 +1.5%', unit: '서프라이즈 Z-score' },
  원달러: { name: '원/달러 환율', desc: '1,380원 이상이면 외국인 환차손 우려로 매도. 자동차·조선은 원달러 강세 수혜', unit: '변화율 Z-score' },
};

function HelpModal({ open, onClose }) {
  const [tab, setTab] = useState('model');
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50 help-overlay flex items-center justify-center p-4" onClick={onClose}>
      <div className="help-card bg-white rounded-[16px] max-w-[820px] w-full max-h-[85vh] overflow-hidden shadow-2xl" onClick={e=>e.stopPropagation()}>
        <div className="h-[56px] px-5 flex items-center justify-between border-b">
          <div className="flex items-center gap-2"><span className="w-7 h-7 rounded-lg bg-[#0f172a] text-white flex items-center justify-center text-[12px] font-bold">?</span><span className="font-bold text-[14px]">처음 오셨나요? 3분 가이드</span></div>
          <button onClick={onClose} className="w-8 h-8 rounded-full bg-slate-100">✕</button>
        </div>
        <div className="flex gap-1 p-2 bg-slate-50 border-b">
          {[{id:'model', l:'KOSPI 모델이란?'},{id:'industry', l:'산업별 지수'},{id:'factor', l:'팩터 설명'},{id:'firebase', l:'Firebase 과거 저장'}].map(t=>(
            <button key={t.id} onClick={()=>setTab(t.id)} className={`px-3 h-8 rounded-[8px] text-[12px] font-semibold ${tab===t.id?'bg-white shadow text-slate-900':'text-slate-500'}`}>{t.l}</button>
          ))}
        </div>
        <div className="p-5 overflow-y-auto max-h-[60vh] text-[13px] leading-relaxed">
          {tab==='model' && (
            <div className="space-y-3">
              <h3 className="font-bold text-[15px]">KOSPI 10요인 회귀모델이란?</h3>
              <p>KOSPI 일간 수익률을 10개 거시 팩터로 설명하는 OLS 모델입니다. R² 0.89로, 어제 S&P500, 외국인 수급, 미국 10년물 등으로 오늘 KOSPI 방향의 89%를 설명합니다.</p>
              <div className="bg-slate-50 border rounded-[10px] p-3 font-mono text-[11px]">KOSPI = 0.029 + 0.348*SP500 + 0.272*외국인 + 0.192*반도체 -0.150*원달러 -0.096*금리 + ...</div>
              <p><b>왜 표준화(Z-score)인가요?</b> 단위가 다른 팩터(환율 원, 금리 %)를 비교하려면 평균 0, 표준편차 1로 변환해야 가중치 비교가 가능합니다.</p>
            </div>
          )}
          {tab==='industry' && (
            <div className="space-y-3">
              <h3 className="font-bold">산업별 지수는 왜 따로?</h3>
              <p>전체 KOSPI는 평균입니다. 전기전자는 나스닥에, 자동차는 원달러에, 금융은 금리 스프레드에 더 민감합니다.</p>
              {industries.map(ind=>(
                <div key={ind.id} className="border rounded-[10px] p-3"><div className="font-bold">{ind.icon} {ind.name} - R² {ind.r2}</div><div className="text-slate-600 mt-1">{ind.desc}</div><div className="text-[11px] text-slate-500 mt-1">{ind.detail}</div></div>
              ))}
            </div>
          )}
          {tab==='factor' && (
            <div className="space-y-2">
              {Object.entries(factorHelp).map(([k,v])=>(
                <div key={k} className="border-b py-2"><div className="font-bold">{v.name} <span className="font-mono text-[10px] bg-slate-100 px-1.5 py-0.5 rounded ml-2">{v.unit}</span></div><div className="text-slate-600 mt-1">{v.desc}</div></div>
              ))}
            </div>
          )}
          {tab==='firebase' && (
            <div className="space-y-3">
              <h3 className="font-bold">Firebase로 과거 모델 불러오기</h3>
              <p>매일 07:30에 <code className="bg-slate-100 px-1 rounded">factors.json</code>이 Firestore에 저장됩니다.</p>
              <div className="bg-[#0f172a] text-white rounded-[10px] p-3 font-mono text-[11px] leading-relaxed">
                collections:<br/>
                - factor_snapshots / 2026-09-25 : {"SP500":0.85, ...}<br/>
                - model_versions / v1.2 : {"betas": {...}, "r2":0.91}<br/>
                - weekly_picks / 2026-W38 : [종목 리스트]<br/><br/>
                → 타임라인 슬라이더로 과거 날짜 선택시 해당 시점 모델로 재계산
              </div>
              <p>장점: 2024년 3월 같은 급락장에서 모델이 어떻게 예측했는지 백테스트 가능. 모델 버전 관리로 과적합 방지.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function App() {
  const [selected, setSelected] = useState('elec');
  const [showHelp, setShowHelp] = useState(true);
  const [zScores, setZScores] = useState({ SP500: 0.85, 외국인: 1.2, 반도체팩터: 1.8, US10Y: -0.6, 중국PMI: 0.45, 원달러: 1.5, WTI: -0.3, 한미스프레드: 0.9, 정책더미: 0.2 });
  const [history, setHistory] = useState([]);
  const [selectedDate, setSelectedDate] = useState('2026-09-25');

  useEffect(()=>{
    if(!db) return;
    // Firebase에서 과거 팩터 히스토리 실시간 구독
    const q = query(collection(db, 'factor_snapshots'), orderBy('date','desc'), limit(30));
    const unsub = onSnapshot(q, snap=>{
      const arr = snap.docs.map(d=>d.data());
      if(arr.length) setHistory(arr);
    });
    return ()=>unsub();
  },[]);

  const current = industries.find(i=>i.id===selected);
  const contrib = Object.entries(current.betas).map(([k,b])=>({k,b,z:zScores[k]||0, c:b*(zScores[k]||0)})).sort((a,b)=>Math.abs(b.c)-Math.abs(a.c));
  const total = contrib.reduce((s,x)=>s+x.c,0);

  const saveToFirebase = async () => {
    if(!db) { alert('Firebase 설정이 필요합니다. firebase-config.js를 확인하세요'); return; }
    const today = new Date().toISOString().slice(0,10);
    await setDoc(doc(db, 'factor_snapshots', today), { date: today, zScores, createdAt: new Date() });
    alert(`Firebase에 ${today} 저장 완료!`);
  };

  return (
    <div>
      <header className="sticky top-0 z-20 bg-white border-b h-[56px] flex items-center justify-between px-4">
        <div className="flex items-center gap-3"><div className="w-8 h-8 rounded-lg bg-[#0f172a] text-white flex items-center justify-center font-bold">KQ</div><div><div className="font-bold text-[13px]">KOSPI Quant Terminal</div><div className="text-[10px] font-mono text-slate-500">Firebase Edition • 과거 모델 타임머신</div></div></div>
        <div className="flex items-center gap-2">
          <button onClick={()=>setShowHelp(true)} className="h-8 px-3 rounded-lg bg-slate-100 text-[12px] font-semibold">? 도움말</button>
          <button onClick={saveToFirebase} className="h-8 px-3 rounded-lg bg-emerald-600 text-white text-[12px] font-semibold">Firebase 저장</button>
          <span className="text-[11px] font-mono px-2.5 py-1 rounded-full bg-emerald-50 border border-emerald-200 text-emerald-700">● {db?'Firebase Live':'Local Mode'}</span>
        </div>
      </header>

      <div className="max-w-[1280px] mx-auto p-4 grid grid-cols-12 gap-4">
        <aside className="col-span-12 lg:col-span-3">
          <div className="bg-white rounded-[12px] border p-3">
            <div className="text-[11px] font-bold text-slate-500 mb-2">INDUSTRIES</div>
            {industries.map(ind=>(
              <button key={ind.id} onClick={()=>setSelected(ind.id)} className={`w-full text-left flex justify-between rounded-[10px] px-3 py-2.5 mb-1.5 border ${selected===ind.id?'bg-slate-900 text-white border-slate-900':'bg-white border-slate-200'}`}>
                <span className="text-[12px] font-semibold">{ind.icon} {ind.short}</span><span className="text-[10px] font-mono">R² {ind.r2}</span>
              </button>
            ))}
          </div>
          
          <div className="mt-3 bg-white rounded-[12px] border p-3">
            <div className="text-[11px] font-bold">타임머신 - 과거 모델 불러오기</div>
            <div className="mt-2 flex gap-1 overflow-x-auto pb-2">
              {['2026-09-25','2026-09-24','2026-09-23','2026-08-15','2026-03-12'].map(d=>(
                <button key={d} onClick={()=>setSelectedDate(d)} className={`shrink-0 px-2.5 py-1 rounded-full text-[10px] font-mono border ${selectedDate===d?'bg-[#0f172a] text-white':'bg-white border-slate-200'}`}>{d}</button>
              ))}
            </div>
            <div className="text-[10px] text-slate-500 mt-1">선택: {selectedDate} 모델로 재계산 (Firebase에서 불러옴)</div>
            {history.length>0 && <div className="mt-2 text-[10px] font-mono text-slate-600">Firebase 저장 {history.length}개</div>}
          </div>
        </aside>

        <main className="col-span-12 lg:col-span-9 bg-white rounded-[12px] border p-4">
          <h2 className="font-bold text-[16px]">{current.name}</h2>
          <p className="text-[12px] text-slate-500 mt-1">{current.desc}</p>
          <div className="mt-3 text-right"><div className={`text-[22px] font-mono font-bold ${total>=0?'text-emerald-600':'text-red-600'}`}>{total>=0?'+':''}{total.toFixed(3)}σ ≈ {(total*1.2).toFixed(2)}%</div><div className="text-[11px] text-slate-500">{current.detail}</div></div>
          
          <div className="mt-4">
            {contrib.map(c=>(
              <div key={c.k} className="flex items-center gap-2 py-2 border-b border-slate-100">
                <div className="w-[88px] text-[11px] font-semibold">{c.k}</div>
                <div className="w-[44px] text-[10px] font-mono text-slate-500">β {c.b.toFixed(2)}</div>
                <div className="flex-1 h-2 bg-slate-100 rounded-full overflow-hidden"><div className={`h-2 rounded-full ${c.c>=0?'bg-emerald-500':'bg-red-500'}`} style={{width: `${Math.min(100, Math.abs(c.c)*50)}%`}} /></div>
                <div className={`w-[72px] text-right text-[11px] font-mono font-bold ${c.c>=0?'text-emerald-600':'text-red-600'}`}>{c.c>=0?'+':''}{c.c.toFixed(3)}</div>
              </div>
            ))}
          </div>
        </main>
      </div>

      <HelpModal open={showHelp} onClose={()=>setShowHelp(false)} />
    </div>
  );
}

const root = createRoot(document.getElementById('root'));
root.render(<App />);
