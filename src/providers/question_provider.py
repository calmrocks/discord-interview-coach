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
            print(f"Attempting to load questions from: {file_path}")  # Debug print
            try:
                if not os.path.exists(file_path):
                    print(f"File does not exist: {file_path}")  # Debug print
                    continue

                with open(file_path, 'r') as f:
                    content = f.read()
                    print(f"Content of {file_path}:")  # Debug print
                    print(content[:100])  # Print first 100 chars
                    questions[question_type] = json.loads(content)["questions"]

            except json.JSONDecodeError as e:
                print(f"JSON decode error in {file_path}: {str(e)}")
                raise
            except Exception as e:
                print(f"Error loading {file_path}: {str(e)}")
                raise

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