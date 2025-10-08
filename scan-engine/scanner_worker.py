#!/usr/bin/env python3
"""
VulnGuard Scan Worker Script
This script orchestrates ZAP scans inside the Docker container.
"""

import time
import os
import argparse
from zapv2 import ZAPv2


def main():
    """
    Main function to orchestrate the ZAP scan.
    This script is designed to be run inside the Docker container.
    """
    # --- Configuration ---
    # The API key is set by the ZAP entrypoint script
    api_key = os.environ.get('ZAP_API_KEY')
    # ZAP is running on localhost inside the container
    zap_proxy = {'http': 'http://127.0.0.1:8080', 'https': 'http://127.0.0.1:8080'}

    # --- Argument Parsing ---
    parser = argparse.ArgumentParser(description='Run a ZAP scan.')
    parser.add_argument('--target', type=str, required=True, help='The target URL to scan (e.g., http://example.com)')
    args = parser.parse_args()
    target_url = args.target

    print(f"[*] Initializing ZAP client with proxy: {zap_proxy}")
    zap = ZAPv2(apikey=api_key, proxies=zap_proxy)

    try:
        # Wait for ZAP to fully start. A more robust solution would be to poll the status endpoint.
        print("[*] Waiting for ZAP to start...")
        time.sleep(15)

        print(f"[*] Starting Scan for Target: {target_url}")

        # --- 1. Spider Scan ---
        print("[*] Starting Spider...")
        scan_id = zap.spider.scan(target_url)
        # Poll the spider status until it's complete
        while int(zap.spider.status(scan_id)) < 100:
            print(f"    Spider progress: {zap.spider.status(scan_id)}%")
            time.sleep(5)
        print("[+] Spider finished.")

        # Give the sites tree time to settle
        time.sleep(5)

        # --- 2. Active Scan ---
        print("[*] Starting Active Scan...")
        scan_id = zap.ascan.scan(target_url)
        # Poll the active scan status until it's complete
        while int(zap.ascan.status(scan_id)) < 100:
            print(f"    Active Scan progress: {zap.ascan.status(scan_id)}%")
            time.sleep(10)
        print("[+] Active Scan finished.")

        # --- 3. Generate Report ---
        report_path = f'/zap/wrk/{target_url.replace("http://", "").replace("https://", "")}_report.json'
        print(f"[*] Generating JSON report at: {report_path}")
        report = zap.core.jsonreport()
        with open(report_path, 'w') as f:
            f.write(report)

        print("[+] Scan complete. Report generated.")
        print(f"[+] To retrieve the report, use 'docker cp <container_id>:{report_path} ./'")

    except Exception as e:
        print(f"[!] An error occurred: {e}")


if __name__ == "__main__":
    main()
