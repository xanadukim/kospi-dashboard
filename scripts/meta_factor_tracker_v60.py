"""
meta_factor_tracker_v60.py - KOSPI Quant Terminal v60 - IC/HitRate 100% REAL + China Proxy

개선점 v56 -> v60:
- China Proxy 팩터 (구리, 상해종합) IC 계산 추가
- 10 Factors 전체: S&P500, US10Y, 외국인, SOX, 원달러, WTI, DXY, VIX, 구리, 상해종합
- performance_tracking 기반 REAL IC (yfinance .KS REAL 수익률)
- IC = corr(스냅샷 z-score @ recDate, ExcessReturn) - 팩터 예측력
- 10개 전체 팩터 IC: performance_tracking을 factor_snapshots zScores와 recDate로 조인
  (targetFactor는 산업별 대표 1개만 기록하므로 팩터 단위 IC는 스냅샷 zScores 기준)
- Hit Rate = sign(Z) == sign(ExcessReturn)
- t-stat, avg_excess, n_samples

실행: 매일 16:30 KST (track_performance_v60.py 이후)
Firestore: factor_validity/{factor}_{date} + meta_summaries/{date} + factor_snapshots 요약

v60 China Proxy 의미:
- 구리(HG=F): 중국 경기민감도 프록시, 철강/화학/건설에 높은 베타
- 상해종합(000001.SS): 중국 증시 심리 프록시, 화학/철강/유통에 베타
- 이 두 팩터의 IC가 높게 나오면 중국 경기가 KOSPI에 미치는 영향 검증
"""

import os
import json
import datetime
from datetime import timezone, timedelta
import firebase_admin
from firebase_admin import credentials, firestore
import numpy as np
from collections import defaultdict

# Firebase
cred_json_str = os.environ.get("FIREBASE_SERVICE_ACCOUNT", "")
if not cred_json_str:
    print("No FIREBASE_SERVICE_ACCOUNT - exit")
    exit(1)

cred_dict = json.loads(cred_json_str)
if not firebase_admin._apps:
    cred = credentials.Certificate(cred_dict)
    firebase_admin.initialize_app(cred)
db = firestore.client()

KST = timezone(timedelta(hours=9))
today = datetime.datetime.now(KST).strftime('%Y-%m-%d')
print(f"\n=== Meta Factor Tracker v60 REAL + China Proxy {today} ===")
print("IC = corr(Z_at_Rec, ExcessReturn) - Factor Predictability")

# Load performance_tracking (REAL yfinance returns)
try:
    perf_docs = list(db.collection('performance_tracking').order_by('recDate', direction=firestore.Query.DESCENDING).limit(1000).stream())
    print(f"Loaded {len(perf_docs)} performance docs (REAL yfinance v60)")
except Exception as e:
    print(f"Load error: {e}")
    perf_docs = []

if not perf_docs:
    print("No performance data yet - run track_performance_v60.py first")
    print("Waiting for first tracking to complete...")
    exit(0)

# performance_tracking은 같은 recDate+ticker가 여러 evalDate로 누적된다.
# IC/HitRate는 look-ahead 혼합을 피하기 위해 종목·추천일 기준 최신 evalDate 1건만 사용한다.
latest_by_pick = {}
for doc in perf_docs:
    d = doc.to_dict()
    key = (d.get('recDate', ''), d.get('ticker', ''))
    eval_date = str(d.get('evalDate', ''))
    prev = latest_by_pick.get(key)
    if prev is None or eval_date > str(prev.get('evalDate', '')):
        latest_by_pick[key] = d

deduped_docs = list(latest_by_pick.values())
print(f"Deduped performance docs: {len(deduped_docs)} / {len(perf_docs)}")

