# Cost Calculator & Billing Strategy

## Monthly Cost Breakdown (Option 3: Hybrid)

### Scenario: 500 leads/month, 10 clients, 2 agents

```
┌─────────────────────────────────────────────────────────────┐
│              EBA MONTHLY COST STRUCTURE                    │
└─────────────────────────────────────────────────────────────┘

INFRASTRUCTURE COSTS
├─ Cloud Hosting (Heroku/DigitalOcean)
│  ├─ App server (Web dyno or equivalent)      $50-100/mo
│  ├─ PostgreSQL database                      $15-30/mo
│  └─ Redis cache (optional)                   $10-20/mo
│  └─ Subtotal:                               $75-150/mo
│
├─ API Costs
│  ├─ Claude API (Anthropic)
│  │  ├─ Multilingual Sales Agent
│  │  │  └─ 500 leads × 450 tokens/call × $0.015/1M = ~$3.38
│  │  ├─ Market Research Agent (batch)
│  │  │  └─ 5 markets × 2000 tokens × $0.015/1M = ~$0.15
│  │  └─ Subtotal Claude:                    $3-5/mo
│  │
│  ├─ Google APIs (Contacts, Maps, etc.)
│  │  └─ Typically free or <$10/mo            $0-10/mo
│  │
│  └─ Other APIs (News, Trade data, etc.)
│     └─ Depends on usage, typically          $0-20/mo
│  
│  └─ API Subtotal:                          $3-35/mo
│
└─ TOTAL INFRASTRUCTURE:                     $78-185/mo
```

### Revenue & Profit Model

```
CUSTOMER TIERS

TIER 1: GoHighLevel Only ($99/mo)
├─ Access to GHL services
├─ No agents included
└─ Revenue: $99 × 10 clients = $990/mo

TIER 2: GHL + Multilingual Sales Agent ($149/mo)
├─ All GHL features
├─ Multilingual sales qualification
├─ Lead scoring & routing
├─ Personalized follow-ups (English/Spanish)
└─ Revenue: $149 × 8 clients = $1,192/mo

TIER 3: GHL + Sales Agent + Market Research ($249/mo)
├─ All TIER 2 features
├─ Unlimited market research reports
├─ Competitive analysis
├─ Market opportunity assessment
└─ Revenue: $249 × 2 clients = $498/mo

TOTAL MONTHLY REVENUE:                       $2,680/mo

MINUS INFRASTRUCTURE:                        -$130/mo (average)
─────────────────────────────
GROSS PROFIT (after cloud/API):              $2,550/mo
```

### Profitability Analysis

```
Scenario 1: Conservative (Month 1)
├─ 10 clients (mix of tiers)
├─ Revenue: $2,680/mo
├─ Infrastructure: $130/mo
├─ Your time: TBD (depends on support needs)
├─ Gross margin: 95% ($2,550)
└─ Per-client profitability: $255/client/mo

Scenario 2: Growing (Month 6)
├─ 25 clients (more tier 3)
├─ Revenue: $6,500/mo
├─ Infrastructure: $180/mo (slightly more load)
├─ Gross margin: 97% ($6,320)
└─ Per-client profitability: $252/client/mo

Scenario 3: Scaling (Month 12)
├─ 50 clients
├─ Revenue: $13,000/mo
├─ Infrastructure: $250/mo (production-grade)
├─ Gross margin: 98% ($12,750)
└─ Per-client profitability: $255/client/mo
```

---

## Detailed Claude API Cost Breakdown

### Multilingual Sales Agent

**Usage Pattern**: Per lead processed

```
Model: Claude Opus (best for multilingual nuance)
Pricing:
- Input: $15 per 1M tokens
- Output: $75 per 1M tokens

Average Per-Call Usage:
├─ Input (system prompt + lead data): ~300 tokens
├─ Output (qualification + email): ~150 tokens
└─ Total per call: ~450 tokens

Cost Per Call:
├─ Input: 300 tokens × ($15/1M) = $0.0045
├─ Output: 150 tokens × ($75/1M) = $0.01125
└─ Total: $0.01575 per call (~$0.016 rounded)

Monthly Cost (500 calls/mo):
└─ 500 calls × $0.016 = $8/month

Cost Per Client (50 leads/mo):
└─ 50 calls × $0.016 = $0.80/month per client

Profit Per Client (if charged $50/mo for agent):
└─ $50 - $0.80 = $49.20 profit
└─ Margin: 98%
```

**Alternative**: Use Claude Haiku (cheaper, faster)
```
Pricing:
- Input: $0.80 per 1M tokens
- Output: $4 per 1M tokens

Cost Per Call:
├─ Input: 300 tokens × ($0.80/1M) = $0.00024
├─ Output: 150 tokens × ($4/1M) = $0.0006
└─ Total: $0.00084 per call

Monthly Cost (500 calls/mo):
└─ 500 × $0.00084 = $0.42/month

Savings: $8 - $0.42 = $7.58/month
```

