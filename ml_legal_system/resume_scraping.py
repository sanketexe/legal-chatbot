"""
Resume scraping from where it left off
Handles network errors and continues from last successful category
"""

import json
import os
from case_scraper import IndianLegalCaseScraper
from config import Config


def get_existing_cases():
    """Load existing cases to avoid duplicates"""
    cases_file = 'data/legal_cases/indian_legal_cases_complete.json'
    
    if os.path.exists(cases_file):
        try:
            with open(cases_file, 'r', encoding='utf-8') as f:
                existing = json.load(f)
            print(f"📚 Found {len(existing)} existing cases")
            return existing
        except:
            return []
    return []


def find_last_processed_category(existing_cases, all_categories):
    """Determine which categories have been fully processed"""
    
    if not existing_cases:
        return 0
    
    # Count cases per category (rough estimate based on titles/content)
    category_keywords = {
        cat: cat.split()[0].lower() for cat in all_categories
    }
    
    # Simple heuristic: if we have close to MAX_CASES_PER_QUERY for a category, it's done
    cases_per_query = Config.MAX_CASES_PER_QUERY
    estimated_categories = len(existing_cases) // cases_per_query
    
    print(f"📊 Estimated {estimated_categories} categories completed")
    return estimated_categories


def resume_scraping():
    """Resume scraping from last successful category"""
    
    print("🔄 Resume Scraping Tool")
    print("=" * 60)
    
    # Load existing cases
    existing_cases = get_existing_cases()
    
    # Get configuration
    all_categories = Config.LEGAL_CATEGORIES
    cases_per_query = Config.MAX_CASES_PER_QUERY
    
    # Find last processed category
    last_processed = find_last_processed_category(existing_cases, all_categories)
    
    # Categories to process
    remaining_categories = all_categories[last_processed:]
    
    print(f"\n📋 Total categories: {len(all_categories)}")
    print(f"✅ Already processed: {last_processed} categories (~{len(existing_cases)} cases)")
    print(f"🔄 Remaining: {len(remaining_categories)} categories")
    print(f"🎯 Target: ~{len(remaining_categories) * cases_per_query} more cases")
    print(f"📊 Grand total target: ~{len(all_categories) * cases_per_query} cases")
    print()
    
    if not remaining_categories:
        print("✅ All categories have been processed!")
        return
    
    # Confirm before starting
    print("⚠️  This will take several hours to complete.")
    print(f"📝 Will scrape: {', '.join(remaining_categories[:5])}...")
    print()
    
    # Initialize scraper
    scraper = IndianLegalCaseScraper()
    
    # Start scraping remaining categories
    print("🚀 Starting scraping...")
    print("=" * 60)
    
    try:
        new_cases = scraper.scrape_bulk_cases(
            remaining_categories, 
            cases_per_query=cases_per_query
        )
        
        # Merge with existing cases
        all_cases = existing_cases + new_cases
        
        # Remove duplicates based on URL
        unique_cases = []
        seen_urls = set()
        
        for case in all_cases:
            url = case.get('url', '')
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_cases.append(case)
        
        print(f"\n📊 Total unique cases: {len(unique_cases)}")
        
        # Save final results
        final_file = scraper.save_cases(unique_cases, "indian_legal_cases_complete.json")
        
        print("\n" + "=" * 60)
        print(f"🎉 Scraping Complete!")
        print(f"📊 Total cases: {len(unique_cases)}")
        print(f"🆕 New cases added: {len(new_cases)}")
        print(f"💾 Saved to: {final_file}")
        print("=" * 60)
        
    except KeyboardInterrupt:
        print("\n⚠️  Scraping interrupted by user")
        print(f"📊 Cases collected so far: {len(existing_cases)}")
        print("💡 Run this script again to resume")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print(f"📊 Cases collected so far: {len(existing_cases)}")
        print("💡 Run this script again to resume")


if __name__ == "__main__":
    resume_scraping()
