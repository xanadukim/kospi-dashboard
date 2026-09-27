"""
regime_detector.py v60 - Regime Detection 100% REAL
- VIX, OVX, DXY, TNX, KRW, KOSPI, SP500, WTI 기반으로 현재 체제 감지
- 평시 / 고변동 / 전시 3단계 + confidence + 트리거 + 권장 윈도우
- daily_update.py에서 import하여 Firebase에 저장
"""

import os
import numpy as np
from datetime import datetime
from typing import Dict, Tuple, List

try:
    from price_provider import get_market_indicator, calc_z_score
except ImportError:
    from scripts.price_provider import get_market_indicator, calc_z_score

def calc_volatility(series: List[float], window: int = 5) -> float:
    """5일 변동성 (%) - 표준편차 기반"""
    try:
        if len(series) < window + 1:
            return 0.0
        recent = series[-window:]
        returns = [(recent[i] - recent[i-1]) / recent[i-1] * 100 for i in range(1, len(recent))]
        if not returns:
            return 0.0
        vol = float(np.std(returns))
        return round(vol, 2)
    except:
        return 0.0

def fetch_regime_indicators() -> Dict:
    """Regime 감지에 필요한 8개 지표 REAL fetch"""
    indicators = {}
    
    # VIX - 공포지수 (핵심)
    closes, latest = get_market_indicator("VIX", period="6mo")
    indicators["VIX"] = {
        "latest": latest,
        "closes": closes,
        "z": calc_z_score(closes),
        "vol_5d": calc_volatility(closes, 5)
    }
    
    # OVX - 원유 변동성 (전시 트리거)
    closes, latest = get_market_indicator("OVX", period="6mo")
    if not closes:
        # OVX가 yfinance에서 간헐적 실패 시 WTI로 프록시
        closes_wti, latest_wti = get_market_indicator("WTI", period="6mo")
        vol_wti = calc_volatility(closes_wti, 5)
        indicators["OVX"] = {
            "latest": vol_wti * 8 + 25,  # WTI vol *8 + 25로 OVX 추정
            "closes": closes_wti,
            "z": calc_z_score(closes_wti),
            "vol_5d": vol_wti,
            "is_proxy": True
        }
    else:
        indicators["OVX"] = {
            "latest": latest,
            "closes": closes,
            "z": calc_z_score(closes),
            "vol_5d": calc_volatility(closes, 5),
            "is_proxy": False
        }
    
    # DXY - 달러 인덱스
    closes, latest = get_market_indicator("DXY", period="6mo")
    indicators["DXY"] = {
        "latest": latest,
        "closes": closes,
        "z": calc_z_score(closes),
        "vol_5d": calc_volatility(closes, 5)
    }
    
    # TNX - US 10Y (금리)
    closes, latest = get_market_indicator("US10Y", period="6mo")
    indicators["TNX"] = {
        "latest": latest,
        "closes": closes,
        "z": calc_z_score(closes),
        "vol_5d": calc_volatility(closes, 5)
    }
    
    # KRW - 원달러
    closes, latest = get_market_indicator("원달러", period="6mo")
    indicators["KRW"] = {
        "latest": latest,
        "closes": closes,
        "z": calc_z_score(closes),
        "vol_5d": calc_volatility(closes, 5)
    }
    
    # KOSPI
    closes, latest = get_market_indicator("KOSPI", period="6mo")
    indicators["KOSPI"] = {
        "latest": latest,
        "closes": closes,
        "z": calc_z_score(closes),
        "vol_5d": calc_volatility(closes, 5),
        "return_3d": round((closes[-1] / closes[-4] - 1) * 100, 2) if len(closes) >= 4 else 0.0
    }
    
    # SP500
    closes, latest = get_market_indicator("SP500", period="6mo")
    indicators["SP500"] = {
        "latest": latest,
        "closes": closes,
        "z": calc_z_score(closes),
        "vol_5d": calc_volatility(closes, 5)
    }
    
    # WTI
    closes, latest = get_market_indicator("WTI", period="6mo")
    indicators["WTI"] = {
        "latest": latest,
        "closes": closes,
        "z": calc_z_score(closes),
        "vol_5d": calc_volatility(closes, 5)
    }
    
    print(f"[Regime] Fetched 8 indicators - VIX {indicators['VIX']['latest']:.1f} OVX {indicators['OVX']['latest']:.1f} DXY {indicators['DXY']['latest']:.1f}")
    return indicators

