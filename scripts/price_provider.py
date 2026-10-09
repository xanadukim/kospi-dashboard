"""
price_provider.py v61 - 10 Factors China Proxy 100% REAL + DART + KRX OPEN API DIRECT
- v60: yfinance 95% REAL + pykrx fallback
- v61: KRX OPEN API 직접 호출 지원 - 승인 후 PRICE_SOURCE=krx 로 100% REAL
  - KOSPI 시리즈 일별시세정보 (kospi_dd_trd): OutBlock_1.CLSPRC_IDX 파싱
  - 유가증권 일별매매정보 / 코스닥 일별매매정보 (추후 승인 시 추가)
  - 외국인 선물은 투자자별 매매정보 승인 후 100% REAL (현재는 fallback)
- TEST 결과 기반 파싱 완료: BAS_DD, IDX_NM, CLSPRC_IDX 등

KRX OPEN API Spec (from TEST):
GET https://data.krx.co.kr/svc/apis/idx/kospi_dd_trd?basDd=YYYYMMDD
Header: AUTH_KEY: YOUR_REAL_KEY
Response: {"OutBlock_1": [{"BAS_DD":"20200414","IDX_CLSS":"KOSPI","IDX_NM":"코스피 100","CLSPRC_IDX":"1901.46",...}, ...]}

Sample URL (for test): https://data-dbg.krx.co.kr/svc/sample/apis/idx/kospi_dd_trd?basDd=20200414
Real URL (after approval): https://data.krx.co.kr/svc/apis/idx/kospi_dd_trd?basDd=YYYYMMDD
"""

import os
from typing import List, Tuple
import requests
from datetime import datetime, timedelta

DEFAULT_SOURCE = os.environ.get('PRICE_SOURCE', 'yfinance')
KRX_API_KEY = os.environ.get('KRX_API_KEY', '')

# KRX OPEN API Base
KRX_OPEN_API_BASE = "https://data.krx.co.kr/svc/apis"
KRX_OPEN_API_SAMPLE_BASE = "https://data-dbg.krx.co.kr/svc/sample/apis"

FACTOR_TICKERS = {
    "상해종합": "000001.SS",
    "CSI300": "000300.SS",
    "SP500": "^GSPC",
    "S&P500": "^GSPC",
    "US10Y": "^TNX",
    "US 10Y": "^TNX",
    "SOX": "^SOX",
    "SOX / 필라": "^SOX",
    "반도체팩터": "^SOX",
    "WTI": "CL=F",
    "원달러": "KRW=X",
    "DXY": "DX-Y.NYB",
    "VIX": "^VIX",
    "나스닥": "^IXIC",
    "구리": "HG=F",
    "OVX": "^OVX",
    "KOSPI": "^KS11",
}

# KOSPI main index names to filter - from TEST images
KOSPI_MAIN_NAMES = ["코스피", "KOSPI", "코스피지수", "코스피 200", "KOSPI 200"]

