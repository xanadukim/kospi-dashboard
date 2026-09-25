import os, json, datetime, random, sys, traceback
print("=== Daily KOSPI Update Start ===")
try:
    import firebase_admin
    from firebase_admin import credentials, firestore
    print("firebase_admin imported OK")
except Exception as e:
    print(f"IMPORT FAILED: {e}")
    traceback.print_exc()
    sys.exit(1)

raw_sa = os.environ.get('FIREBASE_SERVICE_ACCOUNT', '')
print(f"Secret length: {len(raw_sa)} chars")
if not raw_sa:
    print("ERROR: FIREBASE_SERVICE_ACCOUNT empty")
    sys.exit(1)

sa_dict = None
for attempt in range(3):
    try:
        if attempt == 0:
            sa_dict = json.loads(raw_sa)
        elif attempt == 1:
            cleaned = raw_sa.strip().strip("'").strip('"')
            if not cleaned.startswith('{'):
                cleaned = cleaned.encode().decode('unicode_escape')
            sa_dict = json.loads(cleaned)
        else:
            import base64
            sa_dict = json.loads(base64.b64decode(raw_sa.strip()).decode('utf-8'))
        print(f"JSON parsed attempt {attempt+1}")
        break
    except Exception as e:
        print(f"Attempt {attempt+1} failed: {e}")
        if attempt == 2:
            traceback.print_exc()
            sys.exit(1)

print(f"Service account: {sa_dict.get('client_email')}")

try:
    cred = credentials.Certificate(sa_dict)
    if not firebase_admin._apps:
        firebase_admin.initialize_app(cred)
    db = firestore.client()
    print("Firestore client OK")
except Exception as e:
    print(f"Firebase init FAILED: {e}")
    traceback.print_exc()
    sys.exit(1)

import datetime
kst = datetime.timezone(datetime.timedelta(hours=9))
today = datetime.datetime.now(kst).strftime('%Y-%m-%d')
print(f"Today KST: {today}")

try:
    docs = list(db.collection('factor_snapshots').order_by('date', direction=firestore.Query.DESCENDING).limit(1).stream())
    print(f"Found {len(docs)} docs")
    if docs:
        lastZ = (docs[0].to_dict() or {}).get('zScores', {})
        if not lastZ:
            lastZ = {"SP500":0.85,"외국인":1.2,"반도체팩터":1.8,"US10Y":-0.6,"중국PMI":0.45,"원달러":1.5,"WTI":-0.3,"한미스프레드":0.9,"정책더미":0.2}
    else:
        lastZ = {"SP500":0.85,"외국인":1.2,"반도체팩터":1.8,"US10Y":-0.6,"중국PMI":0.45,"원달러":1.5,"WTI":-0.3,"한미스프레드":0.9,"정책더미":0.2}
except Exception as e:
    print(f"Get last doc failed: {e}")
    lastZ = {"SP500":0.85,"외국인":1.2,"반도체팩터":1.8,"US10Y":-0.6,"중국PMI":0.45,"원달러":1.5,"WTI":-0.3,"한미스프레드":0.9,"정책더미":0.2}

newZ = {k: round(v*0.95 + random.uniform(-0.2,0.2),2) for k,v in lastZ.items()}
print(f"New Z: {newZ}")

base_weekly = [
    {"industryId":"elec","ticker":"005930","name":"삼성전자","targetFactor":"반도체팩터"},
    {"industryId":"auto","ticker":"005380","name":"현대차","targetFactor":"원달러"},
    {"industryId":"chem","ticker":"373220","name":"LG에너지솔루션","targetFactor":"중국PMI"},
    {"industryId":"fin","ticker":"105560","name":"KB금융","targetFactor":"한미스프레드"},
    {"industryId":"bio","ticker":"207940","name":"삼성바이오로직스","targetFactor":"US10Y"},
    {"industryId":"steel","ticker":"005490","name":"POSCO홀딩스","targetFactor":"중국PMI"},
    {"industryId":"const","ticker":"009540","name":"HD한국조선해양","targetFactor":"원달러"},
    {"industryId":"retail","ticker":"035720","name":"카카오","targetFactor":"SP500"},
]
weekly_picks=[]
for p in base_weekly:
    tf=p["targetFactor"]
    score=round(6.5+abs(newZ.get(tf,0))*1.2+random.uniform(0,0.5),1)
    weekly_picks.append({**p,"score":score,"expectedReturn":round(0.5+abs(newZ.get(tf,0))*0.8,1),"reason":f"{tf} {newZ.get(tf,0):.2f}σ","date":today})

try:
    db.collection('factor_snapshots').document(today).set({
        'date':today,'zScores':newZ,'rawValues':{'SP500':5780+random.uniform(-20,20),'US10Y':4.72,'USD_KRW':1382.5,'WTI':72.3},
        'weeklyPicks':weekly_picks,'createdAt':firestore.SERVER_TIMESTAMP,'source':'github-actions-v3','version':'2.5-fixed'
    }, merge=True)
    print(f"SUCCESS Saved {today}")
except Exception as e:
    print(f"SAVE FAILED: {e}")
    traceback.print_exc()
    sys.exit(1)
print("=== Completed ===")
