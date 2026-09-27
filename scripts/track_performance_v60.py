"""
track_performance_v60.py - KOSPI Quant Terminal v60 - 10 Factors China Proxy + 64 Picks 성과추적 100% REAL

개선점 v56 -> v60:
- China Proxy 팩터 (구리 HG=F, 상해종합 000001.SS) 지원 - targetFactor에 구리/상해종합 포함
- price_provider v60 사용 (yfinance 95% REAL + KRX fallback 구조)
- KOSPI(^KS11) 대비 초과수익 + 절대수익 동시 계산
- performance_tracking/{recDate}_{ticker}_{evalDate} + performance_snapshots/{evalDate} 요약
- 64 Picks 전체 추적 (v56은 8 Picks 제한이었음) - 4주간 256개 추적

실행: 매일 16:00 KST (장 마감 후)
- daily_update.py가 07:30에 factor_snapshots 생성
- track_performance_v60.py가 16:00에 실제 수익률 계산

Firestore 구조:
- performance_tracking/{2026-09-20_005930_2026-09-27} 개별 종목 성과
- performance_snapshots/{2026-09-27} 일별 요약 (Hit Rate, Avg Return 등 대시보드용)
"""

import os
import json
import datetime
from datetime import timezone, timedelta

# ========== Firebase Init ==========
try:
    import firebase_admin
    from firebase_admin import credentials, firestore

    cred_json_str = os.environ.get("FIREBASE_SERVICE_ACCOUNT", "")
    if cred_json_str:
        cred_dict = json.loads(cred_json_str)
        if not firebase_admin._apps:
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred)
        db = firestore.client()
        print("[Firebase] connected - kospi-quant v60 performance tracker")
    else:
        db = None
        print("[Firebase] No service account - local mode (will save to json)")
except Exception as e:
    db = None
    print(f"[Firebase] init error: {e}")

# ========== Price Provider v60 ==========
try:
    from price_provider import get_stock_return
    HAS_PROVIDER = True
    print("[track v60] price_provider v60 loaded - yfinance + KRX abstraction")
except ImportError:
    try:
        from scripts.price_provider import get_stock_return
        HAS_PROVIDER = True
        print("[track v60] price_provider loaded from scripts")
    except Exception as e:
        HAS_PROVIDER = False
        print(f"[track v60] price_provider not found: {e}, using direct yfinance fallback")

KST = timezone(timedelta(hours=9))
today = datetime.datetime.now(KST).strftime('%Y-%m-%d')
today_dt = datetime.datetime.now(KST)
print(f"\n=== KOSPI Quant Terminal v60 - Performance Tracking {today} ===")
print(f"China Proxy 10 Factors + 64 Picks + DART - 100% REAL")

# ========== Helper: yfinance direct fallback ==========
def get_return_direct_yfinance(ticker: str, buy_date: str, eval_date: str):
    """price_provider 없을 때 직접 yfinance로 수익률 계산"""
    try:
        import yfinance as yf
        from datetime import datetime as dt, timedelta

        yf_ticker = f"{ticker}.KS" if ticker.isdigit() and len(ticker) == 6 else ticker
        if yf_ticker.endswith(".KS.KS"):
            yf_ticker = yf_ticker.replace(".KS.KS", ".KS")

        t = yf.Ticker(yf_ticker)
        buy_dt = dt.strptime(buy_date, '%Y-%m-%d')
        eval_dt = dt.strptime(eval_date, '%Y-%m-%d')
        start = (buy_dt - timedelta(days=7)).strftime('%Y-%m-%d')
        end = (eval_dt + timedelta(days=3)).strftime('%Y-%m-%d')

        hist = t.history(start=start, end=end)
        if hist.empty:
            return None, 0.0, 0.0, "empty hist"

        hist.index = hist.index.tz_localize(None)
        # 매수일 가격 찾기
        buy_date_strs = [d.strftime('%Y-%m-%d') for d in hist.index]
        if buy_date in buy_date_strs:
            buy_price = float(hist.loc[hist.index.strftime('%Y-%m-%d') == buy_date]['Close'].iloc[0])
        else:
            before = hist[hist.index < buy_dt]
            if before.empty:
                return None, 0.0, 0.0, f"no price before {buy_date}"
            buy_price = float(before['Close'].iloc[-1])

        eval_price = float(hist['Close'].iloc[-1])
        ret = (eval_price - buy_price) / buy_price if buy_price != 0 else 0
        return ret, buy_price, eval_price, "yfinance direct"
    except Exception as e:
        print(f"[direct yf] Error {ticker}: {e}")
        return None, 0.0, 0.0, str(e)

