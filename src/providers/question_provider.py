import json
import os
import random
from typing import Dict, Any, List

class QuestionProvider:
    def __init__(self, data_path="data/questions"):
        self.data_path = data_path
        self.questions = self._load_questions()

    def _load_questions(self) -> Dict[str, List[Dict[str, Any]]]:
        """Load questions from JSON files"""
        questions = {}
        for question_type in ["behavioral", "system_design", "technical"]:
            file_path = os.path.join(self.data_path, f"{question_type}.json")
            with open(file_path, 'r') as f:
                questions[question_type] = json.load(f)["questions"]
        return questions

    def get_random_question(self, question_type: str, difficulty: str) -> Dict[str, Any]:
        """Get a random question of the specified type and difficulty"""
        if question_type not in self.questions:
            raise ValueError(f"Invalid question type: {question_type}")

        eligible_questions = [q for q in self.questions[question_type]
                              if q["difficulty"] == difficulty]

        if not eligible_questions:
            raise ValueError(f"No questions found for {question_type} at {difficulty} level")

        return random.choice(eligible_questions)