# Integration Map: Data Flow & System Connections

## Overview: How Data Moves Through the System

```
┌─────────────────────────────────────────────────────────────────┐
│                    REAL-TIME DATA FLOW                          │
└─────────────────────────────────────────────────────────────────┘

   Lead enters GHL
        │
        ▼
   GHL Workflow triggers
        │
        ▼
   Webhook POST to backend:
   POST https://your-api.com/api/agents/qualify-lead
   {
     "lead_id": "ghl-123",
     "name": "Jane Doe",
     "phone": "+1-555-0123",
     "email": "jane@example.com",
     "source": "ghl_webform"
   }
        │
        ▼
   Backend receives (FastAPI/Express)
        │
        ├─> Check: Is lead in Google Contacts? Sync if not
        ├─> Query: Client's agent settings (language, tone, budget limit)
        └─> Call: Claude Multilingual Sales Agent
                │
                ├─> Input: Lead data + client context
                ├─> Process: Claude analyzes, qualifies, generates follow-up
                └─> Output: Score, recommendation, personalized email
        │
        ▼
   Log to Database
   ├─> agent_invocations (for billing)
   ├─> leads (sync status)
   └─> interactions (audit trail)
        │
        ▼
   Return to GHL via Webhook Response
   {
     "score": 8,
     "recommendation": "call",
     "email": "Hello Jane, thanks for interest...",
     "language": "English",
     "tokens": 450,
     "cost_cents": 1
   }
        │
        ▼
   GHL Workflow acts
   ├─> Move lead to "Hot Pipeline"
   ├─> Send personalized email
   ├─> Tag with score & language
   └─> Notify assigned rep

   TOTAL TIME: ~2 seconds
```

---

## Integration Point #1: GHL → Backend → Claude Agent

**When**: Lead/contact event in GHL (new lead, status change, etc.)

**Webhook Configuration in GHL**:
```
Event: New Lead Created
Webhook URL: https://your-api.com/api/webhooks/ghl/new-lead
Method: POST
Retry: Yes (3 times)
Headers: X-API-Key: YOUR_SECRET_KEY
Timeout: 10s
```

**Backend Receives**:
```python
@app.post("/api/webhooks/ghl/new-lead")
async def handle_ghl_lead(request: Request):
    # Verify webhook is from GHL (check signature)
    ghl_data = await request.json()
    
    # Call Claude agent
    agent_response = await multilingual_sales_agent(
        lead_data=ghl_data,
        client_id=ghl_data['client_id'],
        language=ghl_data.get('language', 'English')
    )
    
    # Log for billing
    log_agent_call(
        client_id=ghl_data['client_id'],
        agent_name='multilingual_sales',
        tokens_used=agent_response['tokens'],
        timestamp=now()
    )
    
    # Return response to GHL
    return agent_response
```

**GHL Receives Response** (and acts on it):
```json
{
  "score": 8,
  "recommendation": "call_tomorrow",
  "action": "tag_lead",
  "tags": ["high_priority", "qualified", "english_speaking"],
  "custom_field_score": 8
}
```

**Data Sync Check**:
- If lead exists in Google Contacts → Update sync status
- If lead only in Google Contacts → Add to GHL first

---

## Integration Point #2: Google Contacts ↔ Backend

**When**: 
- Periodic sync (daily at 2am) 
- Manual sync triggered by admin
- Lead imported from CSV

**Process**:
```
┌─────────────────────────────────────┐
│  Google Contacts API Connection     │
│  (OAuth 2.0 flow, save refresh token)
└────────────────┬────────────────────┘
                 │
    ┌────────────┴────────────┐
    │                         │
    ▼                         ▼
[Read Contacts]        [Write Contacts]
- List all contacts    - Update contact
- Get contact details  - Add to group
- Get groups           - Set custom fields
    │                         │
    └────────────┬────────────┘
                 │
    ┌────────────▼────────────────────┐
    │  Backend Sync Job (Daily)       │
    │                                 │
    │  1. Fetch all Google Contacts   │
    │  2. Compare with DB (leads)     │
    │  3. For new contacts:           │
    │     - Add to EBA database       │
    │     - Check if in GHL already   │
    │     - Mark source: "google"     │
    │  4. For updated contacts:       │
    │     - Update in EBA database    │
    │     - Sync back to GHL          │
    │  5. Log sync status             │
    └────────────┬────────────────────┘
                 │
    ┌────────────▼────────────────────┐
    │  EBA Database (PostgreSQL)      │
    │                                 │
    │  leads table:                   │
    │  - id (UUID)                    │
    │  - ghl_id (nullable)            │
    │  - google_contact_id (nullable) │
    │  - source ('ghl'|'google')      │
    │  - data (JSONB - full info)     │
    │  - last_synced (timestamp)      │
    │  - sync_status ('in_sync'|...)  │
    └─────────────────────────────────┘
```

