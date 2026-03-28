# DSA SaaS Platform

Multi-tenant stock analysis platform with modular subscriptions.

---

## 🚀 Quick Start

### Start SaaS Server
```bash
cd /root/.openclaw/workspace/daily_stock_analysis_v3
python3 saas_server.py
```

**URLs:**
- **Onboarding**: http://localhost:8000/onboarding
- **Admin Dashboard**: http://localhost:8000/admin
- **API Docs**: http://localhost:8000/docs

---

## 🏗️ Architecture

### Modular Subscription Model

Clients can choose:
1. **Subscription Tier** (Free, Basic, Pro, Enterprise)
2. **Markets** (US, CN, HK, SG, JP, CRYPTO)
3. **Features** (AI Analysis, News, Portfolio, Backtest, etc.)

### Components

```
saas/
├── models.py          # Tenant, Subscription, Module models
├── manager.py         # Tenant management
└── modules.py         # Module registry

admin/
├── api.py            # Admin API
└── dashboard.html    # Admin dashboard UI

web/
└── onboarding/
    └── index.html    # Client onboarding UI

saas_server.py        # Main SaaS server
```

---

## 💳 Subscription Tiers

| Tier | Price | Markets | Users | API Calls/Day | Features |
|------|-------|---------|-------|---------------|----------|
| **Free** | $0 | 1 | 1 | 10 | Basic |
| **Basic** | $29/mo | 2 | 3 | 1,000 | AI Analysis, News |
| **Pro** | $99/mo | 6 | 10 | 10,000 | +Backtesting, Risk |
| **Enterprise** | $499/mo | 6 | 100 | 100,000 | All + Priority |

---

## 🌍 Available Markets

| Market | Code | Providers | Icon |
|--------|------|-----------|------|
| US Stocks | US | yfinance | 🇺🇸 |
| China A-Shares | CN | akshare, efinance | 🇨🇳 |
| Hong Kong | HK | yfinance | 🇭🇰 |
| Singapore | SG | yahoo_asia | 🇸🇬 |
| Japan | JP | yahoo_asia | 🇯🇵 |
| Cryptocurrency | CRYPTO | binance, coingecko | ₿ |

---

## 🧩 Available Features

| Feature | Tier | Category |
|---------|------|----------|
| AI Analysis | Basic+ | Analysis |
| News & Sentiment | Basic+ | News |
| Portfolio Tracking | Basic+ | Portfolio |
| Technical Indicators | Basic+ | Analysis |
| Backtesting | Pro+ | Backtest |
| Risk Analysis | Pro+ | Portfolio |

---

## 📖 API Usage

### Onboard New Tenant
```bash
curl -X POST http://localhost:8000/api/saas/onboard \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "email": "john@example.com",
    "company": "Acme Corp",
    "tier": "pro",
    "markets": ["market_us", "market_crypto"]
  }'
```

**Response:**
```json
{
  "success": true,
  "tenant_id": "abc123...",
  "api_key": "dsa_abc123_20260323...",
  "tenant": { ... }
}
```

### Use API Key
```bash
curl http://localhost:8000/api/analysis/analyze \
  -H "X-API-Key: dsa_abc123_20260323..." \
  -d '{ "stock_code": "AAPL" }'
```

### Admin: List Tenants
```bash
curl http://localhost:8000/api/admin/tenants
```

### Admin: Upgrade Tenant
```bash
curl -X POST http://localhost:8000/api/admin/tenants/{id}/upgrade \
  -H "Content-Type: application/json" \
  -d '{ "tier": "enterprise" }'
```

---

## 🎯 Client Onboarding Flow

1. **Visit** `/onboarding`
2. **Enter** account info (name, email, company)
3. **Choose** subscription tier
4. **Select** markets to enable
5. **Receive** API key
6. **Start** using the platform!

---

## 🔧 Admin Dashboard

Access at `/admin`

**Features:**
- View all tenants
- Upgrade/downgrade subscriptions
- Enable/disable modules
- Monitor API usage
- Platform statistics

---

## 📊 Tenant Management

### Create Tenant Programmatically
```python
from saas import TenantManager, SubscriptionTier

manager = TenantManager()

tenant = manager.create_tenant(
    name='Client Name',
    email='client@example.com',
    company='Company',
    tier=SubscriptionTier.PRO,
)

# Enable modules
manager.enable_module(tenant.id, 'market_us', 'US Stocks', 'market')
manager.enable_module(tenant.id, 'market_crypto', 'Crypto', 'market')
manager.enable_module(tenant.id, 'feature_ai', 'AI Analysis', 'feature')

# Get API key
api_key = list(manager.api_keys.keys())[0]
```

### Check API Access
```python
allowed = manager.check_api_access(api_key)
if allowed:
    # Process request
    pass
else:
    # Rate limited or invalid
    pass
```

---

## 🔐 API Key Authentication

All API requests (except onboarding) require `X-API-Key` header.

**Rate Limits:**
- Free: 10 calls/day
- Basic: 1,000 calls/day
- Pro: 10,000 calls/day
- Enterprise: 100,000 calls/day

**429 Response** when limit exceeded.

---

## 📈 Usage Tracking

Each tenant tracks:
- API calls today
- API calls total
- Last API call timestamp
- Enabled modules
- Subscription status

**View Usage:**
```bash
curl http://localhost:8000/api/admin/tenants/{id}/usage
```

---

## 🎨 Customization

### Add New Market
```python
from saas.modules import MarketModule, get_module_registry

registry = get_module_registry()

market = MarketModule(
    id="market_uk",
    name="UK Stocks",
    description="London Stock Exchange",
    market_code="UK",
    providers=["yfinance"],
    icon="🇬🇧",
)

registry.register_market(market)
```

### Add New Feature
```python
from saas.modules import FeatureModule

feature = FeatureModule(
    id="feature_options",
    name="Options Chain",
    description="Options chain data",
    category="analysis",
    required_tier="pro",
)

registry.register_feature(feature)
```

---

## 🚀 Production Deployment

### Environment Variables
```bash
export DATABASE_URL=postgresql://user:pass@localhost/dsa
export REDIS_URL=redis://localhost:6379
export SECRET_KEY=your-secret-key
```

### Run with Production Settings
```bash
uvicorn saas_server:app \
  --host 0.0.0.0 \
  --port 8000 \
  --workers 4 \
  --reload
```

### Docker
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python3", "saas_server.py"]
```

---

## 📝 Files Created

| File | Purpose |
|------|---------|
| `saas/models.py` | Tenant & subscription models |
| `saas/manager.py` | Tenant management |
| `saas/modules.py` | Module registry |
| `admin/api.py` | Admin API |
| `admin/dashboard.html` | Admin UI |
| `web/onboarding/index.html` | Onboarding UI |
| `saas_server.py` | Main server |

**Total**: ~70KB of SaaS infrastructure code

---

## 🎉 Ready to Deploy!

The SaaS platform is fully functional with:
- ✅ Multi-tenant architecture
- ✅ Modular subscriptions
- ✅ Client onboarding
- ✅ Admin dashboard
- ✅ API key authentication
- ✅ Usage tracking
- ✅ Rate limiting

**Start server and onboard your first client!** 🚀
