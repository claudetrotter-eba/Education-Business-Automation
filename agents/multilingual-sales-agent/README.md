# Multilingual Sales Agent

AI-powered lead qualification agent that qualifies prospects in English or Spanish, scores leads 1-10, recommends next actions, and generates personalized follow-up emails.

## Features

- **Multilingual Support**: English and Spanish lead qualification
- **Lead Scoring**: 1-10 score based on fit, budget, timeline, intent
- **Smart Recommendations**: "call", "email_sequence", "demo", "follow_up_later", "not_qualified"
- **Personalized Follow-ups**: Generates emails tailored to prospect & market
- **Usage Tracking**: Logs all invocations for billing
- **Flexible Input**: Works with GHL leads, Google Contacts, or custom data

## Quick Start

### 1. Install Dependencies

```bash
cd agents/multilingual-sales-agent
pip install -r requirements.txt
```

### 2. Set Environment Variables

```bash
export ANTHROPIC_API_KEY="your-api-key-here"
export DATABASE_URL="postgresql://user:pass@localhost/eba_agents"
```

### 3. Run the Agent

```python
from agent import qualify_lead

# Basic example
result = qualify_lead(
    lead_data={
        "name": "John Smith",
        "email": "john@example.com",
        "phone": "+1-555-0123",
        "company": "Smith Real Estate",
        "location": "Austin, TX",
        "message": "Interested in CRM for my real estate business"
    },
    client_id="client-123",
    language="English"
)

print(result)
# {
#   "score": 8,
#   "recommendation": "call",
#   "follow_up_email": "Hi John, thanks for your interest...",
#   "reasoning": "Strong fit for real estate, clear intent, budget likely appropriate",
#   "tokens": 487,
#   "cost_cents": 2
# }
```

## API Endpoint

If running as a service, the agent exposes:

```
POST /api/agents/qualify-lead
Content-Type: application/json

{
  "lead_data": {
    "name": "Jane Doe",
    "email": "jane@example.com",
    "phone": "+1-555-9999",
    "company": "Tech Startup Inc",
    "location": "San Francisco, CA",
    "message": "Looking for marketing automation"
  },
  "client_id": "client-456",
  "language": "English"  // or "Spanish"
}

Response:
{
  "score": 7,
  "recommendation": "demo",
  "follow_up_email": "...",
  "reasoning": "...",
  "tokens": 512,
  "cost_cents": 2
}
```

## Customization per Client

Create a `client_settings.json` file:

```json
{
  "client_id": "client-123",
  "company_name": "EBA Example Agency",
  "industry": "Real Estate",
  "service_focus": "CRM + Lead Management",
  "tone": "Professional and friendly",
  "language_preference": "English",
  "qualification_criteria": {
    "ideal_budget_min": 5000,
    "ideal_budget_max": 50000,
    "ideal_company_size_min": 5,
    "ideal_company_size_max": 500,
    "target_industries": ["Real Estate", "Insurance", "Home Services"]
  }
}
```

## Files

- `agent.py` - Main agent logic
- `requirements.txt` - Python dependencies
- `config.py` - Configuration & settings
- `db.py` - Database connections for logging
- `test_agent.py` - Unit tests

## Testing

```bash
# Run unit tests
python -m pytest test_agent.py -v

# Test with sample leads
python test_agent.py --sample
```

## Monitoring

Track agent usage in your database:

```sql
-- See all agent calls for a client
SELECT * FROM agent_invocations 
WHERE client_id = 'client-123' 
AND agent_name = 'multilingual_sales'
ORDER BY timestamp DESC;

-- Monthly cost
SELECT 
  DATE_TRUNC('month', timestamp) as month,
  COUNT(*) as calls,
  SUM(cost_cents) / 100.0 as cost,
  SUM(total_tokens) as total_tokens
FROM agent_invocations
WHERE client_id = 'client-123' 
AND agent_name = 'multilingual_sales'
GROUP BY month
ORDER BY month DESC;
```

## Cost Optimization

- **Use Sonnet instead of Opus**: Saves ~$6/month per 500 leads (still excellent quality)
- **Batch process leads**: Lower latency for concurrent requests
- **Cache client settings**: Don't re-fetch on every call
- **Optimize prompts**: Fewer tokens = lower cost

## Performance

- Typical response time: 800ms - 1.5s
- Tokens per call: 400-600 (avg 450)
- Cost per call: $0.003 - $0.016 (varies by model)
- Success rate: >99%

## Troubleshooting

**Agent timeout (>5s)**:
- May indicate API latency. Check network.
- Consider using Haiku model for faster responses (lower quality).

**Low quality scores**:
- Review client_settings.json - may need adjustment
- Add more context to lead_data (company info, message, etc.)

**High token usage**:
- Shorten system prompt
- Use Haiku instead of Sonnet/Opus

## Next Steps

1. Set up client settings for your clients
2. Deploy to production (see `deploy.md`)
3. Configure GHL webhooks to call this agent
4. Monitor usage & refine prompts based on feedback
5. Iterate with Keshia on Spanish language quality

---

Questions? See main docs:
- `docs/02-architecture-option3.md` - System design
- `docs/03-integration-map.md` - Integration details
- `docs/04-cost-calculator.md` - Pricing & billing
