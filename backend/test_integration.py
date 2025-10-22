"""
Integration tests for PydanticAI refactored agents
Tests extraction agent, response agent, and full pipeline
"""
import asyncio
import os
import sys
from datetime import datetime

# Set test API key
os.environ['OPENROUTER_API_KEY'] = os.getenv('OPENROUTER_API_KEY', 'test-key-placeholder')

from agents.extraction_agent import get_extraction_agent
from agents.response_agent import get_response_agent
from agents.analytics_agent import get_analytics_agent


# Test email samples
TEST_EMAILS = [
    {
        "name": "High Quality Probiotic Lead",
        "data": {
            "sender_email": "john.smith@healthbrand.com",
            "sender_name": "John Smith",
            "subject": "Contract Manufacturing Inquiry - Probiotic Supplements",
            "body": """Hello,

I'm reaching out on behalf of HealthBrand, an established supplement company looking to expand our probiotic line.

We're interested in manufacturing a high-potency probiotic supplement with the following specifications:
- Product: Multi-strain probiotic (Lactobacillus acidophilus, Bifidobacterium lactis, etc.)
- Format: Delayed-release capsules
- Potency: 50 billion CFU
- Certifications: Organic, Non-GMO, Third-party tested
- Quantity: Initial order of 10,000 units, with potential for 25,000-50,000 units quarterly
- Timeline: Looking to launch in 3 months

We have an existing brand with distribution through Amazon, our website, and select retail partners. Could you provide information on:
1. MOQ and pricing for the quantities mentioned
2. Your experience with probiotic formulations
3. Timeline from formulation to delivery
4. Available certifications

Happy to schedule a call to discuss further.

Best regards,
John Smith
VP of Product Development
HealthBrand Supplements
john.smith@healthbrand.com""",
            "message_id": "test-001",
            "received_at": datetime.utcnow()
        }
    },
    {
        "name": "Medium Quality General Inquiry",
        "data": {
            "sender_email": "sarah@startupco.com",
            "sender_name": "Sarah Johnson",
            "subject": "Supplement Manufacturing Question",
            "body": """Hi,

I'm exploring options for manufacturing supplements for my startup. We're interested in protein powder and possibly some greens powder products.

Do you offer white label services? What are your minimum order quantities?

Thanks,
Sarah""",
            "message_id": "test-002",
            "received_at": datetime.utcnow()
        }
    },
    {
        "name": "Low Quality Vague Inquiry",
        "data": {
            "sender_email": "info@example.com",
            "sender_name": "Someone",
            "subject": "Info",
            "body": """Hello, I need some information about supplements. Can you help?""",
            "message_id": "test-003",
            "received_at": datetime.utcnow()
        }
    }
]


async def test_extraction_agent():
    """Test extraction agent with sample emails"""
    print("\n" + "=" * 70)
    print("TEST 1: EXTRACTION AGENT")
    print("=" * 70)

    extraction_agent = get_extraction_agent()
    results = []

    for test_case in TEST_EMAILS:
        print(f"\n📧 Testing: {test_case['name']}")
        print("-" * 70)

        email_data = test_case['data']

        try:
            # Extract data
            extracted = await extraction_agent.extract_from_email(email_data)

            if extracted:
                print(f"✅ Extraction successful!")
                print(f"   Product Types: {extracted.get('product_type', [])}")
                print(f"   Certifications: {extracted.get('certifications_requested', [])}")
                print(f"   Delivery Format: {extracted.get('delivery_format', [])}")
                print(f"   Quantity: {extracted.get('estimated_quantity', 'N/A')}")
                print(f"   Timeline: {extracted.get('timeline_urgency', 'N/A')}")
                print(f"   Experience: {extracted.get('experience_level', 'N/A')}")
                print(f"   Lead Quality Score: {extracted.get('lead_quality_score', 0)}/10")
                print(f"   Priority: {extracted.get('response_priority', 'N/A')}")
                print(f"   Extraction Confidence: {extracted.get('extraction_confidence', 0):.2f}")

                results.append({
                    'test_case': test_case['name'],
                    'extracted': extracted,
                    'success': True
                })
            else:
                print(f"❌ Extraction returned None")
                results.append({
                    'test_case': test_case['name'],
                    'success': False,
                    'error': 'Returned None'
                })

        except Exception as e:
            print(f"❌ Extraction failed: {e}")
            results.append({
                'test_case': test_case['name'],
                'success': False,
                'error': str(e)
            })

    return results


async def test_response_agent(extraction_results):
    """Test response agent with extracted lead data"""
    print("\n" + "=" * 70)
    print("TEST 2: RESPONSE AGENT")
    print("=" * 70)

    response_agent = get_response_agent()
    results = []

    for result in extraction_results:
        if not result.get('success') or not result.get('extracted'):
            print(f"\n⏭️  Skipping {result['test_case']} (extraction failed)")
            continue

        print(f"\n📝 Testing: {result['test_case']}")
        print("-" * 70)

        lead_data = result['extracted']

        try:
            # Generate response
            draft = await response_agent.generate_response(lead_data)

            if draft:
                print(f"✅ Response generation successful!")
                print(f"   Subject: {draft.get('subject_line', 'N/A')}")
                print(f"   Response Type: {draft.get('response_type', 'N/A')}")
                print(f"   Confidence Score: {draft.get('confidence_score', 0):.1f}/10")
                print(f"   Flags: {draft.get('flags', [])}")
                print(f"   RAG Sources: {len(draft.get('rag_sources', []))} sources")
                print(f"   Draft Length: {len(draft.get('draft_content', ''))} chars")
                print(f"   Status: {draft.get('status', 'N/A')}")

                # Show preview of draft
                content = draft.get('draft_content', '')
                preview = content[:200] + "..." if len(content) > 200 else content
                print(f"\n   Preview:\n   {preview}")

                results.append({
                    'test_case': result['test_case'],
                    'draft': draft,
                    'success': True
                })
            else:
                print(f"❌ Response generation returned None")
                results.append({
                    'test_case': result['test_case'],
                    'success': False,
                    'error': 'Returned None'
                })

        except Exception as e:
            print(f"❌ Response generation failed: {e}")
            results.append({
                'test_case': result['test_case'],
                'success': False,
                'error': str(e)
            })

    return results


