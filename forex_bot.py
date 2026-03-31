"""
Professional Forex Trading Bot
Optimized for small accounts ($20-$100)
Features: Signal filtering, risk management, session control, trade expiry
"""

import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import time
import json
import requests
from typing import Dict, List, Optional, Tuple
import logging
from dataclasses import dataclass
from enum import Enum

# ============================================
# CONFIGURATION
# ============================================

# Telegram Configuration
TELEGRAM_TOKEN = "8773664334:AAE4fd4Wpyd2ZQkWBsjlPby7qSGKp00jGng"
TELEGRAM_CHAT_ID = "2057396237"

# Gold Bot (Separate)
GOLD_BOT_TOKEN = "8686418191:AAHtEBJ9Lyehb3geZS1WwWukmYZatqpAe-A"
GOLD_BOT_CHAT_ID = "2057396237"

# Trading Parameters
ACCOUNT_BALANCE = 100  # $100 account (adjust as needed)
RISK_PER_TRADE = 1.5  # 1.5% risk per trade
MAX_TRADES_PER_SESSION = 5  # Maximum trades per trading session
MIN_CONFIDENCE = 70  # Minimum 70% confidence
MIN_RISK_REWARD = 2.0  # Minimum 1:2 risk-reward
MAX_HOLD_HOURS = 2  # Signal expires after 2 hours

# Session Times (UTC)
LONDON_SESSION = (8, 16)  # 8 AM - 4 PM UTC
NEW_YORK_SESSION = (13, 21)  # 1 PM - 9 PM UTC

# Indicators Settings
ADX_THRESHOLD = 25  # ADX < 25 for ranging market
RSI_BUY_THRESHOLD = 35  # RSI < 35 for BUY
RSI_SELL_THRESHOLD = 65  # RSI > 65 for SELL

# ============================================
# DATA CLASSES
# ============================================

class SignalType(Enum):
    BUY = "BUY"
    SELL = "SELL"
    NEUTRAL = "NEUTRAL"

@dataclass
class TradeSignal:
    """Structured trade signal data"""
    pair: str
    signal: SignalType
    entry: float
    stop_loss: float
    take_profit: float
    confidence: int
    rsi: float
    adx: float
    session: str
    risk_reward: float
    timestamp: datetime
    expiry: datetime
    lot_size: float
    
    def to_dict(self) -> dict:
        return {
            'pair': self.pair,
            'signal': self.signal.value,
            'entry': self.entry,
            'stop_loss': self.stop_loss,
            'take_profit': self.take_profit,
            'confidence': self.confidence,
            'rsi': self.rsi,
            'adx': self.adx,
            'session': self.session,
            'risk_reward': self.risk_reward,
            'timestamp': self.timestamp,
            'expiry': self.expiry,
            'lot_size': self.lot_size
        }

@dataclass
class TradeRecord:
    """Record of executed trade"""
    signal: TradeSignal
    status: str = "pending"
    entry_time: datetime = None
    exit_time: datetime = None
    profit_loss: float = 0

# ============================================
# LOW VOLATILITY PAIRS
# ============================================

LOW_VOLATILITY_PAIRS = {
    # Major Stable Pairs
    'EURUSD=X': {'name': 'EUR/USD', 'type': 'Forex', 'decimals': 5, 'min_lot': 0.01, 'pip_value': 0.1},
    'GBPUSD=X': {'name': 'GBP/USD', 'type': 'Forex', 'decimals': 5, 'min_lot': 0.01, 'pip_value': 0.1},
    'USDCHF=X': {'name': 'USD/CHF', 'type': 'Forex', 'decimals': 5, 'min_lot': 0.01, 'pip_value': 0.1},
    'AUDUSD=X': {'name': 'AUD/USD', 'type': 'Forex', 'decimals': 5, 'min_lot': 0.01, 'pip_value': 0.1},
    
    # Cross Pairs (Lower Volatility)
    'EURGBP=X': {'name': 'EUR/GBP', 'type': 'Forex', 'decimals': 5, 'min_lot': 0.01, 'pip_value': 0.1},
    'AUDNZD=X': {'name': 'AUD/NZD', 'type': 'Forex', 'decimals': 5, 'min_lot': 0.01, 'pip_value': 0.1},
    
    # Indices (Moderate)
    '^DJI': {'name': 'US30', 'type': 'Index', 'decimals': 2, 'min_lot': 0.01, 'pip_value': 0.1},
    '^NDX': {'name': 'US100', 'type': 'Index', 'decimals': 2, 'min_lot': 0.01, 'pip_value': 0.1},
    
    # Gold (For main bot - slower signals)
    'GC=F': {'name': 'Gold', 'type': 'Commodity', 'decimals': 2, 'min_lot': 0.01, 'pip_value': 0.1},
}