**Decision**: Use Sonnet (middle ground) for best ROI
```
Pricing:
- Input: $3 per 1M tokens
- Output: $15 per 1M tokens

Cost Per Call:
├─ Input: 300 tokens × ($3/1M) = $0.0009
├─ Output: 150 tokens × ($15/1M) = $0.00225
└─ Total: $0.00315 per call

Monthly Cost (500 calls/mo):
└─ 500 × $0.00315 = $1.58/month

Profit (vs. Opus):
└─ $8.00 - $1.58 = $6.42/month saved
```

---

### Market Research Agent

**Usage Pattern**: Batch job, on-demand per market

```
Model: Claude Opus (need best reasoning for analysis)
Pricing: Same as above

Per-Research Cost:
├─ Input tokens (market data, competitor info, context): ~1500 tokens
├─ Output tokens (analysis, recommendations, findings): ~500 tokens
├─ Total: ~2000 tokens per research job

Cost Per Research:
├─ Input: 1500 × ($15/1M) = $0.0225
├─ Output: 500 × ($75/1M) = $0.0375
└─ Total: $0.06 per research job

Monthly Cost (5 researches/mo):
└─ 5 × $0.06 = $0.30/month

If Charged to Client (TIER 3 plan):
├─ Unlimited market research
├─ Cost: $0.30 (if 5 researches)
├─ Charged: Included in $249/mo plan
└─ Per-research profit: $49.70
```

---

## Tracking & Billing Implementation

### Database Schema for Billing

```sql
-- Log every agent invocation
CREATE TABLE agent_invocations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  client_id VARCHAR NOT NULL,
  agent_name VARCHAR NOT NULL,  -- 'multilingual_sales', 'market_research', etc.
  timestamp TIMESTAMP DEFAULT NOW(),
  input_tokens INT,
  output_tokens INT,
  total_tokens INT,
  model_used VARCHAR,  -- 'opus', 'sonnet', 'haiku'
  cost_cents INT,  -- Store as cents to avoid floating point issues
  request_data JSONB,  -- Original request (lead data, market, etc.)
  response_data JSONB,  -- Agent output
  status VARCHAR,  -- 'success', 'error', 'timeout'
  
  FOREIGN KEY (client_id) REFERENCES clients(id),
  INDEX (client_id, timestamp),
  INDEX (agent_name, timestamp)
);

-- Monthly billing summary per client
CREATE TABLE monthly_billing (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  client_id VARCHAR NOT NULL,
  month DATE,  -- First day of month
  agent_calls_count INT,
  total_tokens INT,
  agent_cost_cents INT,  -- Claude API cost
  subscription_cost_cents INT,  -- Plan fee ($149, $249, etc.)
  total_cost_cents INT,
  invoice_sent_date TIMESTAMP,
  
  FOREIGN KEY (client_id) REFERENCES clients(id),
  UNIQUE (client_id, month)
);

-- Client subscription/plan info
CREATE TABLE client_subscriptions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  client_id VARCHAR NOT NULL,
  plan VARCHAR,  -- 'tier1', 'tier2', 'tier3'
  plan_cost_cents INT,  -- 9900 = $99.00
  agents_enabled JSONB,  -- ["multilingual_sales", "market_research"]
  started_date TIMESTAMP,
  ends_date TIMESTAMP,
  
  FOREIGN KEY (client_id) REFERENCES clients(id)
);
```

### Billing Calculation Logic

```python
def calculate_monthly_bill(client_id, month):
    """Calculate bill for client for given month"""
    
    # Get subscription plan
    subscription = db.query("""
        SELECT plan, plan_cost_cents
        FROM client_subscriptions
        WHERE client_id = %s AND started_date <= %s AND (ends_date IS NULL OR ends_date > %s)
    """, (client_id, month, month))
    
    base_cost = subscription.plan_cost_cents
    
    # Get agent usage for month
    usage = db.query("""
        SELECT 
            agent_name,
            COUNT(*) as calls,
            SUM(total_tokens) as total_tokens,
            SUM(cost_cents) as agent_cost
        FROM agent_invocations
        WHERE client_id = %s 
        AND DATE_TRUNC('month', timestamp) = %s
        GROUP BY agent_name
    """, (client_id, month))
    
    # Calculate total
    agent_cost = sum(u['agent_cost'] for u in usage)
    
    # Check overages (if any)
    overages_cost = 0
    if subscription.plan == 'tier2':
        max_monthly_calls = 1000  # Example limit
        total_calls = sum(u['calls'] for u in usage)
        if total_calls > max_monthly_calls:
            excess_calls = total_calls - max_monthly_calls
            overages_cost = excess_calls * 10  # $0.10 per excess call in cents
    
    total_cost = base_cost + agent_cost + overages_cost
    
    # Store billing record
    db.insert('monthly_billing', {
        'client_id': client_id,
        'month': month,
        'agent_calls_count': sum(u['calls'] for u in usage),
        'total_tokens': sum(u['total_tokens'] for u in usage),
        'agent_cost_cents': agent_cost,
        'subscription_cost_cents': base_cost,
        'total_cost_cents': total_cost,
    })
    
    return {
        'base_plan': base_cost / 100,
        'agent_usage': agent_cost / 100,
        'overages': overages_cost / 100,
        'total': total_cost / 100,
        'breakdown': usage
    }
```

