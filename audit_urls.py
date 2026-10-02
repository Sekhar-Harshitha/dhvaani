import json
import schemes_db
import services_catalog

print("=== SCHEMES ===")
for s in schemes_db.GOVERNMENT_SCHEMES:
    print(f"ID: {s.get('id')}")
    print(f"  Name: {s.get('name')}")
    print(f"  official_source: {s.get('official_source')}")
    print(f"  source_url: {s.get('source_url')}")
    print(f"  official_information_url: {s.get('official_information_url')}")
    print(f"  official_application_url: {s.get('official_application_url')}")
    print(f"  helpline: {s.get('helpline')}")
    print(f"  official_helpline: {s.get('official_helpline')}")

print("\n=== SERVICES CATALOG ===")
for cat, services in services_catalog.SERVICES_CATALOG.items():
    print(f"Category: {cat}")
    for s in services:
        print(f"  ID: {s.get('id')}")
        print(f"    Name: {s.get('name')}")
        print(f"    official_url: {s.get('official_url')}")
        print(f"    portal: {s.get('portal')}")
        print(f"    helpline: {s.get('helpline')}")
        print(f"    status_tracking_url: {s.get('status_tracking_url')}")