# ============================================
# LOGGING SETUP
# ============================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('trading_bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ============================================
# TELEGRAM FUNCTIONS
# ============================================

def send_telegram_message(token: str, chat_id: str, message: str, parse_mode: str = 'HTML') -> bool:
    """Send message to Telegram with retry mechanism"""
    max_retries = 3
    for attempt in range(max_retries):
        try:
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            payload = {
                'chat_id': chat_id,
                'text': message,
                'parse_mode': parse_mode,
                'disable_web_page_preview': True
            }
            response = requests.post(url, json=payload, timeout=10)
            if response.status_code == 200:
                return True
            else:
                logger.warning(f"Telegram attempt {attempt + 1} failed: {response.text}")
        except Exception as e:
            logger.error(f"Telegram error on attempt {attempt + 1}: {e}")
        
        if attempt < max_retries - 1:
            time.sleep(2 ** attempt)  # Exponential backoff
    
    return False

def format_trade_signal(signal: TradeSignal) -> str:
    """Format trade signal for Telegram message"""
    
    # Emoji based on signal
    if signal.signal == SignalType.BUY:
        emoji = "🟢"
        action = "BUY"
        direction = "▲"
    else:
        emoji = "🔴"
        action = "SELL"
        direction = "▼"
    
    # RSI condition text
    if signal.rsi < 30:
        rsi_condition = "Oversold"
    elif signal.rsi > 70:
        rsi_condition = "Overbought"
    else:
        rsi_condition = "Neutral"
    
    # Format price based on pair type
    if signal.pair in ['US30', 'US100']:
        entry_str = f"{signal.entry:,.2f}"
        sl_str = f"{signal.stop_loss:,.2f}"
        tp_str = f"{signal.take_profit:,.2f}"
    else:
        entry_str = f"{signal.entry:.5f}"
        sl_str = f"{signal.stop_loss:.5f}"
        tp_str = f"{signal.take_profit:.5f}"
    
    message = f"""
{emoji} <b>{action} {signal.pair}</b>

<b>📊 Trade Plan:</b>
• Entry: {entry_str}
• Stop Loss: {sl_str}
• Take Profit: {tp_str}
• Risk/Reward: 1:{signal.risk_reward:.1f}

<b>📈 Technicals:</b>
• Confidence: {signal.confidence}%
• RSI: {signal.rsi:.1f} ({rsi_condition})
• ADX: {signal.adx:.1f} (Ranging)

<b>📋 Risk Management:</b>
• Position Size: {signal.lot_size:.2f} lots
• Account Risk: {RISK_PER_TRADE}% (${ACCOUNT_BALANCE * RISK_PER_TRADE / 100:.2f})

<b>⏰ Timing:</b>
• Session: {signal.session}
• Valid Until: {signal.expiry.strftime('%H:%M')} UTC ({MAX_HOLD_HOURS} hours)

<i>⚠️ Educational purposes only. Manage risk!</i>
"""
    return message.strip()

# ============================================
# TECHNICAL INDICATORS
# ============================================

