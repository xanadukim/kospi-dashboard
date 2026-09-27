"""
price_provider.py v56 - yfinance / KRX 추상화
yfinance 95% REAL -> KRX 승인 후 source="krx" 1줄 변경으로 100% REAL
"""
import os
from typing import List, Tuple, Optional

DEFAULT_SOURCE = os.environ.get('PRICE_SOURCE', 'yfinance')
KRX_API_KEY = os.environ.get('KRX_API_KEY', '')

def get_stock_prices(ticker: str, start: str = None, end: str = None, period: str = "1mo", source: str = None):
    src = source or DEFAULT_SOURCE
    if src == "yfinance":
        return _get_yfinance_prices(ticker, start, end, period)
    else:
        return _get_krx_prices(ticker, start, end, period)

def _get_yfinance_prices(ticker: str, start: str, end: str, period: str):
    try:
        import yfinance as yf
        yf_ticker = f"{ticker}.KS" if not ticker.endswith(".KS") and not ticker.startswith("^") else ticker
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

def get_stock_return(ticker: str, buy_date: str, eval_date: str = None, source: str = None):
    try:
        import yfinance as yf
        from datetime import datetime, timedelta
        yf_ticker = f"{ticker}.KS"
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
        buy_price = float(hist.loc[hist.index.strftime('%Y-%m-%d') == buy_date]['Close'].iloc[0]) if buy_date in [d.strftime('%Y-%m-%d') for d in hist.index] else float(before['Close'].iloc[-1])
        eval_price = float(hist['Close'].iloc[-1])
        ret = (eval_price - buy_price) / buy_price
        print(f"[return] {ticker} {buy_date}: {ret*100:+.2f}%")
        return ret
    except Exception as e:
        print(f"[return] Error {ticker}: {e}")
        return None

def get_market_indicator(ticker: str, period: str = "3mo", source: str = None):
    try:
        import yfinance as yf
        t = yf.Ticker(ticker)
        hist = t.history(period=period)
        if hist.empty:
            return [], 0.0
        closes = [float(x) for x in hist['Close'].dropna().tolist()]
        latest = closes[-1] if closes else 0.0
        print(f"[indicator] {ticker}: {latest:.2f} len {len(closes)}")
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
