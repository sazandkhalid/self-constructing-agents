# skill: get_eur_to_gbp_exchange_rate
# version: 1
# tags: cross, border, payment, from, german
# success_count: 0
# fail_count: 0
# verified: true
# last_used: 2026-04-29T22:19:27.794574+00:00
# decaying: false
# protocol: general
# rail: general
# audit_required: false
# protocol: general
# rail: general
# audit_required: false
def get_eur_to_gbp_exchange_rate() -> float:
    """
    Fetches the current EUR to GBP exchange rate.

    Returns:
        float: The exchange rate from EUR to GBP.
               Returns None if the rate cannot be fetched.
    """
    # This function is designed to be called within an agent environment
    # where `fetch_exchange_rate` is available as a tool.
    # For standalone Python execution, it requires the tool to be mocked or
    # an actual API call to be implemented.
    try:
        exchange_data = fetch_exchange_rate(currency_from="EUR", currency_to="GBP")
        return exchange_data.get('rate')
    except Exception as e:
        print(f"Error fetching exchange rate: {e}")
        return None

if __name__ == "__main__":
    # Mocking the tool call for local testing purposes.
    # In the actual agent environment, fetch_exchange_rate would be provided.
    _original_fetch_exchange_rate = globals().get('fetch_exchange_rate')
    def mock_fetch_exchange_rate(currency_from, currency_to):
        if currency_from == "EUR" and currency_to == "GBP":
            return {"currency_from": "EUR", "currency_to": "GBP", "rate": 0.8550}
        return {"error": "Invalid currencies", "rate": None}
    globals()['fetch_exchange_rate'] = mock_fetch_exchange_rate

    # Test case 1: Successful fetch
    rate = get_eur_to_gbp_exchange_rate()
    assert rate == 0.8550, f"Test 1 failed: Expected 0.8550, got {rate}"

    # Test case 2: Error scenario (e.g., invalid currency, tool failure)
    def mock_fetch_exchange_rate_error(currency_from, currency_to):
        raise ValueError("Simulated tool error")
    globals()['fetch_exchange_rate'] = mock_fetch_exchange_rate_error
    rate_error = get_eur_to_gbp_exchange_rate()
    assert rate_error is None, f"Test 2 failed: Expected None on error, got {rate_error}"

    # Restore original function if it was defined
    if _original_fetch_exchange_rate:
        globals()['fetch_exchange_rate'] = _original_fetch_exchange_rate
    print("TEST PASSED")
