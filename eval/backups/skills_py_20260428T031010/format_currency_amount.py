# skill: format_currency_amount
# version: 1
# tags: write, function, format_currency_amount, amount, float
# success_count: 0
# fail_count: 0
# verified: true
# last_used: 2026-04-28T03:03:34.205284+00:00
# decaying: false
# protocol: general
# rail: general
# audit_required: false
# protocol: general
# rail: general
# audit_required: false
def format_currency_amount(amount: float, currency: str) -> str:
    """
    Formats a currency amount into a string like 'USD 1,234.56'.

    Args:
        amount: The numeric amount.
        currency: The ISO 4217 currency code (e.g., "USD", "EUR").

    Returns:
        A formatted currency string.
    """
    # Use currency_formatter_skill logic here.
    # For demonstration, a simplified implementation is provided.
    # In a real scenario, this would use the actual skill logic.
    if not isinstance(amount, (int, float)):
        raise TypeError("Amount must be a number")
    if not isinstance(currency, str) or len(currency) != 3:
        raise ValueError("Currency must be a 3-letter ISO code")

    formatted_amount = f"{amount:,.2f}"
    return f"{currency} {formatted_amount}"

if __name__ == "__main__":
    # Test cases
    assert format_currency_amount(1234.56, "USD") == "USD 1,234.56", f"Test Case 1 Failed: {format_currency_amount(1234.56, 'USD')}"
    assert format_currency_amount(0.00, "EUR") == "EUR 0.00", f"Test Case 2 Failed: {format_currency_amount(0.00, 'EUR')}"
    assert format_currency_amount(-987.65, "GBP") == "GBP -987.65", f"Test Case 3 Failed: {format_currency_amount(-987.65, 'GBP')}"
    assert format_currency_amount(1000000, "JPY") == "JPY 1,000,000.00", f"Test Case 4 Failed: {format_currency_amount(1000000, 'JPY')}"
    print("TEST PASSED")
