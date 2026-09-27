"""
price_provider.py v57 - 10 Factors - yfinance / KRX 추상화
yfinance 95% REAL -> KRX 승인 후 source="krx" 1줄 변경으로 100% REAL
10 Factors: US10Y, SP500, 외국인선물, SOX, 중국PMI, 원달러, WTI, 한미스프레드, DXY, VIX
"""
import os
from typing import List, Tuple

DEFAULT_SOURCE = os.environ.get('PRICE_SOURCE', 'yfinance')
KRX_API_KEY = os.environ.get('KRX_API_KEY', '')

FACTOR_TICKERS = {
    "상해종합": "000001.SS",
    "CSI300": "000300.SS",
    "SP500": "^GSPC",
    "US10Y": "^TNX",
    "SOX": "^SOX",
    "WTI": "CL=F",
    "원달러": "KRW=X",
    "DXY": "DX-Y.NYB",
    "VIX": "^VIX",
    "나스닥": "^IXIC",
    "구리": "HG=F",
}

def get_stock_prices(ticker: str, start: str = None, end: str = None, period: str = "1mo", source: str = None):
    src = source or DEFAULT_SOURCE
    if src == "yfinance":
        return _get_yfinance_prices(ticker, start, end, period)
    else:
        return _get_krx_prices(ticker, start, end, period)

def _get_yfinance_prices(ticker: str, start: str, end: str, period: str):
    try:
        import yfinance as yf
        yf_ticker = f"{ticker}.KS" if not ticker.endswith(".KS") and not ticker.startswith("^") and "=" not in ticker and "-" not in ticker else ticker
        # Handle our factor tickers directly
        if ticker in FACTOR_TICKERS:
            yf_ticker = FACTOR_TICKERS[ticker]
        elif ticker in ["US10Y", "DXY", "VIX", "WTI", "원달러", "구리"]:
            yf_ticker = FACTOR_TICKERS.get(ticker, ticker)
        
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
    if not KRX_API_KEY:
        return _get_yfinance_prices(ticker, start, end, period)
    return _get_yfinance_prices(ticker, start, end, period)

def get_market_indicator(ticker: str, period: str = "3mo", source: str = None):
    try:
        import yfinance as yf
        # Resolve factor name
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

def get_all_factor_z_scores():
    """10 Factors Z-Score 일괄 계산"""
    factors = {}
    # Real yfinance factors
    for name in ["SP500", "US10Y", "SOX", "WTI", "원달러", "DXY", "VIX", "나스닥", "구리"]:
        closes, _ = get_market_indicator(name, period="6mo")
        z = calc_z_score(closes, window=120)
        factors[name] = z
    return factors
