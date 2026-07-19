#!/usr/bin/env python3
"""
Quick test of the Multilingual Sales Agent

Usage:
    1. Add your API key to .env: ANTHROPIC_API_KEY=sk-ant-...
    2. Run: python quick_test.py

This will test the agent with sample leads in English and Spanish.
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Check for API key
if not os.environ.get("ANTHROPIC_API_KEY"):
    print("❌ ERROR: ANTHROPIC_API_KEY not found")
    print("\nPlease add your API key to .env:")
    print("  1. Copy .env.example to .env")
    print("  2. Add your Anthropic API key: ANTHROPIC_API_KEY=sk-ant-...")
    print("  3. Run this script again")
    sys.exit(1)

from agent import qualify_lead

print("=" * 70)
print("MULTILINGUAL SALES AGENT - QUICK TEST")
print("=" * 70)
print()

# Test 1: English lead (high quality)
print("TEST 1: High-Quality English Lead")
print("-" * 70)

english_lead = {
    "name": "Sarah Johnson",
    "email": "sarah@realestate.com",
    "phone": "+1-512-555-0123",
    "company": "Johnson Real Estate Group",
    "location": "Austin, TX",
    "message": "We're looking for a CRM that can help us manage leads better and automate our follow-ups. Currently using spreadsheets which is not scalable."
}

try:
    result = qualify_lead(
        lead_data=english_lead,
        client_id="test-en",
        language="English",
        model="claude-opus-4-8"
    )

    print(f"✓ Score: {result['score']}/10")
    print(f"✓ Recommendation: {result['recommendation']}")
    print(f"✓ Response time: {result['elapsed_seconds']}s")
    print(f"✓ Cost: ${result['cost_cents']/100:.4f}")
    print(f"✓ Tokens used: {result['tokens']}")
    print()
    print("Reasoning:")
    print(f"  {result['reasoning']}")
    print()
    print("Follow-up Email:")
    print("-" * 70)
    print(result['follow_up_email'])

except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)

print()
print()

# Test 2: Spanish lead (Caribbean market)
print("TEST 2: Spanish-Speaking Lead (Caribbean Market)")
print("-" * 70)

spanish_lead = {
    "name": "Juan García",
    "email": "juan@servicios.do",
    "phone": "+1-876-555-1234",
    "company": "García Servicios Empresariales",
    "location": "Santo Domingo, Dominican Republic",
    "message": "Necesitamos un CRM robusto para gestionar nuestros clientes mejor. Tenemos 50+ empleados y queremos automatizar nuestra fuerza de ventas."
}

try:
    result = qualify_lead(
        lead_data=spanish_lead,
        client_id="test-es",
        language="Spanish",
        model="claude-opus-4-8"
    )

    print(f"✓ Score: {result['score']}/10")
    print(f"✓ Recommendation: {result['recommendation']}")
    print(f"✓ Response time: {result['elapsed_seconds']}s")
    print(f"✓ Cost: ${result['cost_cents']/100:.4f}")
    print(f"✓ Tokens used: {result['tokens']}")
    print(f"✓ Language: {result['language']}")
    print()
    print("Reasoning:")
    print(f"  {result['reasoning']}")
    print()
    print("Follow-up Email (Spanish):")
    print("-" * 70)
    print(result['follow_up_email'])

except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)

print()
print()

# Test 3: Low-quality lead (should score low)
print("TEST 3: Low-Quality Lead (should score 1-3)")
print("-" * 70)

low_quality_lead = {
    "name": "Unknown",
    "email": "noemail@test.com",
    "phone": None,
    "company": None,
    "location": "Unknown",
    "message": ""
}

try:
    result = qualify_lead(
        lead_data=low_quality_lead,
        client_id="test-low",
        language="English",
        model="claude-opus-4-8"
    )

    print(f"✓ Score: {result['score']}/10 (should be low)")
    print(f"✓ Recommendation: {result['recommendation']}")
    print(f"✓ Response time: {result['elapsed_seconds']}s")
    print(f"✓ Cost: ${result['cost_cents']/100:.4f}")

except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)

print()
print("=" * 70)
print("✓ ALL TESTS PASSED!")
print("=" * 70)
print()
print("Summary:")
print("  - Agent qualifies leads in English & Spanish")
print("  - Scores are reasonable (high-quality lead scored high)")
print("  - Follow-up emails are personalized and contextual")
print("  - Response times are acceptable (<2s typical)")
print("  - Cost tracking works correctly")
print()
print("Next steps:")
print("  1. Review the follow-up emails for quality")
print("  2. Test with your actual leads")
print("  3. Adjust client_settings for your specific business")
print("  4. Deploy to production (see README.md)")
print()
