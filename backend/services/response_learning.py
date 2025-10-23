"""
Response Learning Service
Analyzes historical responses to extract writing style patterns
"""
import logging
import re
from typing import Dict, List, Optional
from collections import Counter
from sqlalchemy import select

from database import get_db_session
from models.database import HistoricalResponseExample
from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class ResponseStyleAnalyzer:
    """Analyzes historical responses to extract style patterns"""

    def __init__(self):
        """Initialize response style analyzer"""
        self.patterns = None
        logger.info("Initialized ResponseStyleAnalyzer")

    async def analyze_all_responses(self) -> Dict:
        """
        Analyze all historical responses and extract style patterns

        Returns:
            Dictionary of extracted patterns
        """
        logger.info("Analyzing all historical responses...")

        try:
            async with get_db_session() as session:
                # Fetch all active historical responses
                result = await session.execute(
                    select(HistoricalResponseExample).where(
                        HistoricalResponseExample.is_active == True
                    )
                )
                responses = result.scalars().all()

                if not responses:
                    logger.warning("No historical responses found")
                    return self._get_default_patterns()

                logger.info(f"Analyzing {len(responses)} historical responses")

                # Extract response bodies
                response_bodies = [r.response_body for r in responses]
                response_metadata = [r.response_metadata for r in responses]

                # Analyze patterns
                patterns = {
                    'length_patterns': self._analyze_length_patterns(response_bodies),
                    'structure_patterns': self._analyze_structure_patterns(response_bodies),
                    'opening_patterns': self._analyze_opening_patterns(response_bodies),
                    'closing_patterns': self._analyze_closing_patterns(response_bodies),
                    'tone_indicators': self._analyze_tone_indicators(response_bodies),
                    'content_patterns': self._analyze_content_patterns(response_bodies),
                    'vocabulary_patterns': self._analyze_vocabulary_patterns(response_bodies),
                    'cta_patterns': self._analyze_cta_patterns(response_metadata),
                    'sample_count': len(responses)
                }

                self.patterns = patterns

                logger.info("✅ Response analysis complete")

                return patterns

        except Exception as e:
            logger.error(f"Error analyzing responses: {e}", exc_info=True)
            return self._get_default_patterns()

    def _analyze_length_patterns(self, responses: List[str]) -> Dict:
        """Analyze length patterns across responses"""
        try:
            word_counts = [len(response.split()) for response in responses]
            sentence_counts = [len(response.split('.')) for response in responses]

            return {
                'avg_words': int(sum(word_counts) / len(word_counts)),
                'min_words': min(word_counts),
                'max_words': max(word_counts),
                'avg_sentences': int(sum(sentence_counts) / len(sentence_counts)),
                'word_count_distribution': {
                    'short': sum(1 for wc in word_counts if wc < 100),
                    'medium': sum(1 for wc in word_counts if 100 <= wc < 200),
                    'long': sum(1 for wc in word_counts if wc >= 200)
                }
            }
        except Exception as e:
            logger.error(f"Error analyzing length patterns: {e}")
            return {}

    def _analyze_structure_patterns(self, responses: List[str]) -> Dict:
        """Analyze structural patterns"""
        try:
            paragraph_counts = [len(response.split('\n\n')) for response in responses]
            bullet_usage = sum(1 for r in responses if '•' in r or '-' in r[:100])

            return {
                'avg_paragraphs': round(sum(paragraph_counts) / len(paragraph_counts), 1),
                'uses_bullets_percentage': round(bullet_usage / len(responses) * 100, 1),
                'structure_preference': 'multi_paragraph' if sum(paragraph_counts) / len(paragraph_counts) > 3 else 'concise'
            }
        except Exception as e:
            logger.error(f"Error analyzing structure patterns: {e}")
            return {}

    def _analyze_opening_patterns(self, responses: List[str]) -> Dict:
        """Analyze opening greeting patterns"""
        try:
            openings = []
            for response in responses:
                # Extract first line (likely greeting)
                first_line = response.split('\n')[0].strip()
                if len(first_line) < 50:  # Reasonable greeting length
                    openings.append(first_line.lower())

            # Common opening patterns
            greeting_patterns = {
                'hi': sum(1 for o in openings if o.startswith('hi ')),
                'hello': sum(1 for o in openings if o.startswith('hello ')),
                'dear': sum(1 for o in openings if o.startswith('dear ')),
                'hey': sum(1 for o in openings if o.startswith('hey '))
            }

            most_common = max(greeting_patterns, key=greeting_patterns.get)

            return {
                'most_common_greeting': most_common.capitalize(),
                'greeting_distribution': greeting_patterns,
                'uses_name_in_greeting': sum(1 for o in openings if ',' in o),
                'formality_level': 'formal' if greeting_patterns['dear'] > greeting_patterns['hi'] else 'casual'
            }
        except Exception as e:
            logger.error(f"Error analyzing opening patterns: {e}")
            return {}

    def _analyze_closing_patterns(self, responses: List[str]) -> Dict:
        """Analyze closing patterns"""
        try:
            closings = []
            for response in responses:
                # Extract last few lines
                lines = response.split('\n')
                last_lines = '\n'.join(lines[-5:]).lower()
                closings.append(last_lines)

            # Common closing phrases
            closing_phrases = {
                'best regards': sum(1 for c in closings if 'best regards' in c),
                'best': sum(1 for c in closings if 'best' in c and 'best regards' not in c),
                'thanks': sum(1 for c in closings if 'thanks' in c or 'thank you' in c),
                'sincerely': sum(1 for c in closings if 'sincerely' in c),
                'look forward': sum(1 for c in closings if 'look forward' in c)
            }

            most_common = max(closing_phrases, key=closing_phrases.get)

            return {
                'most_common_closing': most_common,
                'closing_distribution': closing_phrases,
                'includes_signature': sum(1 for c in closings if 'nutricraft' in c.lower())
            }
        except Exception as e:
            logger.error(f"Error analyzing closing patterns: {e}")
            return {}

    def _analyze_tone_indicators(self, responses: List[str]) -> Dict:
        """Analyze tone and formality indicators"""
        try:
            # Check for contractions (informal)
            contractions = sum(1 for r in responses if any(c in r.lower() for c in ["i'm", "we're", "you're", "can't", "won't"]))

            # Check for exclamation points (enthusiastic)
            exclamations = sum(1 for r in responses if '!' in r)

            # Check for personal pronouns (warm/personal)
            personal_we = sum(1 for r in responses if ' we ' in r.lower())
            personal_i = sum(1 for r in responses if ' i ' in r.lower())

            # Check for technical terms
            technical_terms = ['manufacturing', 'certification', 'gmp', 'moq', 'formulation']
            technical_usage = sum(1 for r in responses if any(term in r.lower() for term in technical_terms))

            return {
                'uses_contractions_percentage': round(contractions / len(responses) * 100, 1),
                'uses_exclamations_percentage': round(exclamations / len(responses) * 100, 1),
                'uses_we_percentage': round(personal_we / len(responses) * 100, 1),
                'uses_i_percentage': round(personal_i / len(responses) * 100, 1),
                'technical_depth': 'high' if technical_usage > len(responses) * 0.7 else 'medium',
                'overall_tone': 'warm_professional' if personal_we > len(responses) * 0.5 else 'formal_professional'
            }
        except Exception as e:
            logger.error(f"Error analyzing tone indicators: {e}")
            return {}

    def _analyze_content_patterns(self, responses: List[str]) -> Dict:
        """Analyze content and messaging patterns"""
        try:
            # Question patterns
            questions_asked = [r.count('?') for r in responses]

            # Call-to-action mentions
            mentions_call = sum(1 for r in responses if any(p in r.lower() for p in ['call', 'phone', 'speak']))
            mentions_email = sum(1 for r in responses if any(p in r.lower() for p in ['reply', 'let me know', 'email me']))
            mentions_meeting = sum(1 for r in responses if any(p in r.lower() for p in ['meeting', 'discuss', 'schedule']))

            # Pricing/timeline mentions
            mentions_pricing = sum(1 for r in responses if 'pric' in r.lower())
            mentions_timeline = sum(1 for r in responses if any(t in r.lower() for t in ['timeline', 'timeframe', 'how long']))

            # Capability mentions
            mentions_capabilities = sum(1 for r in responses if any(c in r.lower() for c in ['we can', 'we offer', 'we specialize', 'our capabilities']))

            return {
                'avg_questions_per_response': round(sum(questions_asked) / len(questions_asked), 1),
                'asks_clarifying_questions_percentage': round(sum(1 for q in questions_asked if q > 0) / len(questions_asked) * 100, 1),
                'mentions_call_percentage': round(mentions_call / len(responses) * 100, 1),
                'mentions_email_percentage': round(mentions_email / len(responses) * 100, 1),
                'mentions_meeting_percentage': round(mentions_meeting / len(responses) * 100, 1),
                'discusses_pricing_percentage': round(mentions_pricing / len(responses) * 100, 1),
                'discusses_timeline_percentage': round(mentions_timeline / len(responses) * 100, 1),
                'mentions_capabilities_percentage': round(mentions_capabilities / len(responses) * 100, 1)
            }
        except Exception as e:
            logger.error(f"Error analyzing content patterns: {e}")
            return {}

    def _analyze_vocabulary_patterns(self, responses: List[str]) -> Dict:
        """Analyze vocabulary and common phrases"""
        try:
            # Extract common phrases (3-5 words)
            all_text = ' '.join(responses).lower()

            # Common action phrases
            action_phrases = [
                'happy to', 'pleased to', 'glad to',
                'would love to', 'excited to',
                'let me know', 'feel free to',
                'don\'t hesitate', 'reach out'
            ]

            phrase_usage = {
                phrase: all_text.count(phrase)
                for phrase in action_phrases
            }

            # Get top 3 most common phrases
            top_phrases = sorted(phrase_usage.items(), key=lambda x: x[1], reverse=True)[:3]

            return {
                'common_action_phrases': [phrase for phrase, count in top_phrases if count > 0],
                'phrase_frequencies': dict(top_phrases)
            }
        except Exception as e:
            logger.error(f"Error analyzing vocabulary patterns: {e}")
            return {}

    def _analyze_cta_patterns(self, metadata_list: List[Dict]) -> Dict:
        """Analyze call-to-action patterns from metadata"""
        try:
            if not metadata_list or not any(metadata_list):
                return {'cta_preference': 'call'}

            call_ctas = sum(1 for m in metadata_list if m and m.get('has_call_cta'))
            email_ctas = sum(1 for m in metadata_list if m and m.get('has_email_cta'))

            return {
                'prefers_call_cta': call_ctas > email_ctas,
                'cta_preference': 'call' if call_ctas > email_ctas else 'email',
                'call_cta_percentage': round(call_ctas / len(metadata_list) * 100, 1),
                'email_cta_percentage': round(email_ctas / len(metadata_list) * 100, 1)
            }
        except Exception as e:
            logger.error(f"Error analyzing CTA patterns: {e}")
            return {}

    def _get_default_patterns(self) -> Dict:
        """Get default patterns when no historical data is available"""
        return {
            'length_patterns': {'avg_words': 120, 'min_words': 60, 'max_words': 200},
            'structure_patterns': {'avg_paragraphs': 3, 'structure_preference': 'concise'},
            'opening_patterns': {'most_common_greeting': 'Hi', 'formality_level': 'casual'},
            'closing_patterns': {'most_common_closing': 'best regards'},
            'tone_indicators': {'overall_tone': 'warm_professional', 'technical_depth': 'medium'},
            'content_patterns': {'avg_questions_per_response': 2, 'mentions_call_percentage': 50},
            'vocabulary_patterns': {'common_action_phrases': ['happy to', 'let me know']},
            'cta_patterns': {'cta_preference': 'call'},
            'sample_count': 0
        }

    async def get_learned_system_prompt_enhancement(self, base_priority: str) -> str:
        """
        Get system prompt enhancement based on learned patterns

        Args:
            base_priority: Base priority level (critical, high, medium, low)

        Returns:
            System prompt enhancement string
        """
        if self.patterns is None:
            await self.analyze_all_responses()

        if not self.patterns or self.patterns.get('sample_count', 0) == 0:
            return ""

        try:
            length = self.patterns.get('length_patterns', {})
            structure = self.patterns.get('structure_patterns', {})
            opening = self.patterns.get('opening_patterns', {})
            closing = self.patterns.get('closing_patterns', {})
            tone = self.patterns.get('tone_indicators', {})
            content = self.patterns.get('content_patterns', {})
            vocab = self.patterns.get('vocabulary_patterns', {})
            cta = self.patterns.get('cta_patterns', {})

            enhancement = f"""

LEARNED FROM YOUR HISTORICAL RESPONSES ({self.patterns['sample_count']} examples):

LENGTH & STRUCTURE:
- Target length: {length.get('avg_words', 120)} words (range: {length.get('min_words', 60)}-{length.get('max_words', 200)} words)
- Structure: {structure.get('avg_paragraphs', 3)} paragraphs, {structure.get('structure_preference', 'concise')} style

GREETING & CLOSING:
- Opening: Use "{opening.get('most_common_greeting', 'Hi')}" (formality: {opening.get('formality_level', 'casual')})
- Closing: Use "{closing.get('most_common_closing', 'best regards')}"

TONE & STYLE:
- Overall tone: {tone.get('overall_tone', 'warm_professional')}
- Technical depth: {tone.get('technical_depth', 'medium')}
- Personal pronouns: Use "we" in {tone.get('uses_we_percentage', 50)}% of responses
- Contractions: Use in {tone.get('uses_contractions_percentage', 20)}% of responses

CONTENT APPROACH:
- Ask ~{content.get('avg_questions_per_response', 2)} clarifying questions
- Mention capabilities: {content.get('mentions_capabilities_percentage', 60)}% of time
- Discuss pricing: {content.get('discusses_pricing_percentage', 40)}% of time
- Call-to-action preference: {cta.get('cta_preference', 'call')}

COMMON PHRASES YOU USE:
{chr(10).join('- "' + phrase + '"' for phrase in vocab.get('common_action_phrases', ['happy to help']))}

GUIDELINES:
- Keep responses around {length.get('avg_words', 120)} words
- Be {tone.get('overall_tone', 'warm and professional')}
- Prefer {cta.get('cta_preference', 'call')} CTAs when appropriate
"""

            return enhancement

        except Exception as e:
            logger.error(f"Error generating system prompt enhancement: {e}")
            return ""


# Singleton instance
_analyzer = None


def get_response_style_analyzer() -> ResponseStyleAnalyzer:
    """Get singleton response style analyzer instance"""
    global _analyzer
    if _analyzer is None:
        _analyzer = ResponseStyleAnalyzer()
    return _analyzer
