"""Test email quoting functionality"""
from datetime import datetime
import sys
sys.path.insert(0, '/app')

from tasks.email_tasks import _build_email_with_quote


def test_email_quote_formatting():
    """Test that email quote formatting works correctly"""

    # Test data
    response_body = "Thank you for your inquiry!\n\nWe would be happy to help with your probiotic manufacturing needs."
    original_subject = "Probiotic Manufacturing Inquiry"
    original_body = "Hello,\n\nI'm interested in manufacturing probiotics.\nCan you help?\n\nThanks"
    original_sender_name = "John Doe"
    original_sender_email = "john@example.com"
    original_date = datetime(2025, 10, 25, 14, 30, 0)

    # Build quoted email
    result = _build_email_with_quote(
        response_body=response_body,
        original_subject=original_subject,
        original_body=original_body,
        original_sender_name=original_sender_name,
        original_sender_email=original_sender_email,
        original_date=original_date
    )

    print("=" * 80)
    print("EMAIL QUOTE FORMATTING TEST")
    print("=" * 80)
    print("\nGenerated Email Body:\n")
    print(result)
    print("\n" + "=" * 80)

    # Verify key components
    assert response_body in result, "Response body should be in result"
    assert "On October 25, 2025" in result, "Date should be formatted"
    assert original_sender_name in result, "Sender name should be in result"
    assert original_sender_email in result, "Sender email should be in result"
    assert "> Hello," in result, "Original body should be quoted with >"
    assert "> I'm interested in manufacturing probiotics." in result, "Multi-line quote should work"
    assert "---" in result, "Separator should be present"

    print("\n✅ All assertions passed!")
    print("\nExpected format:")
    print("1. AI response first")
    print("2. --- separator")
    print("3. 'On [date], [sender] <email> wrote:'")
    print("4. Original email with '>' prefix on each line")

    return True


if __name__ == "__main__":
    try:
        test_email_quote_formatting()
        print("\n✅ Email quote formatting test PASSED")
    except AssertionError as e:
        print(f"\n❌ Email quote formatting test FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Email quote formatting test ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
