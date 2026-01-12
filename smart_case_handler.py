"""
Smart Case Name Extractor and Query Handler
Extracts case names from user queries and searches the existing ChromaDB database
"""

import re
from typing import Optional, Dict, List, Tuple

class CaseQueryHandler:
    """
    Intelligently handles case-specific queries by extracting case names
    and searching the existing database instead of hardcoding cases
    """
    
    def __init__(self):
        # Famous case aliases - maps common names to actual party names
        self.famous_case_aliases = {
            'nirbhaya': ['Mukesh Kumar', 'Union of India', 'delhi gangrape 2012'],
            'nirbhaya case': ['Mukesh Kumar', 'Union of India', 'delhi gangrape'],
            'unnao': ['unnao rape', 'CBI', 'uttar pradesh'],
            'unnao rape': ['unnao', 'rape case', 'uttar pradesh'],
            'kathua': ['Shubam Sangra', 'State of Jammu', 'kathua rape'],
            'kesavananda': ['Kesavananda Bharati', 'State of Kerala', 'basic structure'],
            'shah bano': ['Shah Bano', 'maintenance', 'muslim women'],
            'vishaka': ['Vishaka', 'sexual harassment', 'workplace'],
            'maneka gandhi': ['Maneka Gandhi', 'passport', 'article 21'],
        }
        
        # Patterns to detect case name queries
        self.query_patterns = [
            # Direct case name patterns
            r'(?:tell me about|what is|explain|details of|information on|about the|regarding)\s+(?:the\s+)?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+(?:case|vs?\.?\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*))',
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+vs?\.?\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s*(?:case)?',
            r'(?:case of|matter of)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            
            # Party names
            r'(?:petitioner|appellant|plaintiff)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            r'(?:respondent|defendant)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            
            # Popular case references (without hardcoding full details)
            r'(nirbhaya|unnao|kesavananda|vishaka|maneka gandhi|golaknath|minerva mills|shah bano|ayodhya|sabarimala|jallikattu|aadhaar|puttaswamy|navtej johar|triple talaq|shreya singhal)(?:\s+case)?',
        ]
        
        # Keywords that indicate case-related queries
        self.case_indicators = [
            'case', 'judgment', 'ruling', 'verdict', 'decision', 
            'supreme court', 'high court', 'vs', 'versus',
            'petitioner', 'respondent', 'appellant', 'plaintiff', 'defendant'
        ]
    
    def is_case_query(self, query: str) -> bool:
        """Check if query is asking about a specific case"""
        query_lower = query.lower()
        
        # Check for case indicators
        has_indicator = any(indicator in query_lower for indicator in self.case_indicators)
        
        # Check for case name patterns
        has_case_pattern = any(re.search(pattern, query, re.IGNORECASE) for pattern in self.query_patterns)
        
        # Check for proper nouns (capitalized words) which might be party names
        has_proper_nouns = bool(re.search(r'\b[A-Z][a-z]+\b', query))
        
        return has_indicator or has_case_pattern or (has_proper_nouns and len(query.split()) < 15)
    
    def extract_case_names(self, query: str) -> List[str]:
        """Extract potential case names or party names from query"""
        extracted = []
        
        # First, check for famous case aliases
        query_lower = query.lower()
        for alias, party_names in self.famous_case_aliases.items():
            if alias in query_lower:
                # Add the actual party names for better search
                extracted.extend(party_names)
                # Also keep the alias for fallback
                extracted.append(alias)
        
        # Then extract from patterns
        for pattern in self.query_patterns:
            matches = re.findall(pattern, query, re.IGNORECASE)
            if matches:
                # Flatten tuples if present
                for match in matches:
                    if isinstance(match, tuple):
                        extracted.extend([m for m in match if m])
                    else:
                        extracted.append(match)
        
        # Also extract capitalized words that might be party names
        proper_nouns = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', query)
        extracted.extend(proper_nouns)
        
        # Remove duplicates and common words
        stop_words = {'Tell', 'What', 'Explain', 'Details', 'Information', 'About', 'Case', 'Court', 'India', 'Indian'}
        extracted = list(set([name for name in extracted if name not in stop_words]))
        
        return extracted
    
    def enhance_search_query(self, original_query: str, case_names: List[str]) -> str:
        """Enhance the search query with extracted case names for better matching"""
        if not case_names:
            return original_query
        
        # Combine original query with extracted names
        enhanced = original_query
        for name in case_names:
            if name.lower() not in original_query.lower():
                enhanced += f" {name}"
        
        return enhanced
    
    def search_database(self, query: str, case_names: List[str], db) -> Tuple[List[Dict], bool]:
        """
        Search the existing ChromaDB database with enhanced query
        Returns: (results, is_high_confidence)
        """
        # Use direct ChromaDB connection to access the correct collection
        import chromadb
        from sentence_transformers import SentenceTransformer
        
        client = chromadb.PersistentClient(path="./data/chromadb")
        collection = client.get_collection(name="legal_cases_full")  # All 418 real cases from Indian Kanoon
        
        # Create embeddings for search
        model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Try exact party name search first (prioritize actual party names)
        if case_names:
            # Prioritize capitalized names (likely actual parties) over aliases
            party_names = [name for name in case_names if name[0].isupper() and len(name.split()) <= 3]
            aliases = [name for name in case_names if name not in party_names]
            
            # Strategy 1: Search with just party names if available
            if party_names:
                enhanced_query = " ".join(party_names[:4])  # Limit to top 4 to avoid dilution
                query_embedding = model.encode([enhanced_query])[0].tolist()
                results = collection.query(
                    query_embeddings=[query_embedding],
                    n_results=5
                )
                
                formatted_results = self._format_chromadb_results(results)
                
                # Return results without filtering by threshold - let the caller decide
                # Check if we have high confidence matches (very high relevance)
                if formatted_results and len(formatted_results) > 0:
                    top_relevance = 1 - formatted_results[0].get('distance', 1)
                    # Only mark as high confidence if relevance is very high (>0.7)
                    # Otherwise return results for caller to decide
                    return formatted_results, top_relevance > 0.7
            
            # Strategy 2: Fall back to all names including aliases
            enhanced_query = " ".join(case_names[:5])  # Limit to avoid too many terms
            query_embedding = model.encode([enhanced_query])[0].tolist()
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=5
            )
            
            # Convert to our format
            formatted_results = self._format_chromadb_results(results)
            
            # Return results - let caller decide based on relevance
            if formatted_results and len(formatted_results) > 0:
                top_relevance = 1 - formatted_results[0].get('distance', 1)
                return formatted_results, top_relevance > 0.7
        
        # Fall back to regular search with enhanced query
        enhanced = self.enhance_search_query(query, case_names)
        query_embedding = model.encode([enhanced])[0].tolist()
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=10
        )
        
        return self._format_chromadb_results(results), False
    
    def _format_chromadb_results(self, results) -> List[Dict]:
        """Convert ChromaDB query results to our standard format"""
        formatted = []
        for i in range(len(results['ids'][0])):
            metadata = results['metadatas'][0][i]
            formatted.append({
                'id': results['ids'][0][i],
                'document': results['documents'][0][i],
                'metadata': metadata,
                'distance': results['distances'][0][i],
                # Extract common fields to top level for easy access
                'title': metadata.get('title', metadata.get('case_name', 'N/A')),
                'court': metadata.get('court', 'Unknown'),
                'date': metadata.get('date', 'Unknown'),
                'url': metadata.get('original_url', 'N/A'),
                'text': results['documents'][0][i]
            })
        return formatted
    
    def format_case_response(self, case_data: Dict, is_direct_match: bool = False) -> str:
        """
        Format case data from ChromaDB into a rich, informative response with case narrative
        """
        metadata = case_data.get('metadata', {})
        document = case_data.get('document', '')
        
        # Extract case title from document
        lines = document.split('\n')
        title = lines[0] if lines else metadata.get('case_id', 'Unknown Case')
        
        # Start with clean case title
        response = f"📋 CASE: {title}\n\n"
        
        # Extract and format case summary from document
        # First 800 characters usually contain the key facts
        case_excerpt = document[:800] if document else ""
        
        # Try to generate AI narrative about the case
        narrative = ""
        try:
            from ml_legal_system.legal_rag import LegalRAG
            rag = LegalRAG(use_openai=False)
            
            # Enhanced prompt for detailed case narrative
            narrative_prompt = f"""You are a legal expert. Based on this case information, write a comprehensive but concise summary (8-10 sentences) that covers:

1. WHAT HAPPENED: The incident, crime, or dispute that led to this case
2. PARTIES INVOLVED: Names of victim(s), accused/defendants, petitioners, respondents
3. CHARGES/ISSUES: What legal charges or questions were involved
4. KEY FACTS: Important details about the case
5. LEGAL ARGUMENTS: Main arguments presented
6. COURT'S REASONING: Why the court decided this way
7. FINAL DECISION: What was the judgment/outcome
8. SIGNIFICANCE: Why this case matters

Case Title: {title}
Court: {metadata.get('court', 'Unknown')}
Date: {metadata.get('date', 'Unknown')}
Judge(s): {metadata.get('judge', 'Unknown')}

Case Document Extract:
{document[:2000]}

Write in a clear, journalistic style. Include names, dates, and specific details. Make it informative and engaging."""
            
            narrative = rag._call_gemini(narrative_prompt, max_tokens=500)
            
            if narrative and len(narrative) > 100:
                # Clean up the narrative
                narrative = narrative.strip()
                response += f"📖 CASE SUMMARY:\n{narrative}\n\n"
        except Exception as e:
            # If AI fails, extract summary from document
            if case_excerpt:
                # Get first few meaningful lines from document
                summary_lines = [line.strip() for line in lines[1:15] if line.strip() and len(line.strip()) > 20]
                if summary_lines:
                    response += f"📖 CASE SUMMARY:\n{' '.join(summary_lines[:5])}\n\n"
        
        # Detailed case information
        response += "⚖️ CASE DETAILS:\n"
        if metadata.get('court'):
            response += f"• Court: {metadata['court']}\n"
        if metadata.get('date'):
            response += f"• Date: {metadata['date']}\n"
        if metadata.get('judge'):
            response += f"• Judge(s): {metadata['judge']}\n"
        if metadata.get('outcome'):
            response += f"• Outcome: {metadata['outcome']}\n"
        if metadata.get('legal_domain'):
            response += f"• Legal Domain: {metadata['legal_domain']}\n"
        
        response += "\n"
        
        # Full case link
        if metadata.get('original_url'):
            response += f"🔗 Read Full Judgment: {metadata['original_url']}\n\n"
        
        # Footer
        response += "─" * 60 + "\n"
        response += "💡 This information is from our legal database. For case-specific legal advice, please consult a qualified attorney.\n"
        
        return response


# Singleton instance
_case_query_handler = None

def get_case_query_handler() -> CaseQueryHandler:
    """Get or create case query handler singleton"""
    global _case_query_handler
    if _case_query_handler is None:
        _case_query_handler = CaseQueryHandler()
    return _case_query_handler
