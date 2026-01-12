"""
Case Summarization Module
Provides extractive and abstractive summarization of legal cases
"""

import os
import re
import google.generativeai as genai
from typing import Dict, List, Optional, Tuple
from collections import Counter
from datetime import datetime
import math
from logging_config import get_logger

logger = get_logger(__name__)

# Configure Gemini AI
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)
    model = genai.GenerativeModel('gemini-pro')
else:
    logger.warning("GOOGLE_API_KEY not found. Abstractive summarization will be limited.")
    model = None


class CaseSummarizer:
    """
    Advanced case summarization with extractive and abstractive methods
    """
    
    # Summary length configurations (word counts)
    LENGTH_CONFIGS = {
        'short': {
            'min_words': 100,
            'max_words': 200,
            'sentences': 3
        },
        'medium': {
            'min_words': 200,
            'max_words': 400,
            'sentences': 6
        },
        'long': {
            'min_words': 400,
            'max_words': 800,
            'sentences': 12
        }
    }
    
    # Legal section markers
    SECTION_PATTERNS = {
        'facts': r'(?:facts?|background|circumstances|case history)',
        'issues': r'(?:issues?|questions?|matters?|points?)',
        'reasoning': r'(?:reasoning|analysis|discussion|consideration|held)',
        'judgment': r'(?:judgment|decision|order|conclusion|ruling)',
        'precedents': r'(?:precedents?|cited cases?|references?)'
    }
    
    def __init__(self):
        """Initialize the case summarizer"""
        self.model = model
        logger.info("CaseSummarizer initialized")
    
    def summarize_case(
        self, 
        case_data: Dict, 
        length: str = 'medium',
        method: str = 'hybrid'
    ) -> Dict:
        """
        Generate a comprehensive case summary
        
        Args:
            case_data: Dictionary containing case information
                - title: Case title
                - text: Full case text
                - court: Court name
                - year: Year of judgment
                - judges: List of judges
                - metadata: Additional metadata
            length: Summary length ('short', 'medium', 'long')
            method: Summarization method ('extractive', 'abstractive', 'hybrid')
        
        Returns:
            Dictionary with summary components:
                - summary: Main summary text
                - facts: Case facts
                - issues: Legal issues
                - reasoning: Court's reasoning
                - judgment: Final judgment
                - key_points: List of key points
                - metadata: Summary metadata
        """
        logger.info(f"Summarizing case: {case_data.get('title', 'Unknown')[:50]}... "
                   f"(length={length}, method={method})")
        
        # Validate inputs
        if length not in self.LENGTH_CONFIGS:
            logger.warning(f"Invalid length '{length}', defaulting to 'medium'")
            length = 'medium'
        
        if method not in ['extractive', 'abstractive', 'hybrid']:
            logger.warning(f"Invalid method '{method}', defaulting to 'hybrid'")
            method = 'hybrid'
        
        # Extract case text
        case_text = case_data.get('text', case_data.get('content', ''))
        if not case_text:
            logger.error("No case text provided")
            return self._create_error_summary("No case text available")
        
        # Prepare result structure
        result = {
            'case_id': case_data.get('case_id', case_data.get('id', 'unknown')),
            'title': case_data.get('title', 'Unknown Case'),
            'court': case_data.get('court', 'Unknown Court'),
            'year': case_data.get('year', 'Unknown'),
            'length': length,
            'method': method,
            'created_at': datetime.utcnow().isoformat()
        }
        
        try:
            # Extract legal components
            components = self._extract_legal_components(case_text)
            
            # Generate summary based on method
            if method == 'extractive':
                summary_data = self._extractive_summarize(
                    case_text, 
                    length, 
                    components
                )
            elif method == 'abstractive':
                summary_data = self._abstractive_summarize(
                    case_text,
                    case_data,
                    length,
                    components
                )
            else:  # hybrid
                summary_data = self._hybrid_summarize(
                    case_text,
                    case_data,
                    length,
                    components
                )
            
            result.update(summary_data)
            logger.info(f"Successfully generated {length} {method} summary")
            
        except Exception as e:
            logger.error(f"Error summarizing case: {e}", exc_info=True)
            result = self._create_error_summary(str(e))
        
        return result
    
    def _extract_legal_components(self, text: str) -> Dict[str, str]:
        """
        Extract different components of a legal case
        
        Args:
            text: Full case text
        
        Returns:
            Dictionary with extracted sections
        """
        components = {
            'facts': '',
            'issues': '',
            'reasoning': '',
            'judgment': '',
            'precedents': ''
        }
        
        # Split text into paragraphs
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        
        # Try to identify sections using patterns
        for section, pattern in self.SECTION_PATTERNS.items():
            section_text = []
            in_section = False
            
            for para in paragraphs:
                # Check if paragraph starts a new section
                if re.search(pattern, para[:100], re.IGNORECASE):
                    in_section = True
                    section_text.append(para)
                elif in_section:
                    # Check if we've entered a different section
                    is_other_section = any(
                        re.search(pat, para[:100], re.IGNORECASE)
                        for sec, pat in self.SECTION_PATTERNS.items()
                        if sec != section
                    )
                    if is_other_section:
                        break
                    section_text.append(para)
            
            if section_text:
                components[section] = '\n\n'.join(section_text[:3])  # Limit to 3 paragraphs
        
        # If no structured sections found, use positional heuristics
        if not any(components.values()):
            total_paras = len(paragraphs)
            if total_paras >= 4:
                components['facts'] = '\n\n'.join(paragraphs[:total_paras//4])
                components['issues'] = '\n\n'.join(paragraphs[total_paras//4:total_paras//2])
                components['reasoning'] = '\n\n'.join(paragraphs[total_paras//2:3*total_paras//4])
                components['judgment'] = '\n\n'.join(paragraphs[3*total_paras//4:])
        
        return components
    
    def _extractive_summarize(
        self, 
        text: str, 
        length: str, 
        components: Dict[str, str]
    ) -> Dict:
        """
        Generate extractive summary using TF-IDF and sentence scoring
        
        Args:
            text: Full case text
            length: Desired summary length
            components: Extracted case components
        
        Returns:
            Dictionary with summary data
        """
        # Split into sentences
        sentences = self._split_sentences(text)
        if not sentences:
            return {'summary': 'Unable to extract summary.'}
        
        # Calculate sentence scores
        sentence_scores = self._score_sentences(sentences, text)
        
        # Get target sentence count
        target_sentences = self.LENGTH_CONFIGS[length]['sentences']
        
        # Select top sentences (maintain original order)
        top_indices = sorted(
            sorted(enumerate(sentence_scores), key=lambda x: x[1], reverse=True)[:target_sentences],
            key=lambda x: x[0]
        )
        
        # Build summary
        summary_sentences = [sentences[idx] for idx, _ in top_indices]
        summary = ' '.join(summary_sentences)
        
        # Extract key points (top 5 sentences)
        key_points = [
            sentences[idx] 
            for idx, _ in sorted(
                enumerate(sentence_scores), 
                key=lambda x: x[1], 
                reverse=True
            )[:5]
        ]
        
        return {
            'summary': summary,
            'facts': self._summarize_component(components.get('facts', ''), length='short'),
            'issues': self._summarize_component(components.get('issues', ''), length='short'),
            'reasoning': self._summarize_component(components.get('reasoning', ''), length='medium'),
            'judgment': self._summarize_component(components.get('judgment', ''), length='short'),
            'key_points': key_points,
            'word_count': len(summary.split())
        }
    
    def _abstractive_summarize(
        self,
        text: str,
        case_data: Dict,
        length: str,
        components: Dict[str, str]
    ) -> Dict:
        """
        Generate abstractive summary using Gemini AI
        
        Args:
            text: Full case text
            case_data: Case metadata
            length: Desired summary length
            components: Extracted case components
        
        Returns:
            Dictionary with summary data
        """
        if not self.model:
            logger.warning("Gemini model not available, falling back to extractive")
            return self._extractive_summarize(text, length, components)
        
        config = self.LENGTH_CONFIGS[length]
        
        # Prepare prompt for Gemini
        prompt = f"""Summarize the following legal case in approximately {config['max_words']} words.

**Case Title:** {case_data.get('title', 'N/A')}
**Court:** {case_data.get('court', 'N/A')}
**Year:** {case_data.get('year', 'N/A')}

**Instructions:**
1. Provide a clear, concise summary suitable for legal professionals
2. Include: key facts, legal issues, court's reasoning, and final judgment
3. Use legal terminology appropriately
4. Maintain objectivity and accuracy
5. Target length: {config['min_words']}-{config['max_words']} words

**Case Text:**
{text[:4000]}  

**Summary:**"""
        
        try:
            response = self.model.generate_content(prompt)
            summary = response.text.strip()
            
            # Generate structured components
            facts_summary = self._generate_ai_component(
                components.get('facts', text[:1000]),
                "facts",
                case_data
            )
            
            issues_summary = self._generate_ai_component(
                components.get('issues', text[1000:2000]),
                "issues",
                case_data
            )
            
            reasoning_summary = self._generate_ai_component(
                components.get('reasoning', text[2000:3000]),
                "reasoning",
                case_data
            )
            
            judgment_summary = self._generate_ai_component(
                components.get('judgment', text[-1000:]),
                "judgment",
                case_data
            )
            
            # Extract key points using AI
            key_points = self._extract_key_points_ai(text, case_data)
            
            return {
                'summary': summary,
                'facts': facts_summary,
                'issues': issues_summary,
                'reasoning': reasoning_summary,
                'judgment': judgment_summary,
                'key_points': key_points,
                'word_count': len(summary.split())
            }
            
        except Exception as e:
            logger.error(f"Error in AI summarization: {e}")
            return self._extractive_summarize(text, length, components)
    
    def _hybrid_summarize(
        self,
        text: str,
        case_data: Dict,
        length: str,
        components: Dict[str, str]
    ) -> Dict:
        """
        Generate hybrid summary combining extractive and abstractive methods
        
        Args:
            text: Full case text
            case_data: Case metadata
            length: Desired summary length
            components: Extracted case components
        
        Returns:
            Dictionary with summary data
        """
        # First, get extractive summary for sentence selection
        extractive_result = self._extractive_summarize(text, length, components)
        
        # Then use AI to refine and improve the summary
        if self.model:
            try:
                config = self.LENGTH_CONFIGS[length]
                prompt = f"""Refine and improve the following legal case summary:

**Case Title:** {case_data.get('title', 'N/A')}
**Extracted Summary:**
{extractive_result['summary']}

**Instructions:**
1. Maintain all key legal information
2. Improve clarity and readability
3. Ensure proper legal terminology
4. Keep length between {config['min_words']}-{config['max_words']} words
5. Ensure smooth flow and coherence

**Refined Summary:**"""
                
                response = self.model.generate_content(prompt)
                refined_summary = response.text.strip()
                
                return {
                    'summary': refined_summary,
                    'facts': extractive_result.get('facts', ''),
                    'issues': extractive_result.get('issues', ''),
                    'reasoning': extractive_result.get('reasoning', ''),
                    'judgment': extractive_result.get('judgment', ''),
                    'key_points': extractive_result.get('key_points', []),
                    'word_count': len(refined_summary.split())
                }
                
            except Exception as e:
                logger.error(f"Error in hybrid refinement: {e}")
                return extractive_result
        
        return extractive_result
    
    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences"""
        # Simple sentence splitting (can be improved with NLTK)
        sentences = re.split(r'(?<=[.!?])\s+', text)
        # Filter out very short sentences
        return [s.strip() for s in sentences if len(s.split()) >= 5]
    
    def _score_sentences(self, sentences: List[str], full_text: str) -> List[float]:
        """
        Score sentences using TF-IDF-like approach
        
        Args:
            sentences: List of sentences
            full_text: Complete text for context
        
        Returns:
            List of scores for each sentence
        """
        # Tokenize and count words
        all_words = re.findall(r'\b\w+\b', full_text.lower())
        word_freq = Counter(all_words)
        
        # Calculate IDF-like scores (rarer words are more important)
        max_freq = max(word_freq.values()) if word_freq else 1
        word_importance = {
            word: (max_freq / freq) for word, freq in word_freq.items()
        }
        
        # Legal term bonus
        legal_terms = {
            'held', 'judgment', 'court', 'precedent', 'statute', 'act',
            'plaintiff', 'defendant', 'petitioner', 'respondent', 'appeal',
            'constitutional', 'fundamental', 'right', 'article', 'section'
        }
        
        scores = []
        for sentence in sentences:
            words = re.findall(r'\b\w+\b', sentence.lower())
            
            # Base score from word importance
            score = sum(word_importance.get(w, 0) for w in words)
            
            # Bonus for legal terms
            legal_bonus = sum(2 for w in words if w in legal_terms)
            score += legal_bonus
            
            # Bonus for sentence position (first and last sentences often important)
            # This is handled externally
            
            # Normalize by sentence length
            score = score / len(words) if words else 0
            
            scores.append(score)
        
        return scores
    
    def _summarize_component(self, text: str, length: str = 'short') -> str:
        """Summarize a specific component of the case"""
        if not text:
            return ''
        
        sentences = self._split_sentences(text)
        if not sentences:
            return text[:200] + '...' if len(text) > 200 else text
        
        # Get target sentences based on length
        target_map = {'short': 2, 'medium': 3, 'long': 5}
        target = min(target_map.get(length, 2), len(sentences))
        
        # Score and select top sentences
        scores = self._score_sentences(sentences, text)
        top_indices = sorted(
            sorted(enumerate(scores), key=lambda x: x[1], reverse=True)[:target],
            key=lambda x: x[0]
        )
        
        return ' '.join(sentences[idx] for idx, _ in top_indices)
    
    def _generate_ai_component(
        self, 
        text: str, 
        component_type: str, 
        case_data: Dict
    ) -> str:
        """Generate AI summary for a specific component"""
        if not text or not self.model:
            return text[:300] + '...' if len(text) > 300 else text
        
        component_prompts = {
            'facts': 'Summarize the key facts of this case in 2-3 sentences:',
            'issues': 'Identify the main legal issues in 1-2 sentences:',
            'reasoning': 'Summarize the court\'s reasoning in 3-4 sentences:',
            'judgment': 'State the final judgment in 1-2 sentences:'
        }
        
        prompt = f"""{component_prompts.get(component_type, 'Summarize:')}

**Case:** {case_data.get('title', 'N/A')}

**Text:**
{text[:1500]}

**Summary:**"""
        
        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            logger.error(f"Error generating AI component: {e}")
            return text[:300] + '...' if len(text) > 300 else text
    
    def _extract_key_points_ai(self, text: str, case_data: Dict) -> List[str]:
        """Extract key points using AI"""
        if not self.model:
            # Fallback to extractive
            sentences = self._split_sentences(text)
            scores = self._score_sentences(sentences, text)
            top_5 = sorted(
                enumerate(scores), 
                key=lambda x: x[1], 
                reverse=True
            )[:5]
            return [sentences[idx] for idx, _ in top_5]
        
        prompt = f"""Extract 5 key legal points from this case:

**Case:** {case_data.get('title', 'N/A')}
**Court:** {case_data.get('court', 'N/A')}

**Text:**
{text[:3000]}

**Format:** Return ONLY 5 bullet points, each starting with "- "

**Key Points:**"""
        
        try:
            response = self.model.generate_content(prompt)
            points_text = response.text.strip()
            
            # Parse bullet points
            points = [
                line.strip('- ').strip() 
                for line in points_text.split('\n') 
                if line.strip().startswith('-')
            ]
            
            return points[:5] if points else []
            
        except Exception as e:
            logger.error(f"Error extracting key points: {e}")
            return []
    
    def _create_error_summary(self, error_message: str) -> Dict:
        """Create error summary response"""
        return {
            'summary': f'Unable to generate summary: {error_message}',
            'facts': '',
            'issues': '',
            'reasoning': '',
            'judgment': '',
            'key_points': [],
            'error': True,
            'error_message': error_message
        }
    
    def batch_summarize(
        self,
        cases: List[Dict],
        length: str = 'medium',
        method: str = 'hybrid'
    ) -> List[Dict]:
        """
        Summarize multiple cases in batch
        
        Args:
            cases: List of case data dictionaries
            length: Summary length
            method: Summarization method
        
        Returns:
            List of summary results
        """
        logger.info(f"Batch summarizing {len(cases)} cases")
        results = []
        
        for i, case_data in enumerate(cases, 1):
            try:
                logger.info(f"Processing case {i}/{len(cases)}")
                summary = self.summarize_case(case_data, length, method)
                results.append(summary)
            except Exception as e:
                logger.error(f"Error summarizing case {i}: {e}")
                results.append(self._create_error_summary(str(e)))
        
        logger.info(f"Batch summarization complete: {len(results)} summaries generated")
        return results


# Singleton instance
_summarizer = None

def get_summarizer() -> CaseSummarizer:
    """Get or create summarizer singleton"""
    global _summarizer
    if _summarizer is None:
        _summarizer = CaseSummarizer()
    return _summarizer
