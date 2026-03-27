import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import requests
import time
import os

# ============================================
# CONFIGURATION - Get from environment variables
# ============================================
TOKEN = os.environ.get('8773664334:AAE4fd4Wpyd2ZQkWBsjlPby7qSGKp00jGng')
CHAT_ID = os.environ.get('2057396237')

if not TOKEN or not CHAT_ID:
    print("ERROR: Please set TELEGRAM_TOKEN and CHAT_ID environment variables")
    exit(1)

MIN_CONFIDENCE = 60
# ============================================

def send_telegram_message(message):
    """Send message to Telegram"""
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {'chat_id': CHAT_ID, 'text': message, 'parse_mode': 'HTML'}
    try:
        response = requests.post(url, json=payload, timeout=30)
        return response.ok
    except Exception as e:
        print(f"Error: {e}")
        return False

def calculate_indicators(df):
    """Calculate all technical indicators"""
    if len(df) < 50:
        return None
    
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
    
    # ATR
    high_low = df['High'] - df['Low']
    high_close = abs(df['High'] - df['Close'].shift())
    low_close = abs(df['Low'] - df['Close'].shift())
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    df['ATR'] = tr.rolling(14).mean()
    
    return df

def calculate_signal_score(df):
    """Calculate buy/sell score"""
    latest = df.iloc[-1]
    buy_score = 0
    sell_score = 0
    
    if latest['Close'] > latest['SMA_20']:
        buy_score += 2
    else:
        sell_score += 2
    
    if latest['RSI'] < 30:
        buy_score += 3
    elif latest['RSI'] > 70:
        sell_score += 3
    elif latest['RSI'] < 50:
        buy_score += 1
    elif latest['RSI'] > 50:
        sell_score += 1
    
    if latest['MACD_Histogram'] > 0:
        buy_score += 2
    else:
        sell_score += 2
    
    return buy_score, sell_score

def calculate_trade_levels(price, signal, atr):
    """Calculate stop loss and take profit levels"""
    if signal == "BUY":
        stop_loss = price - (atr * 1.5)
        take_profit_1 = price + (atr * 2)
        take_profit_2 = price + (atr * 3)
        take_profit_3 = price + (atr * 4)
    else:
        stop_loss = price + (atr * 1.5)
        take_profit_1 = price - (atr * 2)
        take_profit_2 = price - (atr * 3)
        take_profit_3 = price - (atr * 4)
    
    return stop_loss, take_profit_1, take_profit_2, take_profit_3

def get_market_session():
    """Determine current market session"""
    utc_hour = datetime.utcnow().hour
    
    if 13 <= utc_hour < 16:
        return "🔥 Peak Trading - London/NY Overlap", "💥 Maximum Volatility"
    elif 8 <= utc_hour < 13:
        return "🇬🇧 London Session", "📊 Active Trading"
    elif 16 <= utc_hour < 21:
        return "🇺🇸 New York Session", "📈 Active Trading"
    elif 23 <= utc_hour or utc_hour < 8:
        return "🇯🇵 Asian Session", "❄️ Lower Volatility"
    else:
        return "⚡ Inter-session", "😴 Quiet Period"

def get_key_time_name():
    """Get current key time name"""
    utc_hour = datetime.utcnow().hour
    
    key_times = {
        8: "🏛️ London Market Open",
        10: "📊 London Mid-Morning",
        13: "🗽 New York Market Open",
        14: "💥 Peak Trading - London/NY Overlap",
        16: "🇬🇧 London Market Close",
        18: "🇺🇸 New York Mid-Afternoon",
        21: "🌙 New York Market Close",
        0: "🌅 Tokyo Market Open",
        3: "🌏 Sydney/Tokyo Overlap",
        6: "🌄 Asian Session Close"
    }
    
    return key_times.get(utc_hour, "📈 Market Update")

def analyze_pair(symbol, name, df):
    """Analyze a single pair"""
    try:
        df = calculate_indicators(df)
        if df is None:
            return None
        
        latest = df.iloc[-1]
        buy_score, sell_score = calculate_signal_score(df)
        
        total_score = buy_score + sell_score
        if total_score == 0:
            total_score = 1
        
        if buy_score > sell_score and buy_score >= 3:
            signal = "BUY"
            confidence = min(95, int((buy_score / total_score) * 100))
            signal_emoji = "🟢"
        elif sell_score > buy_score and sell_score >= 3:
            signal = "SELL"
            confidence = min(95, int((sell_score / total_score) * 100))
            signal_emoji = "🔴"
        else:
            signal = "NEUTRAL"
            confidence = 0
            signal_emoji = "⚖️"
        
        if confidence < MIN_CONFIDENCE and signal != "NEUTRAL":
            signal = "NEUTRAL"
            confidence = 0
        
        trade_levels = None
        if signal != "NEUTRAL":
            sl, tp1, tp2, tp3 = calculate_trade_levels(latest['Close'], signal, latest['ATR'])
            trade_levels = (sl, tp1, tp2, tp3)
        
        # Trend strength
        if latest['Close'] > latest['SMA_20'] > latest['SMA_50']:
            trend = "📈 Strong Bullish"
        elif latest['Close'] < latest['SMA_20'] < latest['SMA_50']:
            trend = "📉 Strong Bearish"
        elif latest['Close'] > latest['SMA_20']:
            trend = "↗️ Weak Bullish"
        elif latest['Close'] < latest['SMA_20']:
            trend = "↘️ Weak Bearish"
        else:
            trend = "➡️ Sideways"
        
        return {
            'name': name,
            'price': latest['Close'],
            'signal': signal,
            'signal_emoji': signal_emoji,
            'confidence': confidence,
            'rsi': latest['RSI'],
            'trend': trend,
            'macd_trend': "Bullish" if latest['MACD_Histogram'] > 0 else "Bearish",
            'trade_levels': trade_levels
        }
    except Exception as e:
        print(f"Error analyzing {name}: {e}")
        return None

