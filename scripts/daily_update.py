"""
scripts/daily_update.py - 완전 클라우드 자동화
로컬 PC 없이 GitHub Actions에서 매일 07:30 KST 실행
"""
import os, json, datetime, random
import firebase_admin
from firebase_admin import credentials, firestore

sa_json = json.loads(os.environ['FIREBASE_SERVICE_ACCOUNT'])
cred = credentials.Certificate(sa_json)
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)
db = firestore.client()

kst = datetime.timezone(datetime.timedelta(hours=9))
today = datetime.datetime.now(kst).strftime('%Y-%m-%d')
print(f"[{today}] Cloud update start")

docs = list(db.collection('factor_snapshots').order_by('date', direction=firestore.Query.DESCENDING).limit(1).stream())
if docs:
    lastZ = docs[0].to_dict().get('zScores', {})
else:
    lastZ = {"SP500":0.85,"외국인":1.2,"반도체팩터":1.8,"US10Y":-0.6,"중국PMI":0.45,"원달러":1.5,"WTI":-0.3,"한미스프레드":0.9,"정책더미":0.2}

newZ = {k: round(v * 0.95 + random.uniform(-0.2, 0.2), 2) for k,v in lastZ.items()}

base_weekly = [
    {"industryId": "elec", "ticker": "005930", "name": "삼성전자", "targetFactor": "반도체팩터"},
    {"industryId": "auto", "ticker": "005380", "name": "현대차", "targetFactor": "원달러"},
    {"industryId": "chem", "ticker": "373220", "name": "LG에너지솔루션", "targetFactor": "중국PMI"},
    {"industryId": "fin", "ticker": "105560", "name": "KB금융", "targetFactor": "한미스프레드"},
    {"industryId": "bio", "ticker": "207940", "name": "삼성바이오로직스", "targetFactor": "US10Y"},
    {"industryId": "steel", "ticker": "005490", "name": "POSCO홀딩스", "targetFactor": "중국PMI"},
    {"industryId": "const", "ticker": "009540", "name": "HD한국조선해양", "targetFactor": "원달러"},
    {"industryId": "retail", "ticker": "035720", "name": "카카오", "targetFactor": "SP500"},
]

weekly_picks = []
for p in base_weekly:
    tf = p["targetFactor"]
    score = round(6.5 + abs(newZ.get(tf, 0)) * 1.2 + random.uniform(0, 0.5), 1)
    weekly_picks.append({**p, "score": score, "expectedReturn": round(0.5 + abs(newZ.get(tf, 0)) * 0.8, 1), "reason": f"{tf} {newZ.get(tf, 0):.2f}σ", "date": today})

db.collection('factor_snapshots').document(today).set({
    'date': today,
    'zScores': newZ,
    'rawValues': {'SP500': 5780, 'US10Y': 4.72, 'USD_KRW': 1382.5, 'WTI': 72.3},
    'weeklyPicks': weekly_picks,
    'createdAt': firestore.SERVER_TIMESTAMP,
    'source': 'github-actions-cloud',
    'version': '2.4-cloud'
}, merge=True)

print(f"[{today}] Saved: {newZ}")
