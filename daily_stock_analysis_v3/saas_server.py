#!/usr/bin/env python3
"""
Daily Stock Analysis SaaS Server
"""

from fastapi import FastAPI, HTTPException, Header, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import uvicorn
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Daily Stock Analysis SaaS Platform",
    description="AI-powered stock analysis platform",
    version="3.0.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import managers
from saas import TenantManager, ModuleRegistry, SubscriptionTier
from saas.manager import get_tenant_manager
from saas.modules import get_module_registry
from admin.api import get_admin_api
from payments import PaymentProcessor, get_payment_processor
from modules.email import EmailService

# Initialize managers
tenant_manager = get_tenant_manager()
module_registry = get_module_registry()
admin_api = get_admin_api()
payment_processor = get_payment_processor()
email_service = EmailService()

# Pydantic models
class OnboardingRequest(BaseModel):
    name: str
    email: str
    company: Optional[str] = ""
    tier: str = "free"
    markets: List[str] = []


import pandas as pd

# ============ AUTO-TICKER SEARCH ============
# Popular company name to ticker mapping
POPULAR_COMPANIES = {
    # Tech
    'ROBINHOOD': 'HOOD', 'ROBIN HOOD': 'HOOD',
    'APPLE': 'AAPL', 'AAPL': 'AAPL',
    'TESLA': 'TSLA', 'TSLA': 'TSLA',
    'MICROSOFT': 'MSFT', 'MSFT': 'MSFT',
    'AMAZON': 'AMZN', 'AMZN': 'AMZN',
    'GOOGLE': 'GOOGL', 'ALPHABET': 'GOOGL',
    'META': 'META', 'FACEBOOK': 'META', 'FB': 'META',
    'NETFLIX': 'NFLX', 'NFLX': 'NFLX',
    'NVIDIA': 'NVDA', 'NVDA': 'NVDA',
    'AMD': 'AMD', 'ADVANCED MICRO DEVICES': 'AMD',
    'INTEL': 'INTC', 'INTC': 'INTC',
    'ORACLE': 'ORCL', 'ORCL': 'ORCL',
    'CISCO': 'CSCO', 'CSCO': 'CSCO',
    'ADOBE': 'ADBE', 'ADBE': 'ADBE',
    'SALESFORCE': 'CRM', 'CRM': 'CRM',
    'UBER': 'UBER', 'LYFT': 'LYFT',
    'AIRBNB': 'ABNB', 'ABNB': 'ABNB',
    'SHOPIFY': 'SHOP', 'SHOP': 'SHOP',
    'SQUARE': 'SQ', 'BLOCK': 'SQ', 'SQ': 'SQ', 'PELOTON': 'PTON', 'PTON': 'PTON',
    'PAYPAL': 'PYPL', 'PYPL': 'PYPL',
    'SNAPCHAT': 'SNAP', 'SNAP': 'SNAP',
    'TWITTER': 'TWTR', 'X CORP': 'TWTR',
    'PINTEREST': 'PINS', 'PINS': 'PINS',
    'REDDIT': 'RDDT', 'RDDT': 'RDDT',
    'COINBASE': 'COIN', 'COIN': 'COIN',
    
    # Finance
    'VISTRA': 'VST', 'VST': 'VST',
    'JPMORGAN': 'JPM', 'JPM': 'JPM', 'CHASE': 'JPM',
    'BANK OF AMERICA': 'BAC', 'BAC': 'BAC', 'BOA': 'BAC',
    'WELLS FARGO': 'WFC', 'WFC': 'WFC',
    'GOLDMAN SACHS': 'GS', 'GS': 'GS',
    'MORGAN STANLEY': 'MS', 'MS': 'MS',
    'CITIGROUP': 'C', 'CITI': 'C', 'C': 'C',
    'BLACKROCK': 'BLK', 'BLK': 'BLK',
    'VANGUARD': 'VOO', 'VOO': 'VOO',
    'FIDELITY': 'FZROX',
    'SCHWAB': 'SCHW', 'SCHW': 'SCHW',
    
    # Retail
    'WALMART': 'WMT', 'WMT': 'WMT',
    'TARGET': 'TGT', 'TGT': 'TGT',
    'COSTCO': 'COST', 'COST': 'COST',
    'HOME DEPOT': 'HD', 'HD': 'HD',
    'LOWES': 'LOW', 'LOW': 'LOW',
    'BEST BUY': 'BBY', 'BBY': 'BBY',
    
    # Food & Beverage
    'MCDONALDS': 'MCD', 'MCD': 'MCD',
    'STARBUCKS': 'SBUX', 'SBUX': 'SBUX',
    'COCA COLA': 'KO', 'KO': 'KO', 'COKE': 'KO',
    'PEPSI': 'PEP', 'PEP': 'PEP', 'PEPSICO': 'PEP',
    'KFC': 'YUM', 'TACO BELL': 'YUM', 'PIZZA HUT': 'YUM',
    'BURGER KING': 'QSR', 'TIM HORTONS': 'QSR',
    'DOMINOS': 'DPZ', 'DPZ': 'DPZ',
    'SUBWAY': 'Private',
    'CHIPOTLE': 'CMG', 'CMG': 'CMG',
    
    # Entertainment
    'DISNEY': 'DIS', 'DIS': 'DIS',
    'WARNER BROS': 'WBD', 'WBD': 'WBD',
    'PARAMOUNT': 'PARA', 'PARA': 'PARA',
    'SONY': 'SONY', 'SONY': 'SONY',
    'COMCAST': 'CMCSA', 'CMCSA': 'CMCSA',
    'SPOTIFY': 'SPOT', 'SPOT': 'SPOT', 'ZOOM': 'ZM', 'ZM': 'ZM', 'DOORDASH': 'DASH', 'DASH': 'DASH', 'INSTACART': 'CART', 'CART': 'CART',
    
    # Auto
    'FORD': 'F', 'F': 'F',
    'GENERAL MOTORS': 'GM', 'GM': 'GM', 'CHEVROLET': 'GM',
    'TOYOTA': 'TM', 'TM': 'TM',
    'HONDA': 'HMC', 'HMC': 'HMC',
    'BMW': 'BMWYY',
    'MERCEDES': 'MBGYY',
    'VOLKSWAGEN': 'VWAGY',
    'RIVIAN': 'RIVN', 'RIVN': 'RIVN',
    'LUCID': 'LCID', 'LCID': 'LCID',
    
    # Energy
    'EXXON': 'XOM', 'XOM': 'XOM', 'EXXON MOBIL': 'XOM',
    'CHEVRON': 'CVX', 'CVX': 'CVX',
    'SHELL': 'SHEL', 'SHEL': 'SHEL',
    'BP': 'BP', 'BP': 'BP',
    'CONOCOPHILLIPS': 'COP', 'COP': 'COP',
    'OCCIDENTAL PETROLEUM': 'OXY', 'OXY': 'OXY',
    
    # Pharma
    'PFIZER': 'PFE', 'PFE': 'PFE',
    'JOHNSON & JOHNSON': 'JNJ', 'JNJ': 'JNJ', 'J&J': 'JNJ',
    'MODERNA': 'MRNA', 'MRNA': 'MRNA',
    'NOVAVAX': 'NVAX', 'NVAX': 'NVAX',
    'MERCK': 'MRK', 'MRK': 'MRK',
    'ABBVIE': 'ABBV', 'ABBV': 'ABBV',
    'BRISTOL MYERS': 'BMY', 'BMY': 'BMY',
    'ELI LILLY': 'LLY', 'LLY': 'LLY',
    
    # Singapore (correct ticker codes)
    'OCBC': 'O39.SI', 'OCBC.SI': 'O39.SI',
    'DBS': 'D05.SI', 'DBS.SI': 'D05.SI',
    'UOB': 'U11.SI', 'UOB.SI': 'U11.SI',
    'SINGAPORE AIRLINES': 'C6L.SI', 'SIA': 'C6L.SI',
    'CAPITALAND': 'RNM.SI',
    'GENTING SINGAPORE': 'G13.SI',
    'KEPPEL': 'BN4.SI',
    'SEMBCORP': 'U96.SI',
    'SEMBCORP INDUSTRIES': 'S63.SI',
    'SINGTEL': 'Z74.SI',
    'STARHUB': 'CC3.SI',
    'SATS': 'S58.SI',
    'MAPLETREE': 'ME8U.SI',
    'MAPLETREE NORTH': 'N2IU.SI',
    'ASCOTT REIT': 'A17U.SI',
    'SABANA REIT': 'T82U.SI',
    'VENTURE': 'V03.SI',
    'WILMAR': 'F34.SI',
    'THAI BEVERAGE': 'Y92.SI',
    'FRASER & NEAVE': 'O32.SI',
    'COMFORTDELGRO': 'C52.SI',
    'BHG RETAIL': 'MV4.SI',
    'SINGPOST': 'S08.SI',
    'SPH': 'T39.SI',
    'ST ENGINEERING': 'S63.SI',
    'SBS TRANSIT': 'S61.SI',
    'TECKWAH': 'BKG.SI',
    'CMA CGM': 'CRPU.SI',
    'C2X': 'C2X.SI',
    
    # Crypto-related
    'COINBASE': 'COIN', 'COIN': 'COIN',
    'MICROSTRATEGY': 'MSTR', 'MSTR': 'MSTR',
    'MARATHON DIGITAL': 'MARA', 'MARA': 'MARA',
    'RIOT PLATFORMS': 'RIOT', 'RIOT': 'RIOT',
}

