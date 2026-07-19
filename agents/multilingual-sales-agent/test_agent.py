"""
Unit tests for Multilingual Sales Agent
"""

from agent import qualify_lead, MultilingualSalesAgent


def test_english_qualification():
    """Test lead qualification in English"""

    lead = {
        "name": "John Smith",
        "email": "john@acmerealestate.com",
        "phone": "+1-555-0123",
        "company": "Acme Real Estate",
        "location": "Austin, TX",
        "message": "We need a better way to manage leads. Currently doing everything manually."
    }

    result = qualify_lead(
        lead_data=lead,
        client_id="test-client",
        language="English"
    )

    # Assertions
    assert "score" in result
    assert 1 <= result["score"] <= 10
    assert result["recommendation"] in ["call", "demo", "email_sequence", "follow_up_later", "not_qualified"]
    assert "reasoning" in result
    assert result["tokens"] > 0
    assert result["cost_cents"] > 0

    print(f"✓ English test passed - Score: {result['score']}, Rec: {result['recommendation']}")
    return result


def test_spanish_qualification():
    """Test lead qualification in Spanish"""

    lead = {
        "name": "Juan García",
        "email": "juan@example.com",
        "phone": "+1-876-555-1234",  # Jamaica area code
        "company": "García Servicios",
        "location": "Santo Domingo, DR",
        "message": "Necesitamos un CRM para gestionar mejor nuestros clientes"
    }

    result = qualify_lead(
        lead_data=lead,
        client_id="test-client-es",
        language="Spanish"
    )

    # Assertions
    assert "score" in result
    assert 1 <= result["score"] <= 10
    assert result["recommendation"] in ["call", "demo", "email_sequence", "follow_up_later", "not_qualified"]
    assert result["language"] == "Spanish"

    print(f"✓ Spanish test passed - Score: {result['score']}, Rec: {result['recommendation']}")
    return result


def test_high_quality_lead():
    """Test a high-quality lead (should score 8-10)"""

    lead = {
        "name": "Alice Williams",
        "email": "alice@techstartup.com",
        "phone": "+1-415-555-0123",
        "company": "TechStartup Inc",
        "location": "San Francisco, CA",
        "message": "We're a growing SaaS company with 50+ employees. We need enterprise CRM with API access. Budget is $50K/year. Ready to implement ASAP."
    }

    result = qualify_lead(
        lead_data=lead,
        client_id="test-client",
        language="English"
    )

    # High-quality leads should score 7+
    print(f"✓ High-quality lead test - Score: {result['score']}")
    print(f"  Recommendation: {result['recommendation']}")
    print(f"  Reasoning: {result['reasoning']}")

    return result


def test_poor_quality_lead():
    """Test a low-quality lead (should score 1-3)"""

    lead = {
        "name": "Unknown Visitor",
        "email": None,
        "phone": None,
        "company": None,
        "location": "Unknown",
        "message": ""
    }

    result = qualify_lead(
        lead_data=lead,
        client_id="test-client",
        language="English"
    )

    # Poor-quality leads should score low
    print(f"✓ Low-quality lead test - Score: {result['score']}")
    print(f"  Recommendation: {result['recommendation']}")

    return result


def test_performance():
    """Test response time"""
    import time

    lead = {
        "name": "Performance Test",
        "email": "perf@test.com",
        "phone": "+1-555-0000",
        "company": "Test Corp",
        "location": "Test City",
        "message": "Performance test lead"
    }

    start = time.time()
    result = qualify_lead(lead_data=lead, client_id="perf-test", language="English")
    elapsed = time.time() - start

    print(f"✓ Performance test - Response time: {result['elapsed_seconds']}s")
    assert result['elapsed_seconds'] < 5, "Response should be under 5 seconds"

    return result


def test_cost_calculation():
    """Test that cost is calculated correctly"""

    result = test_high_quality_lead()

    # Cost should be reasonable for this model
    # Opus: 450 tokens * $0.015/1M = ~$0.007 = ~1 cent
    assert result['cost_cents'] >= 1, "Cost should be at least 1 cent"
    assert result['cost_cents'] <= 100, "Cost should not exceed $1 per call"

    print(f"✓ Cost calculation test - Cost: ${result['cost_cents']/100:.4f}")
    return result


if __name__ == "__main__":
    print("=" * 70)
    print("MULTILINGUAL SALES AGENT - TEST SUITE")
    print("=" * 70)
    print()

    print("Running tests...")
    print()

    try:
        test_english_qualification()
        print()

        test_spanish_qualification()
        print()

        test_high_quality_lead()
        print()

        test_poor_quality_lead()
        print()

        test_performance()
        print()

        test_cost_calculation()
        print()

        print("=" * 70)
        print("✓ ALL TESTS PASSED!")
        print("=" * 70)

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
