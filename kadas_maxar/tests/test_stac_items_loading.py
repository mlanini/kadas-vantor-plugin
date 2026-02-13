#!/usr/bin/env python3
"""
Test STAC Items Loading Fix

This script simulates the 2-phase STAC loading workflow to verify the fix:
1. Fetch catalog.json to get an event
2. Fetch collection.json
3. Extract items link
4. Fetch items.geojson
5. Parse features

Usage:
    python test_stac_items_loading.py
"""

import json
import sys
from urllib.parse import urljoin
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

# Start with catalog to find a valid event
CATALOG_URL = "https://maxar-opendata.s3.amazonaws.com/events/catalog.json"


def fetch_url(url, timeout=30):
    """Fetch URL content."""
    print(f"📡 Fetching: {url}")
    try:
        req = Request(url)
        req.add_header("User-Agent", "KADAS-Vantor-Test/1.0")
        
        with urlopen(req, timeout=timeout) as response:
            data = response.read().decode('utf-8')
            print(f"✅ Success: {len(data)} bytes")
            return data
    except HTTPError as e:
        print(f"❌ HTTP Error {e.code}: {e.reason}")
        sys.exit(1)
    except URLError as e:
        print(f"❌ URL Error: {e.reason}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


def main():
    print("=" * 70)
    print("STAC Items Loading Test")
    print("=" * 70)
    print()
    
    # Phase 0: Load catalog to get first event
    print("🔍 Phase 0: Loading STAC Catalog to find events")
    print("-" * 70)
    catalog_json = fetch_url(CATALOG_URL)
    
    try:
        catalog = json.loads(catalog_json)
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON: {e}")
        sys.exit(1)
    
    links = catalog.get("links", [])
    collection_url = None
    
    for link in links:
        if link.get("rel") == "child":
            href = link.get("href")
            if href:
                # Resolve relative URL
                if not href.startswith(('http://', 'https://')):
                    catalog_base = "/".join(CATALOG_URL.split("/")[:-1]) + "/"
                    href = urljoin(catalog_base, href)
                
                collection_url = href
                event_name = href.split("/")[-2] if href.endswith("collection.json") else href.split("/")[-1]
                print(f"✅ Found event: {event_name}")
                print(f"   Collection URL: {collection_url}")
                break
    
    if not collection_url:
        print("❌ No events found in catalog")
        sys.exit(1)
    
    print()
    
    # Phase 1: Load collection.json
    print("🔍 Phase 1: Loading STAC Collection Metadata")
    print("-" * 70)
    collection_json = fetch_url(collection_url)
    
    try:
        collection = json.loads(collection_json)
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON: {e}")
        sys.exit(1)
    
    print(f"Collection ID: {collection.get('id', 'N/A')}")
    print(f"Collection Type: {collection.get('type', 'N/A')}")
    print(f"Keys: {', '.join(collection.keys())}")
    print()
    
    # Check for features (should NOT be present)
    if "features" in collection:
        print("⚠️  WARNING: Collection contains 'features' (non-standard STAC)")
        print(f"   Features count: {len(collection['features'])}")
    else:
        print("✅ Collection has no 'features' (correct STAC structure)")
    print()
    
    # Phase 2: Extract items link
    print("🔍 Phase 2: Extracting Items Link")
    print("-" * 70)
    
    links = collection.get("links", [])
    print(f"Total links: {len(links)}")
    
    items_url = None
    for link in links:
        rel = link.get("rel")
        href = link.get("href", "N/A")
        print(f"  - rel='{rel}' → href='{href}'")
        
        if rel == "items":
            items_url = href
            print(f"    ✅ Found items link!")
    
    print()
    
    if not items_url:
        print("❌ ERROR: No 'items' link found in collection")
        print("Available links:")
        for link in links:
            print(f"  - {link.get('rel')}: {link.get('href', 'N/A')}")
        sys.exit(1)
    
    # Resolve relative URLs
    if not items_url.startswith(('http://', 'https://')):
        collection_base = "/".join(collection_url.split("/")[:-1]) + "/"
        items_url = urljoin(collection_base, items_url)
        print(f"🔗 Resolved relative URL:")
        print(f"   Base: {collection_base}")
        print(f"   Resolved: {items_url}")
    else:
        print(f"🔗 Items URL is absolute: {items_url}")
    
    print()
    
    # Phase 3: Load items.geojson
    print("🔍 Phase 3: Loading STAC Items (Features)")
    print("-" * 70)
    items_json = fetch_url(items_url)
    
    try:
        items = json.loads(items_json)
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON: {e}")
        sys.exit(1)
    
    print(f"Items Type: {items.get('type', 'N/A')}")
    print(f"Keys: {', '.join(items.keys())}")
    print()
    
    # Check for features (should be present)
    features = items.get("features", [])
    if not features:
        print("❌ ERROR: No 'features' in items.geojson")
        sys.exit(1)
    
    print(f"✅ Features found: {len(features)}")
    print()
    
    # Analyze first feature
    if features:
        print("📋 Sample Feature Analysis")
        print("-" * 70)
        first = features[0]
        props = first.get("properties", {})
        
        print(f"Feature Type: {first.get('type', 'N/A')}")
        print(f"Geometry Type: {first.get('geometry', {}).get('type', 'N/A')}")
        print()
        print("Properties:")
        for key in ["datetime", "platform", "gsd", "cloud_cover", "catalog_id", "quadkey"]:
            value = props.get(key, "N/A")
            print(f"  - {key}: {value}")
        print()
    
    # Summary
    print("=" * 70)
    print("✅ STAC Items Loading Test PASSED")
    print("=" * 70)
    print(f"✅ Phase 0: Catalog loaded, event found")
    print(f"✅ Phase 1: Collection metadata loaded")
    print(f"✅ Phase 2: Items link extracted and resolved")
    print(f"✅ Phase 3: {len(features)} features loaded successfully")
    print()
    print("🎉 The 2-phase STAC loading workflow is working correctly!")
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(1)