async def test_full_pipeline():
    """Test full pipeline: email -> extraction -> response"""
    print("\n" + "=" * 70)
    print("TEST 3: FULL PIPELINE")
    print("=" * 70)

    extraction_agent = get_extraction_agent()
    response_agent = get_response_agent()

    # Use the high-quality test case
    test_email = TEST_EMAILS[0]['data']

    print(f"\n📧 Processing: {TEST_EMAILS[0]['name']}")
    print("-" * 70)

    try:
        # Step 1: Extract
        print("\n[1/2] Extracting data from email...")
        extracted = await extraction_agent.extract_from_email(test_email)

        if not extracted:
            print("❌ Pipeline failed at extraction step")
            return False

        print(f"✅ Extraction complete (score: {extracted.get('lead_quality_score', 0)}/10)")

        # Step 2: Generate response
        print("\n[2/2] Generating response draft...")
        draft = await response_agent.generate_response(extracted)

        if not draft:
            print("❌ Pipeline failed at response generation step")
            return False

        print(f"✅ Response generation complete (confidence: {draft.get('confidence_score', 0):.1f}/10)")

        # Summary
        print("\n" + "=" * 70)
        print("PIPELINE SUMMARY")
        print("=" * 70)
        print(f"Input: Email from {test_email['sender_name']} <{test_email['sender_email']}>")
        print(f"Output: Draft email response ({len(draft.get('draft_content', ''))} chars)")
        print(f"\nExtraction Metrics:")
        print(f"  - Lead Quality: {extracted.get('lead_quality_score', 0)}/10")
        print(f"  - Priority: {extracted.get('response_priority', 'N/A')}")
        print(f"  - Products: {', '.join(extracted.get('product_type', []))}")
        print(f"\nResponse Metrics:")
        print(f"  - Type: {draft.get('response_type', 'N/A')}")
        print(f"  - Confidence: {draft.get('confidence_score', 0):.1f}/10")
        print(f"  - Flags: {', '.join(draft.get('flags', [])) if draft.get('flags') else 'None'}")

        print("\n✅ Full pipeline test PASSED")
        return True

    except Exception as e:
        print(f"\n❌ Pipeline failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_analytics_agent():
    """Test analytics agent (pure Python)"""
    print("\n" + "=" * 70)
    print("TEST 4: ANALYTICS AGENT (Pure Python)")
    print("=" * 70)

    analytics_agent = get_analytics_agent()

    print("\n✅ Analytics agent instantiated successfully")
    print("   This agent uses pure Python (no LLM) for data analytics")
    print("   Functions: track_product_trend, generate_daily_snapshot, etc.")

    return True


async def run_all_tests():
    """Run all integration tests"""
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 15 + "PYDANTICAI INTEGRATION TESTS" + " " * 25 + "║")
    print("╚" + "=" * 68 + "╝")

    # Check API key
    api_key = os.getenv('OPENROUTER_API_KEY', '')
    if api_key == 'test-key-placeholder' or api_key == 'your_openrouter_api_key_here':
        print("\n⚠️  WARNING: Using placeholder API key")
        print("   Real API calls will fail, but structure/fallback testing will work")
    else:
        print(f"\n✅ OpenRouter API key configured ({api_key[:10]}...)")

    all_passed = True

    try:
        # Test 1: Extraction Agent
        extraction_results = await test_extraction_agent()
        extraction_passed = all(r.get('success', False) for r in extraction_results)

        # Test 2: Response Agent
        response_results = await test_response_agent(extraction_results)
        response_passed = all(r.get('success', False) for r in response_results)

        # Test 3: Full Pipeline
        pipeline_passed = await test_full_pipeline()

        # Test 4: Analytics Agent
        analytics_passed = await test_analytics_agent()

        # Final Summary
        print("\n" + "=" * 70)
        print("FINAL TEST SUMMARY")
        print("=" * 70)

        tests = [
            ("Extraction Agent", extraction_passed),
            ("Response Agent", response_passed),
            ("Full Pipeline", pipeline_passed),
            ("Analytics Agent", analytics_passed),
        ]

        for test_name, passed in tests:
            status = "✅ PASSED" if passed else "❌ FAILED"
            print(f"  {test_name:30s} {status}")

        all_passed = all(passed for _, passed in tests)

        if all_passed:
            print("\n🎉 All integration tests PASSED!")
        else:
            print("\n⚠️  Some tests FAILED - review output above")

    except Exception as e:
        print(f"\n❌ Test suite failed with error: {e}")
        import traceback
        traceback.print_exc()
        all_passed = False

    return all_passed


if __name__ == "__main__":
    # Run tests
    result = asyncio.run(run_all_tests())
    sys.exit(0 if result else 1)