def auto_search_ticker(company_name: str) -> str:
    """Auto-search ticker symbol by company name"""
    import yfinance as yf
    
    company_name = company_name.upper().strip()
    
    # First check popular companies database
    if company_name in POPULAR_COMPANIES:
        ticker = POPULAR_COMPANIES[company_name]
        if ticker != 'Private':
            print(f"Found in database: {company_name} → {ticker}")
            return ticker
        else:
            return f"{company_name} (Private Company)"
    
    # Try direct ticker
    try:
        ticker = yf.Ticker(company_name)
        info = ticker.info
        if info.get('symbol') and info.get('regularMarketPrice'):
            print(f"Found ticker: {company_name} → {info['symbol']}")
            return info['symbol']
    except:
        pass
    
    # Try variations
    variations = [
        company_name.replace(' INC', '').replace(' INC.', ''),
        company_name.replace(' CORP', '').replace(' CORP.', ''),
        company_name.replace(' CO', ''),
        company_name.replace(' LTD', ''),
        company_name.replace(' LLC', ''),
        company_name.replace(' ENERGY', ''),
        company_name.replace(' HOLDINGS', ''),
        company_name.replace(' GROUP', ''),
        company_name.replace(' CORPORATION', ''),
        company_name.replace(' COMPANY', ''),
        company_name.replace(' ', ''),
    ]
    
    for search_term in variations:
        if search_term and search_term != company_name:
            try:
                ticker = yf.Ticker(search_term)
                info = ticker.info
                if info.get('symbol') and info.get('regularMarketPrice'):
                    print(f"Auto-mapped: {company_name} → {info['symbol']}")
                    return info['symbol']
            except:
                pass
    
    return company_name
    """Auto-search ticker symbol by company name"""
    import yfinance as yf
    
    company_name = company_name.upper().strip()
    
    # Try direct ticker first
    try:
        ticker = yf.Ticker(company_name)
        info = ticker.info
        if info.get('symbol') and info.get('regularMarketPrice'):
            print(f"Found ticker: {company_name} → {info['symbol']}")
            return info['symbol']
    except:
        pass
    
    # Try variations
    variations = [
        company_name.replace(' INC', '').replace(' INC.', ''),
        company_name.replace(' CORP', '').replace(' CORP.', ''),
        company_name.replace(' CO', ''),
        company_name.replace(' LTD', ''),
        company_name.replace(' LLC', ''),
        company_name.replace(' ENERGY', ''),
        company_name.replace(' HOLDINGS', ''),
        company_name.replace(' GROUP', ''),
        company_name.replace(' CORPORATION', ''),
        company_name.replace(' COMPANY', ''),
        company_name.replace(' ', ''),  # Remove all spaces
    ]
    
    for search_term in variations:
        if search_term and search_term != company_name:
            try:
                ticker = yf.Ticker(search_term)
                info = ticker.info
                if info.get('symbol') and info.get('regularMarketPrice'):
                    print(f"Auto-mapped: {company_name} → {info['symbol']}")
                    return info['symbol']
            except:
                pass
    
    # Return original if not found
    return company_name


# ============ LANDING PAGE (ROOT) ============
@app.get("/", response_class=HTMLResponse)
async def root():
    """Landing page - MAIN PAGE"""
    landing_path = Path(__file__).parent / "modules" / "landing" / "index.html"
    if landing_path.exists():
        logger.info("Serving landing page")
        return FileResponse(str(landing_path))
    raise HTTPException(status_code=404, detail="Landing page not found")

# ============ ONBOARDING ============
@app.get("/onboarding", response_class=HTMLResponse)
async def onboarding_page():
    """Onboarding page"""
    onboarding_path = Path(__file__).parent / "web" / "onboarding" / "index.html"
    if onboarding_path.exists():
        return FileResponse(str(onboarding_path))
    raise HTTPException(status_code=404, detail="Onboarding page not found")

@app.post("/api/saas/onboard")
async def onboard_tenant(data: OnboardingRequest):
    """Onboard a new tenant"""
    result = admin_api.onboard_tenant(data.dict())
    if not result['success']:
        raise HTTPException(status_code=400, detail=result['error'])
    return result

# ============ CHECKOUT ============
@app.get("/checkout", response_class=HTMLResponse)
async def checkout_page(plan: str = "basic"):
    """Checkout page"""
    checkout_path = Path(__file__).parent / "web" / "checkout.html"
    if checkout_path.exists():
        return FileResponse(str(checkout_path))
    raise HTTPException(status_code=404, detail="Checkout page not found")

@app.get("/checkout/crypto", response_class=HTMLResponse)
async def checkout_crypto(plan: str = "basic"):
    """Crypto checkout page"""
    crypto_path = Path(__file__).parent / "web" / "checkout_crypto.html"
    if crypto_path.exists():
        return FileResponse(str(crypto_path))
    raise HTTPException(status_code=404, detail="Crypto checkout not found")

@app.get("/checkout/singapore", response_class=HTMLResponse)
async def checkout_singapore(plan: str = "basic"):
    """Singapore checkout page"""
    sg_path = Path(__file__).parent / "web" / "checkout_singapore.html"
    if sg_path.exists():
        return FileResponse(str(sg_path))
    raise HTTPException(status_code=404, detail="Singapore checkout not found")

# ============ UPGRADE ============
@app.get("/upgrade", response_class=HTMLResponse)
async def upgrade_page():
    """Upgrade page"""
    upgrade_path = Path(__file__).parent / "web" / "upgrade_page.html"
    if upgrade_path.exists():
        return FileResponse(str(upgrade_path))
    raise HTTPException(status_code=404, detail="Upgrade page not found")

# ============ ADMIN DASHBOARD ============
@app.get("/admin", response_class=HTMLResponse)
async def admin_dashboard():
    """Admin dashboard"""
    admin_path = Path(__file__).parent / "admin" / "dashboard.html"
    if admin_path.exists():
        return FileResponse(str(admin_path))
    raise HTTPException(status_code=404, detail="Admin dashboard not found")

# ============ API DOCS ============
# FastAPI auto-generates /docs and /openapi.json

# ============ PAYMENT APIs ============
@app.post("/api/saas/payment-intent")
async def create_payment_intent(
    plan: str,
    amount: float,
    x_api_key: Optional[str] = Header(None),
):
    """Create payment intent"""
    if not x_api_key:
        raise HTTPException(status_code=401, detail="API key required")
    
    tenant = tenant_manager.get_tenant_by_api_key(x_api_key)
    if not tenant:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    customer_id = payment_processor.setup_customer(
        tenant_id=tenant.id,
        email=tenant.email,
        name=tenant.name,
    )
    
    result = payment_processor.create_payment_intent(
        tenant_id=tenant.id,
        amount=amount,
        payment_type='subscription',
    )
    
    return result

