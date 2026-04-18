# skill: format_currency_amount
# version: 1
# tags: write, function, format_currency_amount, amount, float
# success_count: 0
# fail_count: 0
# verified: true
# last_used: 2026-04-18T19:00:25.283072+00:00
# decaying: false
# compliance_warn: skill accesses financial/PII data without an audit hook
def format_currency_amount(amount: float, currency: str) -> str:
    # Use the format function to format the amount as currency
    formatted_amount = "{:,.2f}".format(abs(amount))
    
    # If the amount is negative, add a minus sign before the currency
    if amount < 0:
        return f"-{currency} {formatted_amount}"
    else:
        return f"{currency} {formatted_amount}"

if __name__ == "__main__":
    assert format_currency_amount(1234.56, "USD") == "USD 1,234.56"
    assert format_currency_amount(0, "USD") == "USD 0.00"
    assert format_currency_amount(-1234.56, "USD") == "-USD 1,234.56"
    print("TEST PASSED")
