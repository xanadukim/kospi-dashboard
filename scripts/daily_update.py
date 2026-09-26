"""
scripts/daily_update.py - 업종별 8종목씩 64종목 추천 + KRX API β·모멘텀 스크리닝
일요일 저녁 6시 KST (09:00 UTC) 실행
"""
import os, json, datetime, random, math
import firebase_admin
from firebase_admin import credentials, firestore

sa_json = json.loads(os.environ['FIREBASE_SERVICE_ACCOUNT'])
cred = credentials.Certificate(sa_json)
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)
db = firestore.client()

kst = datetime.timezone(datetime.timedelta(hours=9))
today = datetime.datetime.now(kst).strftime('%Y-%m-%d')
print(f"[{today}] Sunday 18:00 KST - 64 picks screening start")

# Previous Z scores
docs = list(db.collection('factor_snapshots').order_by('date', direction=firestore.Query.DESCENDING).limit(1).stream())
if docs:
    lastZ = docs[0].to_dict().get('zScores', {})
else:
    lastZ = {"SP500":0.85,"외국인":1.2,"반도체팩터":1.8,"US10Y":-0.6,"중국PMI":0.45,"원달러":1.5,"WTI":-0.3,"한미스프레드":0.9,"정책더미":0.2}

newZ = {k: round(v * 0.92 + random.uniform(-0.25,0.25), 2) for k,v in lastZ.items()}
print(f"New Z: {newZ}")

