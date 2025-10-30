"""
Advanced Legal Case Scraper for Indian Law - IndianKanoon.org
Targets: 5,000+ diverse REAL cases from public legal database
Categories: Constitutional, Criminal, Civil, Family, Corporate, Labor, Tax, IPR

IndianKanoon.org is a public legal database that makes Indian case law freely accessible.
This scraper respects rate limits and terms of service.
"""

import os
import json
import time
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from typing import List, Dict
import re
from urllib.parse import urljoin, quote
import hashlib
from requests.adapters import HTTPAdapter
try:
    from urllib3.util.retry import Retry
except ImportError:
    from requests.packages.urllib3.util.retry import Retry

class LegalCaseScraper:
    """Scrape Indian legal cases from multiple public sources"""
    
    def __init__(self):
        # Create session with retry strategy
        self.session = requests.Session()
        try:
            retry_strategy = Retry(
                total=3,
                backoff_factor=1,
                status_forcelist=[429, 500, 502, 503, 504],
            )
            adapter = HTTPAdapter(max_retries=retry_strategy)
            self.session.mount("http://", adapter)
            self.session.mount("https://", adapter)
        except Exception:
            # Fallback if retry setup fails
            pass
        
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
        })
        
        self.cases = []
        self.seen_case_ids = set()
        self.base_delay = 2  # Respectful delay between requests
        
        # Load existing cases to avoid duplicates
        self.load_existing_cases()
        
        # Case categories to scrape
        self.categories = [
            'constitutional',
            'criminal',
            'civil',
            'family',
            'corporate',
            'labor',
            'tax',
            'intellectual-property',
            'consumer',
            'environmental'
        ]
        
    def load_existing_cases(self):
        """Load existing cases from constitution.json"""
        try:
            existing_file = './data/constitution/constitution.json'
            if os.path.exists(existing_file):
                with open(existing_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        self.cases = data
                        print(f"✅ Loaded {len(self.cases)} existing cases")
                        # Track existing case IDs
                        for case in self.cases:
                            case_id = self.generate_case_id(case.get('title', ''))
                            self.seen_case_ids.add(case_id)
        except Exception as e:
            print(f"⚠️  Could not load existing cases: {e}")
    
    def generate_case_id(self, title: str) -> str:
        """Generate unique case ID from title"""
        return hashlib.md5(title.lower().strip().encode()).hexdigest()[:16]
    
    def is_duplicate(self, title: str) -> bool:
        """Check if case already exists"""
        case_id = self.generate_case_id(title)
        return case_id in self.seen_case_ids
    
    def scrape_indiankanoon(self, query: str, max_results: int = 50, page: int = 0) -> List[Dict]:
        """
        Scrape cases from IndianKanoon.org (public legal database)
        This is a legal and ethical source for Indian case law
        """
        cases = []
        print(f"\n🔍 Searching IndianKanoon: '{query}' (page {page+1})")
        
        try:
            # IndianKanoon search URL with pagination
            base_url = "https://indiankanoon.org"
            search_url = f"{base_url}/search/?formInput={quote(query)}&pagenum={page}"
            
            print(f"  📡 Fetching: {search_url}")
            response = self.session.get(search_url, timeout=15)
            
            if response.status_code != 200:
                print(f"  ❌ HTTP {response.status_code}")
                return cases
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # IndianKanoon uses <div class="result"> for each case
            results = soup.find_all('div', class_='result')
            
            if not results:
                print(f"  ⚠️  No results found (might be end of results)")
                return cases
            
            print(f"  📄 Found {len(results)} results on this page")
            
            for idx, result in enumerate(results[:max_results]):
                try:
                    # Extract case title and URL
                    title_elem = result.find('a', class_='result_title')
                    if not title_elem:
                        # Try alternative structure
                        title_elem = result.find('a')
                    
                    if not title_elem:
                        continue
                    
                    title = title_elem.text.strip()
                    case_url = urljoin(base_url, title_elem.get('href', ''))
                    
                    # Skip duplicates
                    if self.is_duplicate(title):
                        print(f"  ⏭️  Duplicate: {title[:50]}...")
                        continue
                    
                    # Extract snippet/preview
                    snippet_elem = result.find('div', class_='result_info') or result.find('p')
                    snippet_text = snippet_elem.text.strip() if snippet_elem else ''
                    
                    # Fetch full case details
                    print(f"  🔄 [{idx+1}/{len(results)}] Fetching: {title[:50]}...")
                    case_details = self.fetch_case_details(case_url)
                    
                    if not case_details.get('content'):
                        print(f"  ⚠️  No content found, using snippet")
                        case_details['content'] = snippet_text
                    
                    # Build case object
                    case = {
                        'title': title,
                        'category': query,
                        'topic': case_details.get('topic', query),
                        'content': case_details.get('content', snippet_text)[:8000],  # Limit size
                        'court': case_details.get('court', self.extract_court_from_title(title)),
                        'year': case_details.get('year', self.extract_year_from_title(title)),
                        'citation': case_details.get('citation', ''),
                        'keywords': case_details.get('keywords', [query]),
                        'url': case_url,
                        'source': 'IndianKanoon.org',
                        'scraped_date': datetime.now().isoformat()
                    }
                    
                    cases.append(case)
                    case_id = self.generate_case_id(title)
                    self.seen_case_ids.add(case_id)
                    
                    print(f"  ✅ Scraped: {title[:50]}... ({len(case_details.get('content', ''))} chars)")
                    
                    # Rate limiting - be respectful to IndianKanoon
                    time.sleep(self.base_delay)
                    
                except KeyboardInterrupt:
                    print("\n⚠️  Interrupted by user")
                    raise
                except Exception as e:
                    print(f"  ⚠️  Error processing result: {e}")
                    continue
            
            print(f"✅ Scraped {len(cases)} new cases from this page")
            
        except KeyboardInterrupt:
            raise
        except Exception as e:
            print(f"❌ Error scraping IndianKanoon: {e}")
            import traceback
            traceback.print_exc()
        
        return cases
    
    def fetch_case_details(self, url: str) -> Dict:
        """Fetch detailed case information from IndianKanoon case page"""
        try:
            response = self.session.get(url, timeout=15)
            if response.status_code != 200:
                print(f"    ❌ HTTP {response.status_code}")
                return {}
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # IndianKanoon structure: Main content is in <div class="judgments">
            # Try multiple selectors for robustness
            content_elem = (
                soup.find('div', class_='judgments') or
                soup.find('div', class_='doc') or 
                soup.find('div', id='judgment') or
                soup.find('pre')  # Some cases use <pre> tags
            )
            
            content = ''
            if content_elem:
                # Get text and clean up
                content = content_elem.get_text(separator='\n', strip=True)
                # Remove excessive whitespace
                content = re.sub(r'\n\s*\n\s*\n+', '\n\n', content)
            
            # Extract court name - IndianKanoon uses <span> or <a> with court info
            court = 'Unknown Court'
            court_elem = soup.find('span', text=re.compile(r'(Supreme Court|High Court)', re.I))
            if not court_elem:
                court_elem = soup.find('a', href=re.compile(r'/browse/'))
            if court_elem:
                court = court_elem.text.strip()
            
            # Extract citation - usually in bold or specific class
            citation = ''
            citation_elem = soup.find('div', class_='doc_citations') or soup.find('b', text=re.compile(r'\d{4}'))
            if citation_elem:
                citation = citation_elem.text.strip()
            
            # Extract year from content or citation
            year = self.extract_year_from_content(content) or self.extract_year_from_content(citation)
            
            # Extract keywords/topics from metadata
            keywords = []
            keyword_elems = soup.find_all('a', href=re.compile(r'/search/'))
            for elem in keyword_elems[:10]:  # Limit to first 10
                kw = elem.text.strip()
                if len(kw) > 3 and kw not in keywords:
                    keywords.append(kw)
            
            result = {
                'content': content[:8000] if content else '',
                'court': court,
                'citation': citation,
                'year': year,
                'keywords': keywords,
                'topic': keywords[0] if keywords else ''
            }
            
            return result
            
        except KeyboardInterrupt:
            raise
        except Exception as e:
            print(f"    ⚠️  Error fetching details: {e}")
            return {}
    
    def extract_court_from_title(self, title: str) -> str:
        """Extract court name from case title"""
        court_keywords = [
            'Supreme Court',
            'High Court',
            'District Court',
            'Sessions Court',
            'Tribunal',
            'Commission'
        ]
        
        for keyword in court_keywords:
            if keyword.lower() in title.lower():
                return keyword
        
        return 'Unknown Court'
    
    def extract_year_from_title(self, title: str) -> str:
        """Extract year from case title"""
        year_match = re.search(r'\b(19|20)\d{2}\b', title)
        return year_match.group(0) if year_match else 'Unknown'
    
    def extract_year_from_content(self, content: str) -> str:
        """Extract year from case content"""
        # Look for dates in format DD/MM/YYYY or DD-MM-YYYY
        date_match = re.search(r'\b\d{1,2}[-/]\d{1,2}[-/](19|20)\d{2}\b', content[:500])
        if date_match:
            year_match = re.search(r'(19|20)\d{2}', date_match.group(0))
            return year_match.group(0) if year_match else 'Unknown'
        return 'Unknown'
    
    def scrape_landmark_cases(self) -> List[Dict]:
        """Scrape landmark Indian Supreme Court cases"""
        print("\n🏛️  Scraping Landmark Cases...")
        
        landmark_queries = [
            'Kesavananda Bharati',
            'Maneka Gandhi',
            'Vishaka',
            'Indra Sawhney',
            'Minerva Mills',
            'ADM Jabalpur',
            'Golaknath',
            'Shah Bano',
            'MC Mehta',
            'Olga Tellis'
        ]
        
        cases = []
        for query in landmark_queries:
            cases.extend(self.scrape_indiankanoon(query, max_results=5))
            time.sleep(2)  # Rate limiting
        
        return cases
    
    def scrape_by_category(self, category: str, num_cases: int = 100) -> List[Dict]:
        """Scrape cases by legal category with pagination"""
        
        category_queries = {
            'constitutional': ['fundamental rights Supreme Court', 'Article 21', 'Article 32', 'constitutional law'],
            'criminal': ['IPC murder', 'CrPC bail', 'rape case', 'NDPS Act'],
            'civil': ['contract breach', 'property dispute', 'tort damages', 'civil suit'],
            'family': ['divorce decree', 'child custody', 'maintenance order', 'Hindu Marriage Act'],
            'corporate': ['company law breach', 'SEBI regulations', 'insolvency bankruptcy', 'merger acquisition'],
            'labor': ['wrongful termination', 'Industrial Disputes', 'EPF contribution', 'labor law'],
            'tax': ['income tax assessment', 'GST evasion', 'customs duty', 'tax appeal'],
            'intellectual-property': ['trademark infringement', 'patent violation', 'copyright dispute', 'IP case'],
            'consumer': ['consumer complaint', 'deficiency service', 'consumer forum', 'unfair trade'],
            'environmental': ['environmental violation', 'pollution control', 'forest conservation', 'NGT order']
        }
        
        cases = []
        queries = category_queries.get(category, [category])
        
        # Calculate how many cases per query and pages needed
        cases_per_query = num_cases // len(queries)
        pages_per_query = max(1, cases_per_query // 10)  # ~10 cases per page
        
        for query in queries:
            query_cases = []
            for page in range(pages_per_query):
                if len(query_cases) >= cases_per_query:
                    break
                
                page_cases = self.scrape_indiankanoon(query, max_results=15, page=page)
                query_cases.extend(page_cases)
                
                if not page_cases:  # No more results
                    break
                
                # Rate limiting between pages
                time.sleep(self.base_delay)
            
            cases.extend(query_cases)
            print(f"  📊 Collected {len(query_cases)} cases for query '{query}'")
            
            # Rate limiting between queries
            time.sleep(self.base_delay)
        
        return cases
    
    def scrape_all_categories(self, target: int = 5000):
        """Scrape cases across all categories to reach target"""
        print(f"\n{'='*70}")
        print(f"🎯 TARGET: {target} diverse legal cases")
        print(f"📊 Currently have: {len(self.cases)} cases")
        print(f"🔢 Need to scrape: {max(0, target - len(self.cases))} more cases")
        print(f"{'='*70}\n")
        
        # Start with landmark cases
        if len(self.cases) < target:
            landmark = self.scrape_landmark_cases()
            self.cases.extend(landmark)
            print(f"📊 Total cases: {len(self.cases)}/{target}")
        
        # Scrape by category
        cases_per_category = (target - len(self.cases)) // len(self.categories)
        
        for category in self.categories:
            if len(self.cases) >= target:
                break
            
            print(f"\n📂 Category: {category.upper()}")
            category_cases = self.scrape_by_category(category, cases_per_category)
            self.cases.extend(category_cases)
            
            print(f"📊 Total cases: {len(self.cases)}/{target}")
            
            # Save progress periodically
            self.save_cases()
            
            time.sleep(3)  # Rate limiting between categories
        
        print(f"\n{'='*70}")
        print(f"✅ SCRAPING COMPLETE!")
        print(f"📊 Total cases collected: {len(self.cases)}")
        print(f"{'='*70}\n")
    
    def save_cases(self):
        """Save cases to JSON file"""
        try:
            output_dir = './data/constitution'
            os.makedirs(output_dir, exist_ok=True)
            
            output_file = os.path.join(output_dir, 'constitution.json')
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(self.cases, f, indent=2, ensure_ascii=False)
            
            print(f"💾 Saved {len(self.cases)} cases to {output_file}")
            
        except Exception as e:
            print(f"❌ Error saving cases: {e}")
    
    def generate_statistics(self):
        """Generate statistics about scraped cases"""
        print("\n" + "="*70)
        print("📊 CASE STATISTICS")
        print("="*70)
        
        # Category distribution
        categories = {}
        courts = {}
        years = {}
        
        for case in self.cases:
            cat = case.get('category', 'Unknown')
            categories[cat] = categories.get(cat, 0) + 1
            
            court = case.get('court', 'Unknown')
            courts[court] = courts.get(court, 0) + 1
            
            year = case.get('year', 'Unknown')
            years[year] = years.get(year, 0) + 1
        
        print(f"\n📂 Cases by Category:")
        for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"  {cat}: {count}")
        
        print(f"\n🏛️  Cases by Court:")
        for court, count in sorted(courts.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"  {court}: {count}")
        
        print(f"\n📅 Cases by Year:")
        for year, count in sorted(years.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"  {year}: {count}")
        
        print("\n" + "="*70)

def main():
    """Main execution"""
    print("🏛️  INDIAN LEGAL CASE SCRAPER - IndianKanoon.org")
    print("="*70)
    print("Target: 10,000 REAL diverse legal cases")
    print("Source: IndianKanoon.org (public legal database)")
    print("Estimated time: 3-4 hours (respectful rate limiting)")
    print("="*70)
    print("\n⚠️  IMPORTANT:")
    print("  • This will take time due to respectful rate limiting")
    print("  • Cases are scraped from public legal database")
    print("  • You can stop anytime (Ctrl+C) - progress is saved")
    print("  • Resume by running script again")
    print("="*70)
    
    try:
        scraper = LegalCaseScraper()
        
        # Scrape to reach 10,000 real cases
        scraper.scrape_all_categories(target=10000)
        
        # Save final results
        scraper.save_cases()
        
        # Generate statistics
        scraper.generate_statistics()
        
        print("\n" + "="*70)
        print("✅ SCRAPING COMPLETE!")
        print(f"📊 Total: {len(scraper.cases)} real legal cases")
        print("="*70)
        print("\n📝 Next steps:")
        print("  1. Review cases in: ./data/constitution/constitution.json")
        print("  2. Migrate to Pinecone: python fast_migrate_pinecone.py")
        print("  3. Deploy to Vercel")
        print("="*70)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  INTERRUPTED BY USER")
        print("="*70)
        print(f"📊 Progress saved: {len(scraper.cases)} cases")
        print("💾 Saved to: ./data/constitution/constitution.json")
        print("\n▶️  Resume: Run 'python scrape_legal_cases.py' again")
        print("="*70)
        scraper.save_cases()

if __name__ == '__main__':
    main()
