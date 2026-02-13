#!/usr/bin/env python3
"""Quick test of the dualstack endpoint structure"""

import json
from urllib.request import urlopen, Request

DUALSTACK_CATALOG = "https://maxar-opendata.s3.dualstack.us-west-2.amazonaws.com/events/catalog.json"

req = Request(DUALSTACK_CATALOG)
req.add_header("User-Agent", "Test/1.0")

with urlopen(req, timeout=30) as response:
    catalog = json.loads(response.read().decode('utf-8'))

print(f"Catalog type: {catalog.get('type')}")
print(f"Links count: {len(catalog.get('links', []))}")
print()

# Get first event
links = catalog.get("links", [])
for link in links:
    if link.get("rel") == "child":
        print(f"First event: {link.get('title', 'N/A')}")
        print(f"URL: {link.get('href')}")
        break
