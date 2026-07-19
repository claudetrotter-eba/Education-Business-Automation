# Option 3 (Hybrid) Architecture - Detailed Design

## System Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                         EBA AGENT ECOSYSTEM                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────────┐         ┌──────────────────┐                │
│  │   GoHighLevel    │         │ Google Contacts  │                │
│  │    (GHL)         │         │   (Contacts API) │                │
│  │                  │         │                  │                │
│  │ - CRM/Leads      │         │ - CSV imports    │                │
│  │ - Workflows      │         │ - Contact data   │                │
│  │ - Calendar       │         │ - Sync via tool  │                │
│  └────────┬─────────┘         └────────┬─────────┘                │
│           │                            │                          │
│           │ REST API                   │ Contacts API             │
│           │ Webhooks                   │                          │
│           ▼                            ▼                          │
│  ┌────────────────────────────────────────────────┐               │
│  │     EBA Agent Backend (Your Infrastructure)    │               │
│  │                                                │               │
│  │  ┌──────────────────────────────────────────┐ │               │
│  │  │  Agent Orchestration Layer               │ │               │
│  │  │  (FastAPI / Express.js)                  │ │               │
│  │  └──────────────────────────────────────────┘ │               │
│  │           │                                   │               │
│  │      ┌────┼────┬──────────────┐              │               │
│  │      ▼    ▼    ▼              ▼              │               │
│  │  ┌────────────────────────────────────────┐ │               │
│  │  │  GHL Agents (Lightweight)               │ │               │
│  │  │  - Sales qualification                  │ │               │
│  │  │  - Appointment scheduling               │ │               │
│  │  │  - Lead scoring                         │ │               │
│  │  │  (Respond to GHL workflows via webhook) │ │               │
│  │  └────────────────────────────────────────┘ │               │
│  │                                              │               │
│  │  ┌────────────────────────────────────────┐ │               │
│  │  │  External Agents (Heavy Lifting)        │ │               │
│  │  │  - Multilingual Sales Agent             │ │               │
│  │  │  - Market Research Agent                │ │               │
│  │  │  - Content Generator                    │ │               │
│  │  │  (Claude 3.5 Sonnet)                    │ │               │
│  │  └────────────────────────────────────────┘ │               │
│  │                                              │               │
│  │  ┌────────────────────────────────────────┐ │               │
│  │  │  Data Layer                             │ │               │
│  │  │  - PostgreSQL (agent logs, interactions)│ │               │
│  │  │  - Redis (caching, rate limiting)       │ │               │
│  │  │  - Agent usage tracking (for billing)   │ │               │
│  │  └────────────────────────────────────────┘ │               │
│  │                                              │               │
│  │  ┌────────────────────────────────────────┐ │               │
│  │  │  External Integrations                  │ │               │
│  │  │  - Web scraping (market research)       │ │               │
│  │  │  - Translation APIs (Spanish support)   │ │               │
│  │  │  - Public data sources                  │ │               │
│  │  └────────────────────────────────────────┘ │               │
│  │                                              │               │
│  └──────────────────┬──────────────────────────┘               │
│                     │                                          │
│                     │ REST API                                │
│                     │ Webhooks                                │
│                     │                                          │
│  ┌──────────────────┴──────────────────┐                      │
│  │    EBA Client Dashboard             │                      │
│  │  (Web App / Mobile)                 │                      │
│  │                                     │                      │
│  │ - View agent activity               │                      │
│  │ - Agent usage & billing             │                      │
│  │ - Market research results           │                      │
│  │ - Lead conversion metrics           │                      │
│  └─────────────────────────────────────┘                      │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

---

## Component Breakdown

### 1. **GHL-Embedded Agents** (Option 1 style, but feeding into hybrid system)

**Purpose**: Handle real-time client interactions that need instant response

**Examples**:
- Incoming lead → Sales qualification agent → Suggest next step (call, email, SMS)
- Client books appointment → Onboarding agent → Send welcome sequence
- New contact imported → Scoring agent → Assign priority

**Implementation**:
- GHL Workflow triggers webhook to your backend
- Backend runs lightweight Claude agent
- Agent returns structured response (lead score, next action, etc.)
- Workflow acts on response (move lead to pipeline, send email, etc.)

**Latency**: <1 second (webhook + agent call + response)

**Cost**: Pay per webhook call (your infrastructure costs)

---

### 2. **External "Heavy Lifting" Agents** (Option 2 style)

**Purpose**: Complex workflows that need external data, custom logic, async processing

