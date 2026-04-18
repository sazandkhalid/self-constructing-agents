"""
ISO 20022 hybrid address handling.
Mandatory from November 2026: town name + country code must be structured.
"""

from dataclasses import dataclass
from typing import Optional
import re

@dataclass
class HybridAddress:
    """
    ISO 20022 hybrid address format (mandatory post-Nov 2026).
    Town name and country are structured. Up to 2 free-form lines allowed.
    """
    town_name: str
    country: str                      # ISO 3166-1 alpha-2
    address_line_1: Optional[str] = None
    address_line_2: Optional[str] = None
    post_code: Optional[str] = None
    street_name: Optional[str] = None
    building_number: Optional[str] = None

    def is_fully_structured(self) -> bool:
        return all([self.street_name, self.building_number, self.post_code])

    def is_hybrid(self) -> bool:
        return bool(self.town_name and self.country and
                    (self.address_line_1 or not self.is_fully_structured()))

    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items() if v is not None}

def parse_unstructured_address(raw: str, country_hint: str = "US") -> HybridAddress:
    """
    Convert a free-text address to hybrid format.
    Extracts town and country at minimum — required for SWIFT compliance post-Nov 2026.
    """
    lines = [l.strip() for l in raw.strip().splitlines() if l.strip()]
    town = ""
    post_code = ""
    if lines:
        last = lines[-1]
        country_match = re.search(r'\b([A-Z]{2})\b', last)
        if country_match:
            country_hint = country_match.group(1)
        zip_match = re.search(r'\b(\d{5}(?:-\d{4})?)\b', last)
        if zip_match:
            post_code = zip_match.group(1)
            town = last[:zip_match.start()].strip().rstrip(",").strip()
    return HybridAddress(
        town_name=town or "Unknown",
        country=country_hint,
        post_code=post_code or None,
        address_line_1=lines[0] if len(lines) > 1 else None,
        address_line_2=lines[1] if len(lines) > 2 else None,
    )

def validate_hybrid_address(addr: HybridAddress) -> list:
    """Returns list of validation errors. Empty = valid."""
    errors = []
    if not addr.town_name or addr.town_name == "Unknown":
        errors.append("town_name is required and must not be 'Unknown'")
    if not addr.country or len(addr.country) != 2:
        errors.append("country must be a valid ISO 3166-1 alpha-2 code")
    if addr.address_line_1 and len(addr.address_line_1) > 70:
        errors.append("address_line_1 must not exceed 70 characters")
    if addr.address_line_2 and len(addr.address_line_2) > 70:
        errors.append("address_line_2 must not exceed 70 characters")
    return errors


if __name__ == "__main__":
    valid = HybridAddress(town_name="New York", country="US", post_code="10001")
    assert validate_hybrid_address(valid) == []

    invalid = HybridAddress(town_name="Unknown", country="X")
    errs = validate_hybrid_address(invalid)
    assert len(errs) == 2

    addr = parse_unstructured_address("123 Main St\nSpringfield, 62701 US")
    assert addr.country == "US"
    assert addr.post_code == "62701"
    print("TEST PASSED")
