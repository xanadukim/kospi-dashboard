        const currentIndustry = useMemo(() => industries.find((i) => i.id === selectedIndustry) || industries[0], [selectedIndustry]);

        const contributions = useMemo(() => {
          return Object.entries(currentIndustry.betas).map(([factor, beta]) => {
            const z = zScores[factor] ?? zScores[factorMeta[factor]?.label] ?? 0;
            const contrib = beta * z;
            return { factor, beta, z, contrib };
          }).sort((a, b) => Math.abs(b.contrib) - Math.abs(a.contrib));
        }, [currentIndustry, zScores]);

        const predictedReturn = useMemo(() => contributions.reduce((sum, c) => sum + c.contrib, 0), [contributions]);

        const weeklyPicks = useMemo(() => {
          const selected = history.find((d) => d.date === selectedDate) || history[0];
          const getZ = (tf) => {
            const map = { 반도체팩터: zScores["SOX / 필라"] ?? 1.59, 원달러: zScores["원달러"] ?? 1.38, 중국PMI: 0.21, 한미스프레드: 0.91, US10Y: zScores["US 10Y"] ?? -1.13, SP500: zScores["S&P500"] ?? 0.63 };
            return map[tf] ?? 0.8;
          };
          if (selected?.weeklyPicks && selected.weeklyPicks.length >= 20) return selected.weeklyPicks;
          const mockData = [
            { id: "elec", stocks: [["005930","삼성전자",1.0,0.8],["000660","SK하이닉스",1.25,1.2],["066570","LG전자",0.85,0.3],["042700","한미반도체",1.3,2.1],["011070","LG이노텍",0.9,1.5],["058470","리노공업",0.85,1.0],["000990","DB하이텍",0.8,0.9],["095340","ISC",0.9,0.6]] },
            { id: "auto", stocks: [["005380","현대차",1.0,0.7],["000270","기아",1.15,1.1],["064350","현대로템",1.05,1.8],["003490","대한항공",0.95,1.3],["012330","현대모비스",0.9,0.2],["086280","현대글로비스",0.85,0.4],["180640","한진칼",0.8,0.8],["161390","한국타이어",0.75,-0.2]] },
            { id: "chem", stocks: [["086520","에코프로",1.25,2.2],["247540","에코프로비엠",1.3,1.5],["373220","LG에너지솔루션",1.2,0.5],["003670","포스코퓨처엠",1.15,0.9],["051910","LG화학",1.0,-0.3],["011780","금호석유",0.85,0.1],["010130","고려아연",0.75,0.4],["121600","나노신소재",1.0,0.7]] },
            { id: "fin", stocks: [["071050","한국금융지주",1.15,1.2],["105560","KB금융",1.0,0.6],["055550","신한지주",0.95,0.4],["000810","삼성화재",0.85,0.7],["086790","하나금융지주",0.9,0.3],["175330","JB금융",0.75,0.5],["316140","우리금융지주",0.85,0.1],["030200","KT",0.6,-0.3]] },
            { id: "bio", stocks: [["195940","HLB",1.2,2.5],["207940","삼성바이오로직스",1.0,0.9],["068270","셀트리온",1.1,0.2],["214450","파마리서치",0.85,1.4],["145020","휴젤",0.9,1.1],["326030","SK바이오팜",1.05,0.7],["128940","한미약품",0.85,0.5],["185740","셀트리온제약",0.95,0.3]] },
            { id: "steel", stocks: [["005490","POSCO홀딩스",1.0,0.4],["047050","포스코인터",0.95,0.8],["010130","고려아연",0.9,0.6],["009830","한화솔루션",0.85,0.3],["004020","현대제철",0.85,-0.3],["103140","풍산",0.75,0.2],["001430","세아베스틸",0.7,0.1],["010950","S-Oil",0.8,-0.6]] },
            { id: "const", stocks: [["012450","한화에어로",1.2,2.3],["329180","HD현대중공업",1.15,1.9],["064350","현대로템",1.05,1.8],["009540","HD한국조선해양",1.0,1.5],["010140","삼성중공업",0.9,0.8],["034020","두산에너빌리티",0.95,0.4],["028050","삼성엔지니어링",0.85,0.2],["047040","대우건설",0.7,-0.3]] },
            { id: "retail", stocks: [["352820","하이브",0.9,0.6],["035900","JYP",0.85,0.8],["035420","NAVER",1.05,-0.2],["035720","카카오",1.1,-0.4],["030000","제일기획",0.65,0.3],["017670","SK텔레콤",0.65,0.2],["004170","신세계",0.8,-0.3],["139480","이마트",0.75,-0.8]] },
          ];
          const picks = [];
          const tfMap = { elec: "반도체팩터", auto: "원달러", chem: "중국PMI", fin: "한미스프레드", bio: "US10Y", steel: "중국PMI", const: "원달러", retail: "SP500" };
          mockData.forEach((ind) => {
            const tf = tfMap[ind.id];
            const z = getZ(tf);
            ind.stocks.forEach(([ticker, name, beta_adj, mom]) => {
              const score = 6.5 + Math.abs(z) * 1.2 * beta_adj + mom * 0.3 + Math.random()*0.5;
              picks.push({ industryId: ind.id, ticker, name, score: parseFloat(score.toFixed(1)), expectedReturn: parseFloat((0.5 + Math.abs(z)*0.8*beta_adj + mom*0.2).toFixed(1)), reason: `${tf} ${z.toFixed(2)}σ × β${beta_adj} + mom ${mom}%`, targetFactor: tf, date: selectedDate });
            });
          });
          return picks;
        }, [history, selectedDate, zScores]);


        // Regime & Meta & Retrain from history or global
        const currentRegime = useMemo(() => {
          const hist = history[0]?.regime;
          if (hist) return hist;
          if (typeof regimeData !== 'undefined') return regimeData;
          return { regime: "normal", confidence: "평시", window: 120, vix: 16.5, description: "정상 시장" };
        }, [history]);

        const currentMeta = useMemo(() => {
          const hist = history[0]?.meta;
          if (hist) return hist;
          if (typeof metaData !== 'undefined') return metaData;
          return { top_valid: ["S&P500","구리","SOX / 필라","원달러","외국인 선물"], avg_p_valid: 0.72 };
        }, [history]);

        const retrainData = useMemo(() => {
          const hist = history[0]?.retrain || history[0]?.beta_snapshot;
          if (hist) return hist;
          if (typeof retrainMeta !== 'undefined') return retrainMeta;
          return { date: "2026-09-27", avg_r2: 0.84, changes: 41, next_retrain: "2026-10-01", version: "v60.2", window: 180, beta_changes: {}, r2_list: {elec:0.91,auto:0.84,chem:0.79,fin:0.87,bio:0.71,steel:0.84,const:0.76,retail:0.80} };
        }, [history]);

        const isRetrainLive = history[0]?.retrain || (typeof retrainMeta !== 'undefined' && retrainMeta.date !== "2026-09-27");