**Examples**:
- **Multilingual Sales Agent**: 
  - Receives lead from GHL or Google Contacts
  - Qualifies in English OR Spanish (Keshia's process)
  - Customizes pitch based on location/market
  - Writes personalized follow-up email
  - Returns result to GHL via webhook
  
- **Market Research Agent**:
  - Research Caribbean markets (DR, Jamaica, Bahamas, etc.)
  - Scrape competitor sites, economic data, local news
  - Identify opportunities for EBA services
  - Generate market report with recommendations
  - Store results in database for team review

**Implementation**:
- Triggered by GHL webhook OR scheduled batch job
- Runs as async task (doesn't block client)
- Has access to external APIs, databases, web
- Stores results in your database
- Returns summary to GHL (optional) or notifies team via email/Slack

**Latency**: 30 seconds - 5 minutes (depends on complexity)

**Cost**: Pay per Claude API call + infrastructure

---

### 3. **Data Layer** (Essential for hybrid approach)

**Purpose**: Track agent usage for billing, cache data, maintain sync between GHL/Google Contacts

**Components**:

**PostgreSQL Database** (`eba_agents` schema):
```sql
-- Track agent invocations for billing
CREATE TABLE agent_invocations (
  id UUID PRIMARY KEY,
  client_id VARCHAR,
  agent_name VARCHAR,
  timestamp TIMESTAMP,
  tokens_used INT,
  result TEXT,
  cost_cents INT  -- For billing
);

-- Track lead interactions across systems
CREATE TABLE leads (
  id UUID PRIMARY KEY,
  ghl_id VARCHAR,        -- From GHL
  google_contacts_id VARCHAR,  -- From Google Contacts
  source VARCHAR,        -- "ghl" or "google_contacts"
  data JSONB,           -- Full lead data
  last_synced TIMESTAMP
);

-- Track market research findings
CREATE TABLE market_research (
  id UUID PRIMARY KEY,
  market VARCHAR,
  research_date TIMESTAMP,
  findings JSONB,
  created_by_agent BOOLEAN
);

-- Track agent configurations per client
CREATE TABLE client_agent_settings (
  id UUID PRIMARY KEY,
  client_id VARCHAR,
  agent_name VARCHAR,
  enabled BOOLEAN,
  settings JSONB,  -- Language, tone, industry, etc.
  monthly_quota INT
);
```

**Redis Cache**:
- Rate limiting (client per-agent usage)
- Session data (current conversation context)
- Market research cache (don't re-scrape same market)

---

## Data Flow Examples

### Example 1: Multilingual Sales Qualification (Real-time)

```
1. Lead enters GHL workflow
   └─> Webhook fires to your backend: POST /api/agents/qualify-lead
       {
         "lead_id": "123",
         "name": "Juan García",
         "phone": "+1-876-555-1234",  // Jamaica number
         "email": "juan@example.com",
         "ghl_data": {...}
       }

2. Backend receives webhook
   └─> Checks: Is this lead in Google Contacts? (sync if needed)
   └─> Queries: Client's agent settings (language, tone, industry)
   └─> Calls: Claude Agent with lead data + context

3. Claude Agent runs (External)
   └─> Analyzes lead (location: Jamaica → Spanish language support)
   └─> Qualifies: Fit for services? Budget? Timeline?
   └─> Generates: Personalized follow-up email in Spanish
   └─> Returns: {
         "score": 8/10,
         "recommendation": "call",
         "follow_up_email": "Hola Juan, gracias por tu interés...",
         "language": "Spanish",
         "tokens_used": 450
       }

4. Backend processes response
   └─> Logs interaction: agent_invocations table (for billing)
   └─> Updates lead: ghl/google_contacts sync
   └─> Webhook returns to GHL:
       {
         "score": 8,
         "action": "send_email",
         "email_body": "Hola Juan...",
         "language": "Spanish"
       }

5. GHL Workflow acts
   └─> Moves lead to "High Priority"
   └─> Sends personalized email (language-aware)
   └─> Tags lead with score
   └─> Notifies Keshia (Spanish-speaking rep)

6. Billing
   └─> Agent invocation logged: 1 call, 450 tokens (~$0.01)
   └─> Tracked to client for monthly bill
```

**Total latency**: ~2 seconds (acceptable for automated workflow)

---

### Example 2: Market Research for Caribbean Expansion (Async)

```
1. Keshia (or admin) triggers market research
   └─> POST /api/agents/research-market
       {
         "market": "Dominican Republic",
         "focus": "small business automation",
         "language": "Spanish"
       }

2. Backend queues async job
   └─> Returns immediately: "Job ID: research-123, check back later"

3. Market Research Agent runs (External)
   └─> Queries:
       - Economic data (trade, GDP growth, business registration)
       - Competitor analysis (GoHighLevel resellers in DR)
       - Local regulations (business licensing, tax, data privacy)
       - Local news/trends (startup activity, SMB growth)
       - Government resources (business support programs)
   └─> Generates findings:
       {
         "market": "Dominican Republic",
         "opportunity_score": 8/10,
         "market_size": "~500K active SMBs",
         "competitor_count": 3-5 major resellers,
         "regulatory_barriers": "Low",
         "language_advantage": "High (Spanish-primary market)",
         "recommendations": [
           "Partner with local accounting firms",
           "Focus on tourism/hospitality sector",
           "Offer Spanish-language 24/7 support"
         ],
         "confidence": "Medium-High"
       }

4. Results stored in database
   └─> market_research table
   └─> Accessible via dashboard

5. Team notified
   └─> Slack message: "Market research for DR complete, review results"
   └─> Available in client portal for review

6. Billing
   └─> Agent call logged: 1 job, 2000 tokens (~$0.03)
   └─> Charged as "Market Research" premium service
   └─> Monthly bill shows: "Market research (3 markets): $0.09"
```

**Total time**: ~30 seconds (runs in background, doesn't block)

---

## Infrastructure Requirements

### Cloud Hosting (Pick One)

**Option A: Heroku (Easiest for self-taught)**
- Pros: Simple git push deployment, auto-scaling, managed DB
- Cost: $50-100/month (for low usage)
- Best for: Learning, MVP, rapid iteration
- PostgreSQL add-on: $15-30/month

**Option B: AWS (Most flexible)**
- Pros: Complete control, cheaper at scale, EC2 + RDS + Lambda
- Cost: $200-300/month (for production-ready setup)
- Best for: Long-term, scaling, cost optimization
- Learning curve: Steeper

**Option C: DigitalOcean (Good middle ground)**
- Pros: Simple, affordable, good docs, App Platform
- Cost: $100-150/month
- Best for: Small team, moderate scale, learning
- PostgreSQL: Built-in, $15-30/month

**Recommendation for EBA**: Start with **Heroku** or **DigitalOcean**, migrate to AWS if you need to cut costs at scale.

---

### Required Services

1. **Claude API** (Anthropic)
   - Cost: Pay per token (~$0.003 per 1K tokens for Haiku, $0.15 for Opus)
   - For multilingual agent: ~$100-150/month (500-1000 agents × 450 tokens)
   - For market research: ~$50-100/month (heavy batching)

2. **Google Contacts API**
   - Cost: Free (within quota)
   - Used for: Syncing Google Contacts ↔ EBA backend

3. **Google Maps/Places API** (optional, for market research)
   - Cost: $0.015-0.03 per query
   - Used for: Location data, business info

4. **Translation API** (Google Cloud or DeepL)
   - Cost: $0.01-0.02 per 100K characters
   - Used for: Spanish/English translation (if Claude doesn't handle it)
   - Recommendation: Claude handles most translation; only use API for bulk processing

---

## Security Considerations

1. **API Key Management**
   - Store Claude API key in environment variables
   - Rotate quarterly
   - Use separate keys for dev/prod

2. **Data Privacy**
   - Encrypt client data in transit (HTTPS) and at rest (DB encryption)
   - GDPR/CCPA compliance for Caribbean expansion (check local regulations)
   - Don't store unnecessary PII (anonymize for market research)

3. **Rate Limiting**
   - Limit agents per client per minute (prevent abuse)
   - Implement quota per client (for billing enforcement)

4. **Access Control**
   - Only EBA team can trigger market research
   - Clients can view their own agent activity
   - Webhook signatures (verify GHL → backend authenticity)

---

## Deployment Steps (High Level)

1. **Infrastructure**: Set up hosting + PostgreSQL + Redis
2. **Backend API**: Deploy FastAPI or Express.js server
3. **Agent integration**: Connect Claude API, test agents
4. **GHL webhooks**: Configure workflows to call your backend
5. **Google Contacts sync**: Set up periodic sync job
6. **Dashboard**: Build or integrate client portal
7. **Testing**: Test bilingual workflows, market research
8. **Go-live**: Roll out to first clients, monitor

---

## Success Metrics

- **Sales Agent**: Conversion rate improvement (+X% qualified leads)
- **Market Research**: Accuracy of recommendations (compare agent findings vs. manual research)
- **Billing**: Clean tracking, zero billing disputes
- **Performance**: Agent response time <2s for real-time, <30s for async
- **Cost**: Track Claude API spend, optimize prompts for fewer tokens

---

See `docs/03-integration-map.md` for data flow diagrams.
See `docs/04-cost-calculator.md` for pricing details.
See `agents/multilingual-sales-agent/` for working prototype.
