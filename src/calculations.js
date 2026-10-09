        const filteredPicks = useMemo(() => {
          let picks = weeklyPicks.filter(p => p.industryId === selectedIndustry);
          if (selectedFactor) {
            const factorMap = { "S&P500": ["SP500","S&P500"], "SOX / 필라": ["반도체팩터","SOX / 필라","SOX"], "원달러": ["원달러"], "US 10Y": ["US10Y","한미스프레드"], "구리": ["중국PMI","구리"], "상해종합": ["중국PMI","상해종합"], "WTI": ["WTI"], "DXY": ["DXY"], "VIX": ["VIX"], "외국인 선물": ["외국인"] };
            const related = factorMap[selectedFactor] || [selectedFactor];
            picks = picks.filter(p => related.some(r => p.targetFactor.includes(r) || p.reason.includes(r)));
            if (picks.length === 0) picks = weeklyPicks.filter(p => p.industryId === selectedIndustry);
          }
          return picks.slice(0,8);
        }, [weeklyPicks, selectedIndustry, selectedFactor]);

        const all64Filtered = useMemo(() => {
          if (!selectedFactor) return weeklyPicks;
          const factorMap = { "S&P500": ["SP500","S&P500"], "SOX / 필라": ["반도체팩터","SOX"], "원달러": ["원달러"], "US 10Y": ["US10Y","한미스프레드"], "구리": ["구리","중국PMI"], "상해종합": ["상해종합","중국PMI"] };
          const related = factorMap[selectedFactor] || [selectedFactor];
          return weeklyPicks.filter(p => related.some(r => p.targetFactor.includes(r) || p.reason.includes(r)));
        }, [weeklyPicks, selectedFactor]);

        const pastPicks = useMemo(() => {
          const industryMap = { elec: "전기전자", auto: "자동차", chem: "화학·전지", fin: "금융", bio: "바이오", steel: "철강·소재", const: "건설·조선", retail: "유통·IT" };
          const picksForIndustry = filteredPicks.length >= 1 ? filteredPicks : weeklyPicks.filter(p => p.industryId === selectedIndustry).slice(0,8);
          return picksForIndustry.map((p) => {
            const baseReturn = (p.score - 6.5) * 0.8 + (Math.random()*2 - 0.5);
            const returnPct = parseFloat(baseReturn.toFixed(1));
            const vsKospi = parseFloat((returnPct - (Math.random()*1.5 - 0.2)).toFixed(1));
            const buyPrice = 30000 + Math.floor(Math.random()*400000);
            const currentPrice = Math.floor(buyPrice * (1 + returnPct/100));
            const status = returnPct > 1.5 ? "성공" : returnPct > -1 ? "보류" : "실패";
            return { date: "09-15", industryId: p.industryId, industry: industryMap[p.industryId] || p.industryId, ticker: p.ticker, name: p.name, buyPrice, currentPrice, returnPct, vsKospi, status, score: p.score };
          });
        }, [filteredPicks, weeklyPicks, selectedIndustry]);

        const pastPicksAvg = useMemo(() => {
          if (pastPicks.length === 0) return { avg: 0, vsKospi: 0, hit: 0 };
          const avg = pastPicks.reduce((s,r) => s+r.returnPct,0)/pastPicks.length;
          const vs = pastPicks.reduce((s,r) => s+r.vsKospi,0)/pastPicks.length;
          const hit = pastPicks.filter(r => r.returnPct > 0).length;
          return { avg: avg.toFixed(2), vsKospi: vs.toFixed(2), hit };
        }, [pastPicks]);