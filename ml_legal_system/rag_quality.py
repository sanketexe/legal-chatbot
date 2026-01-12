"""
Enhanced RAG Quality Module
Adds confidence scores, citation verification, and source highlighting
"""

from typing import List, Dict, Tuple
import re
from dataclasses import dataclass


@dataclass
class RAGResult:
    """Structured RAG response with quality metrics"""
    answer: str
    confidence_score: float  # 0-100
    sources: List[Dict]
    citations: List[str]
    highlighted_snippets: List[Dict]
    confidence_breakdown: Dict[str, float]
    warnings: List[str]


class RAGQualityEnhancer:
    """Enhances RAG responses with confidence scoring and citation verification"""
    
    def __init__(self):
        self.min_confidence_threshold = 60.0
    
    def calculate_confidence_score(self, query: str, retrieved_docs: List[Dict], 
                                   answer: str) -> Tuple[float, Dict]:
        """
        Calculate confidence score for RAG answer
        
        Returns:
            Tuple of (overall_score, breakdown_dict)
        """
        breakdown = {}
        
        # 1. Retrieval Quality Score (0-30 points)
        retrieval_score = self._score_retrieval_quality(retrieved_docs)
        breakdown['retrieval_quality'] = retrieval_score
        
        # 2. Answer-Source Alignment (0-30 points)
        alignment_score = self._score_answer_alignment(answer, retrieved_docs)
        breakdown['answer_alignment'] = alignment_score
        
        # 3. Citation Coverage (0-20 points)
        citation_score = self._score_citation_coverage(answer, retrieved_docs)
        breakdown['citation_coverage'] = citation_score
        
        # 4. Answer Completeness (0-20 points)
        completeness_score = self._score_answer_completeness(query, answer)
        breakdown['answer_completeness'] = completeness_score
        
        # Calculate overall score
        overall = (retrieval_score + alignment_score + 
                  citation_score + completeness_score)
        
        return overall, breakdown
    
    def _score_retrieval_quality(self, docs: List[Dict]) -> float:
        """Score the quality of retrieved documents"""
        if not docs:
            return 0.0
        
        score = 0.0
        
        # Check number of documents
        if len(docs) >= 3:
            score += 10.0
        elif len(docs) >= 2:
            score += 7.0
        elif len(docs) >= 1:
            score += 4.0
        
        # Check relevance scores (distance)
        avg_distance = sum(doc.get('distance', 1.0) for doc in docs) / len(docs)
        if avg_distance < 0.5:
            score += 20.0
        elif avg_distance < 0.7:
            score += 15.0
        elif avg_distance < 0.9:
            score += 10.0
        else:
            score += 5.0
        
        return min(score, 30.0)
    
    def _score_answer_alignment(self, answer: str, docs: List[Dict]) -> float:
        """Score how well the answer aligns with source documents"""
        if not docs or not answer:
            return 0.0
        
        score = 0.0
        answer_lower = answer.lower()
        
        # Extract key phrases from documents
        doc_text = " ".join([doc.get('document', '') for doc in docs]).lower()
        
        # Check if legal terms from sources appear in answer
        legal_terms = re.findall(r'\b(?:section|article|act|amendment|clause|provision)\s+\d+[a-z]?\b', 
                                doc_text)
        legal_terms_in_answer = [term for term in legal_terms if term in answer_lower]
        
        if legal_terms_in_answer:
            score += min(len(legal_terms_in_answer) * 5, 15.0)
        
        # Check for case names mentioned
        case_names = [doc.get('metadata', {}).get('case_name', '') 
                     for doc in docs if doc.get('metadata', {}).get('case_name')]
        cases_cited = sum(1 for case in case_names if case.lower()[:20] in answer_lower)
        
        if cases_cited > 0:
            score += min(cases_cited * 10, 15.0)
        
        return min(score, 30.0)
    
    def _score_citation_coverage(self, answer: str, docs: List[Dict]) -> float:
        """Score how well sources are cited in the answer"""
        if not docs:
            return 0.0
        
        # Check for explicit citations in answer
        citation_patterns = [
            r'\[source\s*\d+\]',
            r'\(source:\s*\d+\)',
            r'according to',
            r'as per',
            r'ruled in',
            r'held in',
            r'in the case of'
        ]
        
        citations_found = sum(1 for pattern in citation_patterns 
                            if re.search(pattern, answer, re.IGNORECASE))
        
        if citations_found >= 3:
            return 20.0
        elif citations_found >= 2:
            return 15.0
        elif citations_found >= 1:
            return 10.0
        else:
            return 5.0
    
    def _score_answer_completeness(self, query: str, answer: str) -> float:
        """Score the completeness of the answer"""
        if not answer:
            return 0.0
        
        score = 0.0
        
        # Check answer length (should be substantial but not too long)
        word_count = len(answer.split())
        if 50 <= word_count <= 500:
            score += 10.0
        elif 30 <= word_count < 50 or 500 < word_count <= 800:
            score += 7.0
        elif word_count >= 800:
            score += 5.0
        else:
            score += 3.0
        
        # Check if answer addresses the question
        query_keywords = set(query.lower().split())
        answer_keywords = set(answer.lower().split())
        keyword_overlap = len(query_keywords & answer_keywords) / len(query_keywords) if query_keywords else 0
        
        if keyword_overlap > 0.5:
            score += 10.0
        elif keyword_overlap > 0.3:
            score += 7.0
        elif keyword_overlap > 0.1:
            score += 4.0
        
        return min(score, 20.0)
    
    def verify_citations(self, answer: str, sources: List[Dict]) -> List[str]:
        """
        Verify that citations in the answer correspond to actual sources
        
        Returns:
            List of verified case names/citations
        """
        verified = []
        
        for source in sources:
            metadata = source.get('metadata', {})
            case_name = metadata.get('case_name', '')
            
            if case_name:
                # Check if case is mentioned in answer
                if case_name.lower()[:30] in answer.lower():
                    verified.append(case_name)
        
        return verified
    
    def highlight_sources(self, answer: str, sources: List[Dict]) -> List[Dict]:
        """
        Find and highlight snippets from sources that appear in the answer
        
        Returns:
            List of dicts with {snippet, source_id, case_name, relevance}
        """
        highlighted = []
        
        answer_lower = answer.lower()
        
        for i, source in enumerate(sources):
            doc_text = source.get('document', '')
            metadata = source.get('metadata', {})
            
            # Find sentences that appear in both answer and source
            doc_sentences = re.split(r'[.!?]+', doc_text)
            
            for sentence in doc_sentences:
                sentence_clean = sentence.strip()
                if len(sentence_clean) < 20:  # Skip very short sentences
                    continue
                
                # Check if significant portion of sentence appears in answer
                words = sentence_clean.lower().split()
                if len(words) >= 5:
                    # Check if at least 70% of words appear in answer
                    matching_words = sum(1 for word in words if word in answer_lower)
                    if matching_words / len(words) >= 0.7:
                        highlighted.append({
                            'snippet': sentence_clean,
                            'source_id': i + 1,
                            'case_name': metadata.get('case_name', 'Unknown'),
                            'relevance': matching_words / len(words)
                        })
        
        # Sort by relevance
        highlighted.sort(key=lambda x: x['relevance'], reverse=True)
        
        return highlighted[:5]  # Return top 5
    
    def generate_warnings(self, confidence_score: float, 
                         confidence_breakdown: Dict, 
                         verified_citations: List[str]) -> List[str]:
        """Generate warnings about answer quality"""
        warnings = []
        
        if confidence_score < self.min_confidence_threshold:
            warnings.append(
                f"⚠️ Low confidence score ({confidence_score:.1f}/100). "
                "This answer may not be fully reliable."
            )
        
        if confidence_breakdown.get('retrieval_quality', 0) < 15:
            warnings.append(
                "⚠️ Few relevant cases found. Consider rephrasing your query or "
                "consulting a legal professional."
            )
        
        if confidence_breakdown.get('citation_coverage', 0) < 10:
            warnings.append(
                "⚠️ Limited citation coverage. The answer may lack proper legal references."
            )
        
        if len(verified_citations) == 0:
            warnings.append(
                "⚠️ No verified case citations. This answer is based on general legal knowledge."
            )
        
        return warnings
    
    def enhance_rag_response(self, query: str, answer: str, 
                            retrieved_docs: List[Dict]) -> RAGResult:
        """
        Main method to enhance a RAG response with all quality features
        
        Args:
            query: User's question
            answer: Generated answer
            retrieved_docs: List of retrieved documents from vector DB
            
        Returns:
            RAGResult with all enhancements
        """
        # Calculate confidence
        confidence_score, breakdown = self.calculate_confidence_score(
            query, retrieved_docs, answer
        )
        
        # Verify citations
        verified_citations = self.verify_citations(answer, retrieved_docs)
        
        # Highlight source snippets
        highlighted = self.highlight_sources(answer, retrieved_docs)
        
        # Generate warnings
        warnings = self.generate_warnings(
            confidence_score, breakdown, verified_citations
        )
        
        # Format sources
        sources = [
            {
                'case_name': doc.get('metadata', {}).get('case_name', 'Unknown'),
                'category': doc.get('metadata', {}).get('category', ''),
                'relevance': 1 - doc.get('distance', 1.0),
                'verified': doc.get('metadata', {}).get('case_name', '') in verified_citations
            }
            for doc in retrieved_docs
        ]
        
        return RAGResult(
            answer=answer,
            confidence_score=confidence_score,
            sources=sources,
            citations=verified_citations,
            highlighted_snippets=highlighted,
            confidence_breakdown=breakdown,
            warnings=warnings
        )