def get_kospi_return(buy_date: str, eval_date: str):
    """KOSPI 지수 수익률 (^KS11)"""
    try:
        import yfinance as yf
        kos = yf.Ticker("^KS11").history(start=buy_date, end=eval_date)
        if kos.empty or len(kos) < 2:
            # 넉넉하게 5일 여유
            from datetime import timedelta
            import datetime as dt
            bd = dt.datetime.strptime(buy_date, '%Y-%m-%d')
            ed = dt.datetime.strptime(eval_date, '%Y-%m-%d')
            s = (bd - timedelta(days=5)).strftime('%Y-%m-%d')
            e = (ed + timedelta(days=3)).strftime('%Y-%m-%d')
            kos = yf.Ticker("^KS11").history(start=s, end=e)
        if kos.empty:
            return 0.0
        kret = (float(kos['Close'].iloc[-1]) - float(kos['Close'].iloc[0])) / float(kos['Close'].iloc[0]) if float(kos['Close'].iloc[0]) != 0 else 0
        return kret
    except Exception as e:
        print(f"[KOSPI] Error: {e}")
        return 0.0

# ========== Load Snapshots ==========
if not db:
    print("[track v60] Local mode - loading latest_factors.json if exists")
    try:
        with open("latest_factors.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            snapshots_data = [data]
    except:
        try:
            with open("scripts/latest_factors.json", "r", encoding="utf-8") as f:
                data = json.load(f)
                snapshots_data = [data]
        except:
            snapshots_data = []
            print("No snapshots found in local mode")
else:
    # 최근 30일 스냅샷 로드 (4주치)
    try:
        snapshots = list(db.collection('factor_snapshots').order_by('date', direction=firestore.Query.DESCENDING).limit(30).stream())
        snapshots_data = []
        for snap in snapshots:
            d = snap.to_dict()
            d['_id'] = snap.id
            snapshots_data.append(d)
        print(f"Loaded {len(snapshots_data)} snapshots from Firestore (last 30)")
    except Exception as e:
        print(f"Firestore load error: {e}")
        snapshots_data = []

if not snapshots_data:
    print("[track v60] No snapshots to track - need daily_update.py to run first")
    exit(0)

# ========== Main Tracking Loop ==========
batch = db.batch() if db else None
batch_cnt = 0
ok = 0
fail = 0
all_returns = []
all_excess = []
hits = 0
total_for_hit = 0

# 최근 4개 스냅샷만 추적 (너무 오래된 건 제외, 4주 x 64 = 256개)
target_snapshots = snapshots_data[:4]
print(f"Tracking {len(target_snapshots)} recent snapshots (4 weeks x 64 picks = up to 256)")

for snap_data in target_snapshots:
    rec_date = snap_data.get('date')
    if not rec_date:
        continue

    try:
        rec_dt = datetime.datetime.strptime(rec_date, '%Y-%m-%d').replace(tzinfo=KST)
        days_elapsed = (today_dt - rec_dt).days
    except:
        days_elapsed = 7

    if days_elapsed < 1:
        print(f"Skip {rec_date} - too recent ({days_elapsed}d)")
        continue

    picks = snap_data.get('weeklyPicks', [])
    if not picks:
        print(f"No picks in {rec_date}")
        continue

    print(f"\n--- {rec_date} ({days_elapsed}d ago) - {len(picks)} picks ---")

    for pick in picks:
        ticker = pick.get('ticker')
        name = pick.get('name', ticker)
        target_factor = pick.get('targetFactor', '')
        z_at_rec = pick.get('zAtRec', 0)
        score = pick.get('score', 0)
        industry = pick.get('industryId', '')
        pred_industry = pick.get('predIndustry', 0)

        if not ticker:
            continue

        try:
            # 수익률 계산
            if HAS_PROVIDER:
                ret = get_stock_return(ticker, rec_date, today, source="yfinance")
                src_msg = "price_provider v60 yfinance REAL"
            else:
                ret, _, _, src_msg = get_return_direct_yfinance(ticker, rec_date, today)

            if ret is None:
                fail += 1
                continue

            kret = get_kospi_return(rec_date, today)
            excess = ret - kret

            all_returns.append(ret)
            all_excess.append(excess)

            # Hit Rate 계산: Score가 높았을 때(>7.0) 수익이 양수면 Hit
            # 또는 Z*예측이 양수일 때 초과수익 양수면 Hit (팩터 방향성)
            if score >= 7.0:
                total_for_hit += 1
                if ret > 0:
                    hits += 1
            # Z 기반 Hit도 계산 (factor_validity용)
            # 여기서는 단순 수익 양수 여부로

            doc_id = f"{rec_date}_{ticker}_{today}"
            doc = {
                'recDate': rec_date,
                'evalDate': today,
                'ticker': ticker,
                'name': name,
                'industryId': industry,
                'targetFactor': target_factor,
                'zAtRec': z_at_rec,
                'score': score,
                'predIndustry': pred_industry,
                'daysElapsed': days_elapsed,
                'return': round(float(ret), 6),
                'returnPct': round(float(ret) * 100, 2),
                'kospiReturn': round(float(kret), 6),
                'kospiReturnPct': round(float(kret) * 100, 2),
                'excessReturn': round(float(excess), 6),
                'excessReturnPct': round(float(excess) * 100, 2),
                'source': f'yfinance-REAL-v60-ChinaProxy-{src_msg}',
                'priceSource': 'yfinance .KS REAL + price_provider v60',
                'chinaProxy': '구리(HG=F) + 상해종합(000001.SS) 기반 picks',
                'version': 'v60-64Picks-DART-REAL',
                'createdAt': firestore.SERVER_TIMESTAMP if db else today,
            }

            if db:
                batch.set(db.collection('performance_tracking').document(doc_id), doc, merge=True)
                batch_cnt += 1
                ok += 1
                if batch_cnt >= 400:
                    batch.commit()
                    print(f"  Committed {batch_cnt} docs")
                    batch = db.batch()
                    batch_cnt = 0

            print(f"  [OK] {ticker} {name} ({target_factor}): {ret*100:+.2f}% vs KOSPI {kret*100:+.2f}% excess {excess*100:+.2f}% (Z {z_at_rec:+.2f} Score {score})")

        except Exception as e:
            fail += 1
            print(f"  [ERR] {ticker} {name}: {e}")
            import traceback
            traceback.print_exc()

# Final commit for tracking docs
if db and batch_cnt > 0:
    batch.commit()
    print(f"\nFinal commit {batch_cnt} tracking docs")

# ========== Summary Snapshot for Dashboard ==========
if all_returns:
    import numpy as np
    avg_ret = float(np.mean(all_returns))
    avg_excess = float(np.mean(all_excess))
    hit_rate = (hits / total_for_hit) if total_for_hit > 0 else 0
    win_rate = sum(1 for r in all_returns if r > 0) / len(all_returns) if all_returns else 0
    excess_win = sum(1 for r in all_excess if r > 0) / len(all_excess) if all_excess else 0

    summary = {
        'date': today,
        'timestamp': datetime.datetime.now(KST),
        'totalPicks': len(all_returns),
        'avgReturn': round(avg_ret, 6),
        'avgReturnPct': round(avg_ret * 100, 2),
        'avgExcessReturn': round(avg_excess, 6),
        'avgExcessReturnPct': round(avg_excess * 100, 2),
        'hitRate': round(hit_rate, 4),
        'hitRatePct': round(hit_rate * 100, 2),
        'winRate': round(win_rate, 4),
        'winRatePct': round(win_rate * 100, 2),
        'excessWinRate': round(excess_win, 4),
        'excessWinRatePct': round(excess_win * 100, 2),
        'ok': ok,
        'fail': fail,
        'source': 'yfinance-REAL-v60-ChinaProxy-64Picks',
        'version': 'v60-performance-snapshot',
        'chinaProxy': '구리+상해종합 기반 64 Picks 성과',
        'period': f'{target_snapshots[-1].get("date") if target_snapshots else ""} ~ {today}',
    }

    if db:
        try:
            db.collection('performance_snapshots').document(today).set(summary, merge=True)
            print(f"\n[Summary] Saved performance_snapshots/{today}")
        except Exception as e:
            print(f"Summary save error: {e}")
    else:
        with open(f"performance_summary_{today}.json", "w", encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        print(f"Saved local summary")

    print(f"""
=== Performance Summary {today} ===
Total: {len(all_returns)} picks
Avg Return: {avg_ret*100:+.2f}%
Avg Excess vs KOSPI: {avg_excess*100:+.2f}%
Hit Rate (Score>=7): {hit_rate*100:.1f}% ({hits}/{total_for_hit})
Win Rate: {win_rate*100:.1f}%
Excess Win Rate: {excess_win*100:.1f}%
Success: {ok} Fail: {fail}
Source: yfinance REAL v60 China Proxy 64 Picks
""")
else:
    print("No returns calculated")

print(f"\n[{today}] Done - success {ok} fail {fail} - v60 64 Picks China Proxy REAL")