# 10개 전체 팩터 IC를 위해 recDate별 스냅샷 zScores를 로드한다.
# targetFactor는 산업별 대표 팩터 1개만 기록하므로, 이를 그대로 쓰면
# IC가 대표 팩터(실측 4개)에만 계산된다.
FACTOR_ALIAS = {
    "S&P500": "SP500", "SP500": "SP500",
    "SOX / 필라": "SOX", "반도체팩터": "SOX", "SOX": "SOX",
    "US 10Y": "US10Y", "US10Y": "US10Y",
    "외국인 수급": "외국인", "외국인 선물": "외국인", "외국인": "외국인", "외국인_선물": "외국인",
    "원달러": "원달러", "WTI": "WTI", "DXY": "DXY", "VIX": "VIX",
    "구리": "구리", "상해종합": "상해종합",
}
ALL_FACTORS = [
    "SP500", "US10Y", "SOX", "원달러", "WTI",
    "DXY", "VIX", "구리", "상해종합", "외국인",
]

snapshot_z = {}
try:
    snap_docs = list(
        db.collection('factor_snapshots')
        .order_by('date', direction=firestore.Query.DESCENDING)
        .limit(60)
        .stream()
    )
    for s in snap_docs:
        sd = s.to_dict()
        sdate = sd.get('date')
        zs = sd.get('zScores') or {}
        if not sdate or not isinstance(zs, dict):
            continue
        canon = {}
        for k, v in zs.items():
            ck = FACTOR_ALIAS.get(str(k).strip(), str(k).strip())
            try:
                fv = float(v)
            except (TypeError, ValueError):
                continue
            if np.isfinite(fv):
                canon[ck] = fv
        if canon:
            snapshot_z[sdate] = canon
    print(f"Loaded {len(snapshot_z)} snapshot zScores for factor-level IC")
except Exception as e:
    print(f"factor_snapshots load error: {e}")

# Group by factor: recDate의 스냅샷 z-score × 종목 초과수익률
factor_data = defaultdict(list)  # factor -> list of (z, excess_return, return, score)

for d in deduped_docs:
    zs_map = snapshot_z.get(d.get('recDate', ''))
    if not zs_map:
        continue
    try:
        excess_f = float(d.get('excessReturn'))
        ret_f = float(d.get('return'))
        score_f = float(d.get('score', 0))
    except (TypeError, ValueError):
        continue
    if not (np.isfinite(excess_f) and np.isfinite(ret_f)):
        continue
    for f in ALL_FACTORS:
        z_f = zs_map.get(f)
        if z_f is not None:
            factor_data[f].append((z_f, excess_f, ret_f, score_f))

print(f"\nFactors found: {list(factor_data.keys())}")
print(f"China Proxy factors: 구리={len(factor_data.get('구리',[]))}, 상해종합={len(factor_data.get('상해종합',[]))}")

