import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime

st.set_page_config(page_title="Forex Analyzer", layout="wide")

st.title("📊 Forex & Indices Market Analyzer")
st.write("Real-time trading signals (Educational Only)")

st.write(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# Define all instruments
pairs = {
    # Forex Pairs
    'EURUSD=X': {'name': 'EUR/USD', 'type': 'Forex', 'decimals': 5},
    'GBPUSD=X': {'name': 'GBP/USD', 'type': 'Forex', 'decimals': 5},
    'USDJPY=X': {'name': 'USD/JPY', 'type': 'Forex', 'decimals': 3},
    'AUDUSD=X': {'name': 'AUD/USD', 'type': 'Forex', 'decimals': 5},
    'USDCAD=X': {'name': 'USD/CAD', 'type': 'Forex', 'decimals': 5},
    'USDCHF=X': {'name': 'USD/CHF', 'type': 'Forex', 'decimals': 5},
    'NZDUSD=X': {'name': 'NZD/USD', 'type': 'Forex', 'decimals': 5},
    
    # Indices
    '^DJI': {'name': '🇺🇸 US30 (Dow Jones)', 'type': 'Index', 'decimals': 2},
    '^NDX': {'name': '🇺🇸 US100 (NASDAQ)', 'type': 'Index', 'decimals': 2},
    '^GSPC': {'name': '🇺🇸 S&P 500', 'type': 'Index', 'decimals': 2},
    
    # Commodities
    'GC=F': {'name': '🥇 Gold (XAU/USD)', 'type': 'Commodity', 'decimals': 2},
    'SI=F': {'name': '🥈 Silver', 'type': 'Commodity', 'decimals': 3},
}

def analyze_instrument(symbol, instrument_info):
    """Analyze a single instrument and return signal data"""
    try:
        name = instrument_info['name']
        instrument_type = instrument_info['type']
        
        # Adjust period based on instrument type
        if instrument_type == 'Index':
            df = yf.Ticker(symbol).history(period='1mo', interval='1h')
        elif instrument_type == 'Commodity':
            df = yf.Ticker(symbol).history(period='1wk', interval='1h')
        else:
            df = yf.Ticker(symbol).history(period='5d', interval='1h')

        if len(df) < 20:
            return None

        # Calculate indicators
        current = df['Close'].iloc[-1]
        prev_close = df['Close'].iloc[-2]
        sma20 = df['Close'].rolling(20).mean().iloc[-1]
        sma50 = df['Close'].rolling(50).mean().iloc[-1] if len(df) >= 50 else sma20
        
        # RSI Calculation
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs)).iloc[-1]
        
        # MACD Calculation
        exp1 = df['Close'].ewm(span=12, adjust=False).mean()
        exp2 = df['Close'].ewm(span=26, adjust=False).mean()
        macd = exp1 - exp2
        macd_signal = macd.ewm(span=9, adjust=False).mean()
        macd_histogram = (macd - macd_signal).iloc[-1]
        
        # ATR for volatility
        high_low = df['High'] - df['Low']
        high_close = abs(df['High'] - df['Close'].shift())
        low_close = abs(df['Low'] - df['Close'].shift())
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr = tr.rolling(14).mean().iloc[-1]
        atr_percent = (atr / current) * 100
        
        # Determine signal with scoring
        buy_score = 0
        sell_score = 0
        
        # Price vs SMA20
        if current > sma20:
            buy_score += 1
        else:
            sell_score += 1
        
        # SMA20 vs SMA50 (trend)
        if sma20 > sma50:
            buy_score += 1
        else:
            sell_score += 1
        
        # RSI signals
        if rsi < 30:
            buy_score += 2
        elif rsi > 70:
            sell_score += 2
        elif rsi < 45:
            buy_score += 1
        elif rsi > 55:
            sell_score += 1
        
        # MACD signals
        if macd_histogram > 0:
            buy_score += 1
        else:
            sell_score += 1
        
        # Determine final signal
        if buy_score > sell_score and buy_score >= 2:
            signal = "🟢 BUY"
            action = "BUY"
            confidence = min(90, 50 + (buy_score * 10))
            signal_strength = "Strong" if buy_score >= 4 else "Moderate"
        elif sell_score > buy_score and sell_score >= 2:
            signal = "🔴 SELL"
            action = "SELL"
            confidence = min(90, 50 + (sell_score * 10))
            signal_strength = "Strong" if sell_score >= 4 else "Moderate"
        else:
            signal = "⚖️ NEUTRAL"
            action = "NEUTRAL"
            confidence = 0
            signal_strength = "None"
        
        # Calculate trade levels for signals
        stop_loss = None
        take_profit = None
        risk_reward = None
        
        if action != "NEUTRAL":
            if action == "BUY":
                stop_loss = current - (atr * 1.5)
                take_profit = current + (atr * 2.5)
            else:
                stop_loss = current + (atr * 1.5)
                take_profit = current - (atr * 2.5)
            
            risk = abs(current - stop_loss)
            reward = abs(take_profit - current)
            risk_reward = round(reward / risk, 2) if risk > 0 else 0
        
        # Price change
        price_change = ((current - prev_close) / prev_close) * 100
        
        # Format price based on instrument
        decimals = instrument_info['decimals']
        if decimals == 2:
            price_str = f"{current:,.2f}"
        elif decimals == 3:
            price_str = f"{current:.3f}"
        else:
            price_str = f"{current:.5f}"
        
        return {
            'symbol': symbol,
            'name': name,
            'type': instrument_type,
            'price': current,
            'price_str': price_str,
            'price_change': price_change,
            'signal': signal,
            'action': action,
            'confidence': confidence,
            'signal_strength': signal_strength,
            'rsi': rsi,
            'sma20': sma20,
            'sma50': sma50,
            'macd_histogram': macd_histogram,
            'atr': atr,
            'atr_percent': atr_percent,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'risk_reward': risk_reward,
            'buy_score': buy_score,
            'sell_score': sell_score
        }
        
    except Exception as e:
        st.error(f"{name}: Error - {str(e)}")
        return None