@app.post("/api/saas/activate-subscription")
async def activate_subscription(
    plan: str,
    payment_intent_id: str,
    x_api_key: Optional[str] = Header(None),
):
    """Activate subscription after payment"""
    if not x_api_key:
        raise HTTPException(status_code=401, detail="API key required")
    
    tenant = tenant_manager.get_tenant_by_api_key(x_api_key)
    if not tenant:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    result = admin_api.upgrade_tenant(tenant.id, plan)
    
    if result['success']:
        plan_prices = {'basic': 29, 'pro': 99, 'enterprise': 499}
        payment_processor.create_invoice(
            tenant_id=tenant.id,
            amount=plan_prices.get(plan, 29),
            description=f'{plan.capitalize()} Plan Subscription',
        )
    
    return result

@app.post("/api/saas/crypto-charge")
async def create_crypto_charge(
    plan: str,
    crypto_currency: str,
    x_api_key: Optional[str] = Header(None),
):
    """Create crypto charge"""
    if not x_api_key:
        raise HTTPException(status_code=401, detail="API key required")
    
    tenant = tenant_manager.get_tenant_by_api_key(x_api_key)
    if not tenant:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    plan_prices = {'basic': 29, 'pro': 99, 'enterprise': 499}
    amount = plan_prices.get(plan, 29)
    
    charge = payment_processor.create_crypto_charge(
        tenant_id=tenant.id,
        amount=amount,
        crypto_currency=crypto_currency,
    )
    
    return {
        'success': True,
        'charge': charge,
    }

@app.post("/api/saas/verify-crypto-payment")
async def verify_crypto_payment(
    charge_id: str,
    x_api_key: Optional[str] = Header(None),
):
    """Verify crypto payment"""
    if not x_api_key:
        raise HTTPException(status_code=401, detail="API key required")
    
    tenant = tenant_manager.get_tenant_by_api_key(x_api_key)
    if not tenant:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    verification = payment_processor.verify_crypto_payment(charge_id)
    
    if verification.get('verified'):
        result = admin_api.upgrade_tenant(tenant.id, 'pro')
        return {
            'success': True,
            'verified': True,
            'subscription': result,
        }
    
    return {
        'success': False,
        'verified': False,
        'status': verification.get('status'),
    }

@app.post("/api/saas/invoice")
async def create_invoice(
    amount: float,
    description: str,
    x_api_key: Optional[str] = Header(None),
):
    """Create one-time invoice"""
    if not x_api_key:
        raise HTTPException(status_code=401, detail="API key required")
    
    tenant = tenant_manager.get_tenant_by_api_key(x_api_key)
    if not tenant:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    result = payment_processor.create_invoice(
        tenant_id=tenant.id,
        amount=amount,
        description=description,
    )
    
    return result

@app.get("/api/saas/invoices")
async def get_invoices(x_api_key: Optional[str] = Header(None)):
    """Get tenant invoices"""
    if not x_api_key:
        raise HTTPException(status_code=401, detail="API key required")
    
    tenant = tenant_manager.get_tenant_by_api_key(x_api_key)
    if not tenant:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    invoices = payment_processor.get_invoices(tenant.id)
    
    return {
        'success': True,
        'invoices': [inv.to_dict() for inv in invoices],
    }

# ============ UTILITY APIs ============
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "tenants": len(tenant_manager.tenants),
        "modules": len(module_registry.market_modules) + len(module_registry.feature_modules),
    }

@app.get("/api/saas/usage")
async def get_usage(x_api_key: Optional[str] = Header(None)):
    """Get current usage with upgrade triggers"""
    if not x_api_key:
        raise HTTPException(status_code=401, detail="API key required")
    
    tenant = tenant_manager.get_tenant_by_api_key(x_api_key)
    if not tenant:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    usage = tenant_manager.get_usage_report(tenant.id)
    
    return {
        'success': True,
        'usage': usage,
    }

@app.post("/api/saas/upgrade")
async def upgrade_plan(
    tier: str,
    x_api_key: Optional[str] = Header(None),
):
    """Upgrade subscription"""
    if not x_api_key:
        raise HTTPException(status_code=401, detail="API key required")
    
    tenant = tenant_manager.get_tenant_by_api_key(x_api_key)
    if not tenant:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    result = admin_api.upgrade_tenant(tenant.id, tier)
    return result

@app.get("/api/saas/trial")
async def check_trial(x_api_key: Optional[str] = Header(None)):
    """Check Pro trial status"""
    if not x_api_key:
        raise HTTPException(status_code=401, detail="API key required")
    
    tenant = tenant_manager.get_tenant_by_api_key(x_api_key)
    if not tenant:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    trial_end = tenant.config.get('trial_end_date')
    
    if trial_end:
        from datetime import date
        end_date = date.fromisoformat(trial_end)
        days_left = (end_date - date.today()).days
        
        if days_left >= 0:
            return {
                'success': True,
                'on_trial': True,
                'days_remaining': days_left,
                'trial_end': trial_end,
            }
    
    return {
        'success': True,
        'on_trial': False,
    }

@app.post("/api/saas/start-trial")
async def start_pro_trial(x_api_key: Optional[str] = Header(None)):
    """Start 7-day Pro trial"""
    from saas.free_tier import get_free_tier_manager
    
    if not x_api_key:
        raise HTTPException(status_code=401, detail="API key required")
    
    tenant = tenant_manager.get_tenant_by_api_key(x_api_key)
    if not tenant:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    free_tier = get_free_tier_manager()
    result = free_tier.start_pro_trial(tenant)
    
    return result

@app.get("/api/saas/comparison")
async def get_plan_comparison():
    """Get plan comparison table"""
    from saas.free_tier import get_free_tier_manager
    
    free_tier = get_free_tier_manager()
    return {
        'success': True,
        'comparison': free_tier.get_upgrade_comparison(),
    }

@app.get("/api/saas/modules")
async def list_available_modules(tier: Optional[str] = None):
    """List available modules"""
    result = module_registry.get_available_modules_for_tier(tier) if tier else {
        'markets': module_registry.list_markets(),
        'features': module_registry.list_features(),
    }
    
    return {
        'success': True,
        'modules': result,
    }

# ============ SUCCESS PAGE (Post-Payment) ============
@app.get("/success", response_class=HTMLResponse)
async def success_page(
    plan: Optional[str] = "Pro",
amount: Optional[str] = "99.00",
    transaction_id: Optional[str] = None,
):
    """Payment success page"""
    success_path = Path(__file__).parent / "web" / "success.html"
    if success_path.exists():
        return FileResponse(str(success_path))
    raise HTTPException(status_code=404, detail="Success page not found")


# ============ USER DASHBOARD (Main Tools Page) ============
@app.get("/dashboard", response_class=HTMLResponse)
async def user_dashboard():
    """Main user dashboard with all tools"""
    dashboard_path = Path(__file__).parent / "web" / "dashboard.html"
    if dashboard_path.exists():
        return FileResponse(str(dashboard_path))
    raise HTTPException(status_code=404, detail="Dashboard not found")



# ============ ANALYZE PAGE ============
@app.get("/analyze", response_class=HTMLResponse)
async def analyze_page():
    analyze_path = Path(__file__).parent / "web" / "analyze.html"
    if analyze_path.exists():
        return FileResponse(str(analyze_path))
    return HTMLResponse(content="<h1>Not Found</h1>", status_code=404)

# ============ PORTFOLIO PAGE ============
@app.get("/portfolio", response_class=HTMLResponse)
async def portfolio_page():
    portfolio_path = Path(__file__).parent / "web" / "portfolio.html"
    if portfolio_path.exists():
        return FileResponse(str(portfolio_path))
    return HTMLResponse(content="<h1>Not Found</h1>", status_code=404)

