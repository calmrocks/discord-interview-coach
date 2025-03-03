import asyncio
import logging
from typing import Dict, Optional, Tuple, List
import discord
from ..providers.llm_provider import LLMProvider
from ..providers.question_provider import QuestionProvider

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

class InterviewSession:
    def __init__(self, user_id: int, interview_type: str):
        self.user_id = user_id
        self.interview_type = interview_type
        self.difficulty = None
        self.current_question = None
        self.status = "selecting_difficulty"
        self.start_time = discord.utils.utcnow()
        self.is_processing = False
        self.follow_up_count = 0
        self.qa_history = []  # Store all Q&A pairs including follow-ups

class InterviewService:
    def __init__(self):
        self.active_sessions: Dict[int, InterviewSession] = {}
        self.llm_provider = LLMProvider()
        self.question_provider = QuestionProvider()
        self.max_follow_ups = 5  # Maximum number of follow-up questions

    def create_session(self, user_id: int, interview_type: str) -> InterviewSession:
        """Create a new interview session"""
        session = InterviewSession(user_id, interview_type)
        self.active_sessions[user_id] = session
        return session

    def get_session(self, user_id: int) -> Optional[InterviewSession]:
        """Get active session for a user"""
        return self.active_sessions.get(user_id)

    def end_session(self, user_id: int):
        """End an interview session"""
        if user_id in self.active_sessions:
            del self.active_sessions[user_id]

    def set_difficulty(self, user_id: int, difficulty: str) -> bool:
        """Set difficulty for a session"""
        session = self.get_session(user_id)
        if session:
            session.difficulty = difficulty
            session.status = "waiting_for_answer"
            return True
        return False

    async def get_next_question(self, user_id: int) -> Optional[dict]:
        """Get the next question for a session"""
        session = self.get_session(user_id)
        if not session or not session.difficulty:
            return None

        try:
            question_data = self.question_provider.get_random_question(
                session.interview_type,
                session.difficulty
            )
            session.current_question = question_data
            session.status = "waiting_for_answer"
            return question_data
        except Exception as e:
            raise Exception(f"Error getting question: {str(e)}")

    async def process_response(self, user_id: int, response: str) -> Tuple[dict, bool]:
        """Process a user's response and determine if follow-up is needed"""
        session = self.get_session(user_id)
        if not session or session.is_processing:
            raise Exception("No active session or response already being processed")

        session.is_processing = True
        try:
            # Store the Q&A pair
            qa_pair = {
                "question": session.current_question["question"],
                "answer": response,
                "follow_ups": []
            }
            session.qa_history.append(qa_pair)

            # Evaluate response
            logger.debug(f"Evaluating response for user {user_id}")
            needs_followup, followup_question = await self._evaluate_response_async(
                session.current_question["question"],
                response
            )
            logger.debug(f"Evaluation result: needs_followup={needs_followup}, followup_question={followup_question}")

            # Determine if we should continue with follow-up
            should_continue = needs_followup and session.follow_up_count < self.max_follow_ups

            if should_continue:
                session.follow_up_count += 1
                session.current_question = {"question": followup_question}
                qa_pair["follow_ups"].append({
                    "question": followup_question,
                    "answer": None
                })
                logger.debug(f"Returning follow-up question: {followup_question}")
                return {"type": "follow_up", "question": followup_question}, True

            # Generate final summary if no follow-up needed or max reached
            logger.debug("Generating final summary")
            summary = await self._generate_summary_async(
                session.interview_type,
                session.difficulty,
                session.qa_history
            )

            logger.debug(f"Summary generated: {summary}")
            return {"type": "summary", "content": summary}, False

        except Exception as e:
            logger.error(f"Error in process_response: {str(e)}", exc_info=True)
            raise
        finally:
            session.is_processing = False

    async def _evaluate_response_async(self, question: str, response: str) -> Tuple[bool, Optional[str]]:
        """Async wrapper for LLM evaluation"""
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            None,
            self.llm_provider.evaluate_response,
            question,
            response
        )

    async def _generate_summary_async(self, interview_type: str, level: str, qa_history: List[dict]):
        """Async wrapper for summary generation"""
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            None,
            self.llm_provider.generate_interview_summary,
            interview_type,
            level,
            qa_history
        )

    def get_active_sessions(self) -> List[Tuple[int, InterviewSession]]:
        """Get all active interview sessions"""
        return list(self.active_sessions.items())