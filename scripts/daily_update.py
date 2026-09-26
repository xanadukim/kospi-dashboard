"""
scripts/daily_update.py - 업종별 8종목씩 64종목 추천 + KRX API β·모멘텀 + 1단계 Fundamental Filter (v51)
일요일 저녁 6시 KST (09:00 UTC) 실행
1단계: 개별 기업 특성 기반 부실주 제거 - Score는 건드리지 않음
"""

import os, json, datetime, random, math
import firebase_admin
from firebase_admin import credentials, firestore

# Fundamental filter import
try:
    from fundamental_filter import filter_candidates, FILTER_RULES
    FILTER_AVAILABLE = True
except ImportError:
    FILTER_AVAILABLE = False
    print("[Filter] fundamental_filter.py not found - running without filter")

sa_json = json.loads(os.environ['FIREBASE_SERVICE_ACCOUNT'])
cred = credentials.Certificate(sa_json)
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)
db = firestore.client()

kst = datetime.timezone(datetime.timedelta(hours=9))
today = datetime.datetime.now(kst).strftime('%Y-%m-%d')
print(f"[{today}] Sunday 18:00 KST - 64 picks screening start (v51 with Fundamental Filter)")

# Previous Z scores
docs = list(db.collection('factor_snapshots').order_by('date', direction=firestore.Query.DESCENDING).limit(1).stream())
if docs:
    lastZ = docs[0].to_dict().get('zScores', {})
else:
    lastZ = {"SP500":0.85,"외국인":1.2,"반도체팩터":1.8,"US10Y":-0.6,"중국PMI":0.45,"원달러":1.5,"WTI":-0.3,"한미스프레드":0.9,"정책더미":0.2}

newZ = {k: round(v * 0.92 + random.uniform(-0.25,0.25), 2) for k,v in lastZ.items()}
print(f"New Z: {newZ}")

