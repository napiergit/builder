#!/usr/bin/env python3
"""
Discover fastmcp.cloud deployment API endpoints and workflows
"""

import requests
import json
import re
from urllib.parse import urlparse, urljoin

def extract_api_endpoints_from_html(html_content):
    """Extract potential API endpoints from JavaScript and HTML"""
    
    # Look for API endpoints in JavaScript
    api_patterns = [
        r'"(/api[^"]*)"',
        r"'(/api[^']*)'",
        r'api[.:][\s]*["\']([^"\']+)["\']',
        r'fetch[\s]*\(["\']([^"\']*api[^"\']*)["\']',
        r'axios[.\s]*(?:get|post|put|delete)[\s]*\(["\']([^"\']*)["\']',
        r'endpoint[\s]*:[\s]*["\']([^"\']*)["\']'
    ]
    
    endpoints = set()
    
    for pattern in api_patterns:
        matches = re.findall(pattern, html_content, re.IGNORECASE)
        for match in matches:
            if isinstance(match, tuple):
                match = match[0]
            if match.startswith('/'):
                endpoints.add(match)
            elif 'api' in match.lower():
                endpoints.add(match)
    
    # Look for deployment-related endpoints
    deployment_patterns = [
        r'"([^"]*deploy[^"]*)"',
        r'"([^"]*github[^"]*)"',
        r'"([^"]*server[^"]*)"',
        r'"([^"]*webhook[^"]*)"'
    ]
    
    for pattern in deployment_patterns:
        matches = re.findall(pattern, html_content, re.IGNORECASE)
        for match in matches:
            if match.startswith('/') and any(keyword in match for keyword in ['deploy', 'github', 'server', 'webhook']):
                endpoints.add(match)
    
    return sorted(list(endpoints))

def discover_fastmcp_cloud_api():
    """Discover fastmcp.cloud API endpoints"""
    
    base_url = "https://fastmcp.cloud"
    api_key = "fmcp_XTAYZDw3a7nY_1312VA5yxRez3ud5MmWmy3fQ-f8shM"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "User-Agent": "MCP-Builder-Discovery/1.0",
        "Accept": "application/json, text/html"
    }
    
    print("🔍 Discovering fastmcp.cloud API endpoints...")
    
    # Get the main page and extract potential endpoints
    try:
        response = requests.get(base_url, headers=headers, timeout=10)
        html_content = response.text
        
        endpoints = extract_api_endpoints_from_html(html_content)
        
        print(f"📋 Found {len(endpoints)} potential endpoints:")
        for endpoint in endpoints:
            print(f"  - {endpoint}")
        
        # Test common API patterns
        common_api_paths = [
            "/api",
            "/api/v1", 
            "/api/v1/deployments",
            "/api/v1/projects", 
            "/api/v1/servers",
            "/api/deployments",
            "/api/projects",
            "/api/servers",
            "/webhook",
            "/deploy",
            "/github/webhook"
        ]
        
        print(f"\n🧪 Testing common API patterns...")
        working_endpoints = []
        
        for path in common_api_paths + endpoints[:10]:  # Test first 10 discovered endpoints
            test_url = urljoin(base_url, path)
            
            try:
                # Try OPTIONS first to see what methods are supported
                options_response = requests.options(test_url, headers=headers, timeout=5)
                if options_response.status_code not in [404, 405]:
                    allow_header = options_response.headers.get('Allow', '')
                    print(f"✅ {path} - Status: {options_response.status_code}, Methods: {allow_header}")
                    working_endpoints.append((path, options_response.status_code, allow_header))
                    continue
                
                # Try GET
                get_response = requests.get(test_url, headers=headers, timeout=5)
                if get_response.status_code not in [404, 405]:
                    print(f"✅ {path} - GET Status: {get_response.status_code}")
                    if get_response.headers.get('content-type', '').startswith('application/json'):
                        try:
                            data = get_response.json()
                            print(f"   📊 JSON Response: {json.dumps(data, indent=2)[:200]}...")
                        except:
                            pass
                    working_endpoints.append((path, get_response.status_code, 'GET'))
                
            except requests.RequestException as e:
                print(f"❌ {path} - Error: {e}")
        
        if working_endpoints:
            print(f"\n🎉 Found {len(working_endpoints)} working endpoints!")
            return working_endpoints
        else:
            print("\n❌ No working API endpoints found through automated discovery")
            return []
            
    except Exception as e:
        print(f"❌ Discovery failed: {e}")
        return []

if __name__ == "__main__":
    working_endpoints = discover_fastmcp_cloud_api()
    
    if working_endpoints:
        print("\n📝 Summary of working endpoints:")
        for path, status, methods in working_endpoints:
            print(f"  {path} - Status {status} - {methods}")
    else:
        print("\n🤷 Unable to discover API endpoints automatically.")
        print("Manual deployment through fastmcp.cloud web interface may be required.")