# Analyze all instruments
with st.spinner("Analyzing markets..."):
    results = []
    for symbol, info in pairs.items():
        result = analyze_instrument(symbol, info)
        if result:
            results.append(result)

# ============================================
# TABLE 1: TRADE SIGNALS - WHAT TO BUY/SELL
# ============================================
st.markdown("## 🎯 TRADE SIGNALS")
st.markdown("### What to Buy / Sell Now")

# Filter actionable signals
actionable_signals = [r for r in results if r['action'] != 'NEUTRAL']

if actionable_signals:
    # Create trade signals dataframe
    trade_df = pd.DataFrame([
        {
            'Signal': r['signal'],
            'Instrument': r['name'],
            'Type': r['type'],
            'Price': r['price_str'],
            'Confidence': f"{r['confidence']}%",
            'Strength': r['signal_strength'],
            'RSI': f"{r['rsi']:.1f}",
            'Entry': r['price_str'],
            'Stop Loss': f"{r['stop_loss']:.5f}" if r['stop_loss'] else '-',
            'Take Profit': f"{r['take_profit']:.5f}" if r['take_profit'] else '-',
            'R:R': f"1:{r['risk_reward']}" if r['risk_reward'] else '-'
        }
        for r in actionable_signals
    ])
    
    # Display signals table
    st.dataframe(
        trade_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Signal": st.column_config.TextColumn(width="small"),
            "Instrument": st.column_config.TextColumn(width="medium"),
            "Type": st.column_config.TextColumn(width="small"),
            "Price": st.column_config.TextColumn(width="small"),
            "Confidence": st.column_config.TextColumn(width="small"),
            "Strength": st.column_config.TextColumn(width="small"),
            "RSI": st.column_config.TextColumn(width="small"),
            "Entry": st.column_config.TextColumn(width="small"),
            "Stop Loss": st.column_config.TextColumn(width="medium"),
            "Take Profit": st.column_config.TextColumn(width="medium"),
            "R:R": st.column_config.TextColumn(width="small"),
        }
    )
else:
    st.info("⚖️ No strong trade signals at this time. Market is ranging or neutral.")

# ============================================
# TABLE 2: MARKET OVERVIEW - ALL INSTRUMENTS
# ============================================
st.markdown("## 📊 MARKET OVERVIEW")
st.markdown("### All Instruments Analysis")

