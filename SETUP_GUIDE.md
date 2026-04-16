# ScalpBot Pro — Setup Guide

## You have TWO bots:

---

## BOT 1: automation_bot.py  (MT5 — runs trades automatically)

### Requirements
- Windows PC or Windows VPS (MetaTrader5 library is Windows-only)
- MetaTrader 5 terminal installed and logged into your FBS account
- Python 3.9+

### Install
```bash
pip install MetaTrader5 pandas numpy requests
```

### Configure (open automation_bot.py, edit the CONFIG class at the top)
```python
TELEGRAM_TOKEN   = "your_bot_token"
TELEGRAM_CHAT_ID = "your_chat_id"
MT5_LOGIN    = 123456789       # your account number
MT5_PASSWORD = "yourpassword"
MT5_SERVER   = "FBS-Real"      # your broker server name
```

### Run
```bash
python automation_bot.py
```

### What it does
- Scans XAUUSD and EURUSD every 30 seconds
- Only trades during London + NY sessions (08:00–21:00 UTC)
- Full SMC top-down analysis: Daily → H4 → H1 → M15 setup → M5 confirmation
- Regime detection: skips VOLATILE and choppy RANGING markets
- Equity protection: pauses after 3% daily drawdown or 2 consecutive losses
- Breakeven + trailing stop management
- Auto-close after 3 hours if trade still open
- Sends Telegram alerts for every trade opened/closed + hourly status

---

## BOT 2: alert_dashboard.py  (Streamlit — you review signals, decide to enter)

### Deploy FREE on Streamlit Cloud
1. Create GitHub repo → upload alert_dashboard.py + requirements.txt
2. Go to share.streamlit.io → New app → select repo → main file: alert_dashboard.py
3. Deploy → live in ~2 minutes

### Run locally
```bash
pip install -r requirements.txt
streamlit run alert_dashboard.py
```

### What it does
- Beautiful dark dashboard with permanent sidebar
- Full SMC analysis: Daily/4H/1H/Entry TF bias, Order Blocks, FVGs, Liquidity, Supply/Demand
- Regime detection badge (TRENDING/RANGING/VOLATILE)
- Plotly candlestick chart with all SMC levels drawn
- Auto-send toggle with countdown timer
- Sends Telegram alerts when high-probability setups appear
- Signal history with stats

---

## Getting Telegram credentials
1. Open Telegram → search @BotFather → /newbot → copy token
2. Search @userinfobot → it replies with your chat ID

---

## Recommended workflow
1. Start with Bot 2 (alert dashboard) for 2-4 weeks
2. Review every alert before entering manually
3. Track your results in a spreadsheet
4. Only switch to Bot 1 (automation) after you have 20+ winning manual trades

---

## Risk warning
Never risk money you cannot afford to lose.
These bots are for educational purposes.
Past performance does not guarantee future results.
