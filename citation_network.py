"""
Citation Network Analysis Module
Builds and analyzes citation relationships between legal cases
"""

from typing import Dict, List, Set, Tuple, Optional
from dataclasses import dataclass, field
from collections import defaultdict, deque
from datetime import datetime
import re
import json


@dataclass
class Citation:
    """Represents a citation from one case to another"""
    source_case_id: str
    target_case_id: str
    citation_type: str  # 'cited', 'followed', 'overruled', 'distinguished', 'referred'
    context: str = ""  # Text context where citation appears
    strength: float = 1.0  # Citation strength/weight
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'source': self.source_case_id,
            'target': self.target_case_id,
            'type': self.citation_type,
            'context': self.context,
            'strength': self.strength
        }


@dataclass
class CaseNode:
    """Represents a case in the citation network"""
    case_id: str
    title: str
    court: str
    date: str
    year: int
    judges: List[str] = field(default_factory=list)
    
    # Citation metrics
    cited_by_count: int = 0  # Number of cases citing this case
    cites_count: int = 0  # Number of cases this case cites
    importance_score: float = 0.0  # PageRank or centrality score
    
    # Network properties
    citations_received: List[Citation] = field(default_factory=list)
    citations_made: List[Citation] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'id': self.case_id,
            'title': self.title,
            'court': self.court,
            'date': self.date,
            'year': self.year,
            'judges': self.judges,
            'cited_by_count': self.cited_by_count,
            'cites_count': self.cites_count,
            'importance_score': self.importance_score
        }


