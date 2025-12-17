"""AI Flashcard Generation Service using Groq API with Llama."""

import json
import re
import os
from typing import List, Dict, Optional
from groq import Groq
from flask import current_app


class FlashcardGenerator:
    """Generate flashcards from text using Groq API with Llama."""
    
    CARD_TYPES = {
        'qa': 'Question and Answer',
        'mcq': 'Multiple Choice Question',
        'fill_blank': 'Fill in the Blank',
        'mixed': 'Mixed (Q&A and MCQ)'
    }
    
    DIFFICULTY_LEVELS = {
        'beginner': 'Beginner - Basic concepts and definitions',
        'intermediate': 'Intermediate - Application and understanding',
        'advanced': 'Advanced - Analysis and synthesis',
        'expert': 'Expert - Evaluation and complex problem-solving'
    }

    def __init__(self, api_key: Optional[str] = None):
        """Initialize the generator with API key."""
        self.api_key = api_key or current_app.config.get('GROQ_API_KEY') or os.environ.get('GROQ_API_KEY')
        if self.api_key:
            self.client = Groq(api_key=self.api_key)
        else:
            self.client = None
    
    def generate_flashcards(
        self,
        text: str,
        card_type: str = 'mixed',
        difficulty: str = 'intermediate',
        quantity: int = 10,
        focus_area: str = 'key_concepts'
    ) -> List[Dict]:
        """
        Generate flashcards from the provided text.
        
        Args:
            text: Source material to generate flashcards from
            card_type: Type of cards to generate (qa, mcq, fill_blank, mixed)
            difficulty: Difficulty level of questions
            quantity: Number of flashcards to generate
            focus_area: What to focus on (key_concepts, definitions, dates_events)
            
        Returns:
            List of flashcard dictionaries with question, answer, type, etc.
        """
        if not self.client:
            raise ValueError("Groq API key not configured. Set GROQ_API_KEY in environment.")
        
        if not text or len(text.strip()) < 50:
            raise ValueError("Source text must be at least 50 characters")
        
        prompt = self._build_generation_prompt(text, card_type, difficulty, quantity, focus_area)
        
        try:
            response = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": "You are an expert educational content creator. Always respond with valid JSON only, no markdown formatting."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=4000
            )
            flashcards = self._parse_response(response.choices[0].message.content, card_type)
            return flashcards[:quantity]
        except Exception as e:
            current_app.logger.error(f"Flashcard generation failed: {e}")
            raise RuntimeError(f"Failed to generate flashcards: {str(e)}")
    
    def _build_generation_prompt(
        self,
        text: str,
        card_type: str,
        difficulty: str,
        quantity: int,
        focus_area: str
    ) -> str:
        """Build the prompt for the API."""
        
        focus_instructions = {
            'key_concepts': 'Focus on the main concepts, principles, and important ideas.',
            'definitions': 'Focus on definitions, terminology, and vocabulary.',
            'dates_events': 'Focus on dates, events, timelines, and sequences.',
            'processes': 'Focus on processes, steps, and procedures.'
        }
        
        card_type_instructions = {
            'qa': '''Generate Question and Answer flashcards.
Each flashcard should have:
- "type": "qa"
- "question": A clear, specific question
- "answer": A comprehensive but concise answer''',
            
            'mcq': '''Generate Multiple Choice Question flashcards.
Each flashcard should have:
- "type": "mcq"  
- "question": A clear question
- "options": Array of 4 options labeled A, B, C, D
- "answer": The correct option letter (A, B, C, or D)
- "explanation": Brief explanation of why the answer is correct''',
            
            'fill_blank': '''Generate Fill in the Blank flashcards.
Each flashcard should have:
- "type": "fill_blank"
- "question": A sentence with _____ for the blank
- "answer": The word or phrase that fills the blank''',
            
            'mixed': '''Generate a mix of Question/Answer and Multiple Choice flashcards.
For Q&A cards:
- "type": "qa"
- "question": A clear question
- "answer": A comprehensive answer

For MCQ cards:
- "type": "mcq"
- "question": A clear question
- "options": Array of 4 options
- "answer": The correct option letter
- "explanation": Why this is correct'''
        }
        
        prompt = f"""Generate exactly {quantity} high-quality flashcards from the following text.

**Difficulty Level:** {self.DIFFICULTY_LEVELS.get(difficulty, difficulty)}
**Focus:** {focus_instructions.get(focus_area, focus_area)}

{card_type_instructions.get(card_type, card_type_instructions['qa'])}

**Important Instructions:**
1. Each flashcard should test a single concept
2. Questions should be clear and unambiguous
3. Answers should be accurate and based only on the provided text
4. For MCQ, make wrong options plausible but clearly incorrect
5. Add a "category" field to classify each card

**Output Format:**
Return ONLY a valid JSON array of flashcard objects. No markdown, no explanation, just the JSON array.

**Source Text:**
{text[:6000]}

Generate the JSON array now:"""
        
        return prompt
    
    def _parse_response(self, response_text: str, card_type: str) -> List[Dict]:
        """Parse the API response into flashcard dictionaries."""
        try:
            # Remove any markdown code blocks
            cleaned = re.sub(r'```json\s*', '', response_text)
            cleaned = re.sub(r'```\s*', '', cleaned)
            cleaned = cleaned.strip()
            
            flashcards = json.loads(cleaned)
            
            if not isinstance(flashcards, list):
                flashcards = [flashcards]
            
            # Validate and normalize each flashcard
            validated = []
            for i, card in enumerate(flashcards):
                if not isinstance(card, dict):
                    continue
                    
                normalized = {
                    'id': i + 1,
                    'type': card.get('type', 'qa'),
                    'question': card.get('question', ''),
                    'answer': card.get('answer', ''),
                    'category': card.get('category', 'General'),
                    'options': card.get('options', []),
                    'explanation': card.get('explanation', ''),
                    'source': 'ai_generated'
                }
                
                if normalized['question'] and normalized['answer']:
                    validated.append(normalized)
            
            return validated
            
        except json.JSONDecodeError as e:
            current_app.logger.error(f"Failed to parse JSON response: {e}")
            return self._fallback_parse(response_text)
    
    def _fallback_parse(self, text: str) -> List[Dict]:
        """Fallback parser for malformed JSON responses."""
        flashcards = []
        
        qa_pattern = r'"question"\s*:\s*"([^"]+)"[^}]*"answer"\s*:\s*"([^"]+)"'
        matches = re.findall(qa_pattern, text, re.IGNORECASE | re.DOTALL)
        
        for i, (question, answer) in enumerate(matches):
            flashcards.append({
                'id': i + 1,
                'type': 'qa',
                'question': question.strip(),
                'answer': answer.strip(),
                'category': 'General',
                'source': 'ai_generated'
            })
        
        return flashcards
    
    def refine_flashcard(self, flashcard: Dict, feedback: str) -> Dict:
        """Refine a flashcard based on user feedback."""
        if not self.client:
            raise ValueError("Groq API key not configured")
        
        prompt = f"""Improve this flashcard based on the feedback provided.

Current Flashcard:
- Question: {flashcard.get('question', '')}
- Answer: {flashcard.get('answer', '')}
- Type: {flashcard.get('type', 'qa')}

User Feedback: {feedback}

Return the improved flashcard as a JSON object with the same structure.
Only return the JSON object, no other text."""

        try:
            response = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=500
            )
            parsed = self._parse_response(response.choices[0].message.content, flashcard.get('type', 'qa'))
            if parsed:
                return parsed[0]
            return flashcard
        except Exception as e:
            current_app.logger.error(f"Flashcard refinement failed: {e}")
            return flashcard
