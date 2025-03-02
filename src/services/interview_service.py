from typing import Dict, List, Tuple, Any, Optional
import random

from src.providers.question_provider import QuestionProvider
from src.providers.llm_provider import LLMProvider

class InterviewService:
    """Manages the interview flow logic, questions, and evaluation."""

    def __init__(self):
        self.question_provider = QuestionProvider()
        self.llm_provider = LLMProvider()

    def get_question(self, interview_type: str, level: str) -> Dict[str, Any]:
        """Get a random question matching the interview type and level"""
        return self.question_provider.get_random_question(interview_type, level)

    def evaluate_response(self, question: str, response: str) -> Tuple[bool, Optional[str]]:
        """Evaluate a candidate response and determine if follow-up is needed"""
        return self.llm_provider.evaluate_response(question, response)

    def evaluate_followup(self, response: str) -> Tuple[bool, Optional[str]]:
        """Determine if another follow-up question is needed"""
        # Simple random decision for now - in real implementation use LLM
        needs_followup = random.random() < 0.3  # 30% chance of follow-up
        followup = None

        if needs_followup:
            followup = "Could you give me a specific example of how you would handle that?"

        return needs_followup, followup

    def generate_summary(self, interview_type: str, level: str,
                         questions_asked: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate a summary of the interview"""
        return self.llm_provider.generate_interview_summary(
            interview_type,
            level,
            questions_asked
        )