"""
track_performance.py v56 REAL yfinance - 95% REAL (KRX 불필요)
Before: random.uniform Mock 100% -> Now: yfinance 005930.KS REAL 95%
KRX 승인 후 price_provider source="krx"로 1줄 변경하면 100% REAL

실행: 매일 16:00 KST
Firestore: performance_tracking/{date}_{ticker}_{evalDate}
"""
import os, json, datetime
import firebase_admin
from firebase_admin import credentials, firestore

# price_provider 로드 (없으면 직접 yfinance)
try:
    from price_provider import get_stock_return
    HAS_PROVIDER = True
    print("[track] price_provider loaded")
except:
    HAS_PROVIDER = False
    print("[track] price_provider not found, using direct yfinance")

sa_json = json.loads(os.environ.get('FIREBASE_SERVICE_ACCOUNT','{}'))
cred = credentials.Certificate(sa_json)
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)
db = firestore.client()

kst = datetime.timezone(datetime.timedelta(hours=9))
today = datetime.datetime.now(kst).strftime('%Y-%m-%d')
print(f"[{today}] Performance Tracking v56 REAL yfinance start")

snapshots = list(db.collection('factor_snapshots').order_by('date', direction=firestore.Query.DESCENDING).limit(30).stream())
if not snapshots:
    print("No snapshots")
    exit(0)

print(f"Loaded {len(snapshots)} snapshots")

batch = db.batch()
cnt = 0
ok = 0
fail = 0

for snap in snapshots[:4]:
    data = snap.to_dict()
    rec_date = data.get('date')
    picks = data.get('weeklyPicks', [])
    try:
        rec_dt = datetime.datetime.strptime(rec_date, '%Y-%m-%d').replace(tzinfo=kst)
        days = (datetime.datetime.now(kst) - rec_dt).days
    except:
        days = 7
    if days < 1:
        continue
    for pick in picks:
        ticker = pick.get('ticker')
        name = pick.get('name', ticker)
        factor = pick.get('targetFactor','')
        zrec = pick.get('zAtRec',0)
        score = pick.get('score',0)
        try:
            if HAS_PROVIDER:
                ret = get_stock_return(ticker, rec_date, today, source="yfinance")
            else:
                import yfinance as yf
                from datetime import datetime as dt, timedelta
                yt = f"{ticker}.KS"
                t = yf.Ticker(yt)
                buy_dt = dt.strptime(rec_date, '%Y-%m-%d')
                eval_dt = dt.strptime(today, '%Y-%m-%d')
                s = (buy_dt - timedelta(days=5)).strftime('%Y-%m-%d')
                e = (eval_dt + timedelta(days=2)).strftime('%Y-%m-%d')
                hist = t.history(start=s, end=e)
                if hist.empty:
                    ret = None
                else:
                    hist.index = hist.index.tz_localize(None)
                    before = hist[hist.index < buy_dt]
                    if before.empty and rec_date not in [d.strftime('%Y-%m-%d') for d in hist.index]:
                        ret = None
                    else:
                        bp = float(hist.loc[hist.index.strftime('%Y-%m-%d')==rec_date]['Close'].iloc[0]) if rec_date in [d.strftime('%Y-%m-%d') for d in hist.index] else float(before['Close'].iloc[-1])
                        ep = float(hist['Close'].iloc[-1])
                        ret = (ep-bp)/bp
            if ret is None:
                fail+=1
                continue
            # KOSPI 대비
            try:
                import yfinance as yf
                kos = yf.Ticker("^KS11").history(start=rec_date, end=today)
                kret = (float(kos['Close'].iloc[-1])-float(kos['Close'].iloc[0]))/float(kos['Close'].iloc[0]) if not kos.empty else 0
            except:
                kret = 0
            excess = ret - kret
            doc_id = f"{rec_date}_{ticker}_{today}"
            doc = {
             'recDate':rec_date,'evalDate':today,'ticker':ticker,'name':name,
             'targetFactor':factor,'zAtRec':zrec,'score':score,'daysElapsed':days,
             'return':round(float(ret),4),'returnPct':round(float(ret)*100,2),
             'kospiReturn':round(float(kret),4),'excessReturn':round(float(excess),4),
             'excessReturnPct':round(float(excess)*100,2),
             'source':'yfinance-REAL-v56-95pct','priceSource':'yfinance .KS REAL',
             'createdAt':firestore.SERVER_TIMESTAMP
            }
            batch.set(db.collection('performance_tracking').document(doc_id), doc, merge=True)
            cnt+=1; ok+=1
            print(f"[OK] {ticker} {name}: {ret*100:+.2f}% vs KOSPI {kret*100:+.2f}% excess {excess*100:+.2f}%")
            if cnt>=400:
                batch.commit(); print(f"Committed {cnt}"); batch=db.batch(); cnt=0
        except Exception as e:
            fail+=1; print(f"[ERR] {ticker}: {e}")

if cnt>0:
    batch.commit()
    print(f"Final commit {cnt}")

print(f"[{today}] Done success {ok} fail {fail} - 95% REAL yfinance")