class CitationNetworkBuilder:
    """
    Builds and analyzes citation networks from legal cases
    """
    
    # Citation type patterns
    CITATION_PATTERNS = {
        'followed': [
            r'followed\s+in\s+',
            r'following\s+the\s+decision',
            r'relying\s+on\s+',
            r'in\s+accordance\s+with'
        ],
        'overruled': [
            r'overruled?\s+',
            r'overturned?\s+',
            r'reversed?\s+',
            r'set\s+aside'
        ],
        'distinguished': [
            r'distinguished?\s+',
            r'differs?\s+from',
            r'not\s+applicable',
            r'distinguished\s+on\s+facts'
        ],
        'referred': [
            r'referred?\s+to',
            r'mentioned\s+',
            r'noted\s+',
            r'considered\s+'
        ],
        'cited': [
            r'cited\s+',
            r'quoted\s+',
            r'relied\s+upon',
            r'as\s+held\s+in'
        ]
    }
    
    def __init__(self):
        """Initialize citation network builder"""
        self.cases: Dict[str, CaseNode] = {}
        self.citations: List[Citation] = []
        self.adjacency_list: Dict[str, Set[str]] = defaultdict(set)
        self.reverse_adjacency_list: Dict[str, Set[str]] = defaultdict(set)
    
    def add_case(self, case_id: str, title: str, court: str, 
                 date: str, year: int, judges: List[str] = None) -> CaseNode:
        """
        Add a case to the network
        
        Args:
            case_id: Unique case identifier
            title: Case title
            court: Court name
            date: Case date
            year: Case year
            judges: List of judges
            
        Returns:
            CaseNode object
        """
        if case_id not in self.cases:
            node = CaseNode(
                case_id=case_id,
                title=title,
                court=court,
                date=date,
                year=year,
                judges=judges or []
            )
            self.cases[case_id] = node
        
        return self.cases[case_id]
    
    def add_citation(self, source_id: str, target_id: str, 
                    citation_type: str = 'cited', context: str = "",
                    strength: float = 1.0) -> Optional[Citation]:
        """
        Add a citation between two cases
        
        Args:
            source_id: Case making the citation
            target_id: Case being cited
            citation_type: Type of citation
            context: Context text
            strength: Citation strength
            
        Returns:
            Citation object or None if cases don't exist
        """
        if source_id not in self.cases or target_id not in self.cases:
            return None
        
        citation = Citation(
            source_case_id=source_id,
            target_case_id=target_id,
            citation_type=citation_type,
            context=context,
            strength=strength
        )
        
        self.citations.append(citation)
        
        # Update case nodes
        self.cases[source_id].citations_made.append(citation)
        self.cases[source_id].cites_count += 1
        
        self.cases[target_id].citations_received.append(citation)
        self.cases[target_id].cited_by_count += 1
        
        # Update adjacency lists
        self.adjacency_list[source_id].add(target_id)
        self.reverse_adjacency_list[target_id].add(source_id)
        
        return citation
    
    def extract_citations_from_text(self, case_id: str, text: str) -> List[Tuple[str, str, str]]:
        """
        Extract citations from case text
        
        Args:
            case_id: Source case ID
            text: Case text to parse
            
        Returns:
            List of (target_case_id, citation_type, context) tuples
        """
        citations = []
        
        # Look for citation patterns
        # Format: "Case Name v. Case Name [Year] Court Citation"
        # Example: "State of Maharashtra v. Rajesh Kumar [2020] SC 123"
        
        citation_regex = r'([A-Z][A-Za-z\s&\.]+?)\s+v\.?\s+([A-Z][A-Za-z\s&\.]+?)\s+\[(\d{4})\]\s+([A-Z]+)\s+(\d+)'
        
        for match in re.finditer(citation_regex, text):
            full_match = match.group(0)
            party1 = match.group(1).strip()
            party2 = match.group(2).strip()
            year = match.group(3)
            court = match.group(4)
            number = match.group(5)
            
            # Create target case ID
            target_id = f"{court}_{year}_{number}"
            
            # Determine citation type from context
            context_start = max(0, match.start() - 100)
            context_end = min(len(text), match.end() + 100)
            context = text[context_start:context_end]
            
            citation_type = self._determine_citation_type(context)
            
            citations.append((target_id, citation_type, full_match))
        
        return citations
    
    def _determine_citation_type(self, context: str) -> str:
        """
        Determine citation type from context
        
        Args:
            context: Text context around citation
            
        Returns:
            Citation type
        """
        context_lower = context.lower()
        
        # Check each citation type pattern
        for cit_type, patterns in self.CITATION_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, context_lower):
                    return cit_type
        
        return 'cited'  # Default
    
    def calculate_pagerank(self, damping: float = 0.85, 
                          iterations: int = 100, tolerance: float = 1e-6) -> Dict[str, float]:
        """
        Calculate PageRank scores for all cases
        
        Args:
            damping: Damping factor (default 0.85)
            iterations: Maximum iterations
            tolerance: Convergence tolerance
            
        Returns:
            Dictionary of case_id -> PageRank score
        """
        if not self.cases:
            return {}
        
        n = len(self.cases)
        case_ids = list(self.cases.keys())
        
        # Initialize PageRank scores
        pagerank = {case_id: 1.0 / n for case_id in case_ids}
        
        for iteration in range(iterations):
            new_pagerank = {}
            max_diff = 0.0
            
            for case_id in case_ids:
                # Base score (random surfer)
                score = (1 - damping) / n
                
                # Add contributions from citing cases
                for citing_case in self.reverse_adjacency_list[case_id]:
                    citing_out_degree = len(self.adjacency_list[citing_case])
                    if citing_out_degree > 0:
                        score += damping * pagerank[citing_case] / citing_out_degree
                
                new_pagerank[case_id] = score
                max_diff = max(max_diff, abs(score - pagerank[case_id]))
            
            pagerank = new_pagerank
            
            # Check convergence
            if max_diff < tolerance:
                break
        
        # Update case nodes
        for case_id, score in pagerank.items():
            self.cases[case_id].importance_score = score
        
        return pagerank
    
    def find_citation_path(self, source_id: str, target_id: str, 
                          max_depth: int = 5) -> Optional[List[str]]:
        """
        Find shortest citation path between two cases using BFS
        
        Args:
            source_id: Source case ID
            target_id: Target case ID
            max_depth: Maximum path depth
            
        Returns:
            List of case IDs forming path, or None if no path
        """
        if source_id not in self.cases or target_id not in self.cases:
            return None
        
        if source_id == target_id:
            return [source_id]
        
        # BFS
        queue = deque([(source_id, [source_id])])
        visited = {source_id}
        
        while queue:
            current_id, path = queue.popleft()
            
            if len(path) > max_depth:
                continue
            
            # Check adjacent nodes (cases cited by current case)
            for neighbor_id in self.adjacency_list[current_id]:
                if neighbor_id == target_id:
                    return path + [neighbor_id]
                
                if neighbor_id not in visited:
                    visited.add(neighbor_id)
                    queue.append((neighbor_id, path + [neighbor_id]))
        
        return None  # No path found
    
    def get_case_citations(self, case_id: str, direction: str = 'both') -> Dict:
        """
        Get all citations for a case
        
        Args:
            case_id: Case ID
            direction: 'incoming', 'outgoing', or 'both'
            
        Returns:
            Dictionary with citation information
        """
        if case_id not in self.cases:
            return {'error': 'Case not found'}
        
        case = self.cases[case_id]
        result = {
            'case': case.to_dict(),
            'incoming_citations': [],
            'outgoing_citations': []
        }
        
        if direction in ('incoming', 'both'):
            for citation in case.citations_received:
                citing_case = self.cases[citation.source_case_id]
                result['incoming_citations'].append({
                    'case': citing_case.to_dict(),
                    'citation': citation.to_dict()
                })
        
        if direction in ('outgoing', 'both'):
            for citation in case.citations_made:
                cited_case = self.cases[citation.target_case_id]
                result['outgoing_citations'].append({
                    'case': cited_case.to_dict(),
                    'citation': citation.to_dict()
                })
        
        return result
    
    def get_most_cited_cases(self, top_n: int = 10, 
                            court: Optional[str] = None,
                            year_range: Optional[Tuple[int, int]] = None) -> List[Dict]:
        """
        Get most cited cases
        
        Args:
            top_n: Number of cases to return
            court: Filter by court
            year_range: Filter by year range (start, end)
            
        Returns:
            List of case dictionaries with citation counts
        """
        filtered_cases = list(self.cases.values())
        
        # Apply filters
        if court:
            filtered_cases = [c for c in filtered_cases if c.court == court]
        
        if year_range:
            start_year, end_year = year_range
            filtered_cases = [c for c in filtered_cases 
                            if start_year <= c.year <= end_year]
        
        # Sort by citation count
        sorted_cases = sorted(filtered_cases, 
                            key=lambda c: c.cited_by_count, 
                            reverse=True)
        
        return [case.to_dict() for case in sorted_cases[:top_n]]
    
    def get_network_statistics(self) -> Dict:
        """
        Get network statistics
        
        Returns:
            Dictionary with network metrics
        """
        if not self.cases:
            return {
                'total_cases': 0,
                'total_citations': 0,
                'avg_citations_per_case': 0.0,
                'density': 0.0
            }
        
        n = len(self.cases)
        m = len(self.citations)
        
        # Calculate density (actual edges / possible edges)
        max_edges = n * (n - 1)
        density = m / max_edges if max_edges > 0 else 0.0
        
        # Citation statistics
        citation_counts = [case.cited_by_count for case in self.cases.values()]
        
        return {
            'total_cases': n,
            'total_citations': m,
            'avg_citations_per_case': sum(citation_counts) / n if n > 0 else 0.0,
            'max_citations': max(citation_counts) if citation_counts else 0,
            'min_citations': min(citation_counts) if citation_counts else 0,
            'density': density,
            'citation_types': self._count_citation_types()
        }
    
    def _count_citation_types(self) -> Dict[str, int]:
        """Count citations by type"""
        counts = defaultdict(int)
        for citation in self.citations:
            counts[citation.citation_type] += 1
        return dict(counts)
    
    def export_network_data(self) -> Dict:
        """
        Export network data for visualization
        
        Returns:
            Dictionary with nodes and edges
        """
        nodes = [case.to_dict() for case in self.cases.values()]
        edges = [citation.to_dict() for citation in self.citations]
        
        return {
            'nodes': nodes,
            'edges': edges,
            'statistics': self.get_network_statistics()
        }
    
    def export_to_json(self, filepath: str):
        """Export network to JSON file"""
        data = self.export_network_data()
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def import_from_json(self, filepath: str):
        """Import network from JSON file"""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Add cases
        for node in data['nodes']:
            self.add_case(
                case_id=node['id'],
                title=node['title'],
                court=node['court'],
                date=node['date'],
                year=node['year'],
                judges=node.get('judges', [])
            )
        
        # Add citations
        for edge in data['edges']:
            self.add_citation(
                source_id=edge['source'],
                target_id=edge['target'],
                citation_type=edge['type'],
                context=edge.get('context', ''),
                strength=edge.get('strength', 1.0)
            )


