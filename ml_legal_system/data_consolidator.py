"""
Data Consolidation and Validation Module
Consolidates all scraped legal case data and validates integrity
"""

import json
import os
import hashlib
from typing import List, Dict, Set, Tuple
from dataclasses import dataclass
from datetime import datetime
import glob


@dataclass
class DataQualityReport:
    """Data quality report structure"""
    total_files_processed: int
    total_cases_loaded: int
    unique_cases_after_dedup: int
    duplicates_removed: int
    invalid_cases_removed: int
    data_quality_score: float
    processing_time_seconds: float
    file_sizes_mb: Dict[str, float]
    validation_errors: List[str]
    case_statistics: Dict[str, any]


class DataConsolidator:
    """
    Consolidates and validates scraped legal case data
    """
    
    def __init__(self, data_dir: str = "data/legal_cases"):
        """
        Initialize data consolidator
        
        Args:
            data_dir: Directory containing scraped case files
        """
        self.data_dir = data_dir
        self.all_cases = []
        self.unique_cases = []
        self.validation_errors = []
        self.case_hashes = set()
        
    def load_all_cases(self) -> List[Dict]:
        """
        Load and merge all partial case files with complete dataset
        
        Returns:
            List of all loaded cases
        """
        print("📚 Loading all scraped legal case data...")
        print("=" * 60)
        
        all_cases = []
        file_count = 0
        
        # Load complete dataset first
        complete_file = os.path.join(self.data_dir, "indian_legal_cases_complete.json")
        if os.path.exists(complete_file):
            print(f"📖 Loading complete dataset: {complete_file}")
            try:
                with open(complete_file, 'r', encoding='utf-8') as f:
                    complete_cases = json.load(f)
                all_cases.extend(complete_cases)
                file_count += 1
                print(f"✅ Loaded {len(complete_cases)} cases from complete dataset")
            except Exception as e:
                error_msg = f"Error loading complete dataset: {e}"
                print(f"❌ {error_msg}")
                self.validation_errors.append(error_msg)
        
        # Load all partial files
        partial_pattern = os.path.join(self.data_dir, "cases_partial_*.json")
        partial_files = glob.glob(partial_pattern)
        partial_files.sort(key=lambda x: int(x.split('_')[-1].split('.')[0]))
        
        print(f"\n📂 Found {len(partial_files)} partial case files")
        
        for file_path in partial_files:
            try:
                print(f"📖 Loading: {os.path.basename(file_path)}")
                with open(file_path, 'r', encoding='utf-8') as f:
                    partial_cases = json.load(f)
                
                if partial_cases:  # Only add non-empty files
                    all_cases.extend(partial_cases)
                    file_count += 1
                    print(f"   ✅ Added {len(partial_cases)} cases")
                else:
                    print(f"   ⚠️  Empty file skipped")
                    
            except Exception as e:
                error_msg = f"Error loading {file_path}: {e}"
                print(f"   ❌ {error_msg}")
                self.validation_errors.append(error_msg)
        
        self.all_cases = all_cases
        print(f"\n📊 Total loaded: {len(all_cases)} cases from {file_count} files")
        return all_cases
    
    def _generate_case_hash(self, case: Dict) -> str:
        """
        Generate unique hash for a case based on key fields
        
        Args:
            case: Case dictionary
            
        Returns:
            SHA256 hash string
        """
        # Use URL and scraped_at as primary identifiers
        # If not available, use title + court + date
        key_fields = []
        
        if case.get('url'):
            key_fields.append(case['url'])
        if case.get('scraped_at'):
            key_fields.append(case['scraped_at'])
        if case.get('title'):
            key_fields.append(case['title'])
        if case.get('court'):
            key_fields.append(case['court'])
        if case.get('date'):
            key_fields.append(case['date'])
        
        # Create hash from concatenated key fields
        hash_input = '|'.join(str(field) for field in key_fields)
        return hashlib.sha256(hash_input.encode('utf-8')).hexdigest()
    
    def remove_duplicates(self, cases: List[Dict]) -> List[Dict]:
        """
        Remove duplicate cases based on content hash
        
        Args:
            cases: List of cases to deduplicate
            
        Returns:
            List of unique cases
        """
        print("\n🔍 Removing duplicate cases...")
        
        unique_cases = []
        seen_hashes = set()
        duplicates_count = 0
        
        for i, case in enumerate(cases):
            case_hash = self._generate_case_hash(case)
            
            if case_hash not in seen_hashes:
                seen_hashes.add(case_hash)
                unique_cases.append(case)
            else:
                duplicates_count += 1
            
            if (i + 1) % 100 == 0:
                print(f"   Processed {i + 1}/{len(cases)} cases...")
        
        print(f"✅ Removed {duplicates_count} duplicate cases")
        print(f"📊 Unique cases: {len(unique_cases)}")
        
        self.unique_cases = unique_cases
        self.case_hashes = seen_hashes
        return unique_cases
    
    def validate_case_structure(self, case: Dict) -> Tuple[bool, List[str]]:
        """
        Validate individual case data structure
        
        Args:
            case: Case dictionary to validate
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        # Required fields check
        required_fields = ['url', 'scraped_at']
        for field in required_fields:
            if field not in case or not case[field]:
                errors.append(f"Missing required field: {field}")
        
        # Optional but important fields
        important_fields = ['title', 'court', 'date', 'full_text']
        missing_important = [field for field in important_fields 
                           if field not in case or not case[field]]
        
        if len(missing_important) == len(important_fields):
            errors.append("Missing all important content fields (title, court, date, full_text)")
        
        # Data type validation
        if 'citations' in case and not isinstance(case['citations'], list):
            errors.append("Citations field must be a list")
        
        if 'legal_acts' in case and not isinstance(case['legal_acts'], list):
            errors.append("Legal_acts field must be a list")
        
        # URL validation
        if 'url' in case and case['url']:
            if not case['url'].startswith('http'):
                errors.append("Invalid URL format")
        
        return len(errors) == 0, errors
    
    def validate_cases(self, cases: List[Dict]) -> List[Dict]:
        """
        Validate all cases and remove invalid ones
        
        Args:
            cases: List of cases to validate
            
        Returns:
            List of valid cases
        """
        print("\n🔍 Validating case data integrity...")
        
        valid_cases = []
        invalid_count = 0
        
        for i, case in enumerate(cases):
            is_valid, case_errors = self.validate_case_structure(case)
            
            if is_valid:
                valid_cases.append(case)
            else:
                invalid_count += 1
                error_msg = f"Invalid case {i}: {'; '.join(case_errors)}"
                self.validation_errors.append(error_msg)
            
            if (i + 1) % 100 == 0:
                print(f"   Validated {i + 1}/{len(cases)} cases...")
        
        print(f"✅ Valid cases: {len(valid_cases)}")
        print(f"❌ Invalid cases removed: {invalid_count}")
        
        return valid_cases
    
    def analyze_case_statistics(self, cases: List[Dict]) -> Dict[str, any]:
        """
        Generate comprehensive statistics about the case data
        
        Args:
            cases: List of cases to analyze
            
        Returns:
            Dictionary of statistics
        """
        print("\n📊 Analyzing case statistics...")
        
        stats = {
            'total_cases': len(cases),
            'courts': {},
            'years': {},
            'search_queries': {},
            'has_full_text': 0,
            'has_title': 0,
            'has_judges': 0,
            'has_citations': 0,
            'has_legal_acts': 0,
            'avg_text_length': 0,
            'avg_citations_count': 0,
            'date_range': {'earliest': None, 'latest': None}
        }
        
        text_lengths = []
        citation_counts = []
        
        for case in cases:
            # Court statistics
            court = case.get('court', 'Unknown')
            stats['courts'][court] = stats['courts'].get(court, 0) + 1
            
            # Year statistics
            date_str = case.get('date', '')
            if date_str:
                try:
                    # Extract year from various date formats
                    year = None
                    if '-' in date_str:
                        year = date_str.split('-')[0]
                    elif '/' in date_str:
                        parts = date_str.split('/')
                        year = parts[-1] if len(parts[-1]) == 4 else parts[0]
                    
                    if year and year.isdigit():
                        stats['years'][year] = stats['years'].get(year, 0) + 1
                        
                        # Track date range
                        if not stats['date_range']['earliest'] or year < stats['date_range']['earliest']:
                            stats['date_range']['earliest'] = year
                        if not stats['date_range']['latest'] or year > stats['date_range']['latest']:
                            stats['date_range']['latest'] = year
                            
                except Exception:
                    pass
            
            # Search query statistics
            query = case.get('search_query', 'Unknown')
            stats['search_queries'][query] = stats['search_queries'].get(query, 0) + 1
            
            # Field presence statistics
            if case.get('full_text'):
                stats['has_full_text'] += 1
                text_lengths.append(len(case['full_text']))
            
            if case.get('title'):
                stats['has_title'] += 1
            
            if case.get('judges'):
                stats['has_judges'] += 1
            
            if case.get('citations'):
                stats['has_citations'] += 1
                citation_counts.append(len(case['citations']))
            
            if case.get('legal_acts'):
                stats['has_legal_acts'] += 1
        
        # Calculate averages
        if text_lengths:
            stats['avg_text_length'] = sum(text_lengths) / len(text_lengths)
        
        if citation_counts:
            stats['avg_citations_count'] = sum(citation_counts) / len(citation_counts)
        
        # Sort top courts and years
        stats['top_courts'] = sorted(stats['courts'].items(), 
                                   key=lambda x: x[1], reverse=True)[:10]
        stats['top_years'] = sorted(stats['years'].items(), 
                                  key=lambda x: x[1], reverse=True)[:10]
        stats['top_queries'] = sorted(stats['search_queries'].items(), 
                                    key=lambda x: x[1], reverse=True)[:10]
        
        return stats
    
    def calculate_data_quality_score(self, cases: List[Dict], stats: Dict) -> float:
        """
        Calculate overall data quality score (0-100)
        
        Args:
            cases: List of cases
            stats: Case statistics
            
        Returns:
            Quality score as percentage
        """
        if not cases:
            return 0.0
        
        total_cases = len(cases)
        
        # Scoring criteria (weights)
        scores = {
            'has_full_text': (stats['has_full_text'] / total_cases) * 30,  # 30%
            'has_title': (stats['has_title'] / total_cases) * 20,          # 20%
            'has_court': (len([c for c in cases if c.get('court')]) / total_cases) * 15,  # 15%
            'has_date': (len([c for c in cases if c.get('date')]) / total_cases) * 15,    # 15%
            'has_judges': (stats['has_judges'] / total_cases) * 10,        # 10%
            'has_citations': (stats['has_citations'] / total_cases) * 10,  # 10%
        }
        
        total_score = sum(scores.values())
        return min(100.0, total_score)
    
    def get_file_sizes(self) -> Dict[str, float]:
        """
        Get file sizes in MB for all data files
        
        Returns:
            Dictionary of filename -> size in MB
        """
        file_sizes = {}
        
        # Check complete dataset
        complete_file = os.path.join(self.data_dir, "indian_legal_cases_complete.json")
        if os.path.exists(complete_file):
            size_mb = os.path.getsize(complete_file) / (1024 * 1024)
            file_sizes['indian_legal_cases_complete.json'] = round(size_mb, 2)
        
        # Check partial files
        partial_pattern = os.path.join(self.data_dir, "cases_partial_*.json")
        partial_files = glob.glob(partial_pattern)
        
        total_partial_size = 0
        for file_path in partial_files:
            size_mb = os.path.getsize(file_path) / (1024 * 1024)
            total_partial_size += size_mb
        
        file_sizes['all_partial_files_combined'] = round(total_partial_size, 2)
        file_sizes['total_data_size'] = round(sum(file_sizes.values()), 2)
        
        return file_sizes
    
    def generate_quality_report(self, processing_time: float) -> DataQualityReport:
        """
        Generate comprehensive data quality report
        
        Args:
            processing_time: Time taken for processing in seconds
            
        Returns:
            DataQualityReport object
        """
        print("\n📋 Generating data quality report...")
        
        stats = self.analyze_case_statistics(self.unique_cases)
        quality_score = self.calculate_data_quality_score(self.unique_cases, stats)
        file_sizes = self.get_file_sizes()
        
        report = DataQualityReport(
            total_files_processed=len(glob.glob(os.path.join(self.data_dir, "*.json"))),
            total_cases_loaded=len(self.all_cases),
            unique_cases_after_dedup=len(self.unique_cases),
            duplicates_removed=len(self.all_cases) - len(self.unique_cases),
            invalid_cases_removed=len(self.all_cases) - len(self.unique_cases) - len([e for e in self.validation_errors if "Invalid case" in e]),
            data_quality_score=quality_score,
            processing_time_seconds=processing_time,
            file_sizes_mb=file_sizes,
            validation_errors=self.validation_errors,
            case_statistics=stats
        )
        
        return report
    
    def save_consolidated_data(self, output_file: str = None) -> str:
        """
        Save consolidated and validated data to file
        
        Args:
            output_file: Output file path (optional)
            
        Returns:
            Path to saved file
        """
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = os.path.join(self.data_dir, f"consolidated_cases_{timestamp}.json")
        
        print(f"\n💾 Saving consolidated data to: {output_file}")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.unique_cases, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Saved {len(self.unique_cases)} unique cases")
        return output_file
    
    def print_quality_report(self, report: DataQualityReport):
        """
        Print formatted data quality report
        
        Args:
            report: DataQualityReport to print
        """
        print("\n" + "=" * 80)
        print("📊 DATA QUALITY REPORT")
        print("=" * 80)
        
        print(f"\n📁 FILE PROCESSING:")
        print(f"   • Total files processed: {report.total_files_processed}")
        print(f"   • Total data size: {report.file_sizes_mb.get('total_data_size', 0)} MB")
        print(f"   • Processing time: {report.processing_time_seconds:.2f} seconds")
        
        print(f"\n📚 CASE STATISTICS:")
        print(f"   • Total cases loaded: {report.total_cases_loaded:,}")
        print(f"   • Unique cases after deduplication: {report.unique_cases_after_dedup:,}")
        print(f"   • Duplicates removed: {report.duplicates_removed:,}")
        print(f"   • Invalid cases removed: {report.invalid_cases_removed}")
        
        print(f"\n⭐ DATA QUALITY SCORE: {report.data_quality_score:.1f}/100")
        
        stats = report.case_statistics
        print(f"\n📊 CONTENT ANALYSIS:")
        print(f"   • Cases with full text: {stats['has_full_text']:,} ({stats['has_full_text']/stats['total_cases']*100:.1f}%)")
        print(f"   • Cases with title: {stats['has_title']:,} ({stats['has_title']/stats['total_cases']*100:.1f}%)")
        print(f"   • Cases with judges: {stats['has_judges']:,} ({stats['has_judges']/stats['total_cases']*100:.1f}%)")
        print(f"   • Cases with citations: {stats['has_citations']:,} ({stats['has_citations']/stats['total_cases']*100:.1f}%)")
        print(f"   • Average text length: {stats['avg_text_length']:.0f} characters")
        
        if stats['top_courts']:
            print(f"\n🏛️ TOP COURTS:")
            for court, count in stats['top_courts'][:5]:
                print(f"   • {court}: {count:,} cases")
        
        if stats['top_years']:
            print(f"\n📅 TOP YEARS:")
            for year, count in stats['top_years'][:5]:
                print(f"   • {year}: {count:,} cases")
        
        if stats['date_range']['earliest'] and stats['date_range']['latest']:
            print(f"\n📆 DATE RANGE: {stats['date_range']['earliest']} - {stats['date_range']['latest']}")
        
        if report.validation_errors:
            print(f"\n⚠️ VALIDATION ERRORS ({len(report.validation_errors)}):")
            for error in report.validation_errors[:10]:  # Show first 10 errors
                print(f"   • {error}")
            if len(report.validation_errors) > 10:
                print(f"   ... and {len(report.validation_errors) - 10} more errors")
        
        print("\n" + "=" * 80)


def main():
    """
    Main function to consolidate and validate legal case data
    """
    print("🚀 Legal Case Data Consolidation and Validation")
    print("=" * 80)
    
    start_time = datetime.now()
    
    # Initialize consolidator
    consolidator = DataConsolidator()
    
    try:
        # Step 1: Load all cases
        all_cases = consolidator.load_all_cases()
        
        if not all_cases:
            print("❌ No cases loaded. Check data directory and files.")
            return
        
        # Step 2: Remove duplicates
        unique_cases = consolidator.remove_duplicates(all_cases)
        
        # Step 3: Validate cases
        valid_cases = consolidator.validate_cases(unique_cases)
        consolidator.unique_cases = valid_cases
        
        # Step 4: Generate quality report
        processing_time = (datetime.now() - start_time).total_seconds()
        report = consolidator.generate_quality_report(processing_time)
        
        # Step 5: Print report
        consolidator.print_quality_report(report)
        
        # Step 6: Save consolidated data
        output_file = consolidator.save_consolidated_data()
        
        print(f"\n🎉 Data consolidation completed successfully!")
        print(f"📁 Consolidated data saved to: {output_file}")
        print(f"📊 Final dataset: {len(valid_cases):,} unique, validated cases")
        
        # Save report to JSON
        report_file = output_file.replace('.json', '_quality_report.json')
        with open(report_file, 'w', encoding='utf-8') as f:
            # Convert dataclass to dict for JSON serialization
            report_dict = {
                'total_files_processed': report.total_files_processed,
                'total_cases_loaded': report.total_cases_loaded,
                'unique_cases_after_dedup': report.unique_cases_after_dedup,
                'duplicates_removed': report.duplicates_removed,
                'invalid_cases_removed': report.invalid_cases_removed,
                'data_quality_score': report.data_quality_score,
                'processing_time_seconds': report.processing_time_seconds,
                'file_sizes_mb': report.file_sizes_mb,
                'validation_errors': report.validation_errors,
                'case_statistics': report.case_statistics,
                'generated_at': datetime.now().isoformat()
            }
            json.dump(report_dict, f, ensure_ascii=False, indent=2)
        
        print(f"📋 Quality report saved to: {report_file}")
        
    except Exception as e:
        print(f"❌ Error during consolidation: {e}")
        raise


if __name__ == "__main__":
    main()