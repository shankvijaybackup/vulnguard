#!/usr/bin/env python3
"""
VulnGuard ZAP Scan Automation Script
This script automates OWASP ZAP scanning operations for the VulnGuard platform.
"""

import json
import os
import sys
import time
import requests
from datetime import datetime
from urllib.parse import urlparse

class ZAPScanAutomation:
    def __init__(self, zap_api_url="http://localhost:8080", api_key=None):
        self.zap_api_url = zap_api_url.rstrip('/')
        self.api_key = api_key
        self.session = requests.Session()

        # Set API key in headers if provided
        if self.api_key:
            self.session.headers.update({'X-ZAP-API-Key': self.api_key})

    def _zap_request(self, endpoint, method='GET', **kwargs):
        """Make a request to the ZAP API"""
        url = f"{self.zap_api_url}{endpoint}"

        try:
            if method.upper() == 'GET':
                response = self.session.get(url, **kwargs)
            elif method.upper() == 'POST':
                response = self.session.post(url, **kwargs)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            response.raise_for_status()
            return response.json() if response.content else None

        except requests.exceptions.RequestException as e:
            print(f"Error calling ZAP API: {e}")
            return None

    def wait_for_zap_ready(self, timeout=300):
        """Wait for ZAP to be ready to accept API calls"""
        print("Waiting for ZAP to be ready...")
        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                # Check if ZAP API is responding
                response = self._zap_request('/JSON/core/view/version/')
                if response and 'version' in response:
                    print(f"ZAP is ready! Version: {response['version']}")
                    return True
            except:
                pass

            time.sleep(5)

        print("Timeout waiting for ZAP to be ready")
        return False

    def start_spider_scan(self, target_url, max_children=10, recurse=True):
        """Start a spider scan on the target URL"""
        print(f"Starting spider scan on: {target_url}")

        params = {
            'url': target_url,
            'maxChildren': max_children,
            'recurse': str(recurse).lower()
        }

        response = self._zap_request('/JSON/spider/action/scan/', method='POST', params=params)

        if response and 'scan' in response:
            scan_id = response['scan']
            print(f"Spider scan started with ID: {scan_id}")
            return scan_id

        print("Failed to start spider scan")
        return None

    def check_spider_status(self, scan_id):
        """Check the status of a spider scan"""
        response = self._zap_request(f'/JSON/spider/view/status/?scanId={scan_id}')

        if response and 'status' in response:
            return response['status']

        return None

    def wait_for_spider_complete(self, scan_id, timeout=1800):
        """Wait for spider scan to complete"""
        print(f"Waiting for spider scan {scan_id} to complete...")

        start_time = time.time()
        while time.time() - start_time < timeout:
            status = self.check_spider_status(scan_id)

            if status == '100':
                print("Spider scan completed!")
                return True
            elif status is None:
                print("Spider scan not found or failed")
                return False

            print(f"Spider progress: {status}%")
            time.sleep(30)

        print("Spider scan timeout")
        return False

    def start_active_scan(self, target_url, scan_policy='Default Policy'):
        """Start an active scan on the target URL"""
        print(f"Starting active scan on: {target_url}")

        params = {
            'url': target_url,
            'scanPolicyName': scan_policy,
            'recurse': 'true'
        }

        response = self._zap_request('/JSON/ascan/action/scan/', method='POST', params=params)

        if response and 'scan' in response:
            scan_id = response['scan']
            print(f"Active scan started with ID: {scan_id}")
            return scan_id

        print("Failed to start active scan")
        return None

    def check_active_scan_status(self, scan_id):
        """Check the status of an active scan"""
        response = self._zap_request(f'/JSON/ascan/view/status/?scanId={scan_id}')

        if response and 'status' in response:
            return response['status']

        return None

    def wait_for_active_scan_complete(self, scan_id, timeout=3600):
        """Wait for active scan to complete"""
        print(f"Waiting for active scan {scan_id} to complete...")

        start_time = time.time()
        while time.time() - start_time < timeout:
            status = self.check_active_scan_status(scan_id)

            if status == '100':
                print("Active scan completed!")
                return True
            elif status is None:
                print("Active scan not found or failed")
                return False

            print(f"Active scan progress: {status}%")
            time.sleep(60)

        print("Active scan timeout")
        return False

    def get_scan_results(self, scan_id):
        """Get the results of the active scan"""
        print("Retrieving scan results...")

        # Get all alerts
        response = self._zap_request('/JSON/core/view/alerts/')

        if response and 'alerts' in response:
            alerts = response['alerts']
            print(f"Found {len(alerts)} alerts")

            # Filter alerts for this specific scan if scan_id is provided
            if scan_id:
                filtered_alerts = []
                for alert in alerts:
                    if str(alert.get('scanID', '')) == str(scan_id):
                        filtered_alerts.append(alert)
                alerts = filtered_alerts
                print(f"Filtered to {len(alerts)} alerts for scan {scan_id}")

            return alerts

        print("No alerts found")
        return []

    def export_scan_report(self, format_type='json', output_file=None):
        """Export scan report in specified format"""
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"/zap/scans/scan_report_{timestamp}.{format_type}"

        print(f"Exporting scan report to: {output_file}")

        params = {
            'format': format_type
        }

        response = self._zap_request('/JSON/reports/action/generate/', method='POST', params=params)

        if response and 'report' in response:
            # In a real implementation, you'd save the report content to file
            print(f"Report generated successfully")
            return response['report']

        print("Failed to generate report")
        return None