# Global instance
_citation_network = None


def get_citation_network() -> CitationNetworkBuilder:
    """Get or create citation network instance"""
    global _citation_network
    
    if _citation_network is None:
        _citation_network = CitationNetworkBuilder()
    
    return _citation_network


if __name__ == '__main__':
    # Test the citation network
    print("=" * 80)
    print("CITATION NETWORK TEST")
    print("=" * 80)
    
    network = CitationNetworkBuilder()
    
    # Add sample cases
    network.add_case("SC_2020_123", "State v. Kumar", "Supreme Court", 
                    "2020-01-15", 2020, ["Justice A", "Justice B"])
    network.add_case("HC_2019_456", "Sharma v. Singh", "High Court", 
                    "2019-06-20", 2019, ["Justice C"])
    network.add_case("SC_2021_789", "Corporation v. Workers", "Supreme Court", 
                    "2021-03-10", 2021, ["Justice D", "Justice E"])
    
    # Add citations
    network.add_citation("SC_2021_789", "SC_2020_123", "followed", 
                        "Following the precedent in State v. Kumar")
    network.add_citation("SC_2020_123", "HC_2019_456", "cited",
                        "As noted in Sharma v. Singh")
    
    print("\n1. Network Statistics:")
    stats = network.get_network_statistics()
    print(f"   Total Cases: {stats['total_cases']}")
    print(f"   Total Citations: {stats['total_citations']}")
    print(f"   Network Density: {stats['density']:.4f}")
    
    print("\n2. PageRank Scores:")
    pagerank = network.calculate_pagerank()
    for case_id, score in sorted(pagerank.items(), key=lambda x: x[1], reverse=True):
        print(f"   {case_id}: {score:.6f}")
    
    print("\n3. Most Cited Cases:")
    most_cited = network.get_most_cited_cases(top_n=3)
    for case in most_cited:
        print(f"   {case['title']}: {case['cited_by_count']} citations")
    
    print("\n4. Citation Path:")
    path = network.find_citation_path("SC_2021_789", "HC_2019_456")
    if path:
        print(f"   Path: {' -> '.join(path)}")
    else:
        print("   No path found")
    
    print("\n" + "=" * 80)