# ============ BACKTEST PAGE ============
@app.get("/backtest", response_class=HTMLResponse)
async def backtest_page():
    backtest_path = Path(__file__).parent / "web" / "backtest.html"
    if backtest_path.exists():
        return FileResponse(str(backtest_path))
    return HTMLResponse(content="<h1>Not Found</h1>", status_code=404)


# ============ BACKTEST API ============
@app.get("/api/backtest")
async def run_backtest(
    symbol: str,
    strategy: str = "sma_crossover",
    start_date: str = "2025-01-01",
    capital: float = 10000
):
    """Run backtest for a trading strategy"""
    import yfinance as yf
    from datetime import datetime, timedelta
    import math
    
    symbol = symbol.upper()
    
    # Get historical data
    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    end_dt = datetime.now()
    
    ticker = yf.Ticker(symbol)
    hist = ticker.history(start=start_dt, end=end_dt)
    
    if hist.empty or len(hist) < 50:
        return {"success": False, "error": "Insufficient data for backtest"}
    
    # Calculate indicators
    close = hist['Close']
    
    # SMA
    sma20 = close.rolling(window=20).mean()
    sma50 = close.rolling(window=50).mean()
    
    # RSI
    delta = close.diff()
    gain = delta.where(delta > 0, 0).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    
    # Initialize backtest
    cash = capital
    shares = 0
    trades = []
    equity_curve = []
    buy_hold_shares = capital / close.iloc[0]
    buy_hold_value = capital
    
    position = None  # None, 'long'
    
    for i in range(50, len(close)):
        date = close.index[i].strftime('%Y-%m-%d')
        price = close.iloc[i]
        current_sma20 = sma20.iloc[i]
        current_sma50 = sma50.iloc[i]
        current_rsi = rsi.iloc[i]
        
        signal = None
        
        if strategy == "sma_crossover":
            # SMA Crossover
            if position is None and current_sma20 > current_sma50:
                signal = "BUY"
            elif position == "long" and current_sma20 < current_sma50:
                signal = "SELL"
                
        elif strategy == "rsi":
            # RSI Strategy
            if position is None and current_rsi < 30:
                signal = "BUY"
            elif position == "long" and current_rsi > 70:
                signal = "SELL"
                
        elif strategy == "dual_indicator":
            # Combined
            if position is None and current_sma20 > current_sma50 and current_rsi < 40:
                signal = "BUY"
            elif position == "long" and (current_sma20 < current_sma50 or current_rsi > 60):
                signal = "SELL"
        
        # Execute trade
        if signal == "BUY" and cash > 0:
            shares = cash / price
            cash = 0
            position = "long"
            trades.append({
                "date": date,
                "action": "BUY",
                "price": price,
                "shares": shares,
                "value": shares * price
            })
        elif signal == "SELL" and shares > 0:
            cash = shares * price
            trades.append({
                "date": date,
                "action": "SELL",
                "price": price,
                "shares": shares,
                "value": cash
            })
            shares = 0
            position = None
        
        # Record equity
        portfolio_value = cash + (shares * price if shares > 0 else 0)
        buy_hold_value = buy_hold_shares * price
        equity_curve.append({
            "date": date,
            "value": portfolio_value,
            "buyHold": buy_hold_value
        })
    
    # Final close if still holding
    if shares > 0:
        final_price = close.iloc[-1]
        cash = shares * final_price
        trades.append({
            "date": close.index[-1].strftime('%Y-%m-%d'),
            "action": "SELL",
            "price": final_price,
            "shares": shares,
            "value": cash
        })
        shares = 0
    
    # Calculate stats
    final_value = cash
    total_return = ((final_value - capital) / capital) * 100
    
    # Max drawdown
    peak = capital
    max_dd = 0
    for eq in equity_curve:
        if eq['value'] > peak:
            peak = eq['value']
        dd = ((peak - eq['value']) / peak) * 100
        if dd > max_dd:
            max_dd = dd
    
    # Win rate
    winning_trades = 0
    for i in range(0, len(trades) - 1, 2):
        if i + 1 < len(trades):
            buy_val = trades[i]['value']
            sell_val = trades[i + 1]['value']
            if sell_val > buy_val:
                winning_trades += 1
    
    total_trades = len(trades) // 2
    win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
    
    # Sharpe ratio (simplified)
    if len(equity_curve) > 1:
        returns = [eq['value'] / equity_curve[0]['value'] - 1 for eq in equity_curve]
        avg_return = sum(returns) / len(returns)
        std_return = math.sqrt(sum((r - avg_return) ** 2 for r in returns) / len(returns))
        sharpe = (avg_return / std_return * math.sqrt(252)) if std_return > 0 else 0
    else:
        sharpe = 0
    
    return {
        "success": True,
        "symbol": symbol,
        "strategy": strategy,
        "stats": {
            "totalReturn": round(total_return, 2),
            "finalValue": round(final_value, 2),
            "totalTrades": len(trades),
            "winRate": round(win_rate, 1),
            "maxDrawdown": round(max_dd, 2),
            "sharpeRatio": round(sharpe, 2)
        },
        "trades": trades,
        "equityCurve": equity_curve
    }


# ============ NEWS PAGE ============
@app.get("/news", response_class=HTMLResponse)
async def news_page():
    news_path = Path(__file__).parent / "web" / "news.html"
    if news_path.exists():
        return FileResponse(str(news_path))
    return HTMLResponse(content="<h1>Not Found</h1>", status_code=404)