def detect_regime(indicators: Dict) -> Dict:
    """
    Regime 감지 로직 v60
    - 평시: VIX<22, OVX<35, WTI_vol<4%
    - 고변동: VIX 22-30, OVX 35-50, WTI_vol>4% or VIX>22
    - 전시: VIX>30, OVX>50, or KOSPI 3일 -3% 급락, or DXY>105 + VIX>28
    
    Returns: {regime, confidence, triggers, window, color, risk_level}
    """
    vix = indicators.get("VIX", {}).get("latest", 18.5)
    ovx = indicators.get("OVX", {}).get("latest", 30.0)
    wti_vol = indicators.get("WTI", {}).get("vol_5d", 2.0)
    dxy = indicators.get("DXY", {}).get("latest", 103.0)
    kospi_3d = indicators.get("KOSPI", {}).get("return_3d", 0.0)
    vix_z = indicators.get("VIX", {}).get("z", 0.0)
    ovx_z = indicators.get("OVX", {}).get("z", 0.0)
    
    triggers = []
    regime = "평시"
    confidence = 0.85
    color = "#10b981"
    risk_level = "Low"
    window = 120
    
    # 전시 트리거 (가장 높은 우선순위)
    if vix > 30:
        triggers.append(f"VIX {vix:.1f}>30 (공포)")
    if ovx > 50:
        triggers.append(f"OVX {ovx:.1f}>50 (원유 변동성 폭증)")
    if kospi_3d < -3.0:
        triggers.append(f"KOSPI 3일 {kospi_3d:.1f}% 급락")
    if dxy > 105 and vix > 28:
        triggers.append(f"DXY {dxy:.1f}>105 + VIX {vix:.1f}>28 (달러 강세+공포)")
    if vix_z > 2.0 and ovx_z > 1.5:
        triggers.append(f"VIX Z {vix_z:.2f} + OVX Z {ovx_z:.2f} 동시 급등")
    
    if triggers:
        regime = "전시"
        confidence = min(0.95, 0.70 + len(triggers) * 0.10 + max(0, (vix - 30) / 20))
        color = "#dc2626"
        risk_level = "Extreme"
        window = 60
        print(f"[Regime] 전시 감지 - {triggers} - conf {confidence:.2f}")
        return {
            "regime": regime,
            "confidence": round(confidence, 2),
            "triggers": triggers,
            "window": window,
            "color": color,
            "risk_level": risk_level,
            "vix": vix,
            "ovx": ovx,
            "dxy": dxy,
            "wti_vol": wti_vol,
            "kospi_3d": kospi_3d
        }
    
    # 고변동 트리거
    high_vol_triggers = []
    if vix > 22:
        high_vol_triggers.append(f"VIX {vix:.1f}>22")
    if ovx > 35:
        high_vol_triggers.append(f"OVX {ovx:.1f}>35")
    if wti_vol > 4.0:
        high_vol_triggers.append(f"WTI 5일 변동성 {wti_vol:.1f}% >4%")
    if dxy > 104:
        high_vol_triggers.append(f"DXY {dxy:.1f}>104")
    if abs(indicators.get("KRW", {}).get("vol_5d", 0)) > 2.5:
        high_vol_triggers.append(f"KRW 변동성 {indicators.get('KRW', {}).get('vol_5d', 0):.1f}%")
    
    if high_vol_triggers:
        regime = "고변동"
        confidence = min(0.90, 0.60 + len(high_vol_triggers) * 0.12 + max(0, (vix - 22) / 30))
        color = "#f59e0b"
        risk_level = "Medium"
        window = 90
        triggers = high_vol_triggers
        print(f"[Regime] 고변동 감지 - {triggers} - conf {confidence:.2f}")
    else:
        # 평시
        regime = "평시"
        confidence = 0.85 - max(0, (vix - 15) / 50)  # VIX 낮을수록 평시 확신 높음
        color = "#10b981"
        risk_level = "Low"
        window = 120
        triggers = [f"VIX {vix:.1f} 안정", f"OVX {ovx:.1f} 안정", f"WTI vol {wti_vol:.1f}% 정상"]
        print(f"[Regime] 평시 - VIX {vix:.1f} OVX {ovx:.1f} - conf {confidence:.2f}")
    
    return {
        "regime": regime,
        "confidence": round(confidence, 2),
        "triggers": triggers,
        "window": window,
        "color": color,
        "risk_level": risk_level,
        "vix": vix,
        "ovx": ovx,
        "dxy": dxy,
        "wti_vol": wti_vol,
        "kospi_3d": kospi_3d
    }

