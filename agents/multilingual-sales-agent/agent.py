"""
Multilingual Sales Agent

Qualifies leads in English or Spanish, scores 1-10, recommends actions,
and generates personalized follow-up emails.
"""

import os
import json
import time
from datetime import datetime
from typing import Optional
import re

from anthropic import Anthropic


class MultilingualSalesAgent:
    def __init__(self, api_key: Optional[str] = None, db_connection=None):
        """Initialize the agent with Claude API"""
        self.client = Anthropic(api_key=api_key or os.environ.get("ANTHROPIC_API_KEY"))
        self.db = db_connection
        self.model = "claude-opus-4-8"  # Can override to 'claude-sonnet-5' or 'claude-haiku-4-5'

    def qualify_lead(
        self,
        lead_data: dict,
        client_id: str,
        language: str = "English",
        client_settings: Optional[dict] = None
    ) -> dict:
        """
        Qualify a lead using Claude agent.

        Args:
            lead_data: Dict with name, email, phone, company, location, message
            client_id: Client identifier for billing tracking
            language: "English" or "Spanish"
            client_settings: Optional dict with industry, tone, qualification criteria

        Returns:
            Dict with score, recommendation, follow_up_email, reasoning, tokens, cost
        """

        start_time = time.time()

        # Build system prompt based on client settings
        system_prompt = self._build_system_prompt(language, client_settings)

        # Build user message with lead data
        user_message = self._build_user_message(lead_data, language)

        # Call Claude
        response = self.client.messages.create(
            model=self.model,
            max_tokens=800,
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_message}
            ]
        )

        elapsed = time.time() - start_time

        # Parse response
        response_text = response.content[0].text
        parsed = self._parse_agent_response(response_text)

        # Calculate cost
        input_tokens = response.usage.input_tokens
        output_tokens = response.usage.output_tokens
        total_tokens = input_tokens + output_tokens
        cost_cents = self._calculate_cost(input_tokens, output_tokens, self.model)

        # Prepare result
        result = {
            "score": parsed.get("score", 5),
            "recommendation": parsed.get("recommendation", "follow_up_later"),
            "follow_up_email": parsed.get("email", ""),
            "reasoning": parsed.get("reasoning", ""),
            "language": language,
            "tokens": total_tokens,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cost_cents": cost_cents,
            "elapsed_seconds": round(elapsed, 2),
            "model": self.model,
        }

        # Log to database (if connected)
        if self.db:
            self._log_to_database(
                client_id=client_id,
                lead_data=lead_data,
                result=result
            )

        return result

    def _build_system_prompt(self, language: str, client_settings: Optional[dict]) -> str:
        """Build system prompt tailored to client"""

        settings = client_settings or {}
        company_name = settings.get("company_name", "EBA")
        industry = settings.get("industry", "General Business")
        service_focus = settings.get("service_focus", "Business Automation & CRM")
        tone = settings.get("tone", "professional and friendly")

        base_prompt = f"""You are an expert sales qualification agent for {company_name}.

Company: {company_name}
Industry Focus: {industry}
Services: {service_focus}
Tone: {tone}

Your role is to qualify incoming leads and provide actionable recommendations.

QUALIFICATION CRITERIA:
1. Fit: Does the prospect's business align with our services?
2. Budget: Can they afford our solutions (typically $5K-50K/year)?
3. Timeline: Are they ready to move forward soon?
4. Intent: How clear is their need/pain point?
5. Authority: Are they a decision-maker?

SCORING:
- 9-10: Excellent fit, hot lead, high priority
- 7-8: Good fit, qualified, contact soon
- 5-6: Medium fit, needs nurturing, follow-up sequence
- 3-4: Poor fit or unclear, low priority
- 1-2: Not qualified, wrong market/industry

RECOMMENDATIONS:
- "call": Contact by phone within 24 hours (for scores 7+)
- "demo": Schedule product demo (for scores 7+)
- "email_sequence": Nurture with email series (for scores 5-6)
- "follow_up_later": Revisit in 3-6 months (for scores 3-4)
- "not_qualified": Not a fit (for scores 1-2)

OUTPUT FORMAT:
You MUST respond in this exact format:

SCORE: [1-10]
RECOMMENDATION: [call/demo/email_sequence/follow_up_later/not_qualified]
REASONING: [2-3 sentences explaining the score]
EMAIL: [Personalized follow-up email (if recommendation is email_sequence)]

All responses must be in {language}."""

        return base_prompt

    def _build_user_message(self, lead_data: dict, language: str) -> str:
        """Build user message with lead information"""

        message = f"""Lead to Qualify:

Name: {lead_data.get('name', 'Unknown')}
Email: {lead_data.get('email', 'Not provided')}
Phone: {lead_data.get('phone', 'Not provided')}
Company: {lead_data.get('company', 'Unknown')}
Location: {lead_data.get('location', 'Unknown')}
Message: {lead_data.get('message', 'No message provided')}

Please qualify this lead and provide your assessment in {language}."""

        return message

    def _parse_agent_response(self, response_text: str) -> dict:
        """Parse Claude's structured response"""

        parsed = {
            "score": 5,
            "recommendation": "follow_up_later",
            "reasoning": "",
            "email": ""
        }

        # Extract SCORE
        score_match = re.search(r'SCORE:\s*(\d+)', response_text, re.IGNORECASE)
        if score_match:
            score = int(score_match.group(1))
            parsed["score"] = min(10, max(1, score))  # Clamp 1-10

        # Extract RECOMMENDATION
        rec_match = re.search(
            r'RECOMMENDATION:\s*(call|demo|email_sequence|follow_up_later|not_qualified)',
            response_text,
            re.IGNORECASE
        )
        if rec_match:
            parsed["recommendation"] = rec_match.group(1).lower()

        # Extract REASONING
        reasoning_match = re.search(r'REASONING:\s*(.+?)(?=EMAIL:|$)', response_text, re.IGNORECASE | re.DOTALL)
        if reasoning_match:
            parsed["reasoning"] = reasoning_match.group(1).strip()[:500]  # Limit to 500 chars

        # Extract EMAIL
        email_match = re.search(r'EMAIL:\s*(.+?)$', response_text, re.IGNORECASE | re.DOTALL)
        if email_match:
            parsed["email"] = email_match.group(1).strip()[:2000]  # Limit to 2000 chars

        return parsed

    def _calculate_cost(self, input_tokens: int, output_tokens: int, model: str) -> int:
        """Calculate cost in cents based on model and tokens"""

        # Pricing per 1M tokens (in dollars)
        pricing = {
            "claude-opus-4-8": {"input": 15, "output": 75},
            "claude-sonnet-5": {"input": 3, "output": 15},
            "claude-haiku-4-5-20251001": {"input": 0.80, "output": 4},
        }

        rates = pricing.get(model, pricing["claude-sonnet-5"])

        # Calculate cost
        input_cost = (input_tokens / 1_000_000) * rates["input"]
        output_cost = (output_tokens / 1_000_000) * rates["output"]
        total_cost = input_cost + output_cost

        # Convert to cents (rounded up)
        cost_cents = max(1, int(total_cost * 100 + 0.5))

        return cost_cents

    def _log_to_database(self, client_id: str, lead_data: dict, result: dict):
        """Log agent invocation to database for billing"""

        try:
            # This would insert into your agent_invocations table
            # Implementation depends on your database setup

            query = """
            INSERT INTO agent_invocations
            (client_id, agent_name, timestamp, input_tokens, output_tokens, total_tokens,
             model_used, cost_cents, request_data, response_data, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """

            self.db.execute(query, (
                client_id,
                'multilingual_sales',
                datetime.now(),
                result['input_tokens'],
                result['output_tokens'],
                result['tokens'],
                result['model'],
                result['cost_cents'],
                json.dumps(lead_data),
                json.dumps({
                    'score': result['score'],
                    'recommendation': result['recommendation'],
                    'reasoning': result['reasoning']
                }),
                'success'
            ))
            self.db.commit()

        except Exception as e:
            print(f"Database logging error: {e}")
            # Don't fail if logging fails
            pass