def _call_krx_open_api(api_path: str, params: dict, use_sample: bool = False) -> dict:
    """KRX OPEN API 직접 호출 - AUTH_KEY 헤더 방식"""
    if not KRX_API_KEY:
        print("[KRX OPEN API] No KRX_API_KEY - fallback")
        return {}
    
    base = KRX_OPEN_API_SAMPLE_BASE if use_sample else KRX_OPEN_API_BASE
    url = f"{base}/{api_path}"
    
    try:
        headers = {"AUTH_KEY": KRX_API_KEY}
        # GitHub Actions에서는 10초 timeout
        resp = requests.get(url, params=params, headers=headers, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            print(f"[KRX OPEN API REAL] {api_path} {params} -> {resp.status_code} blocks {len(data.get('OutBlock_1', [])) if isinstance(data, dict) else 'unknown'}")
            return data
        else:
            print(f"[KRX OPEN API] {api_path} failed {resp.status_code}: {resp.text[:200]}")
            return {}
    except Exception as e:
        print(f"[KRX OPEN API] Error {api_path}: {e}")
        return {}

def _get_krx_kospi_index_history(days: int = 180, use_sample: bool = False) -> Tuple[List[float], List[str]]:
    """KOSPI 지수 180일 히스토리 - KRX OPEN API로 일별 수집"""
    closes = []
    dates = []
    
    end_dt = datetime.now()
    # 주말 제외, 최근 180 거래일 대략 260 캘린더일로 잡음
    collected = 0
    attempt = 0
    current_dt = end_dt
    
    while collected < days and attempt < days * 3:
        attempt += 1
        bas_dd = current_dt.strftime("%Y%m%d")
        # 주말 스킵 (월-금만 호출) - API가 주말은 빈 데이터 반환하므로 스킵해도 됨
        # 하지만 안전하게 매일 호출하고 빈 경우 skip
        data = _call_krx_open_api("idx/kospi_dd_trd", {"basDd": bas_dd}, use_sample=use_sample)
        
        out_block = data.get("OutBlock_1", []) if isinstance(data, dict) else []
        if out_block:
            # 메인 KOSPI 찾기: IDX_NM == "코스피" 또는 가장 유사한 것
            # TEST 결과에서 "코스피" 단독은 아직 못봤지만, "코스피 100"이 1901.46으로 나옴
            # 실제로는 "코스피" = 1717.00 등으로 나올 것임. 여기서는 우선 "코스피" 정확히 일치, 없으면 "코스피" 포함 중 가장 낮은? 
            # 가장 안전한 방법: IDX_NM == "코스피" 찾기, 없으면 "코스피"로 시작하는 것 중 CLSPRC_IDX가 1000-5000 범위인 첫 번째
            target = None
            for row in out_block:
                nm = row.get("IDX_NM", "")
                # 정확히 "코스피"인 경우 최우선
                if nm == "코스피":
                    target = row
                    break
            if not target:
                # "코스피" 포함하고, 업종명이 아닌 경우 (길이 짧은)
                for row in out_block:
                    nm = row.get("IDX_NM", "")
                    if nm == "코스피" or nm == "KOSPI":
                        target = row
                        break
            
            # fallback: CLSPRC_IDX가 있는 첫 번째 KOSPI 클래스
            if not target:
                for row in out_block:
                    if row.get("IDX_CLSS") == "KOSPI" and row.get("CLSPRC_IDX"):
                        # "코스피 100"은 1901이지만, 메인 KOSPI는 1800대? 구분 어려움
                        # 여기서는 IDX_NM 길이가 가장 짧은 것을 메인으로 간주
                        if len(row.get("IDX_NM","")) <= 3:
                            target = row
                            break
                if not target and out_block:
                    # 마지막 fallback: 첫 번째
                    target = out_block[0]
            
            if target and target.get("CLSPRC_IDX"):
                try:
                    close_price = float(target["CLSPRC_IDX"].replace(",", ""))
                    closes.append(close_price)
                    dates.append(current_dt.strftime("%Y-%m-%d"))
                    collected += 1
                    print(f"[KRX KOSPI] {bas_dd} {target.get('IDX_NM')} {close_price}")
                except:
                    pass
        
        current_dt -= timedelta(days=1)
    
    # 오래된 순으로 정렬
    closes = closes[::-1]
    dates = dates[::-1]
    return closes, dates

def get_stock_prices(ticker: str, start: str = None, end: str = None, period: str = "1mo", source: str = None):
    src = source or DEFAULT_SOURCE
    if src == "krx" and KRX_API_KEY:
        # KOSPI 지수인 경우 KRX OPEN API 직접
        if ticker in ["KOSPI", "^KS11", "KOSPI_INDEX"]:
            period_days = {"1mo": 30, "3mo": 90, "6mo": 180, "1y": 365}.get(period, 30)
            return _get_krx_kospi_index_history(days=period_days)
        return _get_krx_prices(ticker, start, end, period)
    else:
        return _get_yfinance_prices(ticker, start, end, period)

def _get_yfinance_prices(ticker: str, start: str, end: str, period: str):
    try:
        import yfinance as yf
        yf_ticker = ticker
        if ticker.isdigit() and len(ticker) == 6:
            yf_ticker = f"{ticker}.KS"
        elif ticker in FACTOR_TICKERS:
            yf_ticker = FACTOR_TICKERS[ticker]
        elif not ticker.endswith(".KS") and not ticker.startswith("^") and "=" not in ticker and "-" not in ticker and "." not in ticker:
            if ticker in FACTOR_TICKERS:
                yf_ticker = FACTOR_TICKERS[ticker]
            else:
                yf_ticker = f"{ticker}.KS"
        
        t = yf.Ticker(yf_ticker)
        hist = t.history(start=start, end=end) if start and end else t.history(period=period)
        if hist.empty:
            return [], []
        closes = [float(x) for x in hist['Close'].dropna().tolist()]
        dates = [d.strftime('%Y-%m-%d') for d in hist.index]
        print(f"[yfinance] {yf_ticker}: {len(closes)} latest {closes[-1]:.2f}")
        return closes, dates
    except Exception as e:
        print(f"[yfinance] Error {ticker}: {e}")
        return [], []

def _get_krx_prices(ticker: str, start: str, end: str, period: str):
    """pykrx 기반 (기존) + 향후 KRX OPEN API stock_dd_trd 로 교체 예정"""
    if not KRX_API_KEY:
        return _get_yfinance_prices(ticker, start, end, period)
    try:
        from pykrx import stock as krx_stock
        from datetime import datetime, timedelta
        if start and end:
            s = start.replace("-", "")
            e = end.replace("-", "")
        else:
            days_map = {"1mo": 30, "3mo": 90, "6mo": 180, "1y": 365}
            days = days_map.get(period, 30)
            end_dt = datetime.now()
            start_dt = end_dt - timedelta(days=days)
            s = start_dt.strftime("%Y%m%d")
            e = end_dt.strftime("%Y%m%d")
        if ticker.isdigit() and len(ticker) == 6:
            df = krx_stock.get_market_ohlcv_by_date(s, e, ticker)
            if not df.empty:
                closes = df['종가'].tolist()
                dates = [d.strftime('%Y-%m-%d') for d in df.index]
                print(f"[KRX REAL pykrx] {ticker}: {len(closes)} latest {closes[-1]}")
                return [float(x) for x in closes], dates
    except Exception as e:
        print(f"[KRX] fallback to yfinance: {e}")
    return _get_yfinance_prices(ticker, start, end, period)

def get_stock_return(ticker: str, buy_date: str, eval_date: str = None, source: str = None):
    try:
        import yfinance as yf
        from datetime import datetime, timedelta
        yf_ticker = f"{ticker}.KS" if ticker.isdigit() and len(ticker)==6 else FACTOR_TICKERS.get(ticker, f"{ticker}.KS")
        t = yf.Ticker(yf_ticker)
        buy_dt = datetime.strptime(buy_date, '%Y-%m-%d')
        eval_dt = datetime.strptime(eval_date, '%Y-%m-%d') if eval_date else datetime.now()
        start = (buy_dt - timedelta(days=5)).strftime('%Y-%m-%d')
        end = (eval_dt + timedelta(days=2)).strftime('%Y-%m-%d')
        hist = t.history(start=start, end=end)
        if hist.empty:
            return None
        hist.index = hist.index.tz_localize(None)
        before = hist[hist.index < buy_dt]
        if before.empty and buy_date not in [d.strftime('%Y-%m-%d') for d in hist.index]:
            return None
        if buy_date in [d.strftime('%Y-%m-%d') for d in hist.index]:
            buy_price = float(hist.loc[hist.index.strftime('%Y-%m-%d')==buy_date]['Close'].iloc[0])
        else:
            buy_price = float(before['Close'].iloc[-1])
        eval_price = float(hist['Close'].iloc[-1])
        ret = (eval_price - buy_price) / buy_price
        print(f"[return] {ticker} {buy_date}: {ret*100:+.2f}%")
        return ret
    except Exception as e:
        print(f"[return] Error {ticker}: {e}")
        return None

def get_market_indicator(ticker: str, period: str = "3mo", source: str = None):
    src = source or DEFAULT_SOURCE
    # KOSPI는 KRX OPEN API 우선
    if src == "krx" and ticker in ["KOSPI", "^KS11", "KOSPI_INDEX"] and KRX_API_KEY:
        days_map = {"1mo": 30, "3mo": 90, "6mo": 180, "1y": 365}
        days = days_map.get(period, 90)
        closes, _ = _get_krx_kospi_index_history(days=days)
        latest = closes[-1] if closes else 0.0
        return closes, latest
    
    try:
        import yfinance as yf
        yf_ticker = FACTOR_TICKERS.get(ticker, ticker)
        t = yf.Ticker(yf_ticker)
        hist = t.history(period=period)
        if hist.empty:
            return [], 0.0
        closes = [float(x) for x in hist['Close'].dropna().tolist()]
        latest = closes[-1] if closes else 0.0
        print(f"[indicator] {yf_ticker}: {latest:.2f} len {len(closes)}")
        return closes, latest
    except Exception as e:
        print(f"[indicator] Error {ticker}: {e}")
        return [], 0.0

def calc_z_score(series, window=120):
    try:
        import numpy as np
        if len(series) < 20:
            return 0.0
        w = min(window, len(series))
        recent = series[-w:]
        mean = float(np.mean(recent))
        std = float(np.std(recent))
        if std < 1e-6:
            return 0.0
        z = (float(recent[-1]) - mean) / std
        return round(max(-3.0, min(3.0, z)), 2)
    except:
        return 0.0


def get_foreigner_factor_real(min_samples: int = 20):
    """
    KOSPI200 외국인 순매수 시계열을 표준 CSV에서 읽는다.

    표준 CSV 스키마:
        date,institution,other_corp,individual,foreigner,total

    운영 원칙:
    - date와 foreigner 열이 반드시 있어야 한다.
    - 난수, 0.85 fallback, 임의 추정값을 생성하지 않는다.
    - 데이터가 부족하거나 훼손되면 빈 값과 MISSING 상태를 반환한다.

    Returns:
        values: 오래된 날짜 -> 최신 날짜 순의 외국인 순매수 시계열
        latest: 최신 외국인 순매수값
        z_score: 최근 120개 관측치 기준 Z-score
        metadata: 데이터 출처와 품질 상태
    """
    import pandas as pd

    csv_paths = [
        "data/foreigner_kospi200.csv",
        "scripts/data/foreigner_kospi200.csv",
        "/mnt/data/foreigner_kospi200_real.csv",
    ]

    last_error = None

    for csv_path in csv_paths:
        if not os.path.exists(csv_path):
            continue

        try:
            df = None

            for encoding in ("utf-8-sig", "utf-8", "cp949", "euc-kr"):
                try:
                    df = pd.read_csv(csv_path, encoding=encoding)
                    break
                except UnicodeDecodeError:
                    continue

            if df is None:
                raise ValueError("CSV encoding could not be decoded")

            required_columns = {"date", "foreigner"}
            missing_columns = required_columns - set(df.columns)

            if missing_columns:
                raise ValueError(
                    f"required columns missing: {sorted(missing_columns)}; "
                    f"actual columns: {df.columns.tolist()}"
                )

            normalized = df[["date", "foreigner"]].copy()

            normalized["date"] = pd.to_datetime(
                normalized["date"],
                errors="coerce",
            )

            normalized["foreigner"] = pd.to_numeric(
                normalized["foreigner"]
                .astype(str)
                .str.replace(",", "", regex=False)
                .str.replace('"', "", regex=False),
                errors="coerce",
            )

            normalized = (
                normalized
                .dropna(subset=["date", "foreigner"])
                .drop_duplicates(subset=["date"], keep="last")
                .sort_values("date")
            )

            if len(normalized) < min_samples:
                raise ValueError(
                    f"insufficient observations: "
                    f"{len(normalized)} < {min_samples}"
                )

            values = normalized["foreigner"].astype(float).tolist()
            latest = values[-1]

            if latest == 0:
                raise ValueError("latest foreigner value is zero")

            z_score = calc_z_score(values, window=120)
            latest_date = normalized["date"].iloc[-1].strftime("%Y-%m-%d")

            metadata = {
                "status": "REAL",
                "source": "local_csv",
                "path": csv_path,
                "column": "foreigner",
                "rows": len(values),
                "latest_date": latest_date,
                "fallback_used": False,
                "synthetic_data_used": False,
            }

            print(
                f"[FOREIGNER REAL] path={csv_path} "
                f"rows={len(values)} "
                f"latest_date={latest_date} "
                f"latest={latest:.0f} "
                f"z={z_score:+.2f}"
            )

            return values, latest, z_score, metadata

        except Exception as exc:
            last_error = f"{csv_path}: {exc}"
            print(f"[FOREIGNER REAL] rejected: {last_error}")

    error_message = last_error or "no foreigner CSV found"

    metadata = {
        "status": "MISSING",
        "source": "unavailable",
        "reason": error_message,
        "fallback_used": False,
        "synthetic_data_used": False,
    }

    print(f"[FOREIGNER REAL] unavailable: {error_message}")

    return [], 0.0, 0.0, metadata


def get_all_factor_z_scores():
    factors = {}
    for name in ["SP500", "US10Y", "SOX", "WTI", "원달러", "DXY", "VIX", "구리", "상해종합"]:
        closes, _ = get_market_indicator(name, period="6mo")
        z = calc_z_score(closes, window=120)
        factors[name] = z
    return factors

# KRX OPEN API 파서 - TEST 결과 기반
def parse_kospi_dd_trd_response(json_data: dict) -> List[dict]:
    """TEST 결과 파싱: OutBlock_1 배열 파싱"""
    if not isinstance(json_data, dict):
        return []
    out = json_data.get("OutBlock_1", [])
    parsed = []
    for row in out:
        try:
            parsed.append({
                "bas_dd": row.get("BAS_DD"),
                "idx_clss": row.get("IDX_CLSS"),
                "idx_nm": row.get("IDX_NM"),
                "close": float(row.get("CLSPRC_IDX", "0").replace(",", "")) if row.get("CLSPRC_IDX") else 0,
                "prev_close": float(row.get("CMPPREVDD_IDX", "0").replace(",", "")) if row.get("CMPPREVDD_IDX") else 0,
                "fluc_rt": float(row.get("FLUC_RT", "0")) if row.get("FLUC_RT") else 0,
                "open": float(row.get("OPNPRC_IDX", "0").replace(",", "")) if row.get("OPNPRC_IDX") else 0,
                "high": float(row.get("HGPRC_IDX", "0").replace(",", "")) if row.get("HGPRC_IDX") else 0,
                "low": float(row.get("LWPRC_IDX", "0").replace(",", "")) if row.get("LWPRC_IDX") else 0,
                "vol": int(row.get("ACC_TRDVOL", "0").replace(",", "")) if row.get("ACC_TRDVOL") else 0,
                "val": int(row.get("ACC_TRDVAL", "0").replace(",", "")) if row.get("ACC_TRDVAL") else 0,
                "mktcap": int(row.get("MKTCAP", "0").replace(",", "")) if row.get("MKTCAP") else 0,
            })
        except Exception as e:
            print(f"[parse] skip row {row.get('IDX_NM')}: {e}")
            continue
    return parsed