# Calculate IC per factor
results = {}
for factor, tuples in factor_data.items():
    if len(tuples) < 10:
        print(f"{factor}: only {len(tuples)} samples (<10), skip IC but keep count")
        # Still save with low confidence
        if len(tuples) < 3:
            continue
    
    zs = np.array([t[0] for t in tuples])
    excesses = np.array([t[1] for t in tuples])
    rets = np.array([t[2] for t in tuples])
    scores = np.array([t[3] for t in tuples])
    
    # IC = corr(Z, ExcessReturn)
    try:
        if len(zs) > 1 and np.std(zs) > 1e-6 and np.std(excesses) > 1e-6:
            ic = float(np.corrcoef(zs, excesses)[0, 1])
            if np.isnan(ic):
                ic = 0.0
        else:
            ic = 0.0
    except:
        ic = 0.0
    
    # Hit Rate = sign(Z) == sign(ExcessReturn)
    hits = sum(1 for z, e, _, _ in tuples if (z > 0 and e > 0) or (z < 0 and e < 0))
    hit_rate = hits / len(tuples) if tuples else 0
    
    # Win rate for excess
    win_excess = sum(1 for _, e, _, _ in tuples if e > 0) / len(tuples) if tuples else 0
    win_abs = sum(1 for _, _, r, _ in tuples if r > 0) / len(tuples) if tuples else 0
    
    # Avg excess
    avg_excess = float(np.mean(excesses)) if len(excesses) else 0
    avg_ret = float(np.mean(rets)) if len(rets) else 0
    
    # t-stat for IC significance
    n = len(tuples)
    if abs(ic) < 0.99 and n > 2:
        t_stat = ic * (n ** 0.5) / ((1 - ic**2) ** 0.5) if (1 - ic**2) > 1e-6 else 0
    else:
        t_stat = 0
    
    # Score-weighted IC (high score picks should have higher return)
    try:
        if len(scores) > 1 and np.std(scores) > 1e-6:
            score_ic = float(np.corrcoef(scores, excesses)[0, 1])
            if np.isnan(score_ic):
                score_ic = 0.0
        else:
            score_ic = 0.0
    except:
        score_ic = 0.0
    
    results[factor] = {
        'ic': round(ic, 4),
        'hit_rate': round(hit_rate, 4),
        'hit_rate_pct': round(hit_rate * 100, 2),
        'avg_excess': round(avg_excess, 6),
        'avg_excess_pct': round(avg_excess * 100, 2),
        'avg_return': round(avg_ret, 6),
        'avg_return_pct': round(avg_ret * 100, 2),
        't_stat': round(float(t_stat), 2),
        'n_samples': n,
        'win_excess_rate': round(win_excess, 4),
        'win_rate': round(win_abs, 4),
        'score_ic': round(score_ic, 4),
        'is_china_proxy': factor in ['구리', '상해종합'],
        'source': 'REAL performance_tracking × factor_snapshots zScores v61.6',
    }
    
    china_tag = " [China Proxy]" if factor in ['구리', '상해종합'] else ""
    print(f"{factor:12s}{china_tag}: IC {ic:+.3f} Hit {hit_rate:.0%} AvgEx {avg_excess*100:+.2f}% n={n} t={t_stat:.1f} ScoreIC {score_ic:+.2f}")

# Save to Firestore
batch = db.batch()
saved = 0

for factor, metrics in results.items():
    doc_id = f"{factor}_{today}"
    doc_data = {
        'date': today,
        'factor': factor,
        **metrics,
        'createdAt': firestore.SERVER_TIMESTAMP,
        'version': 'v61.6-meta-factorlevel-10factors',
        'real_data_ratio': 1.0,
    }
    batch.set(db.collection('factor_validity').document(doc_id), doc_data, merge=True)
    saved += 1

# Summary for meta_summaries
# Top 3 factors by IC
sorted_by_ic = sorted(results.items(), key=lambda x: abs(x[1]['ic']), reverse=True)
top_ic = sorted_by_ic[:3]

summary = {
    'date': today,
    'timestamp': datetime.datetime.now(KST),
    'factors': results,
    'topIC': {k: v for k, v in top_ic},
    'total_samples': len(deduped_docs),
    'unique_factors': len(results),
    'china_proxy': {
        '구리': results.get('구리', {}),
        '상해종합': results.get('상해종합', {})
    },
    'source': 'yfinance-REAL-v61.6-factorlevel-10factors',
    'version': 'v61.6-meta-tracker-factorlevel-10factors',
    'real_data_ratio': 1.0,
    'createdAt': firestore.SERVER_TIMESTAMP,
    'note': '구리/상해종합 IC가 높으면 중국 경기가 KOSPI 예측에 유효함'
}

batch.set(db.collection('meta_summaries').document(today), summary, merge=True)

# Also update factor_snapshots latest doc with validity hint? No, keep separate

batch.commit()

print(f"\n[{today}] Saved {saved} factors to factor_validity")
print(f"Top IC factors: {[(k, v['ic']) for k, v in top_ic]}")
if '구리' in results or '상해종합' in results:
    print(f"China Proxy Validation:")
    if '구리' in results:
        print(f"  구리 IC {results['구리']['ic']:+.3f} Hit {results['구리']['hit_rate_pct']}% - China 경기민감도")
    if '상해종합' in results:
        print(f"  상해종합 IC {results['상해종합']['ic']:+.3f} Hit {results['상해종합']['hit_rate_pct']}% - China 증시 심리")

print("\n100% REAL IC based on yfinance performance_tracking v60 China Proxy")
print("Next: Check dashboard '성과 IC' tab for IC/HitRate visualization")
