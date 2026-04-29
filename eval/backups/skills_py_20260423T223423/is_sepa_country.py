# skill: is_sepa_country
# version: 1
# tags: write, python, function, called, is_sepa_country
# success_count: 0
# fail_count: 0
# verified: true
# last_used: 2026-04-23T22:28:42.340916+00:00
# decaying: false
def is_sepa_country(country_code: str) -> bool:
    # protocol: general
    # rail: general
    # audit_required: false
    'Returns True if the country code is in the SEPA set, False otherwise.'
    sepa_countries = {
        "GB", "DE", "FR", "ES", "IT", "NL", "BE", "AT", "PT", "IE", "FI", "SE",
        "DK", "NO", "PL", "CZ", "HU", "RO", "SK", "SI", "EE", "LV", "LT", "LU",
        "MT", "CY", "GR", "HR", "BG"
    }
    return country_code in sepa_countries

if __name__ == "__main__":
    assert is_sepa_country("DE") == True
    assert is_sepa_country("US") == False
    assert is_sepa_country("FR") == True
    assert is_sepa_country("XX") == False
    print("TEST PASSED")
