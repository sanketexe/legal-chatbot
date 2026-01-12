"""
Automated Legal Research Summary System
Generate comprehensive summaries from multiple cases
"""

import json
from pathlib import Path
from typing import Dict, List, Optional
from collections import defaultdict
from datetime import datetime
import re


class LegalResearchSummarizer:
    """
    AI-powered legal research summarization
    Features:
    - Multi-case analysis
    - Key points extraction
    - Comparative analysis
    - Citation management
    """
    
    def __init__(self, vector_db=None):
        self.vector_db = vector_db
        self.summaries_dir = Path("data/research_summaries")
        self.summaries_dir.mkdir(parents=True, exist_ok=True)
    
    def summarize_cases(self, cases: List[Dict], topic: str) -> Dict:
        """
        Generate comprehensive summary from multiple cases
        
        Args:
            cases: List of case dictionaries
            topic: Research topic/query
            
        Returns:
            Dict with summary, key points, analysis
        """
        if not cases:
            return {'error': 'No cases provided'}
        
        print(f"\n📚 Summarizing {len(cases)} cases on: {topic}")
        
        # Extract key information
        key_points = self._extract_key_points(cases)
        
        # Identify legal principles
        principles = self._identify_legal_principles(cases)
        
        # Compare outcomes
        outcome_analysis = self._analyze_outcomes(cases)
        
        # Extract citations
        citations = self._extract_citations(cases)
        
        # Generate summary text
        summary_text = self._generate_summary_text(
            topic, cases, key_points, principles, outcome_analysis
        )
        
        # Create timeline if dates available
        timeline = self._create_timeline(cases)
        
        result = {
            'topic': topic,
            'num_cases': len(cases),
            'summary': summary_text,
            'key_points': key_points,
            'legal_principles': principles,
            'outcome_analysis': outcome_analysis,
            'citations': citations,
            'timeline': timeline,
            'generated_at': datetime.now().isoformat()
        }
        
        # Save summary
        self._save_summary(topic, result)
        
        return result
    
    def _extract_key_points(self, cases: List[Dict]) -> List[Dict]:
        """Extract key points from each case"""
        key_points = []
        
        for i, case in enumerate(cases, 1):
            case_text = case.get('text', case.get('document', ''))
            metadata = case.get('metadata', {})
            
            point = {
                'case_number': i,
                'title': metadata.get('title', f'Case {i}'),
                'category': metadata.get('category', 'Unknown'),
                'key_facts': self._extract_facts(case_text),
                'legal_issues': self._extract_legal_issues(case_text),
                'holding': self._extract_holding(case_text),
                'outcome': metadata.get('outcome', 'Unknown')
            }
            
            key_points.append(point)
        
        return key_points
    
    def _extract_facts(self, text: str) -> str:
        """Extract key facts from case text"""
        # Look for facts section
        facts_match = re.search(
            r'(?:facts?|background|circumstances)[:\s]+(.*?)(?=\n\n|issue|held|question)',
            text,
            re.IGNORECASE | re.DOTALL
        )
        
        if facts_match:
            facts = facts_match.group(1).strip()
            # Truncate if too long
            if len(facts) > 500:
                facts = facts[:500] + "..."
            return facts
        
        # Fallback: take first 3 sentences
        sentences = re.split(r'[.!?]+', text)
        return '. '.join(sentences[:3]) + '.'
    
    def _extract_legal_issues(self, text: str) -> List[str]:
        """Extract legal issues/questions"""
        issues = []
        
        # Look for issue/question sections
        issue_patterns = [
            r'(?:issue|question|point)[:\s]+(.*?)(?=\n\n|held|ruling)',
            r'whether\s+(.*?)[.?]',
            r'the\s+question\s+is\s+(.*?)[.?]'
        ]
        
        for pattern in issue_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE | re.DOTALL)
            issues.extend([m.strip() for m in matches if m.strip()])
        
        # Deduplicate and limit
        unique_issues = []
        for issue in issues:
            if issue not in unique_issues and len(issue) < 300:
                unique_issues.append(issue)
        
        return unique_issues[:3]  # Top 3 issues
    
    def _extract_holding(self, text: str) -> str:
        """Extract court's holding/decision"""
        # Look for holding section
        holding_patterns = [
            r'(?:held|ruling|decision|concluded)[:\s]+(.*?)(?=\n\n|therefore|thus)',
            r'the\s+court\s+(?:held|ruled|decided)\s+(?:that\s+)?(.*?)[.]'
        ]
        
        for pattern in holding_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                holding = match.group(1).strip()
                if len(holding) > 400:
                    holding = holding[:400] + "..."
                return holding
        
        return "Holding not clearly identified"
    
    def _identify_legal_principles(self, cases: List[Dict]) -> List[Dict]:
        """Identify common legal principles across cases"""
        principles = defaultdict(lambda: {'count': 0, 'cases': []})
        
        # Extract statutes and sections mentioned
        for i, case in enumerate(cases, 1):
            case_text = case.get('text', case.get('document', ''))
            
            # Find section references
            sections = re.findall(
                r'section\s+(\d+[a-z]?)\s+of\s+(?:the\s+)?([^.]+act[^.]*)',
                case_text,
                re.IGNORECASE
            )
            
            for section, act in sections:
                key = f"Section {section} of {act.strip()}"
                principles[key]['count'] += 1
                principles[key]['cases'].append(i)
        
        # Find common legal terms/doctrines
        legal_doctrines = [
            'natural justice', 'due process', 'burden of proof',
            'reasonable person', 'prima facie', 'res judicata',
            'estoppel', 'laches', 'equity', 'good faith',
            'material breach', 'force majeure', 'frustration of contract'
        ]
        
        for doctrine in legal_doctrines:
            count = 0
            case_nums = []
            
            for i, case in enumerate(cases, 1):
                case_text = case.get('text', case.get('document', '')).lower()
                if doctrine.lower() in case_text:
                    count += 1
                    case_nums.append(i)
            
            if count > 0:
                principles[doctrine.title()]['count'] = count
                principles[doctrine.title()]['cases'] = case_nums
        
        # Sort by frequency
        sorted_principles = sorted(
            [
                {
                    'principle': k,
                    'frequency': v['count'],
                    'cases': v['cases']
                }
                for k, v in principles.items()
            ],
            key=lambda x: x['frequency'],
            reverse=True
        )
        
        return sorted_principles[:10]  # Top 10
    
    def _analyze_outcomes(self, cases: List[Dict]) -> Dict:
        """Analyze case outcomes"""
        outcomes = defaultdict(int)
        outcome_details = defaultdict(list)
        
        for i, case in enumerate(cases, 1):
            metadata = case.get('metadata', {})
            outcome = metadata.get('outcome', 'Unknown')
            category = metadata.get('category', 'Unknown')
            
            outcomes[outcome] += 1
            outcome_details[outcome].append({
                'case_number': i,
                'title': metadata.get('title', f'Case {i}'),
                'category': category
            })
        
        # Calculate percentages
        total = len(cases)
        outcome_stats = [
            {
                'outcome': outcome,
                'count': count,
                'percentage': round((count / total) * 100, 1),
                'cases': outcome_details[outcome]
            }
            for outcome, count in outcomes.items()
        ]
        
        # Sort by count
        outcome_stats.sort(key=lambda x: x['count'], reverse=True)
        
        return {
            'total_cases': total,
            'statistics': outcome_stats,
            'most_common': outcome_stats[0]['outcome'] if outcome_stats else None
        }
    
    def _extract_citations(self, cases: List[Dict]) -> List[Dict]:
        """Extract and format citations"""
        citations = []
        
        for i, case in enumerate(cases, 1):
            metadata = case.get('metadata', {})
            case_text = case.get('text', case.get('document', ''))
            
            citation = {
                'case_number': i,
                'title': metadata.get('title', f'Case {i}'),
                'court': metadata.get('court', 'Court not specified'),
                'year': metadata.get('year', 'Year not specified'),
                'citation': metadata.get('citation', ''),
                'relevance': metadata.get('importance', 50)
            }
            
            # Try to extract citation from text if not in metadata
            if not citation['citation']:
                citation_match = re.search(
                    r'\b(\d{4})\s+([A-Z]+)\s+(\d+)\b',
                    case_text
                )
                if citation_match:
                    citation['citation'] = citation_match.group(0)
            
            citations.append(citation)
        
        # Sort by relevance
        citations.sort(key=lambda x: x['relevance'], reverse=True)
        
        return citations
    
    def _create_timeline(self, cases: List[Dict]) -> List[Dict]:
        """Create chronological timeline of cases"""
        timeline = []
        
        for case in cases:
            metadata = case.get('metadata', {})
            year = metadata.get('year')
            
            if year:
                timeline.append({
                    'year': year,
                    'title': metadata.get('title', 'Untitled'),
                    'outcome': metadata.get('outcome', 'Unknown'),
                    'significance': metadata.get('importance', 50)
                })
        
        # Sort by year
        timeline.sort(key=lambda x: x['year'])
        
        return timeline
    
    def _generate_summary_text(
        self,
        topic: str,
        cases: List[Dict],
        key_points: List[Dict],
        principles: List[Dict],
        outcome_analysis: Dict
    ) -> str:
        """Generate human-readable summary text"""
        summary_parts = []
        
        # Header
        summary_parts.append(f"# Legal Research Summary: {topic}\n")
        summary_parts.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
        summary_parts.append(f"Cases Analyzed: {len(cases)}\n\n")
        
        # Executive Summary
        summary_parts.append("## Executive Summary\n\n")
        summary_parts.append(
            f"This research summary analyzes {len(cases)} legal cases related to {topic}. "
        )
        
        if outcome_analysis['statistics']:
            most_common = outcome_analysis['most_common']
            summary_parts.append(
                f"The most common outcome was '{most_common}' "
                f"({outcome_analysis['statistics'][0]['percentage']}% of cases). "
            )
        
        if principles:
            summary_parts.append(
                f"The analysis identified {len(principles)} key legal principles, "
                f"with '{principles[0]['principle']}' being the most frequently cited.\n\n"
            )
        
        # Outcome Analysis
        summary_parts.append("## Outcome Analysis\n\n")
        for stat in outcome_analysis['statistics']:
            summary_parts.append(
                f"- **{stat['outcome']}**: {stat['count']} cases ({stat['percentage']}%)\n"
            )
        summary_parts.append("\n")
        
        # Key Legal Principles
        if principles:
            summary_parts.append("## Key Legal Principles\n\n")
            for i, principle in enumerate(principles[:5], 1):
                summary_parts.append(
                    f"{i}. **{principle['principle']}** - "
                    f"Referenced in {principle['frequency']} case(s) "
                    f"(Cases: {', '.join(map(str, principle['cases']))})\n"
                )
            summary_parts.append("\n")
        
        # Case Summaries
        summary_parts.append("## Individual Case Summaries\n\n")
        for point in key_points:
            summary_parts.append(f"### Case {point['case_number']}: {point['title']}\n\n")
            summary_parts.append(f"**Category**: {point['category']}\n")
            summary_parts.append(f"**Outcome**: {point['outcome']}\n\n")
            
            if point['key_facts']:
                summary_parts.append(f"**Facts**: {point['key_facts']}\n\n")
            
            if point['legal_issues']:
                summary_parts.append("**Legal Issues**:\n")
                for issue in point['legal_issues']:
                    summary_parts.append(f"- {issue}\n")
                summary_parts.append("\n")
            
            summary_parts.append(f"**Holding**: {point['holding']}\n\n")
            summary_parts.append("---\n\n")
        
        # Conclusion
        summary_parts.append("## Conclusion\n\n")
        summary_parts.append(
            f"Based on the analysis of {len(cases)} cases, "
            "the following conclusions can be drawn:\n\n"
        )
        
        # Trend analysis
        if outcome_analysis['statistics']:
            dominant_outcome = outcome_analysis['statistics'][0]
            summary_parts.append(
                f"1. Courts tend to rule in favor of '{dominant_outcome['outcome']}' "
                f"in {dominant_outcome['percentage']}% of similar cases.\n"
            )
        
        if principles:
            summary_parts.append(
                f"2. The principle of '{principles[0]['principle']}' "
                f"is frequently cited and appears to be well-established.\n"
            )
        
        summary_parts.append(
            "\n**Disclaimer**: This is an automated summary for research purposes only. "
            "Consult a qualified legal professional for legal advice.\n"
        )
        
        return "".join(summary_parts)
    
    def _save_summary(self, topic: str, result: Dict):
        """Save summary to file"""
        # Clean topic for filename
        safe_topic = re.sub(r'[^\w\s-]', '', topic)
        safe_topic = re.sub(r'[-\s]+', '_', safe_topic)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"summary_{safe_topic}_{timestamp}.json"
        
        try:
            # Save JSON
            json_path = self.summaries_dir / filename
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            
            # Save markdown
            md_filename = filename.replace('.json', '.md')
            md_path = self.summaries_dir / md_filename
            with open(md_path, 'w', encoding='utf-8') as f:
                f.write(result['summary'])
            
            print(f"✅ Summary saved to {json_path}")
            
        except Exception as e:
            print(f"⚠️ Could not save summary: {e}")
    
    def compare_cases(self, case_ids: List[str], comparison_aspects: List[str]) -> Dict:
        """
        Compare specific cases side-by-side
        
        Args:
            case_ids: List of case identifiers
            comparison_aspects: Aspects to compare (facts, law, outcome, reasoning)
            
        Returns:
            Dict with comparative analysis
        """
        if not self.vector_db:
            return {'error': 'Vector database not available'}
        
        # Retrieve cases
        cases = []
        for case_id in case_ids:
            # This would query the vector DB
            # Placeholder for now
            cases.append({'id': case_id, 'retrieved': False})
        
        comparison = {
            'case_ids': case_ids,
            'aspects': comparison_aspects,
            'comparison_matrix': {},
            'similarities': [],
            'differences': [],
            'key_takeaways': []
        }
        
        # Build comparison matrix
        for aspect in comparison_aspects:
            comparison['comparison_matrix'][aspect] = {}
            
            for case_id in case_ids:
                # Extract aspect from each case
                comparison['comparison_matrix'][aspect][case_id] = f"[{aspect} for {case_id}]"
        
        return comparison
    
    def generate_research_memo(self, query: str, cases: List[Dict]) -> str:
        """
        Generate formal legal research memorandum
        
        Args:
            query: Legal research question
            cases: Relevant cases
            
        Returns:
            Formatted memo text
        """
        memo_parts = []
        
        memo_parts.append("LEGAL RESEARCH MEMORANDUM\n")
        memo_parts.append("="*60 + "\n\n")
        memo_parts.append(f"DATE: {datetime.now().strftime('%B %d, %Y')}\n")
        memo_parts.append(f"RE: {query}\n\n")
        
        memo_parts.append("QUESTION PRESENTED\n")
        memo_parts.append("-"*60 + "\n")
        memo_parts.append(f"{query}\n\n")
        
        memo_parts.append("BRIEF ANSWER\n")
        memo_parts.append("-"*60 + "\n")
        memo_parts.append(
            f"Based on analysis of {len(cases)} relevant precedents, "
            "[brief answer to be completed].\n\n"
        )
        
        memo_parts.append("ANALYSIS\n")
        memo_parts.append("-"*60 + "\n\n")
        
        # Summarize key cases
        for i, case in enumerate(cases[:5], 1):  # Top 5 cases
            metadata = case.get('metadata', {})
            memo_parts.append(f"{i}. {metadata.get('title', 'Untitled')}\n")
            memo_parts.append(f"   Citation: {metadata.get('citation', 'N/A')}\n")
            memo_parts.append(f"   Outcome: {metadata.get('outcome', 'N/A')}\n\n")
        
        memo_parts.append("\nCONCLUSION\n")
        memo_parts.append("-"*60 + "\n")
        memo_parts.append("[Conclusion to be completed based on analysis]\n\n")
        
        memo_parts.append("---\n")
        memo_parts.append("This memo is for research purposes only and does not constitute legal advice.\n")
        
        return "".join(memo_parts)