def get_regime_factor_adjustment(regime: str) -> Dict:
    """Regime별 팩터 유효성 조정"""
    base_factors = {
        "반도체팩터": {"평시": 0.92, "고변동": 0.85, "전시": 0.60},
        "원달러": {"평시": 0.88, "고변동": 0.82, "전시": 0.55},
        "WTI_vol": {"평시": 0.45, "고변동": 0.75, "전시": 0.90},
        "GPR": {"평시": 0.35, "고변동": 0.55, "전시": 0.85},
        "정제마진": {"평시": 0.50, "고변동": 0.68, "전시": 0.80},
        "US10Y": {"평시": 0.32, "고변동": 0.48, "전시": 0.65},
        "구리": {"평시": 0.78, "고변동": 0.70, "전시": 0.45},
        "상해종합": {"평시": 0.72, "고변동": 0.65, "전시": 0.40},
    }
    
    adjusted = {}
    for factor, probs in base_factors.items():
        adjusted[factor] = probs.get(regime, probs["평시"])
    
    return adjusted

def get_regime_config(regime: str) -> Dict:
    """Regime별 설정"""
    configs = {
        "평시": {
            "window": 120,
            "description": "안정적 - 느린 적응, 긴 윈도우로 노이즈 제거",
            "color": "#10b981",
            "risk": "Low",
            "retrain": "매월 1일",
            "factor_boost": [],
            "factor_penalty": []
        },
        "고변동": {
            "window": 90,
            "description": "변동성 확대 - 빠른 적응, 90일 윈도우로 최근 반영",
            "color": "#f59e0b",
            "risk": "Medium",
            "retrain": "즉시 + 매주",
            "factor_boost": ["WTI_vol", "정제마진"],
            "factor_penalty": ["구리", "상해종합"]
        },
        "전시": {
            "window": 60,
            "description": "위기 - 초단기 적응, 60일 윈도우, 방어적 팩터 활성화",
            "color": "#dc2626",
            "risk": "Extreme",
            "retrain": "매일",
            "factor_boost": ["GPR", "WTI_vol", "US10Y"],
            "factor_penalty": ["구리", "상해종합", "반도체팩터"]
        }
    }
    return configs.get(regime, configs["평시"])

def build_regime_snapshot() -> Dict:
    """전체 Regime 스냅샷 생성 - daily_update.py에서 호출"""
    try:
        indicators = fetch_regime_indicators()
        regime_info = detect_regime(indicators)
        factor_adj = get_regime_factor_adjustment(regime_info["regime"])
        config = get_regime_config(regime_info["regime"])
        
        snapshot = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "timestamp": datetime.now().isoformat(),
            "regime": regime_info["regime"],
            "confidence": regime_info["confidence"],
            "triggers": regime_info["triggers"],
            "window": regime_info["window"],
            "color": regime_info["color"],
            "risk_level": regime_info["risk_level"],
            "indicators": {
                "VIX": round(indicators.get("VIX", {}).get("latest", 0), 2),
                "OVX": round(indicators.get("OVX", {}).get("latest", 0), 2),
                "DXY": round(indicators.get("DXY", {}).get("latest", 0), 2),
                "WTI_vol": round(indicators.get("WTI", {}).get("vol_5d", 0), 2),
                "KOSPI_3d": round(indicators.get("KOSPI", {}).get("return_3d", 0), 2),
                "KRW_vol": round(indicators.get("KRW", {}).get("vol_5d", 0), 2),
            },
            "factor_adjustment": factor_adj,
            "config": config,
            "version": "v60-regime-detector-REAL"
        }
        
        print(f"[Regime] Snapshot: {regime_info['regime']} conf {regime_info['confidence']} window {regime_info['window']} - {regime_info['triggers'][:2]}")
        return snapshot
    except Exception as e:
        print(f"[Regime] Error building snapshot: {e}")
        import traceback
        traceback.print_exc()
        # fallback 평시
        return {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "regime": "평시",
            "confidence": 0.70,
            "triggers": [f"fallback - error: {str(e)[:50]}"],
            "window": 120,
            "color": "#10b981",
            "risk_level": "Low",
            "indicators": {},
            "factor_adjustment": get_regime_factor_adjustment("평시"),
            "config": get_regime_config("평시"),
            "version": "v60-regime-detector-fallback"
        }

if __name__ == "__main__":
    snap = build_regime_snapshot()
    import json
    print(json.dumps(snap, ensure_ascii=False, indent=2))