# Create overview dataframe
overview_df = pd.DataFrame([
    {
        'Instrument': r['name'],
        'Type': r['type'],
        'Price': r['price_str'],
        'Change %': f"{r['price_change']:+.2f}%",
        'Signal': r['signal'],
        'Confidence': f"{r['confidence']}%" if r['confidence'] > 0 else '-',
        'RSI': f"{r['rsi']:.1f}",
        'SMA20': f"{r['sma20']:.5f}" if r['type'] == 'Forex' else f"{r['sma20']:.2f}",
        'SMA50': f"{r['sma50']:.5f}" if r['type'] == 'Forex' else f"{r['sma50']:.2f}",
        'MACD': f"{r['macd_histogram']:.4f}",
        'Volatility': f"{r['atr_percent']:.2f}%"
    }
    for r in results
])

# Color code the signal column
def color_signal(val):
    if '🟢' in val:
        return 'background-color: #1a472a; color: #00ff00'
    elif '🔴' in val:
        return 'background-color: #471a1a; color: #ff4444'
    else:
        return 'background-color: #2a2a2a; color: #ffff00'

# Display overview table with styling
st.dataframe(
    overview_df,
    use_container_width=True,
    hide_index=True,
    column_config={
        "Instrument": st.column_config.TextColumn(width="medium"),
        "Type": st.column_config.TextColumn(width="small"),
        "Price": st.column_config.TextColumn(width="small"),
        "Change %": st.column_config.TextColumn(width="small"),
        "Signal": st.column_config.TextColumn(width="small"),
        "Confidence": st.column_config.TextColumn(width="small"),
        "RSI": st.column_config.TextColumn(width="small"),
        "SMA20": st.column_config.TextColumn(width="medium"),
        "SMA50": st.column_config.TextColumn(width="medium"),
        "MACD": st.column_config.TextColumn(width="small"),
        "Volatility": st.column_config.TextColumn(width="small"),
    }
)

# ============================================
# DETAILED ANALYSIS FOR EACH INSTRUMENT
# ============================================
st.markdown("## 📈 DETAILED ANALYSIS")
st.markdown("### Individual Instrument Breakdown")

# Create tabs for different instrument types
tab1, tab2, tab3 = st.tabs(["💰 Forex Pairs", "📊 Indices", "🥇 Commodities"])

# Filter by type
forex = [r for r in results if r['type'] == 'Forex']
indices = [r for r in results if r['type'] == 'Index']
commodities = [r for r in results if r['type'] == 'Commodity']

with tab1:
    if forex:
        for r in forex:
            with st.expander(f"{r['signal']} {r['name']} - {r['signal']}", expanded=False):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Current Price", r['price_str'], f"{r['price_change']:+.2f}%")
                    st.metric("RSI", f"{r['rsi']:.1f}", 
                             delta="Oversold" if r['rsi'] < 30 else ("Overbought" if r['rsi'] > 70 else "Neutral"))
                    st.metric("ATR Volatility", f"{r['atr_percent']:.2f}%")
                
                with col2:
                    st.metric("SMA 20", f"{r['sma20']:.5f}")
                    st.metric("SMA 50", f"{r['sma50']:.5f}")
                    st.metric("MACD Histogram", f"{r['macd_histogram']:.4f}")
                
                with col3:
                    if r['action'] != 'NEUTRAL':
                        st.metric("Signal Strength", r['signal_strength'])
                        st.metric("Confidence", f"{r['confidence']}%")
                        st.metric("Risk/Reward", f"1:{r['risk_reward']}" if r['risk_reward'] else '-')
                
                if r['action'] != 'NEUTRAL':
                    st.markdown("---")
                    st.markdown("**🎯 Trade Plan:**")
                    col_a, col_b, col_c = st.columns(3)
                    with col_a:
                        st.info(f"🚀 **Entry:** {r['price_str']}")
                    with col_b:
                        st.warning(f"🛑 **Stop Loss:** {r['stop_loss']:.5f}")
                    with col_c:
                        st.success(f"🎯 **Take Profit:** {r['take_profit']:.5f}")
    else:
        st.info("No forex data available")

