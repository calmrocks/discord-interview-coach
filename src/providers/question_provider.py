import json
import os
import random
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

class QuestionProvider:
    def __init__(self, data_path="data/questions"):
        self.data_path = data_path
        self.questions = self._load_questions()

    def _load_questions(self) -> Dict[str, List[Dict[str, Any]]]:
        """Load questions from JSON files"""
        questions = {}
        for question_type in ["behavioral", "system_design", "technical"]:
            file_path = os.path.join(self.data_path, f"{question_type}.json")
            logger.debug(f"Attempting to load questions from: {file_path}")
            try:
                if not os.path.exists(file_path):
                    logger.debug(f"File does not exist: {file_path}")
                    continue

                with open(file_path, 'r') as f:
                    content = f.read()
                    logger.debug(f"Content of {file_path}:")
                    logger.debug(content[:100])
                    questions[question_type] = json.loads(content)["questions"]

            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error in {file_path}: {str(e)}")
                raise
            except Exception as e:
                logger.error(f"Error loading {file_path}: {str(e)}")
                raise

        return questions

    def get_random_question(self, question_type: str, difficulty: str) -> Dict[str, Any]:
        """Get a random question of the specified type and difficulty"""
        if question_type not in self.questions:
            raise ValueError(f"Invalid question type: {question_type}")

        eligible_questions = [q for q in self.questions[question_type]
                              if difficulty in q.get("difficulties", [difficulty])]

        if not eligible_questions:
            raise ValueError(f"No questions found for {question_type} at {difficulty} level")

        return random.choice(eligible_questions)

    def get_questions_by_category(self, question_type: str, category: str) -> List[Dict[str, Any]]:
        """Get questions of a specific type and category"""
        if question_type not in self.questions:
            raise ValueError(f"Invalid question type: {question_type}")

        return [q for q in self.questions[question_type] if category in q.get("categories", [category])]

    def get_questions_by_difficulty(self, question_type: str, difficulty: str) -> List[Dict[str, Any]]:
        """Get questions of a specific type and difficulty"""
        if question_type not in self.questions:
            raise ValueError(f"Invalid question type: {question_type}")

        return [q for q in self.questions[question_type] if difficulty in q.get("difficulties", [difficulty])]