function App(){
  const [activeTab,setActiveTab]=React.useState("recommend");
  const [selectedIndustry,setSelectedIndustry]=React.useState("fc1");
  const [selectedFactor,setSelectedFactor]=React.useState(null);
  const [selectedDate]=React.useState("2026-09-28");
  const [showHistory,setShowHistory]=React.useState(false);
  const [showDisclaimer,setShowDisclaimer]=React.useState(false);
  const [showHelp,setShowHelp]=React.useState(false);
  const [zScores]=React.useState({"S&P500":0.8,"SOX":1.2});
  const [contributions]=React.useState([{factor:"SOX",z:1.2,beta:0.35,contrib:0.42}]);
  const [filteredPicks]=React.useState([{ticker:"005930",name:"삼성전자",reason:"테스트",industryId:"fc1",score:8.5}]);
  const [all64Filtered]=React.useState([{ticker:"005930",name:"삼성전자",industryId:"fc1",reason:"테스트",score:8.5}]);
  const [pastPicks]=React.useState([{ticker:"005930",name:"삼성전자",returnPct:1.5}]);
  const [pastPicksAvg]=React.useState({avg:"1.20",hit:5});
  const currentIndustry=industries.find(i=>i.id===selectedIndustry)||industries[0];
  const predictedReturn=contributions.reduce((s,c)=>s+c.contrib,0);
  const {currentRegime,currentMeta}=useMarketData();
  const {history}=useHistory();
  return (<div className="min-h-screen bg-slate-50"><Header selectedDate={selectedDate} showHistory={showHistory} setShowHistory={setShowHistory} showDisclaimer={showDisclaimer} setShowDisclaimer={setShowDisclaimer} showHelp={showHelp} setShowHelp={setShowHelp}/><div className="max-w-[1920px] mx-auto px-4 py-4"><div className="flex gap-2 mb-4">{["recommend","top","all64","performance","market"].map(tab=>(<button key={tab} onClick={()=>setActiveTab(tab)} className={`px-4 py-2 rounded-full text-xs font-bold ${activeTab===tab ? "bg-[#1e3a8a] text-white" : "bg-white border"}`}>{tab}</button>))}</div><div className="grid grid-cols-12 gap-4"><Sidebar selectedIndustry={selectedIndustry} setSelectedIndustry={setSelectedIndustry} industries={industries} zScores={zScores}/><main className="col-span-12 md:col-span-7"><RecommendTab activeTab={activeTab} currentIndustry={currentIndustry} predictedReturn={predictedReturn} contributions={contributions} filteredPicks={filteredPicks}/><TopPredictionsTab activeTab={activeTab} industries={industries} selectedIndustry={selectedIndustry} setSelectedIndustry={setSelectedIndustry} zScores={zScores}/><All64Tab activeTab={activeTab} all64Filtered={all64Filtered} industries={industries}/><PerformanceTab activeTab={activeTab} pastPicks={pastPicks} pastPicksAvg={pastPicksAvg}/><MarketTab activeTab={activeTab} contributions={contributions} currentRegime={currentRegime} currentMeta={currentMeta}/></main><FactorPanel selectedFactor={selectedFactor} setSelectedFactor={setSelectedFactor} contributions={contributions}/></div></div><HistoryModal open={showHistory} onClose={()=>setShowHistory(false)} history={history}/><DisclaimerModal open={showDisclaimer} onClose={()=>setShowDisclaimer(false)}/><HelpModal open={showHelp} onClose={()=>setShowHelp(false)}/></div>);
}
const root=ReactDOM.createRoot(document.getElementById("root"));
root.render(<App/>);