def calculate_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate all technical indicators with error handling"""
    try:
        if len(df) < 50:
            return None
        
        df = df.copy()
        
        # Moving Averages
        df['SMA_20'] = df['Close'].rolling(20).mean()
        df['SMA_50'] = df['Close'].rolling(50).mean()
        
        # RSI
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        # MACD
        exp1 = df['Close'].ewm(span=12, adjust=False).mean()
        exp2 = df['Close'].ewm(span=26, adjust=False).mean()
        df['MACD'] = exp1 - exp2
        df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
        df['MACD_Histogram'] = df['MACD'] - df['MACD_Signal']
        
        # Bollinger Bands
        df['BB_Middle'] = df['Close'].rolling(20).mean()
        bb_std = df['Close'].rolling(20).std()
        df['BB_Upper'] = df['BB_Middle'] + (bb_std * 2)
        df['BB_Lower'] = df['BB_Middle'] - (bb_std * 2)
        df['BB_Width'] = df['BB_Upper'] - df['BB_Lower']
        df['BB_Position'] = (df['Close'] - df['BB_Lower']) / df['BB_Width']
        
        # ATR
        high_low = df['High'] - df['Low']
        high_close = abs(df['High'] - df['Close'].shift())
        low_close = abs(df['Low'] - df['Close'].shift())
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        df['ATR'] = tr.rolling(14).mean()
        
        # ADX
        plus_dm = df['High'].diff()
        minus_dm = df['Low'].diff()
        plus_dm[plus_dm < 0] = 0
        minus_dm[minus_dm > 0] = 0
        atr = df['ATR']
        df['Plus_DI'] = 100 * (plus_dm.rolling(14).mean() / atr)
        df['Minus_DI'] = 100 * (abs(minus_dm).rolling(14).mean() / atr)
        df['ADX'] = 100 * (abs(df['Plus_DI'] - df['Minus_DI']) / (df['Plus_DI'] + df['Minus_DI'])).rolling(14).mean()
        
        return df
        
    except Exception as e:
        logger.error(f"Indicator calculation error: {e}")
        return None

def check_signal_quality(df: pd.DataFrame) -> Tuple[SignalType, int, float, float, float]:
    """
    Check signal quality with multiple confirmations
    Returns: (signal, confidence, stop_loss, take_profit, risk_reward)
    """
    try:
        latest = df.iloc[-1]
        prev = df.iloc[-2]
        
        # Get current values
        rsi = latest['RSI']
        adx = latest['ADX']
        price = latest['Close']
        atr = latest['ATR']
        bb_position = latest['BB_Position']
        macd_hist = latest['MACD_Histogram']
        
        # Condition 1: ADX < 25 (Ranging market)
        if adx >= ADX_THRESHOLD:
            return SignalType.NEUTRAL, 0, None, None, 0
        
        buy_confirmations = 0
        sell_confirmations = 0
        total_confirmations = 0
        
        # Condition 2: RSI thresholds
        if rsi < RSI_BUY_THRESHOLD:
            buy_confirmations += 2
            total_confirmations += 2
        elif rsi > RSI_SELL_THRESHOLD:
            sell_confirmations += 2
            total_confirmations += 2
        elif rsi < 45:
            buy_confirmations += 1
            total_confirmations += 1
        elif rsi > 55:
            sell_confirmations += 1
            total_confirmations += 1
        
        # Condition 3: Bollinger Bands position
        if bb_position < 0.2:
            buy_confirmations += 1
            total_confirmations += 1
        elif bb_position > 0.8:
            sell_confirmations += 1
            total_confirmations += 1
        
        # Condition 4: MACD confirmation
        if macd_hist > 0 and macd_hist > prev['MACD_Histogram']:
            buy_confirmations += 1
            total_confirmations += 1
        elif macd_hist < 0 and macd_hist < prev['MACD_Histogram']:
            sell_confirmations += 1
            total_confirmations += 1
        
        # Condition 5: Price vs SMA20
        if price > latest['SMA_20']:
            buy_confirmations += 1
            total_confirmations += 1
        else:
            sell_confirmations += 1
            total_confirmations += 1
        
        # Calculate confidence
        if total_confirmations > 0:
            if buy_confirmations > sell_confirmations:
                confidence = int((buy_confirmations / total_confirmations) * 100)
                confidence = min(95, 50 + confidence)  # Scale to 50-95%
                signal = SignalType.BUY
                
                # Calculate ATR-based SL/TP
                stop_loss = price - (atr * 1.5)
                take_profit = price + (atr * 3.0)  # 1:2 ratio
                risk = abs(price - stop_loss)
                reward = abs(take_profit - price)
                risk_reward = reward / risk if risk > 0 else 0
                
                return signal, confidence, stop_loss, take_profit, risk_reward
                
            elif sell_confirmations > buy_confirmations:
                confidence = int((sell_confirmations / total_confirmations) * 100)
                confidence = min(95, 50 + confidence)
                signal = SignalType.SELL
                
                stop_loss = price + (atr * 1.5)
                take_profit = price - (atr * 3.0)
                risk = abs(price - stop_loss)
                reward = abs(take_profit - price)
                risk_reward = reward / risk if risk > 0 else 0
                
                return signal, confidence, stop_loss, take_profit, risk_reward
        
        return SignalType.NEUTRAL, 0, None, None, 0
        
    except Exception as e:
        logger.error(f"Signal quality check error: {e}")
        return SignalType.NEUTRAL, 0, None, None, 0

# ============================================
# RISK MANAGEMENT
# ============================================

def calculate_lot_size(account_balance: float, risk_percent: float, stop_loss_pips: float, pair_info: dict) -> float:
    """Calculate position size based on risk"""
    try:
        risk_amount = account_balance * (risk_percent / 100)
        pip_value = pair_info.get('pip_value', 0.1)
        
        # Calculate lot size
        lot_size = risk_amount / (stop_loss_pips * pip_value)
        
        # Round to 2 decimal places
        lot_size = round(lot_size, 2)
        
        # Apply minimum lot constraint
        min_lot = pair_info.get('min_lot', 0.01)
        lot_size = max(min_lot, lot_size)
        
        # Maximum lot for small accounts
        max_lot = min(1.0, lot_size * 2)
        lot_size = min(max_lot, lot_size)
        
        return lot_size
        
    except Exception as e:
        logger.error(f"Lot size calculation error: {e}")
        return 0.01

def calculate_pips(price: float, stop_loss: float, pair_type: str) -> float:
    """Calculate stop loss in pips"""
    try:
        pips = abs(price - stop_loss)
        if pair_type == 'Forex':
            return pips * 10000
        else:
            return pips * 100
    except:
        return 0

# ============================================
# SESSION MANAGEMENT
# ============================================

def is_trading_session() -> Tuple[bool, str]:
    """Check if currently in active trading session"""
    now = datetime.utcnow()
    current_hour = now.hour
    
    # Check London Session
    if LONDON_SESSION[0] <= current_hour < LONDON_SESSION[1]:
        return True, "London"
    
    # Check New York Session
    if NEW_YORK_SESSION[0] <= current_hour < NEW_YORK_SESSION[1]:
        return True, "New York"
    
    return False, "Closed"

def get_session_name() -> str:
    """Get current session name"""
    active, session = is_trading_session()
    return session if active else "Closed"

# ============================================
# DATA FETCHING
# ============================================

def fetch_pair_data(symbol: str, pair_info: dict) -> Optional[pd.DataFrame]:
    """Fetch data with retry mechanism"""
    max_retries = 2
    for attempt in range(max_retries):
        try:
            pair_type = pair_info['type']
            
            # Different periods based on type
            if pair_type == 'Index':
                df = yf.Ticker(symbol).history(period='1mo', interval='1h')
            elif pair_type == 'Commodity':
                df = yf.Ticker(symbol).history(period='1wk', interval='1h')
            else:
                df = yf.Ticker(symbol).history(period='1wk', interval='1h')
            
            if len(df) >= 50:
                return df
                
        except Exception as e:
            logger.warning(f"Fetch attempt {attempt + 1} failed for {symbol}: {e}")
            if attempt < max_retries - 1:
                time.sleep(1)
    
    return None

# ============================================
# TRADE MANAGEMENT
# ============================================

class TradeManager:
    """Manages trades and prevents duplicates"""
    
    def __init__(self, max_trades: int = MAX_TRADES_PER_SESSION):
        self.trades: List[TradeSignal] = []
        self.sent_signals: Dict[str, datetime] = {}  # Track sent signals per pair
        self.session_trades = 0
        self.current_session = None
        self.last_signal_time: Dict[str, datetime] = {}
        
    def can_trade(self) -> Tuple[bool, str]:
        """Check if we can take new trades"""
        active, session = is_trading_session()
        
        if not active:
            return False, "Market closed"
        
        # Reset session counter if new session
        if self.current_session != session:
            self.session_trades = 0
            self.current_session = session
            logger.info(f"New session: {session}. Resetting trade count.")
        
        if self.session_trades >= MAX_TRADES_PER_SESSION:
            return False, f"Max trades ({MAX_TRADES_PER_SESSION}) reached for {session} session"
        
        return True, "OK"
    
    def add_trade(self, signal: TradeSignal) -> bool:
        """Add trade to manager"""
        self.trades.append(signal)
        self.session_trades += 1
        self.sent_signals[signal.pair] = signal.timestamp
        return True
    
    def is_duplicate(self, pair: str, signal: SignalType) -> bool:
        """Check if signal was recently sent for this pair"""
        if pair in self.last_signal_time:
            time_diff = (datetime.now() - self.last_signal_time[pair]).total_seconds()
            if time_diff < 3600:  # 1 hour cooldown
                return True
        
        self.last_signal_time[pair] = datetime.now()
        return False
    
    def get_stats(self) -> dict:
        """Get trade statistics"""
        return {
            'total_trades': len(self.trades),
            'session_trades': self.session_trades,
            'current_session': self.current_session or "None",
            'pairs_traded': list(self.sent_signals.keys())
        }

# ============================================
# MAIN BOT CLASS
# ============================================

class ForexTradingBot:
    """Main trading bot class"""
    
    def __init__(self):
        self.trade_manager = TradeManager()
        self.account_balance = ACCOUNT_BALANCE
        self.risk_per_trade = RISK_PER_TRADE
        
    def analyze_pair(self, symbol: str, pair_info: dict) -> Optional[TradeSignal]:
        """Analyze a single pair and generate signal if conditions met"""
        try:
            # Fetch data
            df = fetch_pair_data(symbol, pair_info)
            if df is None:
                return None
            
            # Calculate indicators
            df = calculate_indicators(df)
            if df is None:
                return None
            
            # Check signal quality
            signal, confidence, sl, tp, rr = check_signal_quality(df)
            
            if signal == SignalType.NEUTRAL:
                return None
            
            # Check minimum confidence
            if confidence < MIN_CONFIDENCE:
                logger.info(f"{pair_info['name']}: Confidence {confidence}% < {MIN_CONFIDENCE}%")
                return None
            
            # Check minimum risk-reward
            if rr < MIN_RISK_REWARD:
                logger.info(f"{pair_info['name']}: Risk/Reward {rr:.1f} < {MIN_RISK_REWARD}")
                return None
            
            # Check if trading session is active
            active, session = is_trading_session()
            if not active:
                logger.info(f"{pair_info['name']}: Market closed - no trading")
                return None
            
            # Check if we can trade (max trades limit)
            can_trade, reason = self.trade_manager.can_trade()
            if not can_trade:
                logger.info(f"{pair_info['name']}: {reason}")
                return None
            
            # Check for duplicate signals
            if self.trade_manager.is_duplicate(pair_info['name'], signal):
                logger.info(f"{pair_info['name']}: Duplicate signal blocked")
                return None
            
            # Get current price
            latest = df.iloc[-1]
            price = latest['Close']
            atr = latest['ATR']
            rsi = latest['RSI']
            adx = latest['ADX']
            
            # Calculate stop loss in pips
            stop_pips = calculate_pips(price, sl, pair_info['type'])
            
            # Calculate lot size
            lot_size = calculate_lot_size(self.account_balance, self.risk_per_trade, stop_pips, pair_info)
            
            # Create trade signal
            trade_signal = TradeSignal(
                pair=pair_info['name'],
                signal=signal,
                entry=price,
                stop_loss=sl,
                take_profit=tp,
                confidence=confidence,
                rsi=rsi,
                adx=adx,
                session=session,
                risk_reward=rr,
                timestamp=datetime.now(),
                expiry=datetime.now() + timedelta(hours=MAX_HOLD_HOURS),
                lot_size=lot_size
            )
            
            # Add to trade manager
            self.trade_manager.add_trade(trade_signal)
            
            return trade_signal
            
        except Exception as e:
            logger.error(f"Error analyzing {pair_info['name']}: {e}")
            return None
    
    def run_analysis(self) -> List[TradeSignal]:
        """Run analysis on all pairs"""
        signals = []
        
        for symbol, info in LOW_VOLATILITY_PAIRS.items():
            signal = self.analyze_pair(symbol, info)
            if signal:
                signals.append(signal)
                logger.info(f"Signal generated: {signal.pair} {signal.signal.value} - Confidence: {signal.confidence}%")
        
        return signals

# ============================================
# STREAMLIT UI
# ============================================

st.set_page_config(page_title="Professional Forex Bot", layout="wide")

st.title("🤖 Professional Forex Trading Bot")
st.write("Advanced signal filtering | Risk Management | Session Control")

# Initialize bot
if 'bot' not in st.session_state:
    st.session_state.bot = ForexTradingBot()
    st.session_state.last_signals = []
    st.session_state.auto_refresh = False

# Sidebar
with st.sidebar:
    st.header("⚙️ Trading Parameters")
    
    st.subheader("💰 Account Settings")
    account_balance = st.number_input("Account Balance ($)", min_value=20, max_value=10000, value=ACCOUNT_BALANCE)
    risk_percent = st.slider("Risk per Trade (%)", 0.5, 3.0, RISK_PER_TRADE, 0.5)
    
    st.subheader("🎯 Signal Filters")
    st.metric("Min Confidence", f"{MIN_CONFIDENCE}%")
    st.metric("Min Risk/Reward", f"1:{MIN_RISK_REWARD}")
    st.metric("Max Trades/Session", MAX_TRADES_PER_SESSION)
    st.metric("Signal Expiry", f"{MAX_HOLD_HOURS} hours")
    
    st.subheader("📊 Session Status")
    active, session = is_trading_session()
    if active:
        st.success(f"✅ {session} Session ACTIVE")
    else:
        st.warning("⏸️ Market Closed - No signals")
    
    st.subheader("📈 Trade Stats")
    stats = st.session_state.bot.trade_manager.get_stats()
    st.metric("Total Trades Today", stats['total_trades'])
    st.metric("Session Trades", stats['session_trades'])
    st.metric("Current Session", stats['current_session'])
    
    # Manual refresh
    if st.button("🔄 Analyze Now", use_container_width=True):
        st.rerun()
    
    st.session_state.auto_refresh = st.checkbox("🔄 Auto-refresh (every 5 min)", value=False)

# Update bot settings
st.session_state.bot.account_balance = account_balance
st.session_state.bot.risk_per_trade = risk_percent

# Run analysis
if st.button("🚀 Generate Signals", use_container_width=True) or st.session_state.auto_refresh:
    with st.spinner("Analyzing markets..."):
        signals = st.session_state.bot.run_analysis()
        st.session_state.last_signals = signals
        
        # Send to Telegram
        for signal in signals:
            message = format_trade_signal(signal)
            send_telegram_message(TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, message)
            st.success(f"📱 Signal sent: {signal.pair} {signal.signal.value}")
        
        if not signals:
            st.info("⚖️ No signals meet all quality criteria")

# Display signals
st.markdown("## 🎯 ACTIVE TRADE SIGNALS")

if st.session_state.last_signals:
    for signal in st.session_state.last_signals:
        if signal.signal == SignalType.BUY:
            color = "#1a472a"
            border = "#00ff00"
            emoji = "🟢"
        else:
            color = "#471a1a"
            border = "#ff4444"
            emoji = "🔴"
        
        # Format price display
        if signal.pair in ['US30', 'US100']:
            entry_str = f"{signal.entry:,.2f}"
            sl_str = f"{signal.stop_loss:,.2f}"
            tp_str = f"{signal.take_profit:,.2f}"
        else:
            entry_str = f"{signal.entry:.5f}"
            sl_str = f"{signal.stop_loss:.5f}"
            tp_str = f"{signal.take_profit:.5f}"
        
        st.markdown(f"""
        <div style="background: {color}; border-left: 5px solid {border}; padding: 15px; border-radius: 10px; margin-bottom: 15px;">
            <h2>{emoji} {signal.signal.value} {signal.pair}</h2>
            <table style="width: 100%;">
                <tr>
                    <td><b>💰 Entry:</b> {entry_str}</td>
                    <td><b>🎯 Confidence:</b> {signal.confidence}%</td>
                    <td><b>📊 RSI:</b> {signal.rsi:.1f}</td>
                </tr>
                <tr>
                    <td><b>🛑 Stop Loss:</b> {sl_str}</td>
                    <td><b>🎯 Take Profit:</b> {tp_str}</td>
                    <td><b>📈 Risk/Reward:</b> 1:{signal.risk_reward:.1f}</td>
                </tr>
                <tr>
                    <td><b>📊 ADX:</b> {signal.adx:.1f}</td>
                    <td><b>⏰ Session:</b> {signal.session}</td>
                    <td><b>⏱️ Valid Until:</b> {signal.expiry.strftime('%H:%M')} UTC</td>
                </tr>
                <tr>
                    <td><b>💰 Lot Size:</b> {signal.lot_size:.2f}</td>
                    <td><b>💰 Risk Amount:</b> ${account_balance * risk_percent / 100:.2f}</td>
                    <td></td>
                </tr>
            </table>
        </div>
        """, unsafe_allow_html=True)
else:
    st.info("No active signals at this time. Waiting for market conditions to align.")

# Auto-refresh logic
if st.session_state.auto_refresh:
    st.markdown("---")
    st.info("🔄 Auto-refresh enabled - Analyzing every 5 minutes...")
    time.sleep(300)
    st.rerun()

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: gray;'>
    <p>⚠️ <b>Educational purposes only</b> - Not financial advice</p>
    <p>📊 Signal Filters: ADX &lt; 25 | RSI &lt; 35 (BUY) / &gt; 65 (SELL) | Min RR 1:2 | Min Confidence 70%</p>
    <p>📱 <b>Telegram notifications sent for all qualified signals</b></p>
</div>
""", unsafe_allow_html=True)
