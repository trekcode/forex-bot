import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime

st.set_page_config(page_title="Forex Analyzer", layout="centered")

st.title("📊 Forex Market Analyzer")
st.write("Real-time basic forex signals (Educational Only)")

st.write(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# Updated pairs with indices and gold
pairs = {
    # Forex Pairs
    'EURUSD=X': 'EUR/USD',
    'GBPUSD=X': 'GBP/USD',
    'USDJPY=X': 'USD/JPY',
    'AUDUSD=X': 'AUD/USD',
    'USDCAD=X': 'USD/CAD',
    'USDCHF=X': 'USD/CHF',
    'NZDUSD=X': 'NZD/USD',
    
    # Indices
    '^DJI': '🇺🇸 US30 (Dow Jones)',
    '^NDX': '🇺🇸 US100 (NASDAQ)',
    '^GSPC': '🇺🇸 S&P 500',
    
    # Commodities
    'GC=F': '🥇 Gold (XAU/USD)',
    'SI=F': '🥈 Silver',
    
    # Crypto (optional - remove if you don't want)
    'BTC-USD': '₿ Bitcoin',
    'ETH-USD': 'Ξ Ethereum'
}

for symbol, name in pairs.items():
    try:
        # Adjust period for indices (need more data)
        if symbol in ['^DJI', '^NDX', '^GSPC']:
            df = yf.Ticker(symbol).history(period='1mo', interval='1h')
        elif symbol in ['GC=F', 'SI=F']:
            df = yf.Ticker(symbol).history(period='1wk', interval='1h')
        else:
            df = yf.Ticker(symbol).history(period='5d', interval='1h')

        if len(df) < 20:
            st.warning(f"{name}: Not enough data")
            continue

        current = df['Close'].iloc[-1]
        sma20 = df['Close'].rolling(20).mean().iloc[-1]

        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs)).iloc[-1]

        # Adjust signal thresholds for different asset types
        signal = "⚖️ NEUTRAL"
        
        # Indices and Gold can handle slightly different RSI thresholds
        if symbol in ['^DJI', '^NDX', '^GSPC', 'GC=F']:
            if current > sma20 and rsi < 75:
                signal = "🟢 BUY"
            elif current < sma20 and rsi > 25:
                signal = "🔴 SELL"
        else:
            if current > sma20 and rsi < 70:
                signal = "🟢 BUY"
            elif current < sma20 and rsi > 30:
                signal = "🔴 SELL"

        st.subheader(name)
        
        # Format price display for different assets
        if symbol in ['BTC-USD', 'ETH-USD']:
            st.write(f"💰 Price: ${current:,.2f}")
        elif symbol in ['^DJI', '^NDX', '^GSPC']:
            st.write(f"💰 Price: {current:,.2f}")
        else:
            st.write(f"💰 Price: {current:.5f}")
            
        st.write(f"📉 RSI: {rsi:.2f}")
        st.write(f"📊 Signal: {signal}")
        st.markdown("---")

    except Exception as e:
        st.error(f"{name}: Error loading data")

st.warning("⚠️ Educational purposes only. Not financial advice.")

# Add refresh button at the bottom
if st.button("🔄 Refresh Data"):
    st.rerun()
