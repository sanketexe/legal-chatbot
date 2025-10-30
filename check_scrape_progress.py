"""
Quick script to check scraping progress
Run this anytime to see how many cases have been collected
"""

import json
import os
from datetime import datetime

def check_progress():
    json_file = './data/constitution/constitution.json'
    
    if not os.path.exists(json_file):
        print("❌ No data file found yet")
        return
    
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    total = len(data)
    scraped = sum(1 for c in data if 'indiankanoon.org' in str(c.get('source', '')) or 'indiankanoon.org' in str(c.get('url', '')))
    generated = total - scraped
    
    target = 10000
    remaining = max(0, target - total)
    progress_pct = (total / target) * 100
    
    print("=" * 70)
    print("🏛️  LEGAL CASE SCRAPING PROGRESS")
    print("=" * 70)
    print(f"📊 Total Cases:              {total:,}")
    print(f"🌐 Scraped (IndianKanoon):   {scraped:,}")
    print(f"📝 Generated (Synthetic):    {generated:,}")
    print("-" * 70)
    print(f"🎯 Target:                   {target:,}")
    print(f"⏳ Remaining:                {remaining:,}")
    print(f"📈 Progress:                 {progress_pct:.1f}%")
    print("=" * 70)
    
    if remaining > 0:
        print(f"\n⏰ Estimated time remaining: {remaining // 10}-{remaining // 5} minutes")
        print("   (based on ~5-10 cases per minute with rate limiting)")
    else:
        print("\n✅ TARGET REACHED! Ready for Pinecone migration.")
    
    print(f"\n🕒 Checked at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    check_progress()
