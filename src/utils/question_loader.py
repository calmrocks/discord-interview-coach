import json
import os
from typing import Dict, List, Optional
from pathlib import Path

class Question:
    def __init__(self, data: dict):
        self.id = data['id']
        self.question = data['question']
        self.category = data['category']
        self.difficulty = data['difficulty']
        self.follow_up = data.get('follow_up')
        self.keywords = data.get('keywords', [])

class QuestionBank:
    def __init__(self):
        self.questions: Dict[str, List[Question]] = {}
        self.current_version = "1.0"

    def load_questions(self, data_dir: str = "data/questions") -> None:
        """Load all question files from the data directory"""
        data_path = Path(data_dir)

        if not data_path.exists():
            raise FileNotFoundError(f"Question data directory not found: {data_dir}")

        # Load each JSON file in the questions directory
        for file_path in data_path.glob("*.json"):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                # Validate file structure
                if not self._validate_question_file(data):
                    print(f"Warning: Skipping invalid question file: {file_path}")
                    continue

                # Extract interview type from metadata
                interview_type = data['metadata']['type']

                # Convert questions to Question objects
                questions = [Question(q) for q in data['questions']]
                self.questions[interview_type] = questions

                print(f"Loaded {len(questions)} questions for {interview_type} interviews")

            except Exception as e:
                print(f"Error loading question file {file_path}: {e}")

    def _validate_question_file(self, data: dict) -> bool:
        """Validate the structure of a question file"""
        required_metadata = {'type', 'version', 'description'}
        required_question_fields = {'id', 'question', 'category', 'difficulty'}

        # Check metadata
        if 'metadata' not in data or not all(field in data['metadata'] for field in required_metadata):
            return False

        # Check questions array
        if 'questions' not in data or not isinstance(data['questions'], list):
            return False

        # Check each question
        for question in data['questions']:
            if not all(field in question for field in required_question_fields):
                return False

        return True

    def get_questions(self, interview_type: str) -> List[Question]:
        """Get all questions for a specific interview type"""
        return self.questions.get(interview_type, [])

    def get_random_question(self, interview_type: str) -> Optional[Question]:
        """Get a random question for a specific interview type"""
        import random
        questions = self.get_questions(interview_type)
        return random.choice(questions) if questions else None