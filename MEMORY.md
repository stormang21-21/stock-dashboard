# TradeVision - Stock Dashboard Project

## Overview
AI-powered stock analysis platform with 6 global markets. Currently at **v2.1**

## Tech Stack
- **Backend**: Python FastAPI + yfinance
- **Frontend**: HTML/CSS/JS (dark theme)
- **Icons**: Phosphor Icons
- **Host**: 165.22.99.172:8000

## GitHub
https://github.com/stormang21-21/stock-dashboard

## Version History

### v2.1 (Current)
- Glassmorphism UI with dark theme
- Phosphor Icons (professional)
- Mobile responsive (iPhone 15 tested)
- Static market ticker
- Fixed /api/analyze endpoint

### v2.0
- TradeVision-inspired design
- Animated ticker (reverted)
- Cyan/purple gradients

### v1.0
- Original basic dashboard

## Features
- AI Stock Analysis (/analyze)
- Charts with RSI (/charts)
- Crypto prices via Binance (/crypto)
- Global markets (/global)
- Portfolio tracker (/portfolio)
- Dexter AI Agent (/agent)
- Backtesting (/backtest)

## Quick Commands
```bash
# Restart server
cd /root/.openclaw/workspace/daily_stock_analysis_v3
python3 saas_server.py --host 0.0.0.0 --port 8000

# Test analyze API
curl "http://localhost:8000/api/analyze?symbol=AAPL"
```