# ============ ANALYSIS API ============
@app.post("/api/analysis/analyze")
async def analyze_stock(data: dict):
    """Analyze stock with REAL data and AI"""
    import yfinance as yf
    import pandas as pd
    from datetime import datetime, timedelta
    
    # Ticker symbol mapping
    ticker_map = {
        'GOOGLE': 'GOOGL', 'GOOG': 'GOOGL', 'ALPHABET': 'GOOGL',
        'APPLE': 'AAPL', 'MICROSOFT': 'MSFT', 'MS': 'MSFT',
        'AMAZON': 'AMZN', 'TSLA': 'TSLA', 'TESLA': 'TSLA',
        'META': 'META', 'FACEBOOK': 'META', 'FB': 'META',
        'NVDA': 'NVDA', 'NVIDIA': 'NVDA', 'NETFLIX': 'NFLX',
        'DISNEY': 'DIS', 'INTEL': 'INTC', 'AMD': 'AMD',
        'OCBC': 'O39.SI', 'DBS': 'D05.SI', 'UOB': 'U11.SI',
        'VISTRA': 'VST', 'VISTRA ENERGY': 'VST',
        'STARBUCKS': 'SBUX', 'STARBUCKS COFFEE': 'SBUX',
        'NIKE': 'NKE',
        'COCA-COLA': 'KO', 'COCA COLA': 'KO', 'COKE': 'KO',
        'PEPSI': 'PEP', 'PEPSICO': 'PEP',
        'MCDONALDS': 'MCD', 'MCDONALDS': 'MCD',
        'WALMART': 'WMT',
        'JPMORGAN': 'JPM', 'JPMORGAN CHASE': 'JPM', 'CHASE': 'JPM',
        'BANK OF AMERICA': 'BAC', 'BOA': 'BAC',
        'WELLS FARGO': 'WFC',
        'GOLDMAN SACHS': 'GS',
        'MORGAN STANLEY': 'MS',
        'AMERICAN AIRLINES': 'AAL', 'AMERICAN AIR': 'AAL',
        'DELTA AIR': 'DAL', 'DELTA AIRLINES': 'DAL',
        'UNITED AIRLINES': 'UAL', 'UNITED AIR': 'UAL',
        'FORD': 'F', 'FORD MOTOR': 'F',
        'GENERAL MOTORS': 'GM', 'GM': 'GM',
        'BOEING': 'BA',
        'LOCKHEED MARTIN': 'LMT',
        'RAYTHEON': 'RTX',
        'EXXON': 'XOM', 'EXXON MOBIL': 'XOM',
        'CHEVRON': 'CVX',
        'SHELL': 'SHEL',
        'BP': 'BP',
        'TOTAL ENERGIES': 'TTE',
        'CONOCOPHILLIPS': 'COP',
        'PFIZER': 'PFE',
        'JOHNSON & JOHNSON': 'JNJ', 'J&J': 'JNJ',
        'MODERNA': 'MRNA',
        'PFIZER': 'PFE',
        'NVIDIA': 'NVDA',
        'ADVANCED MICRO DEVICES': 'AMD',
        'QUALCOMM': 'QCOM',
        'TEXAS INSTRUMENTS': 'TXN',
        'ORACLE': 'ORCL',
        'IBM': 'IBM',
        'CISCO': 'CSCO',
        'ADOBE': 'ADBE',
        'SALESFORCE': 'CRM',
        'SHOP': 'SHOP', 'SHOPIFY': 'SHOP',
        'UBER': 'UBER',
        'LYFT': 'LYFT',
        'AIRBNB': 'ABNB',
        'BOOKING': 'BKNG', 'BOOKING.COM': 'BKNG',
        'EXPEDIA': 'EXPE',
    }
    
    stock_codes = data.get('stock_codes', [])
    if not stock_codes:
        raise HTTPException(status_code=400, detail="No stock codes provided")
    
    symbol_input = stock_codes[0].upper()
    
    # First check manual mapping (fastest)
    if symbol_input in ticker_map:
        symbol = ticker_map[symbol_input]
        print(f"Mapped: {symbol_input} → {symbol}")
    else:
        # Auto-search ticker by company name
        symbol = auto_search_ticker(symbol_input)
    
    try:
        # Fetch REAL stock data
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="1mo")
        info = ticker.info
        
        if hist.empty:
            raise Exception("No data available")
        
        # Get current price
        current_price = hist['Close'].iloc[-1]
        
        # Calculate REAL technical indicators
        sma_20 = hist['Close'].rolling(window=20).mean().iloc[-1]
        sma_50 = hist['Close'].rolling(window=50).mean().iloc[-1] if len(hist) >= 50 else current_price
        
        # RSI
        delta = hist['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean().iloc[-1]
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean().iloc[-1]
        rs = gain / loss if loss != 0 else 0
        rsi = 100 - (100 / (1 + rs))
        
        # MACD
        exp1 = hist['Close'].ewm(span=12, adjust=False).mean()
        exp2 = hist['Close'].ewm(span=26, adjust=False).mean()
        macd = exp1 - exp2
        
        # Determine recommendation
        signals = []
        if current_price > sma_20:
            signals.append(1)
        else:
            signals.append(-1)
        
        if rsi < 30:
            signals.append(1)
        elif rsi > 70:
            signals.append(-1)
        else:
            signals.append(0)
        
        if macd.iloc[-1] > macd.iloc[-2]:
            signals.append(1)
        else:
            signals.append(-1)
        
        avg_signal = sum(signals) / len(signals)
        
        if avg_signal > 0.5:
            recommendation = "BUY"
        elif avg_signal < -0.5:
            recommendation = "SELL"
        else:
            recommendation = "HOLD"
        
        # Calculate price targets
        ideal_buy = round(current_price * 0.95, 2)
        stop_loss = round(current_price * 0.92, 2)
        take_profit = round(current_price * 1.10, 2)
        
        # Generate summary
        trend = "bullish" if current_price > sma_20 else "bearish"
        rsi_status = "oversold" if rsi < 30 else "overbought" if rsi > 70 else "neutral"
        
        summary = f"{symbol} is currently trading at ${current_price:.2f}. The trend is {trend} with price {'above' if current_price > sma_20 else 'below'} 20-day SMA (${sma_20:.2f}). RSI is {rsi:.1f} ({rsi_status}). MACD is {'rising' if macd.iloc[-1] > macd.iloc[-2] else 'falling'}."
        
        technical = f"SMA20: ${sma_20:.2f} | SMA50: ${sma_50:.2f} | RSI: {rsi:.1f} | MACD: {macd.iloc[-1]:.2f}"
        
        company_name = info.get('shortName', symbol)
        sector = info.get('sector', 'Unknown')
        
        risks = f"Key risks for {company_name} ({sector}): Market volatility, sector rotation, economic conditions. Current RSI suggests {'potential reversal' if rsi > 70 or rsi < 30 else 'stable momentum'}."
        
        return {
            "success": True,
            "data": {
                "symbol": symbol,
                "company": company_name,
                "recommendation": recommendation,
                "summary": summary,
                "price_targets": {
                    "ideal_buy": ideal_buy,
                    "stop_loss": stop_loss,
                    "take_profit": take_profit,
                    "current_price": round(current_price, 2)
                },
                "technical": technical,
                "indicators": {
                    "sma_20": round(sma_20, 2),
                    "sma_50": round(sma_50, 2),
                    "rsi": round(rsi, 1),
                    "macd": round(macd.iloc[-1], 2)
                },
                "risks": risks
            }
        }
        
    except Exception as e:
        return {
            "success": True,
            "data": {
                "symbol": symbol,
                "recommendation": "HOLD",
                "summary": f"Stock '{symbol}' not found in market data. This may be a private company, delisted stock, or incorrect ticker symbol. Showing estimated analysis.",
                "price_targets": {"ideal_buy": 100, "stop_loss": 92, "take_profit": 110},
                "technical": "Data unavailable",
                "risks": "Unable to assess risks without data"
            }
        }




# ============ REAL-TIME NEWS API ============
@app.get("/api/news/{symbol}")
async def get_news(symbol: str, limit: int = 5):
    """Get real-time news for a stock"""
    try:
        from news_fetcher import get_stock_news
        
        news = get_stock_news(symbol.upper(), limit)
        
        return {
            "success": True,
            "symbol": symbol.upper(),
            "news": news,
            "count": len(news)
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "news": []
        }



@app.get("/news", response_class=HTMLResponse)
async def news_page():
    """Standalone news page"""
    news_path = Path(__file__).parent / "web" / "news.html"
    if news_path.exists():
        return FileResponse(str(news_path))
    return HTMLResponse(content="<h1>News page not found</h1>", status_code=404)



# ============ GLOBAL MARKETS API ============
@app.get("/api/global/indices")
async def get_global_indices():
    """Get world indices"""
    import yfinance as yf
    
    indices = [
        ('^GSPC', 'S&P 500', 'US'),
        ('^DJI', 'Dow Jones', 'US'),
        ('^IXIC', 'NASDAQ', 'US'),
        ('^FTSE', 'FTSE 100', 'UK'),
        ('^N225', 'Nikkei 225', 'Japan'),
        ('^HSI', 'Hang Seng', 'HK'),
        ('^STI', 'Straits Times', 'Singapore'),
        ('^KLSE', 'KLSE', 'Malaysia'),
        ('^BSESN', 'BSE Sensex', 'India'),
    ]
    
    results = []
    for code, name, country in indices:
        try:
            ticker = yf.Ticker(code)
            hist = ticker.history(period='5d')
            if not hist.empty:
                current = hist['Close'].iloc[-1]
                prev = hist['Close'].iloc[0] if len(hist) > 1 else current
                change = ((current - prev) / prev * 100) if prev > 0 else 0
                results.append({
                    'symbol': code,
                    'name': name,
                    'country': country,
                    'price': round(current, 2),
                    'change': round(change, 2)
                })
        except:
            pass
    
    return {"success": True, "indices": results}

@app.get("/api/global/forex")
async def get_forex_rates():
    """Get forex rates"""
    import yfinance as yf
    
    pairs = [
        ('SGD=X', 'USD/SGD'),
        ('MYR=X', 'USD/MYR'),
        ('THB=X', 'USD/THB'),
        ('IDR=X', 'USD/IDR'),
        ('EUR=X', 'EUR/USD'),
        ('GBP=X', 'GBP/USD'),
        ('JPY=X', 'USD/JPY'),
        ('AUD=X', 'AUD/USD'),
        ('HKD=X', 'USD/HKD'),
    ]
    
    results = []
    for code, pair in pairs:
        try:
            ticker = yf.Ticker(code)
            hist = ticker.history(period='5d')
            if not hist.empty:
                current = hist['Close'].iloc[-1]
                prev = hist['Close'].iloc[0] if len(hist) > 1 else current
                
                # Convert to quote currency change
                if '/' in pair:
                    base = pair.split('/')[0]
                    if base == 'USD':
                        change = ((current - prev) / prev * 100) if prev > 0 else 0
                    else:
                        change = -((current - prev) / prev * 100) if prev > 0 else 0
                else:
                    change = ((current - prev) / prev * 100) if prev > 0 else 0
                
                rate = 1/current if current > 0 and '/' in pair and pair.split('/')[1] == 'USD' else current
                
                results.append({
                    'pair': pair,
                    'rate': round(rate, 4),
                    'change': round(change, 2)
                })
        except:
            pass
    
    return {"success": True, "rates": results}

@app.get("/api/global/commodities")
async def get_commodities():
    """Get commodity prices"""
    import yfinance as yf
    
    commodities = [
        ('GC=F', 'Gold'),
        ('SI=F', 'Silver'),
        ('CL=F', 'Crude Oil'),
        ('NG=F', 'Natural Gas'),
        ('HG=F', 'Copper'),
        ('PL=F', 'Platinum'),
    ]
    
    results = []
    for code, name in commodities:
        try:
            ticker = yf.Ticker(code)
            hist = ticker.history(period='5d')
            if not hist.empty:
                price = hist['Close'].iloc[-1]
                results.append({
                    'symbol': code,
                    'name': name,
                    'price': round(price, 2)
                })
        except:
            pass
    
    return {"success": True, "commodities": results}


# ============ CHART API ============
@app.get("/api/chart/{symbol}")
async def get_chart_data(symbol: str, time_range: str = "1M"):
    """Get chart data for a stock"""
    try:
        import yfinance as yf
        from datetime import datetime, timedelta
        
        symbol = symbol.upper()
        
        # Map range to yfinance period
        period_map = {
            '1D': '1d', '1W': '5d', '1M': '1mo',
            '3M': '3mo', '6M': '6mo', '1Y': '1y',
            'ALL': 'max'
        }
        period = period_map.get(time_range, '1mo')
        
        # Fetch data
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period=period)
        
        if hist.empty:
            return {"success": False, "error": "No data available"}
        
        # Calculate SMAs
        hist['SMA20'] = hist['Close'].rolling(window=20).mean()
        hist['SMA50'] = hist['Close'].rolling(window=50).mean()
        
        # Format data
        history = []
        for idx, row in hist.iterrows():
            history.append({
                'date': idx.strftime('%Y-%m-%d'),
                'open': round(row['Open'], 2),
                'high': round(row['High'], 2),
                'low': round(row['Low'], 2),
                'close': round(row['Close'], 2),
                'volume': int(row['Volume']),
                'sma20': round(row['SMA20'], 2) if not pd.isna(row['SMA20']) else None,
                'sma50': round(row['SMA50'], 2) if not pd.isna(row['SMA50']) else None,
            })
        
        # Get current info
        info = ticker.info
        current_price = hist['Close'].iloc[-1]
        prev_close = hist['Close'].iloc[-2] if len(hist) > 1 else current_price
        change = current_price - prev_close
        change_percent = (change / prev_close) * 100
        
        return {
            "success": True,
            "symbol": symbol,
            "company": info.get('shortName', ''),
            "price": round(current_price, 2),
            "change": round(change, 2),
            "changePercent": round(change_percent, 2),
            "history": history
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}