# Convenience function
def qualify_lead(
    lead_data: dict,
    client_id: str,
    language: str = "English",
    client_settings: Optional[dict] = None,
    model: str = "claude-opus-4-8"
) -> dict:
    """
    Convenience function to qualify a lead.

    Example:
        result = qualify_lead(
            lead_data={
                "name": "John Doe",
                "email": "john@example.com",
                "phone": "+1-555-0123",
                "company": "Acme Inc",
                "location": "Austin, TX",
                "message": "Interested in your CRM solution"
            },
            client_id="client-123",
            language="English"
        )
    """
    agent = MultilingualSalesAgent()
    agent.model = model
    return agent.qualify_lead(lead_data, client_id, language, client_settings)


if __name__ == "__main__":
    # Simple test
    test_lead = {
        "name": "Sarah Johnson",
        "email": "sarah@realestate.com",
        "phone": "+1-512-555-0123",
        "company": "Johnson Real Estate Group",
        "location": "Austin, TX",
        "message": "We're looking for a CRM that can help us manage leads better and automate our follow-ups. Currently using spreadsheets which is not scalable."
    }

    print("Testing Multilingual Sales Agent...")
    print("-" * 60)

    result = qualify_lead(
        lead_data=test_lead,
        client_id="test-client",
        language="English"
    )

    print(f"Score: {result['score']}/10")
    print(f"Recommendation: {result['recommendation']}")
    print(f"Reasoning: {result['reasoning']}")
    print(f"Tokens used: {result['tokens']} (Cost: ${result['cost_cents']/100:.2f})")
    print(f"Response time: {result['elapsed_seconds']}s")
    print("\n" + "=" * 60)
    print("Follow-up Email:")
    print("=" * 60)
    print(result['follow_up_email'])
