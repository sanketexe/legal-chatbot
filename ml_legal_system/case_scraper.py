"""
Indian Legal Case Scraper
Scrapes cases from Indian Kanoon and other legal databases
"""

import requests
from bs4 import BeautifulSoup
import json
import time
from datetime import datetime
import os
from typing import List, Dict, Optional

class IndianLegalCaseScraper:
    """
    Scraper for Indian legal cases from multiple sources
    """
    
    def __init__(self, output_dir: str = "data/legal_cases"):
        self.output_dir = output_dir
        self.base_url = "https://indiankanoon.org"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
    def search_cases(self, query: str, court: str = None, max_results: int = 100) -> List[Dict]:
        """
        Search for cases on Indian Kanoon
        
        Args:
            query: Search query (e.g., "contract dispute")
            court: Filter by court (e.g., "Supreme Court", "Delhi High Court")
            max_results: Maximum number of cases to retrieve
            
        Returns:
            List of case dictionaries
        """
        cases = []
        page = 1
        
        while len(cases) < max_results:
            try:
                # Construct search URL
                search_url = f"{self.base_url}/search/?formInput={query}"
                if court:
                    search_url += f"&court={court}"
                search_url += f"&pagenum={page}"
                
                print(f"📡 Searching page {page} for: {query}")
                response = self.session.get(search_url, timeout=10)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Find all case links
                case_links = soup.find_all('a', class_='cite_tag')
                
                if not case_links:
                    print(f"✅ No more results found. Total cases: {len(cases)}")
                    break
                
                for link in case_links:
                    if len(cases) >= max_results:
                        break
                        
                    case_url = self.base_url + link.get('href')
                    case_title = link.get_text(strip=True)
                    
                    cases.append({
                        'title': case_title,
                        'url': case_url,
                        'query': query
                    })
                    
                page += 1
                time.sleep(1)  # Be respectful to the server
                
            except Exception as e:
                print(f"❌ Error on page {page}: {str(e)}")
                break
                
        return cases
    
    def scrape_case_details(self, case_url: str) -> Optional[Dict]:
        """
        Scrape detailed information from a single case
        
        Args:
            case_url: URL of the case page
            
        Returns:
            Dictionary with case details
        """
        try:
            print(f"📄 Scraping: {case_url}")
            response = self.session.get(case_url, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract case information
            case_data = {
                'url': case_url,
                'scraped_at': datetime.now().isoformat(),
            }
            
            # Get title
            title_tag = soup.find('h1', class_='doc_title')
            if title_tag:
                case_data['title'] = title_tag.get_text(strip=True)
            
            # Get court name
            court_tag = soup.find('span', class_='docsource_main')
            if court_tag:
                case_data['court'] = court_tag.get_text(strip=True)
            
            # Get date
            date_tag = soup.find('span', class_='judgement_date')
            if date_tag:
                case_data['date'] = date_tag.get_text(strip=True)
            
            # Get judges
            judges_tag = soup.find('span', class_='judges')
            if judges_tag:
                case_data['judges'] = judges_tag.get_text(strip=True)
            
            # Get full judgment text
            judgment_div = soup.find('div', class_='judgments')
            if judgment_div:
                case_data['full_text'] = judgment_div.get_text(separator='\n', strip=True)
            
            # Get citations
            citations = []
            cite_tags = soup.find_all('a', class_='cite_tag')
            for cite in cite_tags[:10]:  # Limit to 10 citations
                citations.append(cite.get_text(strip=True))
            case_data['citations'] = citations
            
            # Extract legal acts mentioned
            acts = []
            act_tags = soup.find_all('a', class_='act_tag')
            for act in act_tags:
                acts.append(act.get_text(strip=True))
            case_data['legal_acts'] = list(set(acts))  # Remove duplicates
            
            time.sleep(2)  # Be respectful to the server
            return case_data
            
        except Exception as e:
            print(f"❌ Error scraping {case_url}: {str(e)}")
            return None
    
    def scrape_bulk_cases(self, queries: List[str], cases_per_query: int = 50) -> List[Dict]:
        """
        Scrape multiple cases for multiple queries
        
        Args:
            queries: List of search queries
            cases_per_query: Number of cases to scrape per query
            
        Returns:
            List of all scraped cases
        """
        all_cases = []
        
        for query in queries:
            print(f"\n🔍 Processing query: {query}")
            print("=" * 60)
            
            # Search for cases
            case_links = self.search_cases(query, max_results=cases_per_query)
            print(f"📊 Found {len(case_links)} cases")
            
            # Scrape details for each case
            for i, case_info in enumerate(case_links, 1):
                print(f"\n[{i}/{len(case_links)}] Processing case...")
                
                case_details = self.scrape_case_details(case_info['url'])
                if case_details:
                    case_details['search_query'] = query
                    all_cases.append(case_details)
                    
                    # Save incrementally
                    if len(all_cases) % 10 == 0:
                        self.save_cases(all_cases, f"cases_partial_{len(all_cases)}.json")
                        print(f"💾 Saved {len(all_cases)} cases")
            
            print(f"\n✅ Completed query: {query}")
            print(f"📊 Total cases collected: {len(all_cases)}")
            
        return all_cases
    
    def save_cases(self, cases: List[Dict], filename: str = None):
        """
        Save scraped cases to JSON file
        """
        if filename is None:
            filename = f"indian_cases_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        filepath = os.path.join(self.output_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(cases, f, ensure_ascii=False, indent=2)
        
        print(f"💾 Saved {len(cases)} cases to {filepath}")
        return filepath


def main():
    """
    Main function to run the scraper
    """
    print("🏛️ Indian Legal Case Scraper")
    print("=" * 60)
    
    # Initialize scraper
    scraper = IndianLegalCaseScraper()
    
    # Import configuration
    from config import Config
    
    # Get legal queries and cases per query from config
    legal_queries = Config.LEGAL_CATEGORIES
    cases_per_query = Config.MAX_CASES_PER_QUERY
    
    print(f"📋 Will scrape cases for {len(legal_queries)} queries")
    print(f"🎯 Target: ~{cases_per_query} cases per query = {len(legal_queries) * cases_per_query} total cases")
    print()
    
    # Start scraping
    all_cases = scraper.scrape_bulk_cases(legal_queries, cases_per_query=cases_per_query)
    
    # Save final results
    final_file = scraper.save_cases(all_cases, "indian_legal_cases_complete.json")
    
    print("\n" + "=" * 60)
    print(f"🎉 Scraping Complete!")
    print(f"📊 Total cases collected: {len(all_cases)}")
    print(f"💾 Saved to: {final_file}")
    print("=" * 60)


if __name__ == "__main__":
    main()