@app.get("/charts", response_class=HTMLResponse)
async def charts_page():
    """Advanced charts page"""
    charts_path = Path(__file__).parent / "web" / "charts.html"
    if charts_path.exists():
        return FileResponse(str(charts_path))
    return HTMLResponse(content="<h1>Charts page not found</h1>", status_code=404)

@app.get("/global", response_class=HTMLResponse)
async def global_page():
    """Global markets page"""
    global_path = Path(__file__).parent / "web" / "global.html"
    if global_path.exists():
        return FileResponse(str(global_path))
    return HTMLResponse(content="<h1>Global markets page not found</h1>", status_code=404)



# ============ PORTFOLIO API ============
@app.get("/api/portfolio")
async def get_portfolio(user_id: str = "demo"):
    """Get portfolio summary"""
    from portfolio_manager import get_portfolio_manager
    
    pm = get_portfolio_manager()
    
    # Update prices
    portfolio = pm.get_portfolio_summary(user_id)
    if 'error' not in portfolio:
        # Fetch current prices
        import yfinance as yf
        prices = {}
        for pos in portfolio.get('positions', []):
            try:
                ticker = yf.Ticker(pos['symbol'])
                prices[pos['symbol']] = ticker.history(period='1d')['Close'].iloc[-1]
            except:
                pass
        
        pm.update_prices(user_id, prices)
        portfolio = pm.get_portfolio_summary(user_id)
    
    return portfolio

@app.post("/api/portfolio/buy")
async def buy_stock(
    symbol: str,
    quantity: float,
    user_id: str = "demo"
):
    """Buy stock"""
    from portfolio_manager import get_portfolio_manager
    
    pm = get_portfolio_manager()
    
    # Get current price
    import yfinance as yf
    try:
        ticker = yf.Ticker(symbol)
        price = ticker.history(period='1d')['Close'].iloc[-1]
    except:
        return {"success": False, "error": "Failed to get price"}
    
    # Execute buy
    success = pm.add_position(user_id, symbol.upper(), quantity, price)
    
    if success:
        return {"success": True, "message": f"Bought {quantity} {symbol} @ ${price:.2f}"}
    else:
        return {"success": False, "error": "Insufficient cash or other error"}

@app.post("/api/portfolio/sell")
async def sell_stock(
    symbol: str,
    quantity: float,
    user_id: str = "demo"
):
    """Sell stock"""
    from portfolio_manager import get_portfolio_manager
    
    pm = get_portfolio_manager()
    
    # Get current price
    import yfinance as yf
    try:
        ticker = yf.Ticker(symbol)
        price = ticker.history(period='1d')['Close'].iloc[-1]
    except:
        return {"success": False, "error": "Failed to get price"}
    
    # Execute sell
    success = pm.remove_position(user_id, symbol.upper(), quantity, price)
    
    if success:
        return {"success": True, "message": f"Sold {quantity} {symbol} @ ${price:.2f}"}
    else:
        return {"success": False, "error": "Insufficient shares or other error"}

@app.get("/api/portfolio/transactions")
async def get_transactions(user_id: str = "demo", limit: int = 50):
    """Get transaction history"""
    from portfolio_manager import get_portfolio_manager
    
    pm = get_portfolio_manager()
    transactions = pm.get_transactions(user_id, limit)
    
    return {
        "success": True,
        "transactions": transactions,
        "count": len(transactions)
    }



@app.get("/portfolio", response_class=HTMLResponse)
async def portfolio_page():
    """Portfolio management page"""
    portfolio_path = Path(__file__).parent / "web" / "portfolio.html"
    if portfolio_path.exists():
        return FileResponse(str(portfolio_path))
    return HTMLResponse(content="<h1>Portfolio page not found</h1>", status_code=404)



