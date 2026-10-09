// useHistory.js - v62 FINAL
const useHistoryLogic = ({ history, setHistory, setZScores, setSelectedDate, setIsViewingHistory, setLiveCount, setLastRefresh, isViewingHistory }) => {
  const loadSnapshot = (dateStr) => {
    const doc = history.find((d) => d.date === dateStr);
    if (!doc) return;
    const cloud = doc.zScores;
    if (cloud) {
      setZScores({
        "S&P500": cloud.SP500 ?? cloud["S&P500"] ?? 0.63,
        "외국인 선물": cloud.외국인 ?? cloud.외국인_선물 ?? 1.07,
        "SOX / 필라": cloud.반도체팩터 ?? cloud["SOX / 필라"] ?? 1.59,
        "US 10Y": cloud.US10Y ?? -1.13,
        원달러: cloud.원달러 ?? 1.38,
        WTI: cloud.WTI ?? -0.32,
        DXY: cloud.DXY ?? 0.45,
        VIX: cloud.VIX ?? -0.52,
        구리: cloud.구리 ?? 0.68,
        상해종합: cloud.상해종합 ?? 0.42,
      });
      setSelectedDate(doc.date);
      setIsViewingHistory(doc.date !== history[0]?.date);
      setLastRefresh(new Date());
    }
  };
  const returnToLatest = () => {
    if (history[0]) {
      loadSnapshot(history[0].date);
      setIsViewingHistory(false);
    }
  };
  return { loadSnapshot, returnToLatest };
};

// Legacy fragment support - original code placed directly inside App
        const loadSnapshot = (dateStr) => {
          const doc = history.find((d) => d.date === dateStr);
          if (!doc) return;
          const cloud = doc.zScores;
          if (cloud) {
            setZScores({
              "S&P500": cloud.SP500 ?? cloud["S&P500"] ?? 0.63,
              "외국인 선물": cloud.외국인 ?? cloud.외국인_선물 ?? 1.07,
              "SOX / 필라": cloud.반도체팩터 ?? cloud["SOX / 필라"] ?? 1.59,
              "US 10Y": cloud.US10Y ?? -1.13,
              원달러: cloud.원달러 ?? 1.38,
              WTI: cloud.WTI ?? -0.32,
              DXY: cloud.DXY ?? 0.45,
              VIX: cloud.VIX ?? -0.52,
              구리: cloud.구리 ?? 0.68,
              상해종합: cloud.상해종합 ?? 0.42,
            });
            setSelectedDate(doc.date);
            setIsViewingHistory(doc.date !== history[0]?.date);
            setLastRefresh(new Date());
          }
        };
        const returnToLatest = () => {
          if (history[0]) {
            loadSnapshot(history[0].date);
            setIsViewingHistory(false);
          }
        };

        useEffect(() => {
          if (!db) return;
          const unsub = db.collection("factor_snapshots").orderBy("date", "desc").limit(10).onSnapshot((snap) => {
            const docs = snap.docs.map((d) => d.data());
            setHistory(docs);
            setLiveCount(docs.length);
            setLastRefresh(new Date());
            if (docs[0]?.zScores && !isViewingHistory) {
              const cloud = docs[0].zScores;
              setZScores({
                "S&P500": cloud.SP500 ?? cloud["S&P500"] ?? 0.63,
                "외국인 선물": cloud.외국인 ?? cloud.외국인_선물 ?? 1.07,
                "SOX / 필라": cloud.반도체팩터 ?? cloud["SOX / 필라"] ?? 1.59,
                "US 10Y": cloud.US10Y ?? -1.13,
                원달러: cloud.원달러 ?? 1.38,
                WTI: cloud.WTI ?? -0.32,
                DXY: cloud.DXY ?? 0.45,
                VIX: cloud.VIX ?? -0.52,
                구리: cloud.구리 ?? 0.68,
                상해종합: cloud.상해종합 ?? 0.42,
              });
              setSelectedDate(docs[0].date);
            }
          });
          return () => unsub();
        }, [isViewingHistory]);
