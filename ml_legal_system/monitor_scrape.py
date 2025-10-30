"""
Monitor the scraping progress and write status updates to a log file.
Run this alongside your scraper; it will check the main JSON and partial files every 60s.
"""

import time
import os
import json
from datetime import datetime

CASES_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'legal_cases')
COMPLETE_FILE = os.path.join(CASES_DIR, 'indian_legal_cases_complete.json')
LOG_FILE = os.path.join(CASES_DIR, 'scrape_status.log')

CHECK_INTERVAL = 60  # seconds


def count_cases_in_file(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, list):
                return len(data)
            return 0
    except Exception:
        return 0


def find_partial_files():
    files = []
    try:
        for fname in os.listdir(CASES_DIR):
            if fname.startswith('cases_partial_') and fname.endswith('.json'):
                files.append(fname)
    except Exception:
        pass
    return sorted(files)


def write_log(message):
    ts = datetime.utcnow().isoformat() + 'Z'
    line = f"[{ts}] {message}\n"
    try:
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(line)
    except Exception:
        print(line)


def get_status():
    complete_count = count_cases_in_file(COMPLETE_FILE)
    partials = find_partial_files()
    partial_info = []
    for p in partials[-3:]:  # last 3 partials
        path = os.path.join(CASES_DIR, p)
        partial_info.append((p, os.path.getsize(path), count_cases_in_file(path)))
    return complete_count, partial_info


if __name__ == '__main__':
    write_log('Monitor started')
    print('Scrape monitor started. Logging to', LOG_FILE)
    try:
        while True:
            complete_count, partial_info = get_status()
            msg = f"Complete cases: {complete_count}; partials: {partial_info}"
            print(msg)
            write_log(msg)
            time.sleep(CHECK_INTERVAL)
    except KeyboardInterrupt:
        write_log('Monitor stopped by user')
        print('Monitor stopped')