# ============ CRYPTO API ============
@app.get("/api/crypto/analyze")
async def analyze_crypto(symbol: str):
    """Analyze cryptocurrency"""
    from crypto_fetcher import get_crypto_price, get_crypto_history
    import math
    
    symbol = symbol.upper()
    
    # Get current price
    price_data = get_crypto_price(symbol)
    
    if not price_data.get('success'):
        return {"success": False, "error": "Crypto not found"}
    
    # Get history for technical analysis
    history = get_crypto_history(symbol, 60)
    
    # Extract crypto data from price_data
    crypto = {
        'symbol': price_data.get('symbol'),
        'name': price_data.get('name'),
        'price': price_data.get('price', 0),
        'change_24h': price_data.get('change_24h', 0),
        'market_cap': price_data.get('market_cap', 0),
    }
    
    # Calculate technical indicators
    tech = {}
    if history and len(history) >= 20:
        closes = [h['close'] for h in history]
        
        # SMA 20
        tech['sma20'] = sum(closes[-20:]) / 20
        
        # SMA 50
        if len(closes) >= 50:
            tech['sma50'] = sum(closes[-50:]) / 50
        else:
            tech['sma50'] = tech['sma20']
        
        # RSI
        deltas = [closes[i+1] - closes[i] for i in range(len(closes)-1)]
        gains = [d if d > 0 else 0 for d in deltas[-14:]]
        losses = [-d if d < 0 else 0 for d in deltas[-14:]]
        avg_gain = sum(gains) / 14
        avg_loss = sum(losses) / 14
        if avg_loss > 0:
            rs = avg_gain / avg_loss
            tech['rsi'] = 100 - (100 / (1 + rs))
        else:
            tech['rsi'] = 100
        
        # Trend
        tech['trend'] = 'bullish' if closes[-1] > tech['sma20'] else 'bearish'
    
    # Generate recommendation
    signals = 0
    if tech.get('rsi', 50) < 30:
        signals += 1
    elif tech.get('rsi', 50) > 70:
        signals -= 1
    
    if tech.get('trend') == 'bullish':
        signals += 1
    else:
        signals -= 1
    
    if tech.get('sma20', 0) > tech.get('sma50', 0):
        signals += 1
    else:
        signals -= 1
    
    if signals > 0:
        recommendation = "BUY"
    elif signals < 0:
        recommendation = "SELL"
    else:
        recommendation = "HOLD"
    
    # Summary
    price = crypto.get('price', 0)
    change = crypto.get('change_24h') or 0
    change_str = f"{change:+.2f}%" if change is not None else "N/A"
    summary = f"{symbol} is currently trading at ${price:,.2f}. "
    
    if change is not None and change != 0:
        summary += f"The 24h change is {change_str}. "
    
    if recommendation == "BUY":
        summary += f"The technical indicators suggest a bullish momentum with RSI at {tech.get('rsi', 0):.1f}. "
    elif recommendation == "SELL":
        summary += f"The technical indicators suggest bearish momentum with RSI at {tech.get('rsi', 0):.1f}. "
    else:
        summary += f"RSI at {tech.get('rsi', 0):.1f} indicates neutral momentum. "
    
    summary += f"Current trend is {tech.get('trend', 'unknown')} based on SMA analysis."
    
    return {
        "success": True,
        "crypto": crypto,
        "technical": tech,
        "recommendation": recommendation,
        "summary": summary
    }

@app.get("/api/crypto/price/{symbol}")
async def get_crypto_price(symbol: str):
    """Get cryptocurrency price"""
    from crypto_fetcher import get_crypto_price
    
    result = get_crypto_price(symbol)
    return result

from fastapi import Query

@app.get("/api/crypto/chart/{symbol}")
async def get_crypto_chart(symbol: str, time_range: str = Query("1M", alias="range")):
    """Get crypto chart data with RSI and volume"""
    from crypto_fetcher import get_crypto_price, get_crypto_history
    
    # Map range to days
    days_map = {'1D': 1, '1W': 7, '1M': 30, '3M': 90, '6M': 180, '1Y': 365, 'ALL': 730}
    days = days_map.get(time_range, 30)
    
    # Get current price
    price_data = get_crypto_price(symbol)
    
    # Get history - request enough for both RSI and the requested range
    history_days = max(days, 60)  # At least 60 for RSI
    full_history = get_crypto_history(symbol, history_days)
    
    if not full_history:
        return {"success": False, "error": "No data available"}
    
    # Calculate RSI using the full available history
    rsi_val = None
    if len(full_history) >= 15:
        prices_for_rsi = [float(h.get('close', 0)) for h in full_history if isinstance(h, dict) and h.get('close')]
        if len(prices_for_rsi) >= 15:
            diffs = []
            for idx in range(len(prices_for_rsi) - 1):
                diffs.append(prices_for_rsi[idx + 1] - prices_for_rsi[idx])
            recent_diffs = diffs[-14:]
            gains = [d if d > 0 else 0 for d in recent_diffs]
            losses = [abs(d) if d < 0 else 0 for d in recent_diffs]
            avg_g = sum(gains) / 14
            avg_l = sum(losses) / 14
            if avg_l > 0:
                rs = avg_g / avg_l
                rsi_val = round(100 - (100 / (1 + rs)), 2)
            else:
                rsi_val = 100
    
    # Now slice to requested range
    if len(full_history) > days:
        history_data = full_history[-days:]
    else:
        history_data = full_history
    
    # Make sure history is a list of dicts
    if not isinstance(history_data, list):
        return {"success": False, "error": "Invalid history data"}
    
    # Calculate SMAs for sliced data
    prices = []
    for h in history_data:
        if isinstance(h, dict) and 'close' in h:
            try:
                prices.append(float(h['close']))
            except:
                pass
    
    if not prices:
        return {"success": False, "error": "No price data"}
    
    # Calculate SMAs
    sma20 = None
    sma50 = None
    if len(prices) >= 20:
        sma20 = sum(prices[-20:]) / 20
        sma20 = round(sma20, 2)
    if len(prices) >= 50:
        sma50 = sum(prices[-50:]) / 50
        sma50 = round(sma50, 2)
    
    # Add indicators to history
    for h in history_data:
        if isinstance(h, dict):
            h['sma20'] = sma20
            h['sma50'] = sma50
            h['rsi'] = rsi_val
    
    current_price = price_data.get('price', prices[-1] if prices else 0)
    prev_price = prices[-2] if len(prices) > 1 else current_price
    change_val = current_price - prev_price
    change_pct = (change_val / prev_price) * 100 if prev_price > 0 else 0
    
    return {
        "success": True,
        "symbol": symbol.upper(),
        "company": price_data.get('name', ''),
        "price": round(current_price, 2),
        "change": round(change_val, 2),
        "changePercent": round(change_pct, 2),
        "rsi": rsi_val,
        "history": history_data
    }

@app.get("/api/crypto/news/{symbol}")
async def get_crypto_news(symbol: str, limit: int = 5):
    """Get crypto news"""
    from crypto_fetcher import get_crypto_news
    
    news = get_crypto_news(symbol, limit)
    
    return {
        "success": True,
        "symbol": symbol.upper(),
        "news": news,
        "count": len(news)
    }

@app.get("/api/crypto/top")
async def get_top_cryptos(limit: int = 20):
    """Get top cryptocurrencies"""
    from crypto_fetcher import get_top_cryptos
    
    cryptos = get_top_cryptos(limit)
    
    return {
        "success": True,
        "cryptos": cryptos,
        "count": len(cryptos)
    }



@app.get("/crypto", response_class=HTMLResponse)
async def crypto_page():
    """Cryptocurrency page"""
    crypto_path = Path(__file__).parent / "web" / "crypto.html"
    if crypto_path.exists():
        return FileResponse(str(crypto_path))
    return HTMLResponse(content="<h1>Crypto page not found</h1>", status_code=404)



# ============ WATCHLIST API ============
@app.get("/api/watchlist")
async def get_watchlists(user_id: str = "demo"):
    """Get all watchlists for user"""
    from watchlist_manager import get_watchlist_manager
    
    wm = get_watchlist_manager()
    watchlists = wm.get_user_watchlists(user_id)
    
    # Create default watchlist if none exist
    if not watchlists:
        wm.create_watchlist(user_id, "My Watchlist")
        watchlists = wm.get_user_watchlists(user_id)
    
    return {
        "success": True,
        "watchlists": [wl.to_dict() for wl in watchlists],
        "count": len(watchlists)
    }

@app.post("/api/watchlist/create")
async def create_watchlist(name: str, user_id: str = "demo"):
    """Create new watchlist"""
    from watchlist_manager import get_watchlist_manager
    
    wm = get_watchlist_manager()
    watchlist = wm.create_watchlist(user_id, name)
    
    return {
        "success": True,
        "watchlist": watchlist.to_dict(),
        "message": f"Created watchlist '{name}'"
    }

