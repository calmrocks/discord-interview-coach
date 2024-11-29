import boto3
import json
from typing import Dict, Optional
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class FeedbackGenerator:
    """
    Feedback generator for interview responses.
    Currently using Amazon Bedrock, but implementation can be changed without affecting other code.
    """
    def __init__(self):
        self.bedrock = boto3.client('bedrock-runtime')
        self.model_id = "anthropic.claude-v2"

    def _create_prompt(self, question: str, answer: str) -> str:
        return f"""Human: You are an experienced technical interviewer. Please evaluate the following interview response.
    
    Question: {question}
    
    Candidate's Answer: {answer}
    
    Please provide a structured evaluation following these criteria:
    1. Bar Assessment: [Raising the Bar / Meeting the Bar / Below the Bar]
    2. Key Strengths: What the candidate did well
    3. Areas for Improvement: Specific points where the answer could be better
    4. Suggested Better Answer: A brief example of a stronger response
    5. Follow-up Questions: 2-3 questions you would ask to probe deeper
    
    Format your response in a clear, structured manner using these exact headers.
    Be specific and constructive in your feedback, focusing on both technical accuracy and communication style.
    
    Assistant: """


    async def generate_feedback(self, question: str, answer: str) -> Dict:
        try:
            prompt = self._create_prompt(question, answer)

            response = self.bedrock.invoke_model(
                modelId=self.model_id,
                body=json.dumps({
                    "prompt": prompt,
                    "max_tokens_to_sample": 1000,
                    "temperature": 0.7,
                    "top_p": 0.9,
                })
            )

            response_body = json.loads(response.get('body').read())
            feedback_text = response_body.get('completion')

            # Parse the structured feedback
            feedback = self._parse_feedback(feedback_text)
            return feedback

        except Exception as e:
            print(f"Error generating feedback: {e}")
            return {
                "error": "Failed to generate feedback",
                "details": str(e)
            }

    def _parse_feedback(self, feedback_text: str) -> Dict:
        """Parse the structured feedback into a dictionary"""
        try:
            lines = feedback_text.split('\n')
            feedback = {
                "bar_assessment": "",
                "strengths": [],
                "improvements": [],
                "better_answer": "",
                "follow_up": []
            }

            current_section = None
            for line in lines:
                if "Bar Assessment:" in line:
                    current_section = "bar_assessment"
                    feedback["bar_assessment"] = line.split(":", 1)[1].strip()
                elif "Key Strengths:" in line:
                    current_section = "strengths"
                elif "Areas for Improvement:" in line:
                    current_section = "improvements"
                elif "Suggested Better Answer:" in line:
                    current_section = "better_answer"
                elif "Follow-up Questions:" in line:
                    current_section = "follow_up"
                elif line.strip() and current_section:
                    if current_section in ["strengths", "improvements", "follow_up"]:
                        feedback[current_section].append(line.strip())
                    elif current_section == "better_answer":
                        feedback["better_answer"] += line.strip() + " "

            return feedback

        except Exception as e:
            print(f"Error parsing feedback: {e}")
            return {"error": "Failed to parse feedback"}