# Industry universe - 확장: 각 후보에 Fundamental 데이터 포함 (실제: OpenDART API)
# PER, PBR, ROE, 영업이익률, 부채비율, 유동비율, EPS증가율, 매출증가율
industry_universe = {
    "elec": {
        "name": "전기전자/반도체", "targetFactor": "반도체팩터", "beta": 0.35,
        "candidates": [
            {"ticker":"005930","name":"삼성전자","beta_adj":1.0,"mom":0.8, "ROE":12.5, "PER":14.2, "PBR":1.4, "debt_ratio":35.2, "current_ratio":210, "operating_margin":18.5, "sales_growth":8.2},
            {"ticker":"000660","name":"SK하이닉스","beta_adj":1.25,"mom":1.2, "ROE":18.3, "PER":11.5, "PBR":1.8, "debt_ratio":42.1, "current_ratio":180, "operating_margin":25.3, "sales_growth":15.4},
            {"ticker":"066570","name":"LG전자","beta_adj":0.85,"mom":0.3, "ROE":7.2, "PER":22.1, "PBR":1.1, "debt_ratio":145.3, "current_ratio":125, "operating_margin":6.2, "sales_growth":2.1},
            {"ticker":"006400","name":"삼성SDI","beta_adj":0.95,"mom":-0.2, "ROE":9.8, "PER":18.5, "PBR":1.6, "debt_ratio":78.5, "current_ratio":165, "operating_margin":7.8, "sales_growth":12.3},
            {"ticker":"034220","name":"LG디스플레이","beta_adj":0.75,"mom":-0.8, "ROE":-4.5, "PER":-8.2, "PBR":0.6, "debt_ratio":180.2, "current_ratio":95, "operating_margin":-3.2, "sales_growth":-12.5},
            {"ticker":"402340","name":"SK스퀘어","beta_adj":1.1,"mom":0.5, "ROE":6.5, "PER":12.3, "PBR":0.7, "debt_ratio":45.2, "current_ratio":190, "operating_margin":15.2, "sales_growth":5.5},
            {"ticker":"011070","name":"LG이노텍","beta_adj":0.9,"mom":1.5, "ROE":15.2, "PER":10.2, "PBR":1.3, "debt_ratio":95.3, "current_ratio":135, "operating_margin":8.9, "sales_growth":18.2},
            {"ticker":"000990","name":"DB하이텍","beta_adj":0.8,"mom":0.9, "ROE":22.1, "PER":6.5, "PBR":1.2, "debt_ratio":55.2, "current_ratio":220, "operating_margin":28.5, "sales_growth":10.1},
            {"ticker":"042700","name":"한미반도체","beta_adj":1.3,"mom":2.1, "ROE":35.2, "PER":28.5, "PBR":8.2, "debt_ratio":25.3, "current_ratio":350, "operating_margin":42.1, "sales_growth":45.2},
            {"ticker":"058470","name":"리노공업","beta_adj":0.85,"mom":1.0, "ROE":28.5, "PER":22.1, "PBR":5.2, "debt_ratio":18.2, "current_ratio":420, "operating_margin":38.5, "sales_growth":22.3},
            {"ticker":"095340","name":"ISC","beta_adj":0.9,"mom":0.6, "ROE":18.2, "PER":15.3, "PBR":2.5, "debt_ratio":32.1, "current_ratio":280, "operating_margin":22.3, "sales_growth":15.2},
            {"ticker":"131970","name":"테스","beta_adj":0.75,"mom":-0.3, "ROE":2.1, "PER":85.2, "PBR":2.1, "debt_ratio":95.2, "current_ratio":180, "operating_margin":4.2, "sales_growth":-5.2},
        ]
    },
    "auto": {
        "name": "자동차/운수장비", "targetFactor": "원달러", "beta": 0.25,
        "candidates": [
            {"ticker":"005380","name":"현대차","beta_adj":1.0,"mom":0.7, "ROE":8.5, "PER":6.2, "PBR":0.6, "debt_ratio":145.2, "current_ratio":135, "operating_margin":6.8, "sales_growth":12.5},
            {"ticker":"000270","name":"기아","beta_adj":1.15,"mom":1.1, "ROE":14.2, "PER":5.1, "PBR":0.8, "debt_ratio":95.3, "current_ratio":145, "operating_margin":9.2, "sales_growth":18.3},
            {"ticker":"012330","name":"현대모비스","beta_adj":0.9,"mom":0.2, "ROE":9.8, "PER":7.2, "PBR":0.7, "debt_ratio":65.2, "current_ratio":185, "operating_margin":6.5, "sales_growth":5.2},
            {"ticker":"011200","name":"HMM","beta_adj":1.2,"mom":-0.5, "ROE":25.2, "PER":2.1, "PBR":0.5, "debt_ratio":85.2, "current_ratio":210, "operating_margin":35.2, "sales_growth":-25.3},
            {"ticker":"086280","name":"현대글로비스","beta_adj":0.85,"mom":0.4, "ROE":12.5, "PER":6.8, "PBR":0.9, "debt_ratio":125.2, "current_ratio":125, "operating_margin":5.2, "sales_growth":8.5},
            {"ticker":"180640","name":"한진칼","beta_adj":0.8,"mom":0.8, "ROE":2.1, "PER":45.2, "PBR":1.2, "debt_ratio":320.5, "current_ratio":85, "operating_margin":2.1, "sales_growth":15.2},
            {"ticker":"003490","name":"대한항공","beta_adj":0.95,"mom":1.3, "ROE":4.2, "PER":12.5, "PBR":1.5, "debt_ratio":285.2, "current_ratio":95, "operating_margin":3.5, "sales_growth":22.3},
            {"ticker":"161390","name":"한국타이어","beta_adj":0.75,"mom":-0.2, "ROE":5.2, "PER":9.2, "PBR":0.7, "debt_ratio":105.2, "current_ratio":155, "operating_margin":6.2, "sales_growth":-2.1},
            {"ticker":"004020","name":"현대제철","beta_adj":0.7,"mom":-0.6, "ROE":-2.5, "PER":-12.3, "PBR":0.3, "debt_ratio":125.2, "current_ratio":105, "operating_margin":-1.2, "sales_growth":-8.5},
            {"ticker":"064350","name":"현대로템","beta_adj":1.05,"mom":1.8, "ROE":8.2, "PER":18.2, "PBR":1.8, "debt_ratio":145.2, "current_ratio":115, "operating_margin":5.8, "sales_growth":25.2},
            {"ticker":"023530","name":"롯데쇼핑","beta_adj":0.6,"mom":-1.0, "ROE":-5.2, "PER":-6.5, "PBR":0.4, "debt_ratio":185.2, "current_ratio":75, "operating_margin":-2.5, "sales_growth":-15.2},
            {"ticker":"003490","name":"대한항공우","beta_adj":0.9,"mom":0.5, "ROE":4.2, "PER":12.5, "PBR":1.5, "debt_ratio":285.2, "current_ratio":95, "operating_margin":3.5, "sales_growth":22.3},
        ]
    },
    "chem": {
        "name": "화학/2차전지", "targetFactor": "중국PMI", "beta": 0.28,
        "candidates": [
            {"ticker":"373220","name":"LG에너지솔루션","beta_adj":1.2,"mom":0.5, "ROE":8.2, "PER":42.5, "PBR":3.2, "debt_ratio":95.2, "current_ratio":135, "operating_margin":6.5, "sales_growth":35.2},
            {"ticker":"051910","name":"LG화학","beta_adj":1.0,"mom":-0.3, "ROE":4.5, "PER":18.2, "PBR":0.9, "debt_ratio":85.2, "current_ratio":125, "operating_margin":5.2, "sales_growth":-5.2},
            {"ticker":"096770","name":"SK이노베이션","beta_adj":0.95,"mom":-0.8, "ROE":-2.1, "PER":-15.2, "PBR":0.6, "debt_ratio":145.2, "current_ratio":95, "operating_margin":-1.5, "sales_growth":-8.2},
            {"ticker":"003670","name":"포스코퓨처엠","beta_adj":1.15,"mom":0.9, "ROE":6.5, "PER":65.2, "PBR":4.2, "debt_ratio":75.2, "current_ratio":125, "operating_margin":4.2, "sales_growth":25.2},
            {"ticker":"247540","name":"에코프로비엠","beta_adj":1.3,"mom":1.5, "ROE":18.2, "PER":42.5, "PBR":6.8, "debt_ratio":125.2, "current_ratio":145, "operating_margin":8.5, "sales_growth":65.2},
            {"ticker":"086520","name":"에코프로","beta_adj":1.25,"mom":2.2, "ROE":22.5, "PER":35.2, "PBR":7.2, "debt_ratio":145.2, "current_ratio":135, "operating_margin":12.5, "sales_growth":85.2},
            {"ticker":"011170","name":"롯데케미칼","beta_adj":0.8,"mom":-1.2, "ROE":-8.2, "PER":-5.2, "PBR":0.3, "debt_ratio":95.2, "current_ratio":115, "operating_margin":-4.2, "sales_growth":-22.5},
            {"ticker":"011780","name":"금호석유","beta_adj":0.85,"mom":0.1, "ROE":12.5, "PER":6.2, "PBR":0.8, "debt_ratio":65.2, "current_ratio":165, "operating_margin":12.5, "sales_growth":-8.5},
            {"ticker":"010130","name":"고려아연","beta_adj":0.75,"mom":0.4, "ROE":8.2, "PER":12.5, "PBR":0.9, "debt_ratio":45.2, "current_ratio":210, "operating_margin":8.2, "sales_growth":5.2},
            {"ticker":"006650","name":"대한유화","beta_adj":0.7,"mom":-0.5, "ROE":1.2, "PER":35.2, "PBR":0.5, "debt_ratio":125.2, "current_ratio":105, "operating_margin":1.5, "sales_growth":-15.2},
            {"ticker":"250970","name":"아모그린텍","beta_adj":1.1,"mom":1.0, "ROE":5.2, "PER":28.5, "PBR":2.5, "debt_ratio":85.2, "current_ratio":145, "operating_margin":4.5, "sales_growth":18.2},
            {"ticker":"121600","name":"나노신소재","beta_adj":1.0,"mom":0.7, "ROE":12.5, "PER":32.5, "PBR":3.8, "debt_ratio":65.2, "current_ratio":155, "operating_margin":12.2, "sales_growth":42.5},
        ]
    },
    "fin": {
        "name": "금융/증권", "targetFactor": "한미스프레드", "beta": 0.35,
        "candidates": [
            {"ticker":"105560","name":"KB금융","beta_adj":1.0,"mom":0.6, "ROE":9.8, "PER":5.2, "PBR":0.5, "debt_ratio":450.2, "current_ratio":110, "operating_margin":25.2, "sales_growth":8.5},
            {"ticker":"055550","name":"신한지주","beta_adj":0.95,"mom":0.4, "ROE":9.2, "PER":5.5, "PBR":0.5, "debt_ratio":480.2, "current_ratio":105, "operating_margin":23.5, "sales_growth":6.2},
            {"ticker":"086790","name":"하나금융지주","beta_adj":0.9,"mom":0.3, "ROE":8.8, "PER":4.8, "PBR":0.4, "debt_ratio":520.2, "current_ratio":100, "operating_margin":22.1, "sales_growth":5.5},
            {"ticker":"316140","name":"우리금융지주","beta_adj":0.85,"mom":0.1, "ROE":7.5, "PER":4.2, "PBR":0.3, "debt_ratio":550.2, "current_ratio":98, "operating_margin":20.2, "sales_growth":4.2},
            {"ticker":"138930","name":"BNK금융지주","beta_adj":0.8,"mom":-0.2, "ROE":6.2, "PER":4.5, "PBR":0.3, "debt_ratio":580.2, "current_ratio":95, "operating_margin":18.5, "sales_growth":2.1},
            {"ticker":"175330","name":"JB금융","beta_adj":0.75,"mom":0.5, "ROE":12.5, "PER":4.2, "PBR":0.6, "debt_ratio":620.2, "current_ratio":92, "operating_margin":28.5, "sales_growth":12.5},
            {"ticker":"071050","name":"한국금융지주","beta_adj":1.15,"mom":1.2, "ROE":11.2, "PER":5.8, "PBR":0.7, "debt_ratio":850.2, "current_ratio":88, "operating_margin":35.2, "sales_growth":15.2},
            {"ticker":"030200","name":"KT","beta_adj":0.6,"mom":-0.3, "ROE":6.5, "PER":8.2, "PBR":0.6, "debt_ratio":125.2, "current_ratio":110, "operating_margin":8.5, "sales_growth":2.5},
            {"ticker":"032640","name":"LG유플러스","beta_adj":0.55,"mom":-0.5, "ROE":5.2, "PER":9.5, "PBR":0.7, "debt_ratio":145.2, "current_ratio":95, "operating_margin":6.2, "sales_growth":3.2},
            {"ticker":"034120","name":"SBS","beta_adj":0.7,"mom":0.2, "ROE":3.2, "PER":12.5, "PBR":0.8, "debt_ratio":85.2, "current_ratio":135, "operating_margin":5.2, "sales_growth":-5.2},
            {"ticker":"000810","name":"삼성화재","beta_adj":0.85,"mom":0.7, "ROE":10.5, "PER":8.5, "PBR":0.8, "debt_ratio":320.2, "current_ratio":115, "operating_margin":15.2, "sales_growth":6.5},
            {"ticker":"088350","name":"한화생명","beta_adj":0.8,"mom":0.3, "ROE":4.5, "PER":12.2, "PBR":0.4, "debt_ratio":950.2, "current_ratio":90, "operating_margin":4.2, "sales_growth":-2.5},
        ]
    },
    "bio": {
        "name": "바이오/의약품", "targetFactor": "US10Y", "beta": -0.20,
        "candidates": [
            {"ticker":"207940","name":"삼성바이오로직스","beta_adj":1.0,"mom":0.9, "ROE":18.2, "PER":55.2, "PBR":8.5, "debt_ratio":55.2, "current_ratio":210, "operating_margin":28.5, "sales_growth":32.5},
            {"ticker":"068270","name":"셀트리온","beta_adj":1.1,"mom":0.2, "ROE":15.2, "PER":32.5, "PBR":4.2, "debt_ratio":35.2, "current_ratio":280, "operating_margin":25.2, "sales_growth":18.5},
            {"ticker":"128940","name":"한미약품","beta_adj":0.85,"mom":0.5, "ROE":12.5, "PER":28.5, "PBR":3.2, "debt_ratio":25.2, "current_ratio":220, "operating_margin":12.5, "sales_growth":12.5},
            {"ticker":"185750","name":"종근당","beta_adj":0.8,"mom":-0.1, "ROE":8.2, "PER":18.2, "PBR":1.8, "debt_ratio":65.2, "current_ratio":165, "operating_margin":8.2, "sales_growth":5.2},
            {"ticker":"145020","name":"휴젤","beta_adj":0.9,"mom":1.1, "ROE":25.2, "PER":22.5, "PBR":5.2, "debt_ratio":15.2, "current_ratio":380, "operating_margin":42.5, "sales_growth":22.5},
            {"ticker":"195940","name":"HLB","beta_adj":1.2,"mom":2.5, "ROE":-15.2, "PER":-12.5, "PBR":8.5, "debt_ratio":85.2, "current_ratio":120, "operating_margin":-45.2, "sales_growth":-12.5},
            {"ticker":"326030","name":"SK바이오팜","beta_adj":1.05,"mom":0.7, "ROE":-8.2, "PER":-22.5, "PBR":6.2, "debt_ratio":25.2, "current_ratio":450, "operating_margin":-32.5, "sales_growth":125.2},
            {"ticker":"185740","name":"셀트리온제약","beta_adj":0.95,"mom":0.3, "ROE":12.5, "PER":28.5, "PBR":3.5, "debt_ratio":35.2, "current_ratio":240, "operating_margin":18.5, "sales_growth":15.2},
            {"ticker":"102780","name":"에이치엘비","beta_adj":1.15,"mom":2.0, "ROE":-15.2, "PER":-12.5, "PBR":8.5, "debt_ratio":85.2, "current_ratio":120, "operating_margin":-45.2, "sales_growth":-12.5},
            {"ticker":"196300","name":"동국제약","beta_adj":0.75,"mom":0.1, "ROE":15.2, "PER":12.5, "PBR":1.8, "debt_ratio":22.5, "current_ratio":280, "operating_margin":18.2, "sales_growth":8.5},
            {"ticker":"214450","name":"파마리서치","beta_adj":0.85,"mom":1.4, "ROE":22.5, "PER":28.5, "PBR":5.8, "debt_ratio":18.2, "current_ratio":350, "operating_margin":32.5, "sales_growth":28.5},
            {"ticker":"185250","name":"REYON","beta_adj":0.7,"mom":-0.4, "ROE":1.2, "PER":55.2, "PBR":2.1, "debt_ratio":125.2, "current_ratio":105, "operating_margin":2.1, "sales_growth":-18.5},
        ]
    },
    "steel": {
        "name": "철강/소재/에너지", "targetFactor": "중국PMI", "beta": 0.30,
        "candidates": [
            {"ticker":"005490","name":"POSCO홀딩스","beta_adj":1.0,"mom":0.4, "ROE":5.2, "PER":8.5, "PBR":0.4, "debt_ratio":85.2, "current_ratio":145, "operating_margin":5.2, "sales_growth":-5.2},
            {"ticker":"004020","name":"현대제철","beta_adj":0.85,"mom":-0.3, "ROE":-2.5, "PER":-12.3, "PBR":0.3, "debt_ratio":125.2, "current_ratio":105, "operating_margin":-1.2, "sales_growth":-8.5},
            {"ticker":"010130","name":"고려아연","beta_adj":0.9,"mom":0.6, "ROE":8.2, "PER":12.5, "PBR":0.9, "debt_ratio":45.2, "current_ratio":210, "operating_margin":8.2, "sales_growth":5.2},
            {"ticker":"000670","name":"영풍","beta_adj":0.75,"mom":-0.2, "ROE":2.1, "PER":25.2, "PBR":0.4, "debt_ratio":35.2, "current_ratio":280, "operating_margin":2.5, "sales_growth":-12.5},
            {"ticker":"010950","name":"S-Oil","beta_adj":0.8,"mom":-0.6, "ROE":12.5, "PER":6.2, "PBR":0.9, "debt_ratio":95.2, "current_ratio":135, "operating_margin":6.5, "sales_growth":-15.2},
            {"ticker":"047050","name":"포스코인터","beta_adj":0.95,"mom":0.8, "ROE":8.5, "PER":9.2, "PBR":0.8, "debt_ratio":125.2, "current_ratio":125, "operating_margin":4.2, "sales_growth":12.5},
            {"ticker":"001430","name":"세아베스틸","beta_adj":0.7,"mom":0.1, "ROE":3.2, "PER":12.5, "PBR":0.4, "debt_ratio":105.2, "current_ratio":135, "operating_margin":3.5, "sales_growth":-2.5},
            {"ticker":"002720","name":"국제약품","beta_adj":0.6,"mom":-0.4, "ROE":1.2, "PER":35.2, "PBR":1.2, "debt_ratio":85.2, "current_ratio":145, "operating_margin":2.2, "sales_growth":-8.5},
            {"ticker":"009830","name":"한화솔루션","beta_adj":0.85,"mom":0.3, "ROE":2.5, "PER":18.5, "PBR":0.6, "debt_ratio":145.2, "current_ratio":105, "operating_margin":2.8, "sales_growth":-12.5},
            {"ticker":"011170","name":"롯데케미칼","beta_adj":0.8,"mom":-1.0, "ROE":-8.2, "PER":-5.2, "PBR":0.3, "debt_ratio":95.2, "current_ratio":115, "operating_margin":-4.2, "sales_growth":-22.5},
            {"ticker":"103140","name":"풍산","beta_adj":0.75,"mom":0.2, "ROE":6.5, "PER":7.2, "PBR":0.5, "debt_ratio":95.2, "current_ratio":145, "operating_margin":5.5, "sales_growth":5.2},
            {"ticker":"002710","name":"롯데에너지","beta_adj":0.7,"mom":-0.3, "ROE":-5.2, "PER":-8.5, "PBR":0.4, "debt_ratio":125.2, "current_ratio":95, "operating_margin":-3.2, "sales_growth":-18.5},
        ]
    },
    "const": {
        "name": "건설/조선/기계", "targetFactor": "원달러", "beta": 0.18,
        "candidates": [
            {"ticker":"009540","name":"HD한국조선해양","beta_adj":1.0,"mom":1.5, "ROE":8.5, "PER":18.5, "PBR":1.2, "debt_ratio":95.2, "current_ratio":135, "operating_margin":3.5, "sales_growth":25.2},
            {"ticker":"010140","name":"삼성중공업","beta_adj":0.9,"mom":0.8, "ROE":2.1, "PER":45.2, "PBR":1.5, "debt_ratio":185.2, "current_ratio":105, "operating_margin":1.2, "sales_growth":18.5},
            {"ticker":"329180","name":"HD현대중공업","beta_adj":1.15,"mom":1.9, "ROE":12.5, "PER":15.2, "PBR":2.2, "debt_ratio":125.2, "current_ratio":115, "operating_margin":5.2, "sales_growth":35.2},
            {"ticker":"064350","name":"현대로템","beta_adj":1.05,"mom":1.8, "ROE":8.2, "PER":18.2, "PBR":1.8, "debt_ratio":145.2, "current_ratio":115, "operating_margin":5.8, "sales_growth":25.2},
            {"ticker":"034020","name":"두산에너빌리티","beta_adj":0.95,"mom":0.4, "ROE":4.5, "PER":22.5, "PBR":0.9, "debt_ratio":185.2, "current_ratio":95, "operating_margin":3.2, "sales_growth":-5.2},
            {"ticker":"028050","name":"삼성엔지니어링","beta_adj":0.85,"mom":0.2, "ROE":18.2, "PER":12.5, "PBR":2.2, "debt_ratio":85.2, "current_ratio":125, "operating_margin":6.5, "sales_growth":12.5},
            {"ticker":"006360","name":"GS건설","beta_adj":0.75,"mom":-0.6, "ROE":-15.2, "PER":-3.2, "PBR":0.3, "debt_ratio":320.5, "current_ratio":85, "operating_margin":-4.2, "sales_growth":-18.5},
            {"ticker":"047040","name":"대우건설","beta_adj":0.7,"mom":-0.3, "ROE":5.2, "PER":6.2, "PBR":0.5, "debt_ratio":185.2, "current_ratio":115, "operating_margin":3.5, "sales_growth":-5.2},
            {"ticker":"009410","name":"한화","beta_adj":0.8,"mom":0.3, "ROE":6.5, "PER":8.5, "PBR":0.6, "debt_ratio":145.2, "current_ratio":105, "operating_margin":4.2, "sales_growth":8.5},
            {"ticker":"012450","name":"한화에어로","beta_adj":1.2,"mom":2.3, "ROE":22.5, "PER":22.5, "PBR":4.2, "debt_ratio":85.2, "current_ratio":145, "operating_margin":12.5, "sales_growth":45.2},
            {"ticker":"097230","name":"한진중공업","beta_adj":0.85,"mom":0.5, "ROE":2.5, "PER":25.2, "PBR":0.8, "debt_ratio":350.2, "current_ratio":75, "operating_margin":2.1, "sales_growth":15.2},
            {"ticker":"000720","name":"현대건설","beta_adj":0.8,"mom":-0.1, "ROE":3.2, "PER":12.5, "PBR":0.5, "debt_ratio":165.2, "current_ratio":115, "operating_margin":3.2, "sales_growth":-2.5},
        ]
    },
    "retail": {
        "name": "유통/IT서비스", "targetFactor": "SP500", "beta": 0.22,
        "candidates": [
            {"ticker":"035720","name":"카카오","beta_adj":1.1,"mom":-0.4, "ROE":2.1, "PER":45.2, "PBR":2.2, "debt_ratio":35.2, "current_ratio":180, "operating_margin":5.2, "sales_growth":2.5},
            {"ticker":"035420","name":"NAVER","beta_adj":1.05,"mom":-0.2, "ROE":8.5, "PER":22.5, "PBR":2.5, "debt_ratio":25.2, "current_ratio":210, "operating_margin":15.2, "sales_growth":12.5},
            {"ticker":"030200","name":"KT","beta_adj":0.7,"mom":0.1, "ROE":6.5, "PER":8.2, "PBR":0.6, "debt_ratio":125.2, "current_ratio":110, "operating_margin":8.5, "sales_growth":2.5},
            {"ticker":"017670","name":"SK텔레콤","beta_adj":0.65,"mom":0.2, "ROE":8.2, "PER":9.5, "PBR":0.8, "debt_ratio":105.2, "current_ratio":95, "operating_margin":12.5, "sales_growth":1.2},
            {"ticker":"032640","name":"LG유플러스","beta_adj":0.6,"mom":-0.1, "ROE":5.2, "PER":9.5, "PBR":0.7, "debt_ratio":145.2, "current_ratio":95, "operating_margin":6.2, "sales_growth":3.2},
            {"ticker":"139480","name":"이마트","beta_adj":0.75,"mom":-0.8, "ROE":-2.5, "PER":-12.5, "PBR":0.3, "debt_ratio":185.2, "current_ratio":75, "operating_margin":-1.2, "sales_growth":-8.5},
            {"ticker":"023530","name":"롯데쇼핑","beta_adj":0.7,"mom":-0.5, "ROE":-5.2, "PER":-6.5, "PBR":0.4, "debt_ratio":185.2, "current_ratio":75, "operating_margin":-2.5, "sales_growth":-15.2},
            {"ticker":"004170","name":"신세계","beta_adj":0.8,"mom":-0.3, "ROE":2.1, "PER":18.5, "PBR":0.5, "debt_ratio":165.2, "current_ratio":85, "operating_margin":3.2, "sales_growth":-5.2},
            {"ticker":"030000","name":"제일기획","beta_adj":0.65,"mom":0.3, "ROE":15.2, "PER":12.5, "PBR":2.2, "debt_ratio":22.5, "current_ratio":185, "operating_margin":18.5, "sales_growth":5.2},
            {"ticker":"064760","name":"엔씨소프트","beta_adj":0.85,"mom":-1.2, "ROE":-2.5, "PER":-15.2, "PBR":1.2, "debt_ratio":15.2, "current_ratio":320, "operating_margin":-5.2, "sales_growth":-22.5},
            {"ticker":"352820","name":"하이브","beta_adj":0.9,"mom":0.6, "ROE":8.5, "PER":28.5, "PBR":3.2, "debt_ratio":45.2, "current_ratio":165, "operating_margin":12.5, "sales_growth":18.5},
            {"ticker":"035900","name":"JYP","beta_adj":0.85,"mom":0.8, "ROE":22.5, "PER":18.5, "PBR":5.2, "debt_ratio":15.2, "current_ratio":280, "operating_margin":22.5, "sales_growth":25.2},
        ]
    },
}