**Sync Algorithm**:
```python
async def sync_google_contacts():
    # Get all Google Contacts
    google_contacts = await google_contacts_api.list_contacts()
    
    # Get all leads already in our DB
    db_leads = db.query('SELECT * FROM leads')
    
    # Create sync map
    for google_contact in google_contacts:
        # Check if this contact already in DB
        matching_lead = find_by_email_or_phone(
            google_contact['email'],
            google_contact['phone']
        )
        
        if matching_lead:
            # Update existing lead
            db.update('leads', matching_lead['id'], {
                'google_contact_id': google_contact['id'],
                'data': google_contact,
                'last_synced': now(),
                'sync_status': 'in_sync'
            })
        else:
            # Insert new lead
            db.insert('leads', {
                'google_contact_id': google_contact['id'],
                'ghl_id': None,
                'source': 'google_contacts',
                'data': google_contact,
                'last_synced': now(),
                'sync_status': 'new'
            })
            
            # If client wants auto-add to GHL, call GHL API
            if client_settings.auto_import_google_contacts:
                await ghl_api.create_contact(google_contact)
                update_lead_ghl_id(...)
```

---

## Integration Point #3: Backend → Claude API (Anthropic)

**Configuration**:
```python
from anthropic import Anthropic

client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

async def multilingual_sales_agent(lead_data, client_id, language="English"):
    # Get client's agent settings (tone, industry, service focus)
    settings = db.get_client_settings(client_id, 'multilingual_sales')
    
    # Build system prompt (tailored to client)
    system_prompt = f"""
    You are a multilingual sales agent for {settings['company_name']}.
    
    Company Focus: {settings['service_focus']}
    Industry: {settings['industry']}
    Tone: {settings['tone']}
    Language Preference: {language}
    
    Your job:
    1. Qualify leads (fit, budget, timeline)
    2. Score 1-10 (how likely to convert)
    3. Recommend next action (call, email, demo, archive)
    4. Write personalized follow-up message in {language}
    
    Be professional, concise, and action-oriented.
    """
    
    # Build user message (lead data)
    user_message = f"""
    New lead to qualify:
    - Name: {lead_data['name']}
    - Email: {lead_data['email']}
    - Phone: {lead_data['phone']}
    - Company: {lead_data.get('company', 'Unknown')}
    - Message: {lead_data.get('message', '')}
    - Location: {lead_data.get('location', 'Unknown')}
    
    Provide your qualification in this format:
    SCORE: [1-10]
    RECOMMENDATION: [call/email/demo/archive]
    MESSAGE: [Personalized follow-up message in {language}]
    REASONING: [Why this score?]
    """
    
    # Call Claude
    response = client.messages.create(
        model="claude-opus-4-8",  # Use latest for better quality
        max_tokens=500,
        system=system_prompt,
        messages=[
            {"role": "user", "content": user_message}
        ]
    )
    
    # Parse response
    response_text = response.content[0].text
    parsed = parse_agent_response(response_text)
    
    # Log for billing
    token_usage = response.usage.input_tokens + response.usage.output_tokens
    cost_cents = calculate_cost(token_usage, model="opus")
    
    return {
        "score": parsed['score'],
        "recommendation": parsed['recommendation'],
        "email": parsed['message'],
        "reasoning": parsed['reasoning'],
        "tokens": token_usage,
        "cost_cents": cost_cents,
        "model": "claude-opus-4-8"
    }
```

**API Costs**:
- Haiku (cheap, fast): $0.80 per 1M input, $4 per 1M output
- Sonnet (balanced): $3 per 1M input, $15 per 1M output  
- Opus (best, slower): $15 per 1M input, $75 per 1M output

**Recommendation**: Start with Sonnet, move to Opus for multilingual/nuance

---

## Integration Point #4: Backend → Client Dashboard

**Data Available to Clients**:
```
Dashboard: https://client-portal.your-domain.com/dashboard

Sections:
├─ Agent Activity
│  ├─ Leads processed this month: 145
│  ├─ Avg score: 6.8/10
│  ├─ Top recommendation: "Call" (65%)
│  └─ Recent leads (table with scores, recommendations)
│
├─ Billing
│  ├─ Current month usage:
│  │  ├─ Multilingual Sales Agent: 145 calls × $0.01 = $1.45
│  │  └─ Market Research: 3 jobs × $0.03 = $0.09
│  │  └─ Total: $1.54
│  └─ Monthly agent fee: $29.99
│
├─ Agent Configuration
│  ├─ Language preference: English / Spanish
│  ├─ Industry: Real Estate
│  ├─ Tone: Professional, friendly
│  └─ Lead score thresholds
│
└─ Market Research (Premium)
   ├─ Available markets
   ├─ Previous research
   └─ Request new research
```

