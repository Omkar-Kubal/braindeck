"""Answer Evaluation Service using Groq API for semantic similarity."""

import json
import re
import os
from dataclasses import dataclass
from typing import Optional, Dict, List
from groq import Groq
from flask import current_app


@dataclass
class EvaluationResult:
    """Result of answer evaluation."""
    score: float  # 0.0 to 1.0 match score
    is_correct: bool  # Whether the answer passes threshold
    partial_credit: float  # 0.0 to 1.0 for partial correctness
    feedback: str  # Explanation for the student
    model_answer: str  # Reference correct answer
    highlights: Dict[str, List[str]]  # correct/missing concepts


class AnswerEvaluator:
    """Evaluate student answers using AI semantic understanding."""
    
    CORRECT_THRESHOLD = 0.7  # Score above this is considered correct
    PARTIAL_THRESHOLD = 0.4  # Score above this gets partial credit
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the evaluator with API key."""
        self.api_key = api_key or current_app.config.get('GROQ_API_KEY') or os.environ.get('GROQ_API_KEY')
        if self.api_key:
            self.client = Groq(api_key=self.api_key)
        else:
            self.client = None
    
    def evaluate(
        self,
        question: str,
        expected_answer: str,
        student_answer: str,
        card_type: str = 'qa'
    ) -> EvaluationResult:
        """
        Evaluate a student's answer against the expected answer.
        """
        # Handle empty answers
        if not student_answer or not student_answer.strip():
            return EvaluationResult(
                score=0.0,
                is_correct=False,
                partial_credit=0.0,
                feedback="No answer was provided. Please try again.",
                model_answer=expected_answer,
                highlights={'correct': [], 'missing': ['Complete answer required']}
            )
        
        # For MCQ, do exact letter matching
        if card_type == 'mcq':
            return self._evaluate_mcq(expected_answer, student_answer)
        
        # For exact match (optional fast path)
        if student_answer.strip().lower() == expected_answer.strip().lower():
            return EvaluationResult(
                score=1.0,
                is_correct=True,
                partial_credit=1.0,
                feedback="Perfect! Your answer matches exactly.",
                model_answer=expected_answer,
                highlights={'correct': [student_answer], 'missing': []}
            )
        
        # Use AI for semantic evaluation
        if self.client:
            try:
                return self._ai_evaluate(question, expected_answer, student_answer)
            except Exception as e:
                current_app.logger.error(f"AI evaluation failed: {e}")
                return self._simple_evaluate(expected_answer, student_answer)
        else:
            return self._simple_evaluate(expected_answer, student_answer)
    
    def _evaluate_mcq(self, expected: str, student: str) -> EvaluationResult:
        """Evaluate MCQ answer (letter matching)."""
        expected_letter = expected.strip().upper()[0] if expected else ''
        student_letter = student.strip().upper()[0] if student else ''
        
        is_correct = expected_letter == student_letter
        
        return EvaluationResult(
            score=1.0 if is_correct else 0.0,
            is_correct=is_correct,
            partial_credit=1.0 if is_correct else 0.0,
            feedback="Correct!" if is_correct else f"The correct answer is {expected_letter}.",
            model_answer=expected,
            highlights={
                'correct': [student_letter] if is_correct else [],
                'missing': [] if is_correct else [expected_letter]
            }
        )
    
    def _ai_evaluate(
        self,
        question: str,
        expected_answer: str,
        student_answer: str
    ) -> EvaluationResult:
        """Use Groq to semantically evaluate the answer."""
        
        prompt = f"""You are an expert educator evaluating a student's answer. Analyze the semantic correctness.

**Question:** {question}

**Expected Answer:** {expected_answer}

**Student's Answer:** {student_answer}

Evaluate and respond with a JSON object:
{{
    "score": <float 0.0-1.0>,
    "is_correct": <boolean>,
    "partial_credit": <float 0.0-1.0>,
    "feedback": "<constructive feedback>",
    "correct_concepts": ["list", "of", "correct", "concepts"],
    "missing_concepts": ["list", "of", "missing", "concepts"]
}}

Scoring: 0.9-1.0=excellent, 0.7-0.9=mostly correct, 0.4-0.7=partial, 0.0-0.4=incorrect

Return ONLY the JSON object."""

        response = self.client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=500
        )
        
        try:
            cleaned = re.sub(r'```json\s*', '', response.choices[0].message.content)
            cleaned = re.sub(r'```\s*', '', cleaned)
            result = json.loads(cleaned.strip())
            
            score = float(result.get('score', 0.5))
            
            return EvaluationResult(
                score=score,
                is_correct=result.get('is_correct', score >= self.CORRECT_THRESHOLD),
                partial_credit=float(result.get('partial_credit', score)),
                feedback=result.get('feedback', 'Answer evaluated.'),
                model_answer=expected_answer,
                highlights={
                    'correct': result.get('correct_concepts', []),
                    'missing': result.get('missing_concepts', [])
                }
            )
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            current_app.logger.error(f"Failed to parse evaluation response: {e}")
            return self._simple_evaluate(expected_answer, student_answer)
    
    def _simple_evaluate(self, expected: str, student: str) -> EvaluationResult:
        """Simple keyword-based evaluation as fallback."""
        expected_words = set(expected.lower().split())
        student_words = set(student.lower().split())
        
        stop_words = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 
                      'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
                      'would', 'could', 'should', 'may', 'might', 'must', 'shall',
                      'to', 'of', 'in', 'for', 'on', 'with', 'at', 'by', 'from',
                      'as', 'into', 'through', 'during', 'before', 'after', 'above',
                      'below', 'between', 'under', 'again', 'further', 'then', 'once',
                      'and', 'but', 'or', 'nor', 'so', 'yet', 'both', 'either', 'neither',
                      'not', 'only', 'own', 'same', 'than', 'too', 'very', 'just'}
        
        expected_keywords = expected_words - stop_words
        student_keywords = student_words - stop_words
        
        if not expected_keywords:
            expected_keywords = expected_words
        
        correct = expected_keywords & student_keywords
        missing = expected_keywords - student_keywords
        
        if not expected_keywords:
            score = 0.5
        else:
            score = len(correct) / len(expected_keywords)
        
        is_correct = score >= self.CORRECT_THRESHOLD
        
        if score >= 0.9:
            feedback = "Excellent! Your answer covers all the key points."
        elif score >= 0.7:
            feedback = "Good answer! You got most of the key concepts."
        elif score >= 0.4:
            feedback = "Partial answer. You're on the right track but missing some key points."
        else:
            feedback = "Your answer needs improvement. Review the model answer below."
        
        return EvaluationResult(
            score=score,
            is_correct=is_correct,
            partial_credit=score if score >= self.PARTIAL_THRESHOLD else 0.0,
            feedback=feedback,
            model_answer=expected,
            highlights={
                'correct': list(correct)[:5],
                'missing': list(missing)[:5]
            }
        )
