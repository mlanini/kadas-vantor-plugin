#!/usr/bin/env python3
"""
Explore Maxar STAC catalog structure to understand the hierarchy.
"""

import json
from urllib.parse import urljoin
from urllib.request import urlopen, Request

CATALOG_URL = "https://maxar-opendata.s3.amazonaws.com/events/catalog.json"


def fetch(url):
    """Fetch and parse JSON."""
    req = Request(url)
    req.add_header("User-Agent", "Explorer/1.0")
    with urlopen(req, timeout=30) as response:
        return json.loads(response.read().decode('utf-8'))


def explore_collection(url, depth=0):
    """Recursively explore collection structure."""
    indent = "  " * depth
    print(f"{indent}📄 {url.split('/')[-1]}")
    
    try:
        data = fetch(url)
    except Exception as e:
        print(f"{indent}   ❌ Error: {e}")
        return
    
    print(f"{indent}   Type: {data.get('type', 'N/A')}")
    print(f"{indent}   ID: {data.get('id', 'N/A')}")
    
    links = data.get("links", [])
    items_link = None
    child_links = []
    
    for link in links:
        rel = link.get("rel")
        href = link.get("href")
        
        if rel == "items":
            items_link = href
            if not href.startswith(('http://', 'https://')):
                base = "/".join(url.split("/")[:-1]) + "/"
                items_link = urljoin(base, href)
            print(f"{indent}   ✅ ITEMS: {items_link}")
        elif rel == "child":
            if not href.startswith(('http://', 'https://')):
                base = "/".join(url.split("/")[:-1]) + "/"
                href = urljoin(base, href)
            child_links.append(href)
    
    if items_link and depth < 3:
        # Try to fetch items
        print(f"{indent}   🔗 Fetching items...")
        try:
            items = fetch(items_link)
            features = items.get("features", [])
            print(f"{indent}   ✅ Features: {len(features)}")
            if features:
                props = features[0].get("properties", {})
                print(f"{indent}      Sample: {props.get('datetime', 'N/A')}, {props.get('platform', 'N/A')}")
        except Exception as e:
            print(f"{indent}   ❌ Error loading items: {e}")
    
    # Explore first child only (to avoid too much output)
    if child_links and depth < 2:
        print(f"{indent}   📁 Children: {len(child_links)}")
        print(f"{indent}   Exploring first child...")
        explore_collection(child_links[0], depth + 1)


print("=" * 70)
print("Maxar STAC Catalog Structure Explorer")
print("=" * 70)
print()

catalog = fetch(CATALOG_URL)
links = catalog.get("links", [])

# Get first event
for link in links:
    if link.get("rel") == "child":
        href = link.get("href")
        if not href.startswith(('http://', 'https://')):
            base = "/".join(CATALOG_URL.split("/")[:-1]) + "/"
            href = urljoin(base, href)
        
        print(f"Exploring first event: {href}")
        print()
        explore_collection(href)
        break