**API Endpoints**:
```
GET  /api/client/{client_id}/agents/activity
GET  /api/client/{client_id}/agents/activity/{agent_name}
GET  /api/client/{client_id}/billing/usage
GET  /api/client/{client_id}/billing/invoice/{month}
POST /api/client/{client_id}/agents/{agent_name}/configure
GET  /api/client/{client_id}/market-research
POST /api/client/{client_id}/market-research/request
```

---

## Integration Point #5: Market Research Agent → External Data Sources

**When**: Scheduled batch job (e.g., weekly) or admin-triggered

**Data Sources**:
```
Market Research Agent
    │
    ├─> Trade.gov API (US market research)
    ├─> World Bank API (economic indicators, country data)
    ├─> Google Maps API (business density, location analysis)
    ├─> News APIs (market trends, local news)
    ├─> Web scraping (competitor sites, local listings)
    ├─> Government statistics (business registration, regulations)
    └─> LinkedIn (market professionals, company data)

Results compiled into:
{
  "market": "Dominican Republic",
  "research_date": "2026-07-19",
  "executive_summary": "...",
  "market_size": "$X billion",
  "competitor_analysis": [...],
  "regulatory_environment": "...",
  "opportunities": [...],
  "risks": [...],
  "recommendations": [...]
}

Stored in:
database.market_research table
dashboard.market_research section
email notification to team
```

---

## Integration Point #6: Webhook Response Handling

**GHL Receives Agent Response** and acts on it:

**Example**: Lead qualified, score 8/10, recommend "call tomorrow"

```
GHL Workflow Flow:
│
├─ Receive webhook response
│  └─ Parse: score=8, recommendation="call_tomorrow"
│
├─ Conditional Logic:
│  ├─ IF score >= 8:
│  │  └─ Tag: "High Priority"
│  │  └─ Assign to: Top Sales Rep
│  │  └─ Task: "Call tomorrow at 9am"
│  │  └─ Notify: Sales rep via SMS
│  │
│  ├─ ELSE IF score >= 5:
│  │  └─ Tag: "Medium Priority"
│  │  └─ Email follow-up sequence
│  │
│  └─ ELSE:
│     └─ Tag: "Archive"
│     └─ Move to archive pipeline
│
└─ Send personalized email
   └─ Use message from Claude agent
   └─ Personalized greeting + company info
   └─ Call-to-action specific to recommendation
```

---

## Error Handling & Retry Logic

```
Lead comes in → Webhook sent → Backend receives
                    │
                    ├─ SUCCESS → Claude agent runs → Log & respond
                    │
                    └─ FAILURE (Backend down, Claude API error, etc.)
                         │
                         ├─ GHL Retry Logic: 3 attempts, exponential backoff
                         │  ├─ 1st retry: 5 seconds
                         │  ├─ 2nd retry: 60 seconds
                         │  └─ 3rd retry: 600 seconds
                         │
                         └─ If all fail:
                            ├─ Log error to database
                            ├─ Notify EBA team
                            ├─ Add lead to "Manual Review" queue
                            └─ Don't block GHL workflow
```

---

## Performance & Monitoring

**Key Metrics to Track**:
1. **Webhook Response Time**: Target <2 seconds
2. **Claude API Latency**: Typically 500ms-1s
3. **Database Query Time**: Target <100ms
4. **Error Rate**: Target <0.5%
5. **Availability**: Target 99.5%

**Monitoring Setup**:
```python
# Log every step with timing
import time

@app.post("/api/webhooks/ghl/new-lead")
async def handle_ghl_lead(request: Request):
    start = time.time()
    
    # Parse: ~10ms
    ghl_data = await request.json()
    log_timing("parse", time.time() - start)
    
    # Sync check: ~50-100ms
    sync_start = time.time()
    await sync_with_google_contacts_if_needed(ghl_data)
    log_timing("sync", time.time() - sync_start)
    
    # Claude call: ~500-1000ms
    agent_start = time.time()
    agent_response = await multilingual_sales_agent(ghl_data)
    log_timing("agent", time.time() - agent_start)
    
    # Log: ~10-20ms
    log_agent_call(...)
    
    # Total: ~600-1150ms
    total = time.time() - start
    log_timing("total", total)
    
    if total > 5000:  # If over 5 seconds, alert
        send_alert("Slow webhook response", {"lead_id": ghl_data['id']})
    
    return agent_response
```

---

See `docs/04-cost-calculator.md` for pricing & billing.
See `agents/multilingual-sales-agent/` for working code.
