"""
Automated validation test for all government scheme and service URLs in Dhvaani.
Enforces Task 8 requirements:
- URL is not missing
- URL uses HTTPS
- URL does not contain localhost
- URL does not contain example.com
- URL is well-formed
- URL belongs to an approved official domain
- URL does not belong to unapproved third-party domains
"""

import urllib.parse
import pytest
from schemes_db import GOVERNMENT_SCHEMES, GRIEVANCE_DEPARTMENTS
from services_catalog import GRIEVANCE_SERVICES

# Authoritative government and designated statutory authority domains
APPROVED_DOMAIN_SUFFIXES = (
    ".gov.in",
    ".nic.in",
    ".tn.gov.in",
    ".tnega.org",
    "cmchistn.com",
    "pfrda.org.in",
    "tneb.in",
)

DISALLOWED_DOMAINS = (
    "myscheme.gov.in",
    "example.com",
    "localhost",
    "127.0.0.1",
    "wikipedia.org",
)


def _validate_single_url(url: str, context: str, allow_empty: bool = False):
    if not url:
        if allow_empty:
            return
        pytest.fail(f"[{context}] URL is missing or empty.")

    # 1. Must use HTTPS
    assert url.startswith("https://"), f"[{context}] URL does not use HTTPS: {url}"

    # 2. Must not contain localhost or example.com
    assert "localhost" not in url.lower(), f"[{context}] URL contains localhost: {url}"
    assert "127.0.0.1" not in url, f"[{context}] URL contains loopback: {url}"
    assert "example.com" not in url.lower(), f"[{context}] URL contains example.com: {url}"

    # 3. Must be well-formed
    parsed = urllib.parse.urlparse(url)
    assert parsed.scheme == "https", f"[{context}] URL scheme is not https: {url}"
    assert parsed.netloc, f"[{context}] URL is malformed, missing netloc: {url}"

    # 4. Must not belong to disallowed third-party / aggregator domains
    for disallowed in DISALLOWED_DOMAINS:
        assert disallowed not in parsed.netloc.lower(), (
            f"[{context}] URL belongs to unapproved/disallowed domain '{disallowed}': {url}"
        )

    # 5. Must belong to an approved official government or designated statutory domain
    domain = parsed.netloc.lower()
    matches_approved = any(domain.endswith(suffix) or domain == suffix for suffix in APPROVED_DOMAIN_SUFFIXES)
    assert matches_approved, (
        f"[{context}] Domain '{domain}' is not in approved government/statutory authorities: {APPROVED_DOMAIN_SUFFIXES}"
    )


def test_scheme_urls_valid_and_authoritative():
    """Verify all 12 government schemes have valid, authoritative HTTPS URLs."""
    assert len(GOVERNMENT_SCHEMES) == 12, "Expected 12 government schemes in database"

    for s in GOVERNMENT_SCHEMES:
        sid = s.get("id") or s.get("scheme_id")
        
        # Test official source / information URLs
        _validate_single_url(s.get("official_source"), f"Scheme {sid} official_source")
        _validate_single_url(s.get("official_source_url"), f"Scheme {sid} official_source_url")
        _validate_single_url(s.get("official_information_url"), f"Scheme {sid} official_information_url")
        _validate_single_url(s.get("source_url"), f"Scheme {sid} source_url")
        _validate_single_url(s.get("official_application_url"), f"Scheme {sid} official_application_url")

        # Dedicated application_url (if provided) must be valid
        if s.get("application_url"):
            _validate_single_url(s.get("application_url"), f"Scheme {sid} application_url", allow_empty=False)

        # Dedicated status_url (if provided) must be valid
        if s.get("status_url"):
            _validate_single_url(s.get("status_url"), f"Scheme {sid} status_url", allow_empty=False)


def test_grievance_catalog_urls_valid_and_authoritative():
    """Verify all grievance services in services_catalog have valid, authoritative HTTPS URLs."""
    for cat, svc in GRIEVANCE_SERVICES.items():
        _validate_single_url(svc.official_info.portal_url, f"Grievance {cat} portal_url")
        _validate_single_url(svc.official_info.information_url, f"Grievance {cat} information_url")
        _validate_single_url(svc.official_info.application_url, f"Grievance {cat} application_url")
        _validate_single_url(svc.official_info.status_tracking_url, f"Grievance {cat} status_tracking_url")
        _validate_single_url(svc.verification.source_url, f"Grievance {cat} source_url")


def test_grievance_department_portals_valid():
    """Verify all grievance departments in schemes_db have valid HTTPS portals."""
    for dept_id, dept in GRIEVANCE_DEPARTMENTS.items():
        portal = dept.get("portal")
        _validate_single_url(portal, f"Department {dept_id} portal")


def test_cmchis_specific_requirements():
    """Verify CMCHIS explicitly points to https://www.cmchistn.com/ for both source and application."""
    cmchis = next((s for s in GOVERNMENT_SCHEMES if s.get("id") == "tamilnadu_chief_minister_health_insurance"), None)
    assert cmchis is not None
    assert cmchis["official_source"] == "https://www.cmchistn.com/"
    assert cmchis["official_source_url"] == "https://www.cmchistn.com/"
    assert cmchis["official_application_url"] == "https://www.cmchistn.com/"
    assert cmchis["application_url"] == "https://www.cmchistn.com/"