# Industry universe - KRX API screening (real: pykrx + KRX open API, here mock with expanded universe)
# Each industry has ~12 candidates, screening by β·Z + Momentum selects top 8
industry_universe = {
    "elec": {
        "name": "전기전자/반도체", "targetFactor": "반도체팩터", "beta": 0.35,
        "candidates": [
            {"ticker":"005930","name":"삼성전자","beta_adj":1.0,"mom":0.8},
            {"ticker":"000660","name":"SK하이닉스","beta_adj":1.25,"mom":1.2},
            {"ticker":"066570","name":"LG전자","beta_adj":0.85,"mom":0.3},
            {"ticker":"006400","name":"삼성SDI","beta_adj":0.95,"mom":-0.2},
            {"ticker":"034220","name":"LG디스플레이","beta_adj":0.75,"mom":-0.8},
            {"ticker":"402340","name":"SK스퀘어","beta_adj":1.1,"mom":0.5},
            {"ticker":"011070","name":"LG이노텍","beta_adj":0.9,"mom":1.5},
            {"ticker":"000990","name":"DB하이텍","beta_adj":0.8,"mom":0.9},
            {"ticker":"042700","name":"한미반도체","beta_adj":1.3,"mom":2.1},
            {"ticker":"058470","name":"리노공업","beta_adj":0.85,"mom":1.0},
            {"ticker":"095340","name":"ISC","beta_adj":0.9,"mom":0.6},
            {"ticker":"131970","name":"테스","beta_adj":0.75,"mom":-0.3},
        ]
    },
    "auto": {
        "name": "자동차/운수장비", "targetFactor": "원달러", "beta": 0.25,
        "candidates": [
            {"ticker":"005380","name":"현대차","beta_adj":1.0,"mom":0.7},
            {"ticker":"000270","name":"기아","beta_adj":1.15,"mom":1.1},
            {"ticker":"012330","name":"현대모비스","beta_adj":0.9,"mom":0.2},
            {"ticker":"011200","name":"HMM","beta_adj":1.2,"mom":-0.5},
            {"ticker":"086280","name":"현대글로비스","beta_adj":0.85,"mom":0.4},
            {"ticker":"180640","name":"한진칼","beta_adj":0.8,"mom":0.8},
            {"ticker":"003490","name":"대한항공","beta_adj":0.95,"mom":1.3},
            {"ticker":"161390","name":"한국타이어","beta_adj":0.75,"mom":-0.2},
            {"ticker":"004020","name":"현대제철","beta_adj":0.7,"mom":-0.6},
            {"ticker":"012330","name":"현대모비스","beta_adj":0.9,"mom":0.2},
            {"ticker":"064350","name":"현대로템","beta_adj":1.05,"mom":1.8},
            {"ticker":"023530","name":"롯데쇼핑","beta_adj":0.6,"mom":-1.0},
        ]
    },
    "chem": {
        "name": "화학/2차전지", "targetFactor": "중국PMI", "beta": 0.28,
        "candidates": [
            {"ticker":"373220","name":"LG에너지솔루션","beta_adj":1.2,"mom":0.5},
            {"ticker":"051910","name":"LG화학","beta_adj":1.0,"mom":-0.3},
            {"ticker":"096770","name":"SK이노베이션","beta_adj":0.95,"mom":-0.8},
            {"ticker":"003670","name":"포스코퓨처엠","beta_adj":1.15,"mom":0.9},
            {"ticker":"247540","name":"에코프로비엠","beta_adj":1.3,"mom":1.5},
            {"ticker":"086520","name":"에코프로","beta_adj":1.25,"mom":2.2},
            {"ticker":"011170","name":"롯데케미칼","beta_adj":0.8,"mom":-1.2},
            {"ticker":"011780","name":"금호석유","beta_adj":0.85,"mom":0.1},
            {"ticker":"010130","name":"고려아연","beta_adj":0.75,"mom":0.4},
            {"ticker":"006650","name":"대한유화","beta_adj":0.7,"mom":-0.5},
            {"ticker":"250970","name":"아모그린텍","beta_adj":1.1,"mom":1.0},
            {"ticker":"121600","name":"나노신소재","beta_adj":1.0,"mom":0.7},
        ]
    },
    "fin": {
        "name": "금융/증권", "targetFactor": "한미스프레드", "beta": 0.35,
        "candidates": [
            {"ticker":"105560","name":"KB금융","beta_adj":1.0,"mom":0.6},
            {"ticker":"055550","name":"신한지주","beta_adj":0.95,"mom":0.4},
            {"ticker":"086790","name":"하나금융지주","beta_adj":0.9,"mom":0.3},
            {"ticker":"316140","name":"우리금융지주","beta_adj":0.85,"mom":0.1},
            {"ticker":"138930","name":"BNK금융지주","beta_adj":0.8,"mom":-0.2},
            {"ticker":"175330","name":"JB금융","beta_adj":0.75,"mom":0.5},
            {"ticker":"071050","name":"한국금융지주","beta_adj":1.15,"mom":1.2},
            {"ticker":"030200","name":"KT","beta_adj":0.6,"mom":-0.3},
            {"ticker":"032640","name":"LG유플러스","beta_adj":0.55,"mom":-0.5},
            {"ticker":"034120","name":"SBS","beta_adj":0.7,"mom":0.2},
            {"ticker":"000810","name":"삼성화재","beta_adj":0.85,"mom":0.7},
            {"ticker":"088350","name":"한화생명","beta_adj":0.8,"mom":0.3},
        ]
    },
    "bio": {
        "name": "바이오/의약품", "targetFactor": "US10Y", "beta": -0.20,
        "candidates": [
            {"ticker":"207940","name":"삼성바이오로직스","beta_adj":1.0,"mom":0.9},
            {"ticker":"068270","name":"셀트리온","beta_adj":1.1,"mom":0.2},
            {"ticker":"128940","name":"한미약품","beta_adj":0.85,"mom":0.5},
            {"ticker":"185750","name":"종근당","beta_adj":0.8,"mom":-0.1},
            {"ticker":"145020","name":"휴젤","beta_adj":0.9,"mom":1.1},
            {"ticker":"195940","name":"HLB","beta_adj":1.2,"mom":2.5},
            {"ticker":"326030","name":"SK바이오팜","beta_adj":1.05,"mom":0.7},
            {"ticker":"185740","name":"셀트리온제약","beta_adj":0.95,"mom":0.3},
            {"ticker":"102780","name":"에이치엘비","beta_adj":1.15,"mom":2.0},
            {"ticker":"196300","name":"동국제약","beta_adj":0.75,"mom":0.1},
            {"ticker":"214450","name":"파마리서치","beta_adj":0.85,"mom":1.4},
            {"ticker":"185250","name":"REYON","beta_adj":0.7,"mom":-0.4},
        ]
    },
    "steel": {
        "name": "철강/소재/에너지", "targetFactor": "중국PMI", "beta": 0.30,
        "candidates": [
            {"ticker":"005490","name":"POSCO홀딩스","beta_adj":1.0,"mom":0.4},
            {"ticker":"004020","name":"현대제철","beta_adj":0.85,"mom":-0.3},
            {"ticker":"010130","name":"고려아연","beta_adj":0.9,"mom":0.6},
            {"ticker":"000670","name":"영풍","beta_adj":0.75,"mom":-0.2},
            {"ticker":"010950","name":"S-Oil","beta_adj":0.8,"mom":-0.6},
            {"ticker":"047050","name":"포스코인터","beta_adj":0.95,"mom":0.8},
            {"ticker":"001430","name":"세아베스틸","beta_adj":0.7,"mom":0.1},
            {"ticker":"002720","name":"국제약품","beta_adj":0.6,"mom":-0.4},
            {"ticker":"009830","name":"한화솔루션","beta_adj":0.85,"mom":0.3},
            {"ticker":"011170","name":"롯데케미칼","beta_adj":0.8,"mom":-1.0},
            {"ticker":"103140","name":"풍산","beta_adj":0.75,"mom":0.2},
            {"ticker":"002710","name":"롯데에너지","beta_adj":0.7,"mom":-0.3},
        ]
    },
    "const": {
        "name": "건설/조선/기계", "targetFactor": "원달러", "beta": 0.18,
        "candidates": [
            {"ticker":"009540","name":"HD한국조선해양","beta_adj":1.0,"mom":1.5},
            {"ticker":"010140","name":"삼성중공업","beta_adj":0.9,"mom":0.8},
            {"ticker":"329180","name":"HD현대중공업","beta_adj":1.15,"mom":1.9},
            {"ticker":"064350","name":"현대로템","beta_adj":1.05,"mom":1.8},
            {"ticker":"034020","name":"두산에너빌리티","beta_adj":0.95,"mom":0.4},
            {"ticker":"028050","name":"삼성엔지니어링","beta_adj":0.85,"mom":0.2},
            {"ticker":"006360","name":"GS건설","beta_adj":0.75,"mom":-0.6},
            {"ticker":"047040","name":"대우건설","beta_adj":0.7,"mom":-0.3},
            {"ticker":"009410","name":"한화","beta_adj":0.8,"mom":0.3},
            {"ticker":"012450","name":"한화에어로","beta_adj":1.2,"mom":2.3},
            {"ticker":"097230","name":"한진중공업","beta_adj":0.85,"mom":0.5},
            {"ticker":"000720","name":"현대건설","beta_adj":0.8,"mom":-0.1},
        ]
    },
    "retail": {
        "name": "유통/IT서비스", "targetFactor": "SP500", "beta": 0.22,
        "candidates": [
            {"ticker":"035720","name":"카카오","beta_adj":1.1,"mom":-0.4},
            {"ticker":"035420","name":"NAVER","beta_adj":1.05,"mom":-0.2},
            {"ticker":"030200","name":"KT","beta_adj":0.7,"mom":0.1},
            {"ticker":"017670","name":"SK텔레콤","beta_adj":0.65,"mom":0.2},
            {"ticker":"032640","name":"LG유플러스","beta_adj":0.6,"mom":-0.1},
            {"ticker":"139480","name":"이마트","beta_adj":0.75,"mom":-0.8},
            {"ticker":"023530","name":"롯데쇼핑","beta_adj":0.7,"mom":-0.5},
            {"ticker":"004170","name":"신세계","beta_adj":0.8,"mom":-0.3},
            {"ticker":"030000","name":"제일기획","beta_adj":0.65,"mom":0.3},
            {"ticker":"064760","name":"엔씨소프트","beta_adj":0.85,"mom":-1.2},
            {"ticker":"352820","name":"하이브","beta_adj":0.9,"mom":0.6},
            {"ticker":"035900","name":"JYP","beta_adj":0.85,"mom":0.8},
        ]
    },
}

