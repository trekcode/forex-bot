# ================================================================
# SCALPBOT PRO — STREAMLIT ALERT DASHBOARD v4.0
# SMC/ICT Top-Down · Regime Aware · Beautiful Dark UI
# Plotly Charts · Auto-Send · Full Confluence Scoring
# ================================================================
# Deploy: Upload to GitHub → Streamlit Cloud (free)
# Requirements: streamlit yfinance pandas numpy requests plotly
# ================================================================

import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime, timedelta
import requests
import logging
import time
from dataclasses import dataclass, field
from typing import Optional, List, Tuple, Dict
from enum import Enum

# ── PAGE CONFIG (must be first) ──────────────────────────────────
st.set_page_config(
    page_title="ScalpBot Pro",
    page_icon="🥇",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ================================================================
# GLOBAL CSS — dark pro theme, permanent sidebar
# ================================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.stApp { background: #0a0e1a; color: #e8eaf6; }
#MainMenu, footer, header { visibility: hidden; }

/* ── PERMANENT SIDEBAR ── */
[data-testid="stSidebar"] {
    background: #0d1117 !important;
    border-right: 1px solid #1e2d40 !important;
    min-width: 280px !important;
    max-width: 280px !important;
}
[data-testid="stSidebarCollapseButton"],
button[aria-label="Close sidebar"],
button[aria-label="Collapse sidebar"],
button[aria-label="Open sidebar"],
[data-testid="collapsedControl"] { display: none !important; }
[data-testid="stSidebar"] * { color: #c9d1d9 !important; }

/* ── Metrics ── */
[data-testid="metric-container"] {
    background: #0d1117; border: 1px solid #1e2d40;
    border-radius: 12px; padding: .9rem 1.1rem;
}
[data-testid="stMetricValue"] { color: #e8eaf6 !important; font-size: 1.3rem !important; }
[data-testid="stMetricLabel"] { color: #8b949e !important; }
[data-testid="stMetricDelta"] { font-size: .75rem !important; }

/* ── Buttons ── */
.stButton > button {
    border-radius: 8px; font-weight: 600; border: none;
    transition: all .2s; color: #e8eaf6 !important;
}
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #238636, #2ea043) !important;
    color: white !important;
}
.stButton > button:hover { transform: translateY(-1px); opacity: .9; }

/* ── Tabs ── */
[data-baseweb="tab-list"] {
    background: #0d1117; border-radius: 10px;
    padding: 4px; gap: 4px; border: 1px solid #1e2d40;
}
[data-baseweb="tab"] { border-radius: 8px; color: #8b949e !important; }
[aria-selected="true"][data-baseweb="tab"] {
    background: #1e2d40 !important; color: #e8eaf6 !important; font-weight: 600;
}
hr { border-color: #1e2d40; }
.stSpinner > div { border-top-color: #238636 !important; }
input, textarea, select {
    background: #0d1117 !important; border: 1px solid #30363d !important;
    color: #e8eaf6 !important; border-radius: 6px !important;
}

/* ── HERO ── */
.hero {
    background: linear-gradient(135deg, #0d1f3c 0%, #0a2a1a 50%, #1a0d3c 100%);
    border: 1px solid #1e2d40; border-radius: 16px;
    padding: 1.5rem 2rem; margin-bottom: 1.2rem;
    position: relative; overflow: hidden;
}
.hero::before {
    content:''; position:absolute; top:-60px; right:-60px;
    width:200px; height:200px;
    background:radial-gradient(circle,rgba(35,134,54,.15) 0%,transparent 70%);
    border-radius:50%;
}
.hero h1 { margin:0; font-size:1.75rem; font-weight:700; color:#e8eaf6; }
.hero p  { margin:.3rem 0 0; color:#8b949e; font-size:.85rem; }

/* ── SIGNAL CARDS ── */
.signal-card {
    border-radius: 14px; padding: 1.4rem;
    margin: .4rem 0 .8rem; position: relative; overflow: hidden;
}
.signal-buy  { background:linear-gradient(135deg,#051f0f,#0d3320); border:1px solid #238636; }
.signal-sell { background:linear-gradient(135deg,#1f0505,#330d0d); border:1px solid #da3633; }
.signal-hold { background:linear-gradient(135deg,#0d1117,#161b22); border:1px solid #30363d; }
.glow-buy  { position:absolute;top:-40px;right:-40px;width:150px;height:150px;background:radial-gradient(circle,rgba(35,134,54,.22) 0%,transparent 70%);border-radius:50%; }
.glow-sell { position:absolute;top:-40px;right:-40px;width:150px;height:150px;background:radial-gradient(circle,rgba(218,54,51,.22) 0%,transparent 70%);border-radius:50%; }
.sig-title { font-size:1.6rem; font-weight:700; margin:0 0 .15rem; }
.sig-sub   { color:#8b949e; font-size:.82rem; margin:0 0 1rem; }
.sig-grid  { display:grid; grid-template-columns:repeat(3,1fr); gap:.65rem; }
.sig-item  { background:rgba(255,255,255,.045); border-radius:8px; padding:.5rem .7rem; }
.sig-item .label { font-size:10px; color:#8b949e; text-transform:uppercase; letter-spacing:.04em; }
.sig-item .value { font-size:.92rem; font-weight:600; color:#e8eaf6; margin-top:2px; }
.sig-item .value.green { color:#3fb950; }
.sig-item .value.red   { color:#f85149; }
.sig-item .value.gold  { color:#d29922; }

/* ── INDICATORS ── */
.ind-row { display:flex; justify-content:space-between; align-items:center; padding:6px 0; border-bottom:1px solid #1e2d40; font-size:12.5px; }
.ind-row:last-child { border-bottom:none; }
.ind-label { color:#8b949e; }

/* ── BADGES ── */
.badge { display:inline-block; padding:2px 9px; border-radius:20px; font-size:11px; font-weight:600; }
.bg { background:#0d2618; color:#3fb950; border:1px solid #238636; }
.br { background:#26070a; color:#f85149; border:1px solid #da3633; }
.bgy{ background:#161b22; color:#8b949e; border:1px solid #30363d; }
.by { background:#261d05; color:#d29922; border:1px solid #9e6a03; }
.bp { background:#1a0d2e; color:#bc8cff; border:1px solid #6e40c9; }
.bb { background:#051929; color:#58a6ff; border:1px solid #1f6feb; }
.bo { background:#271700; color:#f0883e; border:1px solid #bd561d; }

/* ── SCORE BARS ── */
.sbar-wrap { margin-bottom:.7rem; }
.sbar-row  { display:flex; justify-content:space-between; font-size:12px; margin-bottom:3px; color:#c9d1d9; }
.sbar-bg   { background:#1e2d40; border-radius:4px; height:6px; }
.sbar-fill { height:6px; border-radius:4px; }

/* ── SMC STRENGTH METER ── */
.smc-meter { display:grid; grid-template-columns:repeat(5,1fr); gap:8px; margin:.5rem 0; }
.smc-bw { text-align:center; }
.smc-bl { font-size:9.5px; color:#8b949e; margin-bottom:3px; text-transform:uppercase; }
.smc-bo { background:#1e2d40; border-radius:5px; height:55px; display:flex; flex-direction:column-reverse; overflow:hidden; }
.smc-bi { border-radius:5px; }

/* ── BIAS PILLS ── */
.bias-row { display:flex; gap:8px; margin:.4rem 0 .9rem; flex-wrap:wrap; }
.bias-pill { padding:.35rem .85rem; border-radius:20px; font-size:12.5px; font-weight:600; border:1px solid transparent; }
.bull { background:#0d2618; color:#3fb950; border-color:#238636; }
.bear { background:#26070a; color:#f85149; border-color:#da3633; }
.neut { background:#161b22; color:#8b949e; border-color:#30363d; }

/* ── REGIME BADGE ── */
.regime-tag { display:inline-block; padding:3px 12px; border-radius:6px; font-size:12px; font-weight:600; margin-bottom:.7rem; }
.regime-trend  { background:#0d2618; color:#3fb950; border:1px solid #238636; }
.regime-range  { background:#261d05; color:#d29922; border:1px solid #9e6a03; }
.regime-vol    { background:#26070a; color:#f85149; border:1px solid #da3633; }

/* ── AUTO PANEL ── */
.auto-panel { background:#0d1117; border:1px solid #1e2d40; border-radius:12px; padding:.9rem 1.1rem; margin-bottom:.8rem; }
.auto-panel.active { border-color:#238636; box-shadow:0 0 14px rgba(35,134,54,.18); }
.countdown { font-size:1.85rem; font-weight:700; color:#3fb950; }

/* ── SMC LEVEL CARDS ── */
.smc-card { background:#0d1117; border:1px solid #1e2d40; border-radius:9px; padding:.75rem .9rem; margin-bottom:.4rem; font-size:12.5px; }
.smc-card.ob-b { border-left:3px solid #238636; }
.smc-card.ob-s { border-left:3px solid #da3633; }
.smc-card.fvg-b { border-left:3px solid #58a6ff; }
.smc-card.fvg-s { border-left:3px solid #bc8cff; }
.smc-card.liq   { border-left:3px solid #d29922; }
.smc-card.sd-d  { border-left:3px solid #3fb950; }
.smc-card.sd-s  { border-left:3px solid #f85149; }

/* ── HISTORY ── */
.hist-buy  { border-left:3px solid #238636; background:rgba(35,134,54,.06); }
.hist-sell { border-left:3px solid #da3633; background:rgba(218,54,51,.06); }
.hist-row  { padding:.45rem .7rem; border-radius:6px; margin-bottom:3px; display:grid; grid-template-columns:65px 1fr 55px 70px 1fr 1fr 50px; gap:6px; font-size:11.5px; align-items:center; }
.hist-hdr  { padding:.35rem .7rem; border-radius:6px; display:grid; grid-template-columns:65px 1fr 55px 70px 1fr 1fr 50px; gap:6px; font-size:10px; color:#8b949e; text-transform:uppercase; letter-spacing:.04em; margin-bottom:4px; }

/* ── STAT CARDS ── */
.stat-card { background:#0d1117; border:1px solid #1e2d40; border-radius:10px; padding:.85rem; text-align:center; }
.stat-v { font-size:1.4rem; font-weight:700; }
.stat-l { font-size:11px; color:#8b949e; margin-top:2px; }

/* ── TOAST ── */
.toast-ok  { background:#0d2618; border:1px solid #238636; color:#3fb950; border-radius:8px; padding:.5rem .9rem; font-size:12.5px; margin:.3rem 0; }
.toast-err { background:#26070a; border:1px solid #da3633; color:#f85149; border-radius:8px; padding:.5rem .9rem; font-size:12.5px; margin:.3rem 0; }

.stitle { font-size:.72rem; font-weight:600; text-transform:uppercase; letter-spacing:.08em; color:#8b949e; margin:.45rem 0 .6rem; }
</style>
""", unsafe_allow_html=True)

# ================================================================
# LOGGING
# ================================================================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ScalpBot")

# ================================================================
# ENUMS & DATACLASSES
# ================================================================
class SignalType(Enum):
    BUY  = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"

class MarketRegime(Enum):
    TRENDING = "TRENDING"
    RANGING  = "RANGING"
    VOLATILE = "VOLATILE"

@dataclass
class SMCData:
    """Full SMC analysis result"""
    daily_bias:    str
    h4_bias:       str
    h1_bias:       str
    entry_bias:    str
    regime:        MarketRegime
    adx:           float
    bos:           bool
    choch:         bool
    struct_dir:    str
    order_blocks:  List[dict] = field(default_factory=list)
    fvgs:          List[dict] = field(default_factory=list)
    liquidity:     List[dict] = field(default_factory=list)
    supply_demand: List[dict] = field(default_factory=list)
    structure_score: float = 0.0
    ob_score:       float = 0.0
    fvg_score:      float = 0.0
    liq_score:      float = 0.0
    confluence_score: float = 0.0
    key_level:      str = "None"
    df_entry:       Optional[pd.DataFrame] = None

@dataclass
class TradeSignal:
    """Complete signal with SMC enrichment"""
    signal:          SignalType
    pair:            str
    symbol:          str
    entry:           float
    stop_loss:       float
    take_profit:     float
    confidence:      int
    risk_reward:     float
    lot_size:        float
    session:         str
    timestamp:       datetime
    expiry:          datetime
    rsi:             float
    macd_hist:       float
    stoch_k:         float
    volume_ratio:    float
    trend:           str
    atr:             float
    bb_pct:          float
    regime:          str
    adx:             float
    # Score components
    trend_score:     float
    momentum_score:  float
    volume_score:    float
    mtf_score:       float
    smc_score:       float
    # SMC enrichment
    smc_confluence_score: float
    key_level_type:  str
    daily_bias:      str
    h4_bias:         str
    entry_pattern:   str = "—"

# ================================================================
# INSTRUMENTS
# ================================================================
INSTRUMENTS = {
    "GC=F":     {"name": "XAU/USD · Gold",   "emoji": "🥇", "dec": 2, "pip": 0.10},
    "EURUSD=X": {"name": "EUR/USD",          "emoji": "🇪🇺", "dec": 5, "pip": 10.0},
    "GBPUSD=X": {"name": "GBP/USD",          "emoji": "🇬🇧", "dec": 5, "pip": 10.0},
    "USDJPY=X": {"name": "USD/JPY",          "emoji": "🇯🇵", "dec": 3, "pip": 9.0},
    "^DJI":     {"name": "US30 · Dow Jones", "emoji": "🇺🇸", "dec": 2, "pip": 1.0},
    "^NDX":     {"name": "US100 · Nasdaq",   "emoji": "💻",  "dec": 2, "pip": 0.5},
    "SI=F":     {"name": "XAG/USD · Silver", "emoji": "🥈", "dec": 3, "pip": 50.0},
}

# ================================================================
# DATA FETCHING
# ================================================================
@st.cache_data(ttl=55, show_spinner=False)
def fetch(symbol: str, period: str, interval: str) -> Optional[pd.DataFrame]:
    try:
        df = yf.Ticker(symbol).history(period=period, interval=interval)
        return df if len(df) >= 30 else None
    except Exception as e:
        logger.error(f"Fetch {symbol} {interval}: {e}")
        return None

# ================================================================
# INDICATORS ENGINE
# ================================================================
def rsi_series(c: pd.Series, n: int = 14) -> pd.Series:
    d = c.diff()
    g = d.where(d > 0, 0).rolling(n).mean()
    l = (-d.where(d < 0, 0)).rolling(n).mean()
    return 100 - 100 / (1 + g / l.replace(0, np.nan))

def ema(c: pd.Series, n: int) -> pd.Series:
    return c.ewm(span=n, adjust=False).mean()

def compute_indicators(df: pd.DataFrame) -> Optional[dict]:
    try:
        c, h, l, v = df["Close"], df["High"], df["Low"], df["Volume"]
        e20 = ema(c, 20); e50 = ema(c, 50)
        delta = c.diff()
        gain  = delta.where(delta > 0, 0).rolling(14).mean()
        loss  = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rsi   = 100 - 100 / (1 + gain / loss.replace(0, np.nan))
        macd  = c.ewm(span=12, adjust=False).mean() - c.ewm(span=26, adjust=False).mean()
        macd_h = macd - macd.ewm(span=9, adjust=False).mean()
        tr    = pd.concat([h-l, abs(h-c.shift()), abs(l-c.shift())], axis=1).max(axis=1)
        atr   = tr.rolling(14).mean()
        sma20 = c.rolling(20).mean(); std20 = c.rolling(20).std()
        bb_pct = (c - (sma20 - 2*std20)) / (4*std20).replace(0, np.nan)
        lo14 = l.rolling(14).min(); hi14 = h.rolling(14).max()
        stoch = 100 * (c - lo14) / (hi14 - lo14).replace(0, np.nan)
        vol_r = v / v.rolling(20).mean().replace(0, np.nan)
        # ADX
        up_ = h.diff(); dn_ = -l.diff()
        dmp = up_.where((up_>dn_)&(up_>0), 0)
        dmm = dn_.where((dn_>up_)&(dn_>0), 0)
        atr14 = atr
        dip = 100 * dmp.rolling(14).mean() / atr14.replace(0, np.nan)
        dim = 100 * dmm.rolling(14).mean() / atr14.replace(0, np.nan)
        dx  = 100 * abs(dip - dim) / (dip + dim).replace(0, np.nan)
        adx = dx.rolling(14).mean()
        price = float(c.iloc[-1])
        trend = ("bullish" if price > e20.iloc[-1] > e50.iloc[-1]
                 else "bearish" if price < e20.iloc[-1] < e50.iloc[-1] else "mixed")
        atr_v = float(atr.iloc[-1]); atr_pct = atr_v / price * 100
        regime = (MarketRegime.VOLATILE if atr_pct > 0.8
                  else MarketRegime.TRENDING if float(adx.iloc[-1]) >= 25 else MarketRegime.RANGING)
        return dict(
            price=price, ema20=float(e20.iloc[-1]), ema50=float(e50.iloc[-1]),
            rsi=float(rsi.iloc[-1]), macd_hist=float(macd_h.iloc[-1]),
            atr=atr_v, bb_pct=float(bb_pct.iloc[-1]),
            stoch_k=float(stoch.iloc[-1]), volume_ratio=float(vol_r.iloc[-1]),
            trend=trend, adx=float(adx.iloc[-1]), regime=regime,
        )
    except Exception as e:
        logger.error(f"Indicators: {e}")
        return None

# ================================================================
# SMC ENGINE
# ================================================================
def _bias(symbol: str, period: str, interval: str) -> str:
    df = fetch(symbol, period, interval)
    if df is None or len(df) < 22: return "unknown"
    c = df["Close"]
    e20 = ema(c, 20); e50 = ema(c, 50)
    p = float(c.iloc[-1])
    if p > e20.iloc[-1] > e50.iloc[-1]: return "bullish"
    if p < e20.iloc[-1] < e50.iloc[-1]: return "bearish"
    return "mixed"

def _swings(df: pd.DataFrame, left: int = 3, right: int = 3):
    h, l = df["High"].values, df["Low"].values
    sh, sl = [], []
    for i in range(left, len(h) - right):
        if all(h[i] >= h[i-j] for j in range(1, left+1)) and all(h[i] >= h[i+j] for j in range(1, right+1)):
            sh.append((i, float(h[i])))
        if all(l[i] <= l[i-j] for j in range(1, left+1)) and all(l[i] <= l[i+j] for j in range(1, right+1)):
            sl.append((i, float(l[i])))
    return sh, sl

def detect_bos_choch(df: pd.DataFrame) -> dict:
    sh, sl = _swings(df)
    price = float(df["Close"].iloc[-1])
    res = {"bos": False, "choch": False, "dir": "none"}
    if len(sh) >= 2 and price > sh[-1][1]:
        res["bos"]  = sh[-1][1] > sh[-2][1]
        res["choch"]= sh[-1][1] <= sh[-2][1]
        res["dir"]  = "bullish"
    if len(sl) >= 2 and price < sl[-1][1]:
        res["bos"]  = sl[-1][1] < sl[-2][1]
        res["choch"]= sl[-1][1] >= sl[-2][1]
        res["dir"]  = "bearish"
    return res

def detect_order_blocks(df: pd.DataFrame, lookback: int = 50) -> List[dict]:
    obs = []
    df_ = df.tail(lookback).reset_index(drop=True)
    o, c = df_["Open"].values, df_["Close"].values
    h_, l_ = df_["High"].values, df_["Low"].values
    atr_v = float(pd.Series(h_ - l_).rolling(5).mean().iloc[-1]) if len(df_) > 5 else (h_[-1] - l_[-1])
    price = c[-1]
    for i in range(2, len(df_) - 2):
        imp = abs(c[min(i+3, len(df_)-1)] - c[i])
        if c[i] < o[i] and imp > atr_v * 0.9:   # bullish OB
            strength = min(1.0, imp / (atr_v * 3))
            mitig = any(l_[j] < float(o[i]) and c[j] < float(l_[i]) for j in range(i+1, len(df_)))
            obs.append({"type":"bullish","top":float(o[i]),"bottom":float(l_[i]),
                        "mid":(float(o[i])+float(l_[i]))/2,"strength":strength,"mitigated":mitig})
        elif c[i] > o[i] and imp > atr_v * 0.9: # bearish OB
            strength = min(1.0, imp / (atr_v * 3))
            mitig = any(h_[j] > float(o[i]) and c[j] > float(h_[i]) for j in range(i+1, len(df_)))
            obs.append({"type":"bearish","top":float(h_[i]),"bottom":float(o[i]),
                        "mid":(float(h_[i])+float(o[i]))/2,"strength":strength,"mitigated":mitig})
    fresh = [x for x in obs if not x["mitigated"]]
    fresh.sort(key=lambda x: x["strength"], reverse=True)
    return fresh[:4]

def detect_fvgs(df: pd.DataFrame, lookback: int = 40) -> List[dict]:
    fvgs = []
    df_ = df.tail(lookback).reset_index(drop=True)
    h_, l_, c_ = df_["High"].values, df_["Low"].values, df_["Close"].values
    price = c_[-1]
    for i in range(1, len(df_) - 1):
        if h_[i-1] < l_[i+1]:   # bullish FVG
            top, bot = float(l_[i+1]), float(h_[i-1])
            filled = any(l_[j] <= bot for j in range(i+1, len(df_)))
            if not filled: fvgs.append({"type":"bullish","top":top,"bottom":bot,"mid":(top+bot)/2})
        elif l_[i-1] > h_[i+1]: # bearish FVG
            top, bot = float(l_[i-1]), float(h_[i+1])
            filled = any(h_[j] >= top for j in range(i+1, len(df_)))
            if not filled: fvgs.append({"type":"bearish","top":top,"bottom":bot,"mid":(top+bot)/2})
    fvgs.sort(key=lambda x: abs(x["mid"] - price))
    return fvgs[:4]

def detect_liquidity(df: pd.DataFrame, lookback: int = 40, tol_pct: float = 0.0015) -> List[dict]:
    levels = []
    df_ = df.tail(lookback).reset_index(drop=True)
    h_, l_, c_ = df_["High"].values, df_["Low"].values, df_["Close"].values
    n = len(df_); price = c_[-1]
    seen = []
    for i in range(n - 1):
        for j in range(i+1, min(i+8, n)):
            tol_h = h_[i] * tol_pct
            if abs(h_[i] - h_[j]) < tol_h:
                lp = float((h_[i] + h_[j]) / 2)
                swept = any(h_[k] > lp and c_[k] < lp for k in range(j+1, n))
                if not any(abs(lp - s) < lp * 0.002 for s in seen):
                    seen.append(lp)
                    levels.append({"type":"buy_side","price":lp,"swept":swept,"strength":0.8 if swept else 0.5})
            tol_l = l_[i] * tol_pct
            if abs(l_[i] - l_[j]) < tol_l:
                lp = float((l_[i] + l_[j]) / 2)
                swept = any(l_[k] < lp and c_[k] > lp for k in range(j+1, n))
                if not any(abs(lp - s) < lp * 0.002 for s in seen):
                    seen.append(lp)
                    levels.append({"type":"sell_side","price":lp,"swept":swept,"strength":0.8 if swept else 0.5})
    levels.sort(key=lambda x: x["strength"], reverse=True)
    return levels[:5]

def detect_sd_zones(df: pd.DataFrame, lookback: int = 60) -> List[dict]:
    zones = []
    df_ = df.tail(lookback).reset_index(drop=True)
    h_, l_, c_, o_ = df_["High"].values, df_["Low"].values, df_["Close"].values, df_["Open"].values
    avg_r = float(np.mean(h_ - l_))
    for i in range(2, len(df_) - 2):
        imp = abs(c_[min(i+3, len(df_)-1)] - c_[i])
        if c_[i] > o_[i] and imp > avg_r * 1.5:   # demand
            zones.append({"type":"demand","top":float(c_[i]),"bottom":float(min(l_[max(0,i-2):i+1])),
                          "mid":float((c_[i]+min(l_[max(0,i-2):i+1]))/2),"strength":min(1.0,imp/(avg_r*4))})
        elif c_[i] < o_[i] and imp > avg_r * 1.5:  # supply
            zones.append({"type":"supply","top":float(max(h_[max(0,i-2):i+1])),"bottom":float(c_[i]),
                          "mid":float((max(h_[max(0,i-2):i+1])+c_[i])/2),"strength":min(1.0,imp/(avg_r*4))})
    zones.sort(key=lambda x: x["strength"], reverse=True)
    return zones[:3]

def detect_entry_pattern(df: pd.DataFrame, direction: str) -> str:
    if len(df) < 3: return "—"
    last, prev, m = df.iloc[-1], df.iloc[-2], df.iloc[-3]
    if direction == "bullish":
        if (last["Close"] > last["Open"] and prev["Close"] < prev["Open"] and
                last["Close"] > prev["Open"] and last["Open"] < prev["Close"]):
            return "Bullish Engulfing"
        body = abs(last["Close"] - last["Open"])
        lw   = min(last["Close"], last["Open"]) - last["Low"]
        if lw > body * 2.2 and last["Close"] > last["Open"]: return "Hammer"
    else:
        if (last["Close"] < last["Open"] and prev["Close"] > prev["Open"] and
                last["Close"] < prev["Open"] and last["Open"] > prev["Close"]):
            return "Bearish Engulfing"
        body = abs(last["Close"] - last["Open"])
        uw   = last["High"] - max(last["Close"], last["Open"])
        if uw > body * 2.2 and last["Close"] < last["Open"]: return "Shooting Star"
    return "—"

@st.cache_data(ttl=55, show_spinner=False)
def run_smc_analysis(symbol: str, entry_tf: str, period_map: dict) -> SMCData:
    daily_bias = _bias(symbol, "60d", "1d")
    h4_bias    = _bias(symbol, "30d", "4h")
    h1_bias    = _bias(symbol, "10d", "1h")
    entry_bias = _bias(symbol, period_map.get(entry_tf, "5d"), entry_tf)

    df_entry = fetch(symbol, period_map.get(entry_tf, "5d"), entry_tf)
    if df_entry is None:
        return SMCData(daily_bias=daily_bias, h4_bias=h4_bias, h1_bias=h1_bias, entry_bias=entry_bias,
                       regime=MarketRegime.RANGING, adx=20.0, bos=False, choch=False, struct_dir="none")

    struct  = detect_bos_choch(df_entry)
    obs     = detect_order_blocks(df_entry)
    fvgs    = detect_fvgs(df_entry)
    liqs    = detect_liquidity(df_entry)
    sds     = detect_sd_zones(df_entry)

    ind     = compute_indicators(df_entry)
    regime  = ind["regime"] if ind else MarketRegime.RANGING
    adx_v   = ind["adx"] if ind else 20.0
    price   = float(df_entry["Close"].iloc[-1]) if ind else 0.0

    # Scores
    biases = [daily_bias, h4_bias, h1_bias, entry_bias]
    align  = max(biases.count("bullish"), biases.count("bearish"))
    struct_score = min(100, (align / 4) * 60 + (40 if struct["bos"] or struct["choch"] else 0))
    ob_score     = min(100, sum(o["strength"] * 40 for o in obs[:2]))
    fvg_score    = min(100, len(fvgs) * 25.0)
    liq_score    = min(100, len(liqs) * 15 + sum(1 for l in liqs if l["swept"]) * 20)

    # Confluence
    conf_score = 0.0; conf_hits = []
    for ob in obs[:2]:
        if ob["bottom"] <= price <= ob["top"] * 1.003:
            conf_hits.append(f"{'🟢' if ob['type']=='bullish' else '🔴'} {'Bull' if ob['type']=='bullish' else 'Bear'} OB @ {ob['mid']:.4f}")
            conf_score += 30
    for fvg in fvgs[:2]:
        if fvg["bottom"] <= price <= fvg["top"]:
            conf_hits.append(f"{'🔵' if fvg['type']=='bullish' else '🟣'} FVG @ {fvg['mid']:.4f}")
            conf_score += 25
    for lv in liqs:
        if lv["swept"] and abs(price - lv["price"]) / max(price, 1) < 0.004:
            conf_hits.append(f"⚡ Swept Liq @ {lv['price']:.4f}")
            conf_score += 20
    for z in sds:
        if z["bottom"] <= price <= z["top"]:
            conf_hits.append(f"{'📗' if z['type']=='demand' else '📕'} {z['type'].title()} Zone @ {z['mid']:.4f}")
            conf_score += 15
    conf_score = min(100, conf_score)
    key_level  = " + ".join(conf_hits[:2]) if conf_hits else "Price not at key SMC level"

    return SMCData(
        daily_bias=daily_bias, h4_bias=h4_bias, h1_bias=h1_bias, entry_bias=entry_bias,
        regime=regime, adx=adx_v,
        bos=struct["bos"], choch=struct["choch"], struct_dir=struct["dir"],
        order_blocks=obs, fvgs=fvgs, liquidity=liqs, supply_demand=sds,
        structure_score=struct_score, ob_score=ob_score,
        fvg_score=fvg_score, liq_score=liq_score, confluence_score=conf_score,
        key_level=key_level, df_entry=df_entry,
    )

# ================================================================
# SIGNAL GENERATOR
# ================================================================
def generate_signal(symbol, ind, smc: SMCData, balance, risk_pct, min_conf, min_rr,
                    atr_sl, atr_tp, hold_mins, w_trend, w_mom, w_vol, w_mtf, w_smc) -> Optional[TradeSignal]:
    buy = sell = 0.0
    t_sc = m_sc = v_sc = mtf_sc = smc_sc = 0.0
    price, atr = ind["price"], ind["atr"]

    # ── Regime gate: don't trade in volatile markets
    if smc.regime == MarketRegime.VOLATILE:
        return None
    if smc.regime == MarketRegime.RANGING and smc.adx < 18:
        return None

    # ── HTF Bias gate (Daily + H4 must agree)
    htf_bull = smc.daily_bias == "bullish" and smc.h4_bias in ("bullish", "mixed")
    htf_bear = smc.daily_bias == "bearish" and smc.h4_bias in ("bearish", "mixed")
    if not htf_bull and not htf_bear:
        return None   # HTF mismatch — skip

    if htf_bull:   buy  += 4; mtf_sc = w_mtf
    elif htf_bear: sell += 4; mtf_sc = w_mtf

    # ── Structure
    if smc.bos or smc.choch:
        if smc.struct_dir == "bullish":   buy  += 3; t_sc += w_trend * 0.6
        elif smc.struct_dir == "bearish": sell += 3; t_sc += w_trend * 0.6
    if ind["trend"] == "bullish":   buy  += 2; t_sc += w_trend * 0.4
    elif ind["trend"] == "bearish": sell += 2; t_sc += w_trend * 0.4

    # ── SMC confluence
    direction_now = "bullish" if buy > sell else "bearish"
    for ob in smc.order_blocks[:2]:
        if ob["bottom"] <= price <= ob["top"] * 1.003:
            if ob["type"] == direction_now:
                buy  += 2.5 if direction_now == "bullish" else 0
                sell += 2.5 if direction_now == "bearish" else 0
                smc_sc += w_smc * 0.35
    for fvg in smc.fvgs[:2]:
        if fvg["bottom"] <= price <= fvg["top"] and fvg["type"] == direction_now:
            buy  += 1.5 if direction_now == "bullish" else 0
            sell += 1.5 if direction_now == "bearish" else 0
            smc_sc += w_smc * 0.25
    for lv in smc.liquidity:
        if lv["swept"] and abs(price - lv["price"]) / max(price, 1) < 0.004:
            if lv["type"] == "sell_side": buy  += 2
            else:                         sell += 2
            smc_sc += w_smc * 0.20
    for z in smc.supply_demand:
        if z["bottom"] <= price <= z["top"]:
            if z["type"] == "demand": buy  += 1
            else:                     sell += 1
            smc_sc += w_smc * 0.10
    smc_sc = min(w_smc, smc_sc)

    # ── Classic momentum
    rsi = ind["rsi"]
    if   rsi < 30:  buy  += 3; m_sc += w_mom * .40
    elif rsi < 45:  buy  += 1.5; m_sc += w_mom * .20
    elif rsi > 70:  sell += 3; m_sc += w_mom * .40
    elif rsi > 55:  sell += 1.5; m_sc += w_mom * .20
    if ind["macd_hist"] > 0: buy  += 1.5; m_sc += w_mom * .25
    else:                    sell += 1.5; m_sc += w_mom * .25
    sk = ind["stoch_k"]
    if sk < 20: buy += 1.5; m_sc += w_mom * .20
    elif sk > 80: sell += 1.5; m_sc += w_mom * .20

    bp = ind["bb_pct"]
    if bp < .15: buy += 1
    elif bp > .85: sell += 1

    # ── Volume
    vr = ind["volume_ratio"]
    if   vr > 2.0: v_sc = w_vol;    buy += 1.5 if buy > sell else 0; sell += 1.5 if sell > buy else 0
    elif vr > 1.5: v_sc = w_vol*.7; buy += 1   if buy > sell else 0; sell += 1   if sell > buy else 0
    elif vr > 1.2: v_sc = w_vol*.4
    else:          v_sc = w_vol*.1

    total = buy + sell
    if total == 0: return None
    if buy > sell and buy >= 7:
        direction = SignalType.BUY; conf = min(94, int((buy/total)*100))
    elif sell > buy and sell >= 7:
        direction = SignalType.SELL; conf = min(94, int((sell/total)*100))
    else:
        return None

    # SMC bonus
    conf = min(96, conf + int(smc.confluence_score * 0.07))
    if conf < min_conf: return None

    # ── Levels
    dir_str = "bullish" if direction == SignalType.BUY else "bearish"
    # Try OB-anchored SL first
    ob_sl = None
    for ob in smc.order_blocks[:2]:
        if ob["type"] == dir_str:
            if direction == SignalType.BUY and ob["bottom"] < price:
                ob_sl = ob["bottom"] * 0.9995; break
            elif direction == SignalType.SELL and ob["top"] > price:
                ob_sl = ob["top"] * 1.0005; break

    if direction == SignalType.BUY:
        sl = ob_sl if ob_sl and abs(price-ob_sl) < atr*atr_sl*2 else price - atr*atr_sl
        tp = price + atr * atr_tp
    else:
        sl = ob_sl if ob_sl and abs(price-ob_sl) < atr*atr_sl*2 else price + atr*atr_sl
        tp = price - atr * atr_tp

    risk = abs(price - sl); reward = abs(tp - price)
    rr   = reward / risk if risk > 0 else 0
    if rr < min_rr: return None

    pip_val = INSTRUMENTS[symbol]["pip"] / 100
    lot = round(min(10, max(0.01, (balance*(risk_pct/100)) / (risk*100*pip_val))), 2)

    h_now = datetime.utcnow().hour
    session = "London 🇬🇧" if 8<=h_now<16 else "New York 🇺🇸" if 13<=h_now<21 else "Asian 🌏"

    entry_pat = detect_entry_pattern(smc.df_entry, dir_str) if smc.df_entry is not None else "—"

    return TradeSignal(
        signal=direction, pair=INSTRUMENTS[symbol]["name"], symbol=symbol,
        entry=price, stop_loss=sl, take_profit=tp, confidence=conf,
        risk_reward=round(rr,2), lot_size=lot, session=session,
        timestamp=datetime.now(), expiry=datetime.now()+timedelta(minutes=hold_mins),
        rsi=rsi, macd_hist=ind["macd_hist"], stoch_k=sk,
        volume_ratio=ind["volume_ratio"], trend=ind["trend"],
        atr=atr, bb_pct=bp, regime=smc.regime.value, adx=smc.adx,
        trend_score=t_sc, momentum_score=m_sc, volume_score=v_sc,
        mtf_score=mtf_sc, smc_score=smc_sc,
        smc_confluence_score=smc.confluence_score,
        key_level_type=smc.key_level,
        daily_bias=smc.daily_bias, h4_bias=smc.h4_bias,
        entry_pattern=entry_pat,
    )

# ================================================================
# PLOTLY CHART
# ================================================================
def build_chart(df: pd.DataFrame, smc: SMCData, sig: Optional[TradeSignal], symbol: str, tf: str) -> go.Figure:
    df_ = df.tail(80).copy().reset_index()
    x = df_.get("Datetime", df_.get("Date", df_.index))
    fig = go.Figure()
    fig.add_trace(go.Candlestick(
        x=x, open=df_["Open"], high=df_["High"], low=df_["Low"], close=df_["Close"],
        name="Price", increasing_line_color="#3fb950", increasing_fillcolor="#1a3a20",
        decreasing_line_color="#f85149", decreasing_fillcolor="#3a1a1a", line_width=1,
    ))
    e20 = df_["Close"].ewm(span=20, adjust=False).mean()
    e50 = df_["Close"].ewm(span=50, adjust=False).mean()
    fig.add_trace(go.Scatter(x=x, y=e20, name="EMA 20", line=dict(color="#58a6ff", width=1.2), opacity=.7))
    fig.add_trace(go.Scatter(x=x, y=e50, name="EMA 50", line=dict(color="#d29922", width=1.2), opacity=.7))
    x0, x1 = x.iloc[0], x.iloc[-1]

    for ob in smc.order_blocks[:3]:
        clr  = "rgba(63,185,80,.11)"  if ob["type"] == "bullish" else "rgba(248,81,73,.11)"
        bclr = "#238636"              if ob["type"] == "bullish" else "#da3633"
        fig.add_hrect(y0=ob["bottom"], y1=ob["top"], x0=x0, x1=x1, fillcolor=clr,
                      line=dict(color=bclr, width=1, dash="dot"),
                      annotation_text=f"{'Bull' if ob['type']=='bullish' else 'Bear'} OB",
                      annotation_font=dict(size=9, color=bclr), annotation_position="top left")
    for fvg in smc.fvgs[:3]:
        clr  = "rgba(88,166,255,.09)"  if fvg["type"] == "bullish" else "rgba(188,140,255,.09)"
        bclr = "#58a6ff"               if fvg["type"] == "bullish" else "#bc8cff"
        fig.add_hrect(y0=fvg["bottom"], y1=fvg["top"], x0=x0, x1=x1, fillcolor=clr,
                      line=dict(color=bclr, width=0.8, dash="dot"),
                      annotation_text=f"{'Bull' if fvg['type']=='bullish' else 'Bear'} FVG",
                      annotation_font=dict(size=9, color=bclr), annotation_position="bottom right")
    for lv in smc.liquidity[:4]:
        clr = "#d29922" if not lv["swept"] else "#8b949e"
        fig.add_hline(y=lv["price"], line=dict(color=clr, width=1, dash="dash"),
                      annotation_text=f"{'Buy' if lv['type']=='buy_side' else 'Sell'} Liq{' ✓' if lv['swept'] else ''}",
                      annotation_font=dict(size=9, color=clr), annotation_position="top right")
    for z in smc.supply_demand[:2]:
        clr = "rgba(63,185,80,.07)" if z["type"] == "demand" else "rgba(248,81,73,.07)"
        bc  = "#3fb950"             if z["type"] == "demand" else "#f85149"
        fig.add_hrect(y0=z["bottom"], y1=z["top"], x0=x0, x1=x1, fillcolor=clr,
                      line=dict(color=bc, width=0.8, dash="longdash"),
                      annotation_text=z["type"].title(),
                      annotation_font=dict(size=9, color=bc), annotation_position="bottom left")
    if sig:
        for lvl, clr, lbl, dash in [
            (sig.entry,     "#e8eaf6", f"Entry {sig.entry:.2f}",    "solid"),
            (sig.stop_loss, "#f85149", f"SL {sig.stop_loss:.2f}",   "dash"),
            (sig.take_profit,"#3fb950",f"TP {sig.take_profit:.2f}", "dash"),
        ]:
            fig.add_hline(y=lvl, line=dict(color=clr, width=1.5, dash=dash),
                          annotation_text=lbl, annotation_font=dict(size=10, color=clr),
                          annotation_position="right")

    fig.update_layout(
        paper_bgcolor="#0a0e1a", plot_bgcolor="#0d1117",
        font=dict(family="Inter", color="#8b949e"),
        xaxis=dict(gridcolor="#1e2d40", rangeslider=dict(visible=False)),
        yaxis=dict(gridcolor="#1e2d40", side="right"),
        legend=dict(bgcolor="#0d1117", bordercolor="#1e2d40", borderwidth=1,
                    font=dict(size=11), orientation="h", yanchor="bottom", y=1.01),
        margin=dict(l=10, r=70, t=35, b=10), height=460,
        title=dict(text=f"{INSTRUMENTS[symbol]['emoji']} {INSTRUMENTS[symbol]['name']} · {tf.upper()} · SMC Analysis",
                   font=dict(size=12, color="#c9d1d9"), x=0),
    )
    return fig

# ================================================================
# TELEGRAM
# ================================================================
def send_telegram(sig: TradeSignal, token: str, chat_id: str) -> bool:
    if not token or not chat_id: return False
    dec  = INSTRUMENTS[sig.symbol]["dec"]
    icon = "🟢⚡" if sig.signal == SignalType.BUY else "🔴⚡"
    strength = "🔥 STRONG" if sig.confidence >= 82 else "⚡ GOOD" if sig.confidence >= 70 else "📊 MODERATE"
    msg = f"""{icon} <b>{sig.signal.value} ALERT — {sig.pair}</b>

<b>{strength} · {sig.confidence}% confidence</b>

💰 <b>Trade Levels</b>
• Entry:        <code>{sig.entry:.{dec}f}</code>
• Stop Loss:    <code>{sig.stop_loss:.{dec}f}</code>
• Take Profit:  <code>{sig.take_profit:.{dec}f}</code>
• Risk/Reward:  1:{sig.risk_reward:.1f}

🏛️ <b>SMC Analysis</b>
• Daily Bias:   {sig.daily_bias.upper()}
• 4H Bias:      {sig.h4_bias.upper()}
• Regime:       {sig.regime}  (ADX {sig.adx:.1f})
• Key Level:    {sig.key_level_type}
• Pattern:      {sig.entry_pattern}
• SMC Score:    {sig.smc_confluence_score:.0f}/100

📊 <b>Confluence</b>
• RSI: {sig.rsi:.1f}  |  MACD: {sig.macd_hist:+.4f}
• Stoch: {sig.stoch_k:.1f}  |  Vol: {sig.volume_ratio:.1f}x

📋 <b>Position</b>
• Lot: {sig.lot_size:.2f}  |  {sig.session}
• Expires: {sig.expiry.strftime('%H:%M UTC')}

<i>⚠️ Alert only — review chart before entering</i>"""
    try:
        r = requests.post(f"https://api.telegram.org/bot{token}/sendMessage",
                          json={"chat_id": chat_id, "text": msg, "parse_mode": "HTML",
                                "disable_web_page_preview": True}, timeout=10)
        return r.status_code == 200
    except Exception as e:
        logger.error(f"Telegram: {e}")
        return False

# ================================================================
# UI HELPERS
# ================================================================
def badge(text: str, c: str = "gy") -> str:
    return f'<span class="badge b{c}">{text}</span>'

def sbar(label: str, score: float, max_w: float, clr: str) -> str:
    pct = min(100, int(score / max(max_w, 1) * 100))
    return f"""<div class="sbar-wrap">
<div class="sbar-row"><span>{label}</span><span style="color:#8b949e;">{int(score)}/{int(max_w)}</span></div>
<div class="sbar-bg"><div class="sbar-fill" style="width:{pct}%;background:{clr};"></div></div>
</div>"""

def bias_pill(label: str, bias: str) -> str:
    cls = {"bullish":"bull","bearish":"bear"}.get(bias, "neut")
    ic  = "🟢" if bias == "bullish" else "🔴" if bias == "bearish" else "⚪"
    return f'<span class="bias-pill {cls}">{ic} {label}: {bias.upper()}</span>'

def smc_meter(smc: SMCData) -> str:
    bars = [
        ("Struct", smc.structure_score, "#3fb950"),
        ("OB",     smc.ob_score,        "#58a6ff"),
        ("FVG",    smc.fvg_score,       "#bc8cff"),
        ("Liq",    smc.liq_score,       "#d29922"),
        ("Conf",   smc.confluence_score,"#f0883e"),
    ]
    items = ""
    for lbl, sc, clr in bars:
        h = max(4, int(sc * 0.55))
        items += f"""<div class="smc-bw">
  <div class="smc-bl">{lbl}</div>
  <div class="smc-bo" style="height:55px;">
    <div class="smc-bi" style="height:{h}px;background:{clr};"></div>
  </div>
  <div style="font-size:9.5px;color:{clr};margin-top:3px;font-weight:600;">{int(sc)}</div>
</div>"""
    return f'<div class="smc-meter">{items}</div>'

def regime_html(regime: MarketRegime, adx: float) -> str:
    cls  = {"TRENDING":"regime-trend","RANGING":"regime-range","VOLATILE":"regime-vol"}.get(regime.value,"regime-range")
    icon = {"TRENDING":"📈","RANGING":"↔️","VOLATILE":"⚡"}.get(regime.value,"—")
    return f'<span class="regime-tag {cls}">{icon} {regime.value} (ADX {adx:.1f})</span>'

# ================================================================
# SESSION STATE
# ================================================================
for k, v in [("history",[]),("last_result",None),("last_smc",None),
              ("auto_on",False),("auto_interval",120),
              ("next_run",None),("total_sent",0),("last_tg",None)]:
    if k not in st.session_state:
        st.session_state[k] = v

# ================================================================
# SIDEBAR
# ================================================================
with st.sidebar:
    st.markdown("## 🥇 ScalpBot Pro")
    st.markdown('<p style="color:#8b949e;font-size:.78rem;margin-top:-8px;">SMC/ICT Alert Dashboard</p>', unsafe_allow_html=True)
    st.markdown("---")

    st.markdown('<p style="font-size:.72rem;font-weight:600;text-transform:uppercase;letter-spacing:.05em;color:#8b949e;">Instrument & Timeframe</p>', unsafe_allow_html=True)
    symbol    = st.selectbox("Pair", list(INSTRUMENTS.keys()),
                             format_func=lambda x: f"{INSTRUMENTS[x]['emoji']}  {INSTRUMENTS[x]['name']}")
    timeframe = st.selectbox("Timeframe", ["1h","30m","15m","5m"])
    period_map = {"1h":"5d","30m":"3d","15m":"2d","5m":"1d"}

    st.markdown("---")
    st.markdown('<p style="font-size:.72rem;font-weight:600;text-transform:uppercase;letter-spacing:.05em;color:#8b949e;">Risk Management</p>', unsafe_allow_html=True)
    balance  = st.number_input("Account Balance ($)", 10.0, 1_000_000.0, 100.0, 10.0)
    risk_pct = st.slider("Risk per Trade (%)", 0.1, 5.0, 0.5, 0.1)
    min_conf = st.slider("Min Confidence (%)", 50, 92, 68, 1)
    min_rr   = st.slider("Min Risk/Reward", 1.0, 5.0, 2.5, 0.1)
    atr_sl   = st.slider("ATR SL ×", 0.5, 3.0, 1.0, 0.1)
    atr_tp   = st.slider("ATR TP ×", 0.5, 6.0, 2.5, 0.1)
    hold_mins= st.slider("Signal Expiry (min)", 5, 240, 60, 5)

    st.markdown("---")
    st.markdown('<p style="font-size:.72rem;font-weight:600;text-transform:uppercase;letter-spacing:.05em;color:#8b949e;">Signal Weights</p>', unsafe_allow_html=True)
    w_trend = st.slider("Trend/Structure", 0, 30, 20, 5)
    w_mom   = st.slider("Momentum", 0, 30, 20, 5)
    w_vol   = st.slider("Volume", 0, 20, 15, 5)
    w_mtf   = st.slider("Multi-TF Bias", 0, 30, 20, 5)
    w_smc   = st.slider("SMC Confluence", 0, 40, 30, 5)

    st.markdown("---")
    st.markdown('<p style="font-size:.72rem;font-weight:600;text-transform:uppercase;letter-spacing:.05em;color:#8b949e;">Telegram Alerts</p>', unsafe_allow_html=True)
    tg_token   = st.text_input("Bot Token",  type="password", placeholder="123456:ABC-xxx")
    tg_chat_id = st.text_input("Chat ID",    placeholder="Your chat ID")
    if st.button("🔔 Test Telegram", use_container_width=True):
        if tg_token and tg_chat_id:
            try:
                r = requests.post(f"https://api.telegram.org/bot{tg_token}/sendMessage",
                    json={"chat_id":tg_chat_id,"text":"✅ ScalpBot Pro connected! Alerts ready."},timeout=10)
                st.success("✅ Connected!") if r.ok else st.error("❌ " + r.json().get("description","Failed"))
            except: st.error("❌ Network error")
        else: st.warning("Enter token & chat ID first")

    st.markdown("---")
    st.markdown('<p style="font-size:.72rem;font-weight:600;text-transform:uppercase;letter-spacing:.05em;color:#8b949e;">Auto-Send Interval</p>', unsafe_allow_html=True)
    auto_iv = st.select_slider("", options=[60,120,300,600,900],
                                value=st.session_state.auto_interval,
                                format_func=lambda x: f"{x//60} min")
    st.session_state.auto_interval = auto_iv

# ================================================================
# HERO
# ================================================================
pair_info = INSTRUMENTS[symbol]
h_now = datetime.utcnow().hour
sess_now = "London 🇬🇧" if 8<=h_now<16 else "New York 🇺🇸" if 13<=h_now<21 else "Asian 🌏"
st.markdown(f"""
<div class="hero">
  <h1>🥇 ScalpBot Pro <span style="color:#3fb950;">v4</span></h1>
  <p>SMC/ICT Alert Dashboard &nbsp;·&nbsp; {pair_info['emoji']} {pair_info['name']}
     &nbsp;·&nbsp; {timeframe.upper()} &nbsp;·&nbsp; {sess_now}
     &nbsp;·&nbsp; {datetime.utcnow().strftime('%H:%M UTC')}</p>
</div>
""", unsafe_allow_html=True)

# ================================================================
# AUTO-SEND PANEL
# ================================================================
ac1, ac2 = st.columns([4, 1])
with ac1:
    pcls  = "auto-panel active" if st.session_state.auto_on else "auto-panel"
    albl  = "🟢 AUTO-ALERTS ON" if st.session_state.auto_on else "⚫ AUTO-ALERTS OFF"
    if st.session_state.auto_on and st.session_state.next_run:
        sl = max(0, int((st.session_state.next_run - datetime.now()).total_seconds()))
        m_, s_ = divmod(sl, 60)
        cd_html = f'<span class="countdown">{m_:02d}:{s_:02d}</span> <span style="color:#8b949e;font-size:.8rem;">until next scan</span>'
    else:
        cd_html = '<span style="color:#8b949e;font-size:.85rem;">Toggle to auto-scan and alert</span>'
    st.markdown(f"""
<div class="{pcls}">
  <div style="display:flex;justify-content:space-between;align-items:center;">
    <div>
      <div style="font-weight:700;font-size:.93rem;color:{'#3fb950' if st.session_state.auto_on else '#8b949e'};">{albl}</div>
      <div style="margin-top:.25rem;">{cd_html}</div>
    </div>
    <div style="text-align:right;font-size:11px;color:#8b949e;">
      Every {auto_iv//60}m &nbsp;|&nbsp; Sent: {st.session_state.total_sent}
    </div>
  </div>
</div>""", unsafe_allow_html=True)
with ac2:
    st.write(""); st.write("")
    if st.button("⏹ Stop" if st.session_state.auto_on else "▶ Start Auto", use_container_width=True):
        st.session_state.auto_on = not st.session_state.auto_on
        st.session_state.next_run = datetime.now() if st.session_state.auto_on else None
        st.rerun()

# ================================================================
# ANALYZE BUTTON
# ================================================================
b1, b2, _ = st.columns([3, 1, 2])
with b1:
    manual_run = st.button("🚀 Analyze Market & Generate Alert", use_container_width=True, type="primary")
with b2:
    if st.button("🗑️ Clear", use_container_width=True):
        st.session_state.update({"history":[],"last_result":None,"last_smc":None,"total_sent":0})
        st.rerun()

# ================================================================
# TRIGGER
# ================================================================
should_run = manual_run
if (st.session_state.auto_on and st.session_state.next_run and
        datetime.now() >= st.session_state.next_run):
    should_run = True
    st.session_state.next_run = datetime.now() + timedelta(seconds=st.session_state.auto_interval)

# ================================================================
# RUN
# ================================================================
if should_run:
    with st.spinner("Running full SMC top-down analysis..."):
        fetch.clear()
        run_smc_analysis.clear()
        smc_res = run_smc_analysis(symbol, timeframe, period_map)
        df_e    = fetch(symbol, period_map[timeframe], timeframe)
        ind_    = compute_indicators(df_e) if df_e is not None else None

    if ind_ is None:
        st.error("⚠️ Could not fetch market data.")
    else:
        sig_ = generate_signal(symbol, ind_, smc_res, balance, risk_pct, min_conf, min_rr,
                                atr_sl, atr_tp, hold_mins, w_trend, w_mom, w_vol, w_mtf, w_smc)
        st.session_state.last_result = (sig_, ind_, smc_res)
        st.session_state.last_smc    = smc_res
        if sig_:
            st.session_state.history.insert(0, sig_)
            if len(st.session_state.history) > 30:
                st.session_state.history = st.session_state.history[:30]
            ok = send_telegram(sig_, tg_token, tg_chat_id)
            st.session_state.last_tg = ("✅ Alert sent to Telegram!" if ok
                                        else ("⚠️ No Telegram configured" if not tg_token else "❌ Telegram failed"))
            st.session_state.total_sent += 1
        else:
            st.session_state.last_tg = None

# ================================================================
# DISPLAY
# ================================================================
if st.session_state.last_result:
    sig, ind, smc = st.session_state.last_result
    dec = INSTRUMENTS[symbol]["dec"]
    pair_info = INSTRUMENTS[symbol]

    if st.session_state.last_tg:
        cls = "toast-ok" if "✅" in st.session_state.last_tg else "toast-err"
        st.markdown(f'<div class="{cls}">{st.session_state.last_tg}</div>', unsafe_allow_html=True)

    # ── TABS ────────────────────────────────────────────────────
    t1, t2, t3, t4 = st.tabs(["📊 Signal", "🏛️ SMC Analysis", "📈 Chart", "📋 History"])

    # ──────────────────────────────────────────────────────────
    # TAB 1 — SIGNAL
    # ──────────────────────────────────────────────────────────
    with t1:
        st.markdown('<p class="stitle" style="margin-top:.6rem;">Snapshot</p>', unsafe_allow_html=True)
        # Regime badge
        st.markdown(regime_html(smc.regime, smc.adx), unsafe_allow_html=True)

        m1,m2,m3,m4,m5,m6 = st.columns(6)
        m1.metric("Price",    f"{ind['price']:.{dec}f}")
        m2.metric("RSI (14)", f"{ind['rsi']:.1f}",
                  delta="Oversold" if ind['rsi']<30 else "Overbought" if ind['rsi']>70 else None)
        m3.metric("MACD",     f"{ind['macd_hist']:+.4f}",
                  delta="Bull" if ind['macd_hist']>0 else "Bear")
        m4.metric("ADX",      f"{ind['adx']:.1f}",
                  delta="Trending" if ind['adx']>=25 else "Ranging")
        m5.metric("Stoch %K", f"{ind['stoch_k']:.1f}")
        m6.metric("Vol Ratio",f"{ind['volume_ratio']:.2f}x",
                  delta="Spike!" if ind['volume_ratio']>1.5 else None)

        # Signal card
        if sig:
            is_buy  = sig.signal == SignalType.BUY
            cv      = "#3fb950" if is_buy else "#f85149"
            css_    = "signal-buy" if is_buy else "signal-sell"
            glow_   = "glow-buy"  if is_buy else "glow-sell"
            icon_   = "🟢 BUY"   if is_buy else "🔴 SELL"
            cc_     = "#3fb950" if sig.confidence>=75 else "#d29922" if sig.confidence>=60 else "#f85149"
            str_    = "🔥 Strong" if sig.confidence>=82 else "⚡ Good" if sig.confidence>=70 else "📊 Moderate"
            st.markdown(f"""
<div class="signal-card {css_}">
  <div class="{glow_}"></div>
  <div class="sig-title" style="color:{cv};">{icon_}</div>
  <div class="sig-sub">{pair_info['emoji']} {pair_info['name']} · {timeframe.upper()}
    · <span style="color:{cc_};font-weight:600;">{sig.confidence}% conf</span>
    · {str_} · {sig.session}</div>
  <div class="sig-grid">
    <div class="sig-item"><div class="label">Entry</div><div class="value">{sig.entry:.{dec}f}</div></div>
    <div class="sig-item"><div class="label">Stop Loss</div><div class="value red">{sig.stop_loss:.{dec}f}</div></div>
    <div class="sig-item"><div class="label">Take Profit</div><div class="value green">{sig.take_profit:.{dec}f}</div></div>
    <div class="sig-item"><div class="label">Risk/Reward</div><div class="value">1:{sig.risk_reward}</div></div>
    <div class="sig-item"><div class="label">Lot Size</div><div class="value">{sig.lot_size}</div></div>
    <div class="sig-item"><div class="label">Expires</div><div class="value">{sig.expiry.strftime('%H:%M UTC')}</div></div>
    <div class="sig-item"><div class="label">Daily Bias</div><div class="value {'green' if sig.daily_bias=='bullish' else 'red' if sig.daily_bias=='bearish' else ''}">{sig.daily_bias.upper()}</div></div>
    <div class="sig-item"><div class="label">4H Bias</div><div class="value {'green' if sig.h4_bias=='bullish' else 'red' if sig.h4_bias=='bearish' else ''}">{sig.h4_bias.upper()}</div></div>
    <div class="sig-item"><div class="label">Pattern</div><div class="value gold">{sig.entry_pattern}</div></div>
  </div>
</div>""", unsafe_allow_html=True)
        else:
            st.markdown("""
<div class="signal-card signal-hold">
  <div class="sig-title" style="color:#8b949e;">⚖️ HOLD — No Signal</div>
  <div class="sig-sub">No high-probability setup found right now.
  HTF bias may conflict, or regime is unfavorable. Wait for price to reach a key SMC level.</div>
</div>""", unsafe_allow_html=True)

        # Indicators + scores
        ca, cb = st.columns(2)
        with ca:
            st.markdown('<p class="stitle">Indicators</p>', unsafe_allow_html=True)
            rows_ = [
                ("RSI (14)",      f"{ind['rsi']:.1f}",           "g" if ind['rsi']<40 else "r" if ind['rsi']>60 else "gy"),
                ("MACD Histogram",f"{ind['macd_hist']:+.5f}",    "g" if ind['macd_hist']>0 else "r"),
                ("Stochastic %K", f"{ind['stoch_k']:.1f}",       "g" if ind['stoch_k']<30 else "r" if ind['stoch_k']>70 else "gy"),
                ("Bollinger %B",  f"{ind['bb_pct']*100:.1f}%",   "g" if ind['bb_pct']<.2 else "r" if ind['bb_pct']>.8 else "gy"),
                ("ATR (14)",      f"{ind['atr']:.{dec}f}",       "gy"),
                ("EMA 20",        f"{ind['ema20']:.{dec}f}",     "gy"),
                ("ADX",           f"{ind['adx']:.1f}",           "g" if ind['adx']>=25 else "y"),
                ("Volume Ratio",  f"{ind['volume_ratio']:.2f}x", "g" if ind['volume_ratio']>1.5 else "gy"),
                ("Daily Bias",    smc.daily_bias.title(),        "g" if smc.daily_bias=="bullish" else "r" if smc.daily_bias=="bearish" else "gy"),
                ("4H Bias",       smc.h4_bias.title(),           "g" if smc.h4_bias=="bullish" else "r" if smc.h4_bias=="bearish" else "gy"),
                ("1H Bias",       smc.h1_bias.title(),           "g" if smc.h1_bias=="bullish" else "r" if smc.h1_bias=="bearish" else "gy"),
            ]
            html_ = ""
            for n_, v_, c_ in rows_:
                html_ += f'<div class="ind-row"><span class="ind-label">{n_}</span>{badge(v_,c_)}</div>'
            st.markdown(html_, unsafe_allow_html=True)

        with cb:
            st.markdown('<p class="stitle">Score Breakdown</p>', unsafe_allow_html=True)
            if sig:
                bh = ""
                bh += sbar("Trend / Structure",       sig.trend_score,    w_trend,     "#3fb950")
                bh += sbar("Momentum (RSI+MACD+Stoch)",sig.momentum_score,w_mom*1.3,   "#58a6ff")
                bh += sbar("Volume",                   sig.volume_score,   w_vol,       "#d29922")
                bh += sbar("Multi-TF Bias",            sig.mtf_score,      w_mtf,       "#bc8cff")
                bh += sbar("SMC Confluence",           sig.smc_score,      w_smc,       "#f0883e")
                conf_clr = "#3fb950" if sig.confidence>=75 else "#d29922" if sig.confidence>=60 else "#f85149"
                bh += f"""
<div style="background:#0d1117;border:1px solid #1e2d40;border-radius:10px;padding:.85rem;margin-top:.7rem;">
  <div style="display:flex;justify-content:space-between;font-weight:600;margin-bottom:6px;font-size:.85rem;">
    <span>Overall Confidence</span><span style="color:{conf_clr};">{sig.confidence}%</span>
  </div>
  <div style="background:#1e2d40;border-radius:5px;height:9px;">
    <div style="width:{sig.confidence}%;background:{conf_clr};height:9px;border-radius:5px;"></div>
  </div>
</div>"""
                st.markdown(bh, unsafe_allow_html=True)
            else:
                st.markdown('<p style="color:#8b949e;font-size:.85rem;">Run analysis to see scores.</p>', unsafe_allow_html=True)
            st.markdown('<p class="stitle" style="margin-top:.9rem;">SMC Strength Meter</p>', unsafe_allow_html=True)
            st.markdown(smc_meter(smc), unsafe_allow_html=True)

    # ──────────────────────────────────────────────────────────
    # TAB 2 — SMC ANALYSIS
    # ──────────────────────────────────────────────────────────
    with t2:
        st.markdown('<p class="stitle" style="margin-top:.5rem;">Top-Down Bias</p>', unsafe_allow_html=True)
        brow = '<div class="bias-row">'
        for lbl_, b_ in [("Daily",smc.daily_bias),("4H",smc.h4_bias),
                          ("1H",smc.h1_bias),(f"{timeframe.upper()} Entry",smc.entry_bias)]:
            brow += bias_pill(lbl_, b_)
        brow += '</div>'
        st.markdown(brow, unsafe_allow_html=True)

        sc1_, sc2_ = st.columns(2)
        with sc1_:
            st.markdown('<p class="stitle">Market Structure</p>', unsafe_allow_html=True)
            if smc.bos:
                dc_ = "g" if smc.struct_dir=="bullish" else "r"
                st.markdown(f'{badge("BOS",dc_)} &nbsp; {badge(smc.struct_dir.upper(),dc_)}', unsafe_allow_html=True)
            if smc.choch:
                dc_ = "g" if smc.struct_dir=="bullish" else "r"
                st.markdown(f'{badge("CHOCH","o")} &nbsp; {badge(smc.struct_dir.upper(),dc_)}', unsafe_allow_html=True)
            if not smc.bos and not smc.choch:
                st.markdown(f'{badge("No BOS/CHOCH","gy")}', unsafe_allow_html=True)
        with sc2_:
            st.markdown('<p class="stitle">Key Confluence</p>', unsafe_allow_html=True)
            kl_ = smc.key_level
            if kl_ and kl_ not in ("None","Price not at key SMC level"):
                for p_ in kl_.split(" + "):
                    st.markdown(f'<div style="font-size:12.5px;color:#d29922;margin-bottom:3px;">{p_}</div>', unsafe_allow_html=True)
            else:
                st.markdown('<p style="color:#8b949e;font-size:.83rem;">Price not at a key level right now.</p>', unsafe_allow_html=True)

        st.markdown("---")
        lc1_, lc2_ = st.columns(2)
        with lc1_:
            st.markdown('<p class="stitle">Order Blocks</p>', unsafe_allow_html=True)
            if smc.order_blocks:
                for ob_ in smc.order_blocks[:4]:
                    ic_ = "🟢" if ob_["type"]=="bullish" else "🔴"
                    css_ = "ob-b" if ob_["type"]=="bullish" else "ob-s"
                    st.markdown(f"""
<div class="smc-card {css_}">
  <div style="display:flex;justify-content:space-between;margin-bottom:2px;">
    <b style="font-size:12.5px;">{ic_} {'Bullish' if ob_['type']=='bullish' else 'Bearish'} OB</b>
    {badge(f"Str:{ob_['strength']:.0%}", 'g' if ob_['strength']>0.6 else 'y')}
  </div>
  <div style="color:#8b949e;">Top:{ob_['top']:.{dec}f} · Bot:{ob_['bottom']:.{dec}f} · Mid:{ob_['mid']:.{dec}f}</div>
</div>""", unsafe_allow_html=True)
            else:
                st.markdown('<p style="color:#8b949e;font-size:.83rem;">No fresh OBs.</p>', unsafe_allow_html=True)

            st.markdown('<p class="stitle" style="margin-top:.7rem;">Supply & Demand</p>', unsafe_allow_html=True)
            if smc.supply_demand:
                for z_ in smc.supply_demand[:3]:
                    ic_ = "📗" if z_["type"]=="demand" else "📕"
                    css_ = "sd-d" if z_["type"]=="demand" else "sd-s"
                    st.markdown(f"""
<div class="smc-card {css_}">
  <b style="font-size:12.5px;">{ic_} {z_['type'].title()} Zone</b>
  <div style="color:#8b949e;margin-top:2px;">Top:{z_['top']:.{dec}f} · Bot:{z_['bottom']:.{dec}f}</div>
</div>""", unsafe_allow_html=True)
            else:
                st.markdown('<p style="color:#8b949e;font-size:.83rem;">No zones.</p>', unsafe_allow_html=True)

        with lc2_:
            st.markdown('<p class="stitle">Fair Value Gaps</p>', unsafe_allow_html=True)
            if smc.fvgs:
                for fv_ in smc.fvgs[:4]:
                    ic_ = "🔵" if fv_["type"]=="bullish" else "🟣"
                    css_ = "fvg-b" if fv_["type"]=="bullish" else "fvg-s"
                    st.markdown(f"""
<div class="smc-card {css_}">
  <div style="display:flex;justify-content:space-between;margin-bottom:2px;">
    <b style="font-size:12.5px;">{ic_} {'Bull' if fv_['type']=='bullish' else 'Bear'} FVG</b>
    {badge("Unfilled","b")}
  </div>
  <div style="color:#8b949e;">Top:{fv_['top']:.{dec}f} · Bot:{fv_['bottom']:.{dec}f} · Mid:{fv_['mid']:.{dec}f}</div>
</div>""", unsafe_allow_html=True)
            else:
                st.markdown('<p style="color:#8b949e;font-size:.83rem;">No unfilled FVGs.</p>', unsafe_allow_html=True)

            st.markdown('<p class="stitle" style="margin-top:.7rem;">Liquidity Levels</p>', unsafe_allow_html=True)
            if smc.liquidity:
                for lv_ in smc.liquidity[:5]:
                    ic_ = "⬆️" if lv_["type"]=="buy_side" else "⬇️"
                    swb = badge("Swept ✓","o") if lv_["swept"] else badge("Unswept","gy")
                    st.markdown(f"""
<div class="smc-card liq">
  <div style="display:flex;justify-content:space-between;margin-bottom:2px;">
    <b style="font-size:12.5px;">{ic_} {'Buy-Side' if lv_['type']=='buy_side' else 'Sell-Side'} Liq</b>
    {swb}
  </div>
  <div style="color:#8b949e;">Price:{lv_['price']:.{dec}f} · Strength:{lv_['strength']:.0%}</div>
</div>""", unsafe_allow_html=True)
            else:
                st.markdown('<p style="color:#8b949e;font-size:.83rem;">No liquidity levels.</p>', unsafe_allow_html=True)

    # ──────────────────────────────────────────────────────────
    # TAB 3 — CHART
    # ──────────────────────────────────────────────────────────
    with t3:
        df_chart = fetch(symbol, period_map[timeframe], timeframe)
        if df_chart is not None and len(df_chart) >= 10:
            st.plotly_chart(build_chart(df_chart, smc, sig, symbol, timeframe),
                            use_container_width=True, config={"displayModeBar":True})
        else:
            st.warning("Not enough chart data.")
        st.markdown("""
<div style="display:flex;flex-wrap:wrap;gap:12px;font-size:11px;color:#8b949e;margin-top:.4rem;">
  <span><span style="color:#238636;">■</span> Bull OB</span>
  <span><span style="color:#da3633;">■</span> Bear OB</span>
  <span><span style="color:#58a6ff;">■</span> Bull FVG</span>
  <span><span style="color:#bc8cff;">■</span> Bear FVG</span>
  <span><span style="color:#d29922;">—</span> Liquidity</span>
  <span><span style="color:#3fb950;">—</span> Demand</span>
  <span><span style="color:#f85149;">—</span> Supply</span>
  <span><span style="color:#e8eaf6;">—</span> Entry</span>
  <span><span style="color:#f85149;">- -</span> SL</span>
  <span><span style="color:#3fb950;">- -</span> TP</span>
</div>""", unsafe_allow_html=True)

    # ──────────────────────────────────────────────────────────
    # TAB 4 — HISTORY
    # ──────────────────────────────────────────────────────────
    with t4:
        if st.session_state.history:
            buys_  = sum(1 for s in st.session_state.history if s.signal==SignalType.BUY)
            sells_ = sum(1 for s in st.session_state.history if s.signal==SignalType.SELL)
            avg_c_ = int(np.mean([s.confidence for s in st.session_state.history]))
            avg_r_ = round(np.mean([s.risk_reward for s in st.session_state.history]),2)
            avg_smc_ = round(np.mean([s.smc_confluence_score for s in st.session_state.history]),1)

            hc1,hc2,hc3,hc4,hc5 = st.columns(5)
            def sc_(col,v,l,color="#e8eaf6"):
                col.markdown(f'<div class="stat-card"><div class="stat-v" style="color:{color};">{v}</div><div class="stat-l">{l}</div></div>', unsafe_allow_html=True)
            sc_(hc1,len(st.session_state.history),"Total")
            sc_(hc2,buys_,"Buys","#3fb950")
            sc_(hc3,sells_,"Sells","#f85149")
            sc_(hc4,f"{avg_c_}%","Avg Conf")
            sc_(hc5,f"{avg_smc_}","Avg SMC")

            st.markdown("")
            st.markdown('<div class="hist-hdr"><span>Time</span><span>Pair</span><span>Type</span><span>Conf</span><span>Entry</span><span>TP</span><span>R/R</span></div>', unsafe_allow_html=True)
            rh_ = ""
            for s_ in st.session_state.history[:20]:
                ib_ = s_.signal == SignalType.BUY
                d_  = INSTRUMENTS.get(s_.symbol,{}).get("dec",5)
                rh_ += f"""
<div class="hist-row {'hist-buy' if ib_ else 'hist-sell'}">
  <span style="color:#8b949e;">{s_.timestamp.strftime('%H:%M:%S')}</span>
  <span style="font-weight:600;">{INSTRUMENTS.get(s_.symbol,{}).get('emoji','')}{s_.pair.split('·')[0].strip()}</span>
  <span>{badge('BUY','g') if ib_ else badge('SELL','r')}</span>
  <span>{badge(f"{s_.confidence}%",'g' if s_.confidence>=75 else 'y' if s_.confidence>=65 else 'r')}</span>
  <span>{s_.entry:.{d_}f}</span>
  <span style="color:#3fb950;">{s_.take_profit:.{d_}f}</span>
  <span>1:{s_.risk_reward}</span>
</div>"""
            st.markdown(rh_, unsafe_allow_html=True)
        else:
            st.markdown('<p style="color:#8b949e;font-size:.88rem;margin-top:.8rem;">No alerts generated yet.</p>', unsafe_allow_html=True)

# ================================================================
# FOOTER
# ================================================================
st.markdown("---")
st.markdown("""
<div style="text-align:center;color:#8b949e;font-size:11px;padding:.3rem 0 .6rem;">
  ⚠️ <b>For educational use only.</b> Not financial advice. Always manage risk.
  <br>ScalpBot Pro · SMC: OB · FVG · BOS/CHOCH · Liquidity · Supply/Demand · Regime Detection · Top-Down Bias
</div>""", unsafe_allow_html=True)

# ================================================================
# AUTO-REFRESH LOOP
# ================================================================
if st.session_state.auto_on and st.session_state.next_run:
    remaining = (st.session_state.next_run - datetime.now()).total_seconds()
    if remaining > 0:
        time.sleep(min(remaining, 8))
        st.rerun()