with tab2:
    if indices:
        for r in indices:
            with st.expander(f"{r['signal']} {r['name']} - {r['signal']}", expanded=False):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Current Price", r['price_str'], f"{r['price_change']:+.2f}%")
                    st.metric("RSI", f"{r['rsi']:.1f}",
                             delta="Oversold" if r['rsi'] < 30 else ("Overbought" if r['rsi'] > 70 else "Neutral"))
                    st.metric("ATR Volatility", f"{r['atr_percent']:.2f}%")
                
                with col2:
                    st.metric("SMA 20", f"{r['sma20']:.2f}")
                    st.metric("SMA 50", f"{r['sma50']:.2f}")
                    st.metric("MACD Histogram", f"{r['macd_histogram']:.4f}")
                
                with col3:
                    if r['action'] != 'NEUTRAL':
                        st.metric("Signal Strength", r['signal_strength'])
                        st.metric("Confidence", f"{r['confidence']}%")
                        st.metric("Risk/Reward", f"1:{r['risk_reward']}" if r['risk_reward'] else '-')
                
                if r['action'] != 'NEUTRAL':
                    st.markdown("---")
                    st.markdown("**🎯 Trade Plan:**")
                    col_a, col_b, col_c = st.columns(3)
                    with col_a:
                        st.info(f"🚀 **Entry:** {r['price_str']}")
                    with col_b:
                        st.warning(f"🛑 **Stop Loss:** {r['stop_loss']:.2f}")
                    with col_c:
                        st.success(f"🎯 **Take Profit:** {r['take_profit']:.2f}")
    else:
        st.info("No index data available")

with tab3:
    if commodities:
        for r in commodities:
            with st.expander(f"{r['signal']} {r['name']} - {r['signal']}", expanded=False):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Current Price", r['price_str'], f"{r['price_change']:+.2f}%")
                    st.metric("RSI", f"{r['rsi']:.1f}",
                             delta="Oversold" if r['rsi'] < 30 else ("Overbought" if r['rsi'] > 70 else "Neutral"))
                    st.metric("ATR Volatility", f"{r['atr_percent']:.2f}%")
                
                with col2:
                    if r['type'] == 'Commodity':
                        st.metric("SMA 20", f"{r['sma20']:.2f}")
                        st.metric("SMA 50", f"{r['sma50']:.2f}")
                    else:
                        st.metric("SMA 20", f"{r['sma20']:.3f}")
                        st.metric("SMA 50", f"{r['sma50']:.3f}")
                    st.metric("MACD Histogram", f"{r['macd_histogram']:.4f}")
                
                with col3:
                    if r['action'] != 'NEUTRAL':
                        st.metric("Signal Strength", r['signal_strength'])
                        st.metric("Confidence", f"{r['confidence']}%")
                        st.metric("Risk/Reward", f"1:{r['risk_reward']}" if r['risk_reward'] else '-')
                
                if r['action'] != 'NEUTRAL':
                    st.markdown("---")
                    st.markdown("**🎯 Trade Plan:**")
                    col_a, col_b, col_c = st.columns(3)
                    with col_a:
                        st.info(f"🚀 **Entry:** {r['price_str']}")
                    with col_b:
                        st.warning(f"🛑 **Stop Loss:** {r['stop_loss']:.2f}")
                    with col_c:
                        st.success(f"🎯 **Take Profit:** {r['take_profit']:.2f}")
    else:
        st.info("No commodity data available")

# ============================================
# SUMMARY STATISTICS
# ============================================
st.markdown("## 📊 SUMMARY STATISTICS")

col1, col2, col3, col4 = st.columns(4)

with col1:
    buy_signals = len([r for r in results if r['action'] == 'BUY'])
    st.metric("🟢 BUY Signals", buy_signals)

with col2:
    sell_signals = len([r for r in results if r['action'] == 'SELL'])
    st.metric("🔴 SELL Signals", sell_signals)

with col3:
    neutral = len([r for r in results if r['action'] == 'NEUTRAL'])
    st.metric("⚖️ Neutral", neutral)

with col4:
    avg_confidence = sum(r['confidence'] for r in results if r['confidence'] > 0) / len([r for r in results if r['confidence'] > 0]) if [r for r in results if r['confidence'] > 0] else 0
    st.metric("Avg Confidence", f"{avg_confidence:.0f}%")

# ============================================
# FOOTER
# ============================================
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: gray;'>
    <p>⚠️ <b>Educational purposes only</b> - Not financial advice</p>
    <p>📊 Signals based on: RSI, MACD, Moving Averages, and Volatility (ATR)</p>
    <p>🔄 Data updates on page refresh | Click refresh button below for latest data</p>
</div>
""", unsafe_allow_html=True)

# Refresh button
if st.button("🔄 Refresh Data", use_container_width=True):
    st.rerun()