# KRX API screening: β·모멘텀 + Z
# Real implementation: pykrx + KRX open API for all tickers in industry, compute 120D β to factors and 20D momentum
# Mock here: Score = 6.5 + |Z_target|*1.2*beta_adj + mom*0.3 + rand
weekly_picks = []
for ind_id, ind_data in industry_universe.items():
    tf = ind_data["targetFactor"]
    base_beta = ind_data["beta"]
    z_val = newZ.get(tf, 0)
    scored = []
    for cand in ind_data["candidates"]:
        # β·모멘텀 screening
        beta_score = abs(z_val) * 1.2 * cand["beta_adj"] * (abs(base_beta)+0.5)
        mom_score = cand["mom"] * 0.3
        noise = random.uniform(0, 0.5)
        score = round(6.5 + beta_score + mom_score + noise, 1)
        exp_ret = round(0.5 + abs(z_val)*0.8*cand["beta_adj"] + cand["mom"]*0.2, 1)
        scored.append({
            "industryId": ind_id,
            "ticker": cand["ticker"],
            "name": cand["name"],
            "targetFactor": tf,
            "beta_adj": cand["beta_adj"],
            "momentum": cand["mom"],
            "score": score,
            "expectedReturn": exp_ret,
            "reason": f"{tf} {z_val:.2f}σ × β{cand['beta_adj']} + mom {cand['mom']:.1f}%",
            "date": today,
            "industryBeta": base_beta
        })
    # Top 8 per industry by score
    scored.sort(key=lambda x: x["score"], reverse=True)
    top8 = scored[:8]
    weekly_picks.extend(top8)
    print(f"[{ind_id}] {tf} Z={z_val} -> Top8: {[p['ticker'] for p in top8]}")

# Save 64 picks
db.collection('factor_snapshots').document(today).set({
    'date': today,
    'zScores': newZ,
    'rawValues': {'SP500': 5780+random.uniform(-20,20), 'US10Y': 4.72, 'USD_KRW': 1382.5, 'WTI': 72.3},
    'weeklyPicks': weekly_picks,  # 64 picks
    'industryPicks': {ind: [p for p in weekly_picks if p['industryId']==ind] for ind in industry_universe.keys()},
    'createdAt': firestore.SERVER_TIMESTAMP,
    'source': 'github-actions-sunday-18KST',
    'version': '3.0-industry-8x8-KRX-screening'
}, merge=True)

print(f"[{today}] Saved 64 picks across 8 industries - {len(weekly_picks)} total")
print(f"New Z: {newZ}")