# 1단계 필터 적용 + KRX API screening
weekly_picks = []
filter_summary = {}
all_rejected = []

for ind_id, ind_data in industry_universe.items():
    tf = ind_data["targetFactor"]
    base_beta = ind_data["beta"]
    z_val = newZ.get(tf, 0)
    
    # 1단계: Fundamental Filter 적용
    raw_candidates = ind_data["candidates"]
    if FILTER_AVAILABLE:
        passed, rejected = filter_candidates(raw_candidates, ind_id)
        filter_summary[ind_id] = {
            "raw": len(raw_candidates),
            "passed": len(passed),
            "rejected": len(rejected),
            "rejected_tickers": [r["ticker"] for r in rejected]
        }
        all_rejected.extend([{"industryId": ind_id, **r} for r in rejected])
        candidates_to_score = passed
        print(f"[{ind_id}] Filter: {len(raw_candidates)} -> {len(passed)} passed, {len(rejected)} rejected: {[r['ticker'] for r in rejected]}")
    else:
        candidates_to_score = raw_candidates
        filter_summary[ind_id] = {"raw": len(raw_candidates), "passed": len(raw_candidates), "rejected": 0, "rejected_tickers": []}
    
    # 2단계: β·모멘텀 스코어링 (필터 통과된 종목만)
    scored = []
    for cand in candidates_to_score:
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
            "industryBeta": base_beta,
            # Fundamental 데이터 포함
            "ROE": cand.get("ROE"),
            "PER": cand.get("PER"),
            "PBR": cand.get("PBR"),
            "debt_ratio": cand.get("debt_ratio"),
            "current_ratio": cand.get("current_ratio"),
            "operating_margin": cand.get("operating_margin"),
            "sales_growth": cand.get("sales_growth"),
            "filter_pass": True
        })
    # Top 8 per industry by score (필터 후에도 8개 미만이면 가능한 만큼)
    scored.sort(key=lambda x: x["score"], reverse=True)
    top8 = scored[:8]
    weekly_picks.extend(top8)
    print(f"[{ind_id}] {tf} Z={z_val} -> Top8: {[p['ticker'] for p in top8]}")

# Save 64 picks + filter summary
db.collection('factor_snapshots').document(today).set({
    'date': today,
    'zScores': newZ,
    'rawValues': {'SP500': 5780+random.uniform(-20,20), 'US10Y': 4.72, 'USD_KRW': 1382.5, 'WTI': 72.3},
    'weeklyPicks': weekly_picks,
    'industryPicks': {ind: [p for p in weekly_picks if p['industryId']==ind] for ind in industry_universe.keys()},
    'filterSummary': filter_summary,
    'rejectedPicks': all_rejected,
    'createdAt': firestore.SERVER_TIMESTAMP,
    'source': 'github-actions-sunday-18KST-v51-filter',
    'version': '4.0-industry-8x8-KRX-screening-v51-fundamental-filter',
    'filterVersion': 'v51-optimal-stage1'
}, merge=True)

print(f"[{today}] Saved {len(weekly_picks)} picks across 8 industries (after filter)")
print(f"Filter Summary: {filter_summary}")
print(f"New Z: {newZ}")