### Transparent Customer Billing Dashboard

```
Client Dashboard > Billing

This Month (July 2026)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Plan: GHL + Multilingual Sales Agent
Base Plan Fee:                           $149.00

Agent Usage:
├─ Multilingual Sales Qualification
│  ├─ Leads processed: 148
│  ├─ Cost: 148 × $0.016 = $2.37
│  └─ Included in plan (first 1000 calls)
└─ Total Agent Cost:                     $0.00

Total Due:                               $149.00

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Detailed Breakdown:
├─ Jul 1-7:   47 leads → $0.75 (included)
├─ Jul 8-14:  38 leads → $0.61 (included)
├─ Jul 15-21: 41 leads → $0.66 (included)
├─ Jul 22-28: 22 leads → $0.35 (included)
└─ Jul 29-31: 0 leads

Usage Graph: [████████░░] 148/1000 calls (14.8%)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Previous Invoices:
├─ June 2026: $149.00 (paid)
├─ May 2026:  $149.00 (paid)
└─ Apr 2026:  $149.00 (paid)
```

---

## Pricing Tiers (Recommended)

### Option A: Simple (Easiest to manage)

```
TIER 1: GoHighLevel Essentials
├─ Price: $99/month
├─ Includes: All GHL features, basic CRM
└─ No agents

TIER 2: GHL + Smart Sales
├─ Price: $149/month
├─ Includes: TIER 1 + Multilingual Sales Agent
├─ Features:
│  ├─ Lead qualification (English/Spanish)
│  ├─ Lead scoring (1-10)
│  ├─ Auto-generated follow-up emails
│  └─ Up to 1,000 leads/month
└─ Per-lead cost: $0.016 (transparent)

TIER 3: GHL + Smart Sales + Market Research
├─ Price: $249/month
├─ Includes: TIER 2 + Market Research Agent
├─ Features:
│  ├─ All TIER 2 features
│  ├─ Unlimited market research reports
│  ├─ Competitive analysis (per market)
│  ├─ Opportunity assessment
│  └─ Quarterly strategy briefing
└─ Research cost: Included
```

### Option B: Usage-Based (More flexible, harder to track)

```
TIER 1: Pay-as-you-go
├─ Price: $99/month base + $0.016 per lead processed
├─ Good for: Variable volume businesses
└─ Example: 500 leads/mo = $99 + $8 = $107/mo

TIER 2: Monthly Plan
├─ Price: $149/month (includes 1000 leads)
├─ Overage: $0.01 per lead after 1000
├─ Good for: Predictable, growing businesses
└─ Example: 1500 leads/mo = $149 + $5 = $154/mo

TIER 3: Enterprise
├─ Price: Custom (usually $499+/month)
├─ Includes: All agents, custom integrations
├─ Good for: Large agencies, heavy automation
└─ Negotiable based on volume & commitment
```

**Recommendation**: Start with **Option A (Simple)** - easier for you, clearer for customers

---

## Sample Customer Invoice

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                     INVOICE
        Education Business Automation (EBA)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Invoice #: INV-2026-07-001
Date: July 19, 2026
Due Date: August 2, 2026
Client: Acme Real Estate, LLC
Period: July 1-31, 2026

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

DESCRIPTION                          QTY    RATE      AMOUNT
────────────────────────────────────────────────────────────
GHL + Smart Sales Agent             1    $149.00   $149.00
(Includes 1,000 lead qualifications)

Leads Processed (148)              148      Free        $0.00
  - Within monthly allowance

Market Research Reports (0)           0      N/A         N/A

────────────────────────────────────────────────────────────
SUBTOTAL                                              $149.00
Tax (8.25%)                                           $12.29
────────────────────────────────────────────────────────────
TOTAL DUE                                            $161.29

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Payment Method: Auto-billed to card ending in 4242
Status: PAID (2026-07-15)

Questions? Contact: billing@educationbusinessautomation.com
```

---

## Implementation Checklist

- [ ] Set up database tables (agent_invocations, monthly_billing, client_subscriptions)
- [ ] Implement cost logging in Claude agent calls
- [ ] Build billing calculation logic
- [ ] Create customer billing dashboard
- [ ] Set up automated invoicing (Stripe, QuickBooks, etc.)
- [ ] Test billing with first 5 customers
- [ ] Document pricing in sales materials
- [ ] Train Keshia on billing/pricing
- [ ] Set up monthly billing automation

---

See `agents/multilingual-sales-agent/` for working prototype.
See `docs/02-architecture-option3.md` for system design.