def get_forex_data():
    """Fetch all forex and index data"""
    instruments = {
        '^DJI': '🇺🇸 US30 (Dow Jones)',
        '^NDX': '🇺🇸 US100 (NASDAQ)',
        'GC=F': '🥇 XAUUSD (Gold)',
        'EURUSD=X': '🇪🇺 EUR/USD',
        'GBPUSD=X': '🇬🇧 GBP/USD',
        'USDJPY=X': '🇯🇵 USD/JPY',
        'USDCHF=X': '🇨🇭 USD/CHF',
        'AUDUSD=X': '🇦🇺 AUD/USD',
        'USDCAD=X': '🇨🇦 USD/CAD',
        'EURGBP=X': '🇪🇺/🇬🇧 EUR/GBP'
    }
    
    results = []
    
    for symbol, name in instruments.items():
        try:
            if symbol in ['^DJI', '^NDX']:
                df = yf.Ticker(symbol).history(period='2wk', interval='1h')
            else:
                df = yf.Ticker(symbol).history(period='1wk', interval='1h')
            
            if len(df) > 0:
                analysis = analyze_pair(symbol, name, df)
                if analysis:
                    results.append(analysis)
        except:
            continue
    
    results.sort(key=lambda x: (x['confidence'] if x['signal'] != 'NEUTRAL' else 0), reverse=True)
    return results

def format_message(results):
    """Format analysis results"""
    session_name, session_volatility = get_market_session()
    key_time = get_key_time_name()
    
    lines = [
        "=" * 40,
        f"<b>📊 FOREX & INDICES ANALYSIS</b>",
        f"{session_name} • {session_volatility}",
        f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC",
        f"🎯 {key_time}",
        "=" * 40,
        ""
    ]
    
    strong_signals = [r for r in results if r['signal'] != 'NEUTRAL']
    
    if strong_signals:
        lines.append("🎯 <b>TRADE SIGNALS</b>")
        lines.append("-" * 35)
        
        for r in strong_signals[:3]:  # Top 3 signals
            lines.append(f"\n{r['signal_emoji']} <b>{r['name']}</b>")
            lines.append(f"   💰 Price: ${r['price']:.5f}")
            lines.append(f"   🎯 Signal: <b>{r['signal']}</b> (Confidence: {r['confidence']}%)")
            lines.append(f"   📊 RSI: {r['rsi']:.1f}")
            lines.append(f"   📈 Trend: {r['trend']}")
            
            if r['trade_levels']:
                sl, tp1, tp2, tp3 = r['trade_levels']
                lines.append(f"\n   🛑 Stop Loss: ${sl:.5f}")
                lines.append(f"   🎯 Take Profit 1: ${tp1:.5f}")
    
    lines.append("\n" + "=" * 40)
    lines.append("⚠️ <i>Educational purposes only</i>")
    lines.append("💰 Risk per trade: 1-2% of account")
    
    return "\n".join(lines)

def get_next_key_time():
    """Return next key time"""
    now = datetime.now()
    key_times = [8, 10, 13, 14, 16, 18, 21, 0, 3, 6]
    
    for hour in key_times:
        next_time = now.replace(hour=hour, minute=0, second=0, microsecond=0)
        if next_time > now:
            return next_time
    
    return now.replace(hour=8, minute=0, second=0, microsecond=0) + timedelta(days=1)

def main():
    """Main bot loop"""
    print("🤖 Forex Bot Started on Render!")
    print(f"Time: {datetime.now()}")
    
    # Send startup message
    send_telegram_message("🤖 Forex Bot is now online and running 24/7!")
    
    while True:
        try:
            next_update = get_next_key_time()
            now = datetime.now()
            wait_seconds = (next_update - now).total_seconds()
            
            if wait_seconds <= 60 and wait_seconds > 0:
                print(f"\n[{datetime.now()}] Analyzing markets...")
                results = get_forex_data()
                
                if results:
                    message = format_message(results)
                    send_telegram_message(message)
                    print("✓ Analysis sent")
                
                time.sleep(60)  # Avoid duplicate
            else:
                if int(wait_seconds) % 3600 < 30:
                    print(f"Next update in {wait_seconds/3600:.1f} hours")
                time.sleep(30)
                
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(300)

if __name__ == "__main__":
    main()