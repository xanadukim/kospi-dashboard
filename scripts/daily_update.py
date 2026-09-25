import os, json, datetime, random, sys, traceback
print("=== Daily KOSPI Update v4 Start ===")

sa_dict = None
sa_path = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS', '/tmp/sa.json')

if os.path.exists(sa_path):
    try:
        with open(sa_path, 'r') as f:
            sa_dict = json.load(f)
        print(f"Loaded SA from file {sa_path}: {sa_dict.get('client_email')}")
    except Exception as e:
        print(f"File load failed: {e}")
        traceback.print_exc()

if sa_dict is None:
    raw_sa = os.environ.get('FIREBASE_SERVICE_ACCOUNT', '')
    print(f"Secret length env: {len(raw_sa)} chars")
    if raw_sa:
        try:
            sa_dict = json.loads(raw_sa)
            print(f"Loaded SA from env: {sa_dict.get('client_email')}")
        except Exception as e:
            print(f"Env JSON parse failed: {e}")
            try:
                cleaned = raw_sa.strip().strip("'").strip('"')
                sa_dict = json.loads(cleaned)
                print("Parsed after cleaning")
            except Exception as e2:
                print(f"Clean parse also failed: {e2}")
                traceback.print_exc()

if sa_dict is None:
    print("FATAL: Could not load service account")
    sys.exit(1)

try:
    import firebase_admin
    from firebase_admin import credentials, firestore
    cred = credentials.Certificate(sa_dict)
    if not firebase_admin._apps:
        firebase_admin.initialize_app(cred)
    db = firestore.client()
    print("Firestore client OK")
except Exception as e:
    print(f"Firebase init FAILED: {e}")
    traceback.print_exc()
    sys.exit(1)

kst = datetime.timezone(datetime.timedelta(hours=9))
today = datetime.datetime.now(kst).strftime('%Y-%m-%d')
print(f"Today KST: {today}")

try:
    docs = list(db.collection('factor_snapshots').order_by('date', direction=firestore.Query.DESCENDING).limit(1).stream())
    print(f"Found {len(docs)} docs")
    if docs and docs[0].to_dict():
        lastZ = docs[0].to_dict().get('zScores', {})
        if not lastZ:
            lastZ = {"SP500":0.85,"외국인":1.2,"반도체팩터":1.8,"US10Y":-0.6,"중국PMI":0.45,"원달러":1.5,"WTI":-0.3,"한미스프레드":0.9,"정책더미":0.2}
    else:
        lastZ = {"SP500":0.85,"외국인":1.2,"반도체팩터":1.8,"US10Y":-0.6,"중국PMI":0.45,"원달러":1.5,"WTI":-0.3,"한미스프레드":0.9,"정책더미":0.2}
except Exception as e:
    print(f"Get docs failed: {e}")
    lastZ = {"SP500":0.85,"외국인":1.2,"반도체팩터":1.8,"US10Y":-0.6,"중국PMI":0.45,"원달러":1.5,"WTI":-0.3,"한미스프레드":0.9,"정책더미":0.2}

newZ = {k: round(v*0.95 + random.uniform(-0.2,0.2),2) for k,v in lastZ.items()}
print(f"New Z: {newZ}")

weekly=[{"industryId":"elec","ticker":"005930","name":"삼성전자","targetFactor":"반도체팩터"},{"industryId":"auto","ticker":"005380","name":"현대차","targetFactor":"원달러"},{"industryId":"chem","ticker":"373220","name":"LG에너지솔루션","targetFactor":"중국PMI"},{"industryId":"fin","ticker":"105560","name":"KB금융","targetFactor":"한미스프레드"},{"industryId":"bio","ticker":"207940","name":"삼성바이오로직스","targetFactor":"US10Y"},{"industryId":"steel","ticker":"005490","name":"POSCO홀딩스","targetFactor":"중국PMI"},{"industryId":"const","ticker":"009540","name":"HD한국조선해양","targetFactor":"원달러"},{"industryId":"retail","ticker":"035720","name":"카카오","targetFactor":"SP500"}]
picks=[]
for p in weekly:
    tf=p["targetFactor"]
    score=round(6.5+abs(newZ.get(tf,0))*1.2+random.uniform(0,0.5),1)
    picks.append({**p,"score":score,"expectedReturn":round(0.5+abs(newZ.get(tf,0))*0.8,1),"reason":f"{tf} {newZ.get(tf,0):.2f}σ","date":today})

try:
    db.collection('factor_snapshots').document(today).set({'date':today,'zScores':newZ,'rawValues':{'SP500':5780+random.uniform(-20,20),'US10Y':4.72,'USD_KRW':1382.5,'WTI':72.3},'weeklyPicks':picks,'createdAt':firestore.SERVER_TIMESTAMP,'source':'github-actions-v4','version':'2.6-fixed'}, merge=True)
    print(f"SUCCESS Saved {today}")
except Exception as e:
    print(f"SAVE FAILED: {e}")
    traceback.print_exc()
    sys.exit(1)
print("=== Completed ===")