@app.delete("/api/watchlist/{watchlist_id}")
async def delete_watchlist(watchlist_id: str, user_id: str = "demo"):
    """Delete watchlist"""
    from watchlist_manager import get_watchlist_manager
    
    wm = get_watchlist_manager()
    success = wm.delete_watchlist(user_id, watchlist_id)
    
    return {
        "success": success,
        "message": "Watchlist deleted" if success else "Failed to delete"
    }

@app.post("/api/watchlist/{watchlist_id}/add")
async def add_to_watchlist(watchlist_id: str, symbol: str, user_id: str = "demo"):
    """Add stock to watchlist"""
    from watchlist_manager import get_watchlist_manager
    
    wm = get_watchlist_manager()
    success = wm.add_stock(user_id, watchlist_id, symbol)
    
    return {
        "success": success,
        "message": f"Added {symbol} to watchlist" if success else "Failed to add"
    }

@app.delete("/api/watchlist/{watchlist_id}/remove/{symbol}")
async def remove_from_watchlist(watchlist_id: str, symbol: str, user_id: str = "demo"):
    """Remove stock from watchlist"""
    from watchlist_manager import get_watchlist_manager
    
    wm = get_watchlist_manager()
    success = wm.remove_stock(user_id, watchlist_id, symbol)
    
    return {
        "success": success,
        "message": f"Removed {symbol} from watchlist" if success else "Failed to remove"
    }

@app.get("/api/watchlist/{watchlist_id}")
async def get_watchlist(watchlist_id: str, user_id: str = "demo"):
    """Get specific watchlist with prices"""
    from watchlist_manager import get_watchlist_manager
    import yfinance as yf
    
    wm = get_watchlist_manager()
    watchlist = wm.get_watchlist(user_id, watchlist_id)
    
    if not watchlist:
        return {"success": False, "error": "Watchlist not found"}
    
    # Fetch current prices
    prices = {}
    for stock in watchlist.stocks:
        try:
            ticker = yf.Ticker(stock.symbol)
            prices[stock.symbol] = ticker.history(period='1d')['Close'].iloc[-1]
        except:
            prices[stock.symbol] = 0
    
    stocks_with_prices = wm.update_stock_prices(watchlist, prices)
    
    return {
        "success": True,
        "watchlist": watchlist.to_dict(),
        "stocks": stocks_with_prices
    }



@app.get("/watchlist", response_class=HTMLResponse)
async def watchlist_page():
    """Watchlist management page"""
    watchlist_path = Path(__file__).parent / "web" / "watchlist.html"
    if watchlist_path.exists():
        return FileResponse(str(watchlist_path))
    return HTMLResponse(content="<h1>Watchlist page not found</h1>", status_code=404)



# ============ PERFORMANCE ANALYTICS API ============
@app.get("/api/analytics/summary")
async def get_analytics_summary(user_id: str = "demo"):
    """Get portfolio analytics summary"""
    from performance_analytics import get_analytics
    from portfolio_manager import get_portfolio_manager
    
    pm = get_portfolio_manager()
    analytics_engine = get_analytics()
    
    # Get portfolio
    portfolio = pm.get_portfolio_summary(user_id)
    
    if 'error' in portfolio:
        return portfolio
    
    # Get analytics summary
    summary = analytics_engine.get_summary(portfolio)
    
    return {
        "success": True,
        "summary": summary
    }

@app.get("/api/analytics/returns")
async def get_portfolio_returns(user_id: str = "demo", days: int = 30):
    """Get portfolio returns over time"""
    from performance_analytics import get_analytics
    from portfolio_manager import get_portfolio_manager
    
    pm = get_portfolio_manager()
    analytics_engine = get_analytics()
    
    # Get portfolio
    portfolio = pm.get_portfolio_summary(user_id)
    
    if 'error' in portfolio:
        return {"success": False, "error": "No portfolio"}
    
    # Calculate returns
    returns = analytics_engine.calculate_portfolio_returns(
        portfolio.get('positions', []),
        days
    )
    
    return {
        "success": True,
        "returns": returns
    }

@app.get("/api/analytics/allocation")
async def get_asset_allocation(user_id: str = "demo"):
    """Get asset allocation by sector"""
    from performance_analytics import get_analytics
    from portfolio_manager import get_portfolio_manager
    
    pm = get_portfolio_manager()
    analytics_engine = get_analytics()
    
    # Get portfolio
    portfolio = pm.get_portfolio_summary(user_id)
    
    if 'error' in portfolio:
        return {"success": False, "error": "No portfolio"}
    
    # Calculate allocation
    allocation = analytics_engine.calculate_asset_allocation(
        portfolio.get('positions', [])
    )
    
    return {
        "success": True,
        "allocation": allocation
    }

@app.get("/api/analytics/performers")
async def get_top_performers(user_id: str = "demo"):
    """Get top and worst performers"""
    from performance_analytics import get_analytics
    from portfolio_manager import get_portfolio_manager
    
    pm = get_portfolio_manager()
    analytics_engine = get_analytics()
    
    # Get portfolio
    portfolio = pm.get_portfolio_summary(user_id)
    
    if 'error' in portfolio:
        return {"success": False, "error": "No portfolio"}
    
    # Calculate performers
    performers = analytics_engine.calculate_top_performers(
        portfolio.get('positions', [])
    )
    
    return {
        "success": True,
        "performers": performers
    }



@app.get("/analytics", response_class=HTMLResponse)
async def analytics_page():
    """Performance analytics page"""
    analytics_path = Path(__file__).parent / "web" / "analytics.html"
    if analytics_path.exists():
        return FileResponse(str(analytics_path))
    return HTMLResponse(content="<h1>Analytics page not found</h1>", status_code=404)

@app.get("/agent", response_class=HTMLResponse)
async def agent_page():
    """Dexter Research Agent page"""
    agent_path = Path(__file__).parent / "web" / "agent.html"
    if agent_path.exists():
        return FileResponse(str(agent_path))
    return HTMLResponse(content="<h1>Agent page not found</h1>", status_code=404)




# ============ AGENT CONFIG API ============
@app.get("/api/agent/config")
async def get_agent_config():
    """Get agent configuration"""
    from agent_config import get_agent_config
    config = get_agent_config()
    return {
        "success": True,
        "config": config.to_dict()
    }

@app.post("/api/agent/config/api")
async def configure_agent_api(api_name: str, enabled: bool, api_key: Optional[str] = None):
    """Configure agent API integration"""
    from agent_config import get_agent_config
    config = get_agent_config()
    config.update_api(api_name, enabled, api_key)
    return {
        "success": True,
        "message": f"Updated {api_name} configuration",
        "config": config.to_dict()
    }


# ============ AUTONOMOUS AGENT API ============
from fastapi.responses import StreamingResponse
import json

@app.get("/api/agent/research")
async def run_research(query: str):
    """Run autonomous research agent - streaming"""
    from autonomous_agent import run_research
    
    async def event_generator():
        for event in run_research(query):
            yield f"data: {json.dumps(event)}\n\n"
    
    return StreamingResponse(event_generator(), media_type="text/event-stream")

@app.post("/api/agent/analyze")
async def autonomous_analyze(query: str, symbol: Optional[str] = None):
    """Autonomous stock analysis"""
    from autonomous_agent import run_research
    
    # Build query
    if symbol:
        full_query = f"Analyze {symbol}: {query}"
    else:
        full_query = query
    
    results = []
    for event in run_research(full_query):
        results.append(event)
    
    return {
        "success": True,
        "events": results,
        "final_result": [e for e in results if e.get('type') == 'result']
    }


if __name__ == "__main__":
    print("\n" + "="*60)
    print("DAILY STOCK ANALYSIS SAAS SERVER")
    print("="*60)
    print("\n🚀 Starting server...")
    print("\n📍 URLs:")
    print("   🏠 Landing Page:    http://localhost:8000/")
    print("   📝 Onboarding:      http://localhost:8000/onboarding")
    print("   💳 Checkout:        http://localhost:8000/checkout")
    print("   📊 Dashboard:       http://localhost:8000/dashboard")
    print("   🔍 Analyze:         http://localhost:8000/analyze")
    print("   📖 API Docs:        http://localhost:8000/docs")
    print("\n" + "="*60 + "\n")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
    )