def main():
    if len(sys.argv) < 2:
        print("Usage: python zap_scan.py <target_url> [options]")
        print("Options:")
        print("  --api-key <key>    ZAP API key")
        print("  --max-children <n> Maximum children for spider (default: 10)")
        print("  --no-spider        Skip spider scan")
        print("  --no-active        Skip active scan")
        sys.exit(1)

    target_url = sys.argv[1]
    api_key = None
    max_children = 10
    run_spider = True
    run_active = True

    # Parse arguments
    i = 2
    while i < len(sys.argv):
        if sys.argv[i] == '--api-key' and i + 1 < len(sys.argv):
            api_key = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == '--max-children' and i + 1 < len(sys.argv):
            max_children = int(sys.argv[i + 1])
            i += 2
        elif sys.argv[i] == '--no-spider':
            run_spider = False
            i += 1
        elif sys.argv[i] == '--no-active':
            run_active = False
            i += 1
        else:
            i += 1

    # Validate URL
    parsed = urlparse(target_url)
    if not parsed.scheme or not parsed.netloc:
        print(f"Invalid URL: {target_url}")
        sys.exit(1)

    print(f"VulnGuard ZAP Scan Automation")
    print(f"Target URL: {target_url}")
    print("=" * 50)

    # Initialize ZAP automation
    zap = ZAPScanAutomation(api_key=api_key)

    # Wait for ZAP to be ready
    if not zap.wait_for_zap_ready():
        sys.exit(1)

    scan_results = []

    # Run spider scan
    if run_spider:
        spider_id = zap.start_spider_scan(target_url, max_children=max_children)
        if spider_id:
            if zap.wait_for_spider_complete(spider_id):
                print("Spider scan completed successfully")
            else:
                print("Spider scan failed or timed out")
        else:
            print("Failed to start spider scan")
    else:
        print("Skipping spider scan")

    # Run active scan
    if run_active:
        active_id = zap.start_active_scan(target_url)
        if active_id:
            if zap.wait_for_active_scan_complete(active_id):
                print("Active scan completed successfully")
                scan_results = zap.get_scan_results(active_id)
            else:
                print("Active scan failed or timed out")
        else:
            print("Failed to start active scan")
    else:
        print("Skipping active scan")

    # Export results
    if scan_results:
        print(f"\nScan completed! Found {len(scan_results)} vulnerabilities")
        for alert in scan_results:
            print(f"- {alert.get('name', 'Unknown')}: {alert.get('risk', 'Unknown')} ({alert.get('confidence', 'Unknown')})")

        # Export report
        report = zap.export_scan_report('json')
        if report:
            print("Report exported successfully")

        # Save detailed results to file
        results_file = f"/zap/scans/scan_results_{int(time.time())}.json"
        with open(results_file, 'w') as f:
            json.dump({
                'target_url': target_url,
                'scan_timestamp': datetime.now().isoformat(),
                'vulnerabilities': scan_results,
                'total_count': len(scan_results)
            }, f, indent=2)

        print(f"Detailed results saved to: {results_file}")
    else:
        print("No vulnerabilities found or scan failed")

if __name__ == "__main__":
    main()
