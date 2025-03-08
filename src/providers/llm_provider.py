import os
import logging
import json
from typing import Dict, Any, Optional, List, Tuple

import boto3
from botocore.exceptions import ClientError

from .prompt_manager import PromptManager

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

class LLMProvider:
    """
    Provider for LLM services using AWS Bedrock.
    Handles formatting prompts and communicating with the LLM API.
    """

    def __init__(self):
        """Initialize the LLM provider with AWS Bedrock client and prompt manager."""
        self.prompt_manager = PromptManager()
        logger.info("PromptManager initialized successfully")

        # Initialize AWS Bedrock client
        self.bedrock_runtime = boto3.client(
            service_name='bedrock-runtime'
        )

        # Default model configuration
        self.default_model_id = os.getenv('BEDROCK_MODEL_ID', 'anthropic.claude-instant-1.2')
        self.max_tokens = int(os.getenv('LLM_MAX_TOKENS', 1000))
        self.temperature = float(os.getenv('LLM_TEMPERATURE', 0.7))

        logger.info(f"Using model: {self.default_model_id}, max_tokens: {self.max_tokens}, temperature: {self.temperature}")

    def _invoke_model(self, prompt: str, model_id: Optional[str] = None,
                      max_tokens: Optional[int] = None,
                      temperature: Optional[float] = None) -> Dict[str, Any]:
        """
        Send a request to the LLM model and return the response.
        """
        model_id = model_id or self.default_model_id
        max_tokens = max_tokens or self.max_tokens
        temperature = temperature or self.temperature

        logger.debug(f"Invoking model with prompt: {prompt}")
        logger.debug(f"Model ID: {model_id}, Max Tokens: {max_tokens}, Temperature: {temperature}")

        try:
            # Configure the request based on the model type
            if "anthropic.claude" in model_id:
                body = json.dumps({
                    "prompt": f"\n\nHuman: {prompt}\n\nAssistant:",
                    "max_tokens_to_sample": max_tokens,
                    "temperature": temperature,
                    "anthropic_version": "bedrock-2023-05-31"
                })
            else:
                raise ValueError(f"Unsupported model: {model_id}")

            logger.debug(f"Request body: {body}")

            response = self.bedrock_runtime.invoke_model(
                modelId=model_id,
                body=body
            )

            logger.debug(f"Raw response from Bedrock: {response}")

            # Read the response body
            response_body = json.loads(response.get('body').read())
            logger.debug(f"Parsed response body: {response_body}")

            # Parse response based on model type
            if "anthropic.claude" in model_id:
                content = response_body.get('completion', '')
                logger.debug(f"Extracted content: {content}")
                return {"content": content}
            else:
                return {"content": "Unsupported model response"}

        except Exception as e:
            logger.error(f"Error invoking Bedrock model: {e}", exc_info=True)
            raise Exception(f"Failed to invoke LLM: {str(e)}")

    def evaluate_response(self, interview_type: str, level: str, question_history: List[Dict[str, str]], current_question: str, current_response: str) -> Tuple[bool, Optional[str]]:
        """
        Evaluate a candidate's response to determine if a follow-up is needed.
        """
        history_prompt = self._format_question_history(question_history)

        prompt = self.prompt_manager.format_prompt(
            "evaluation",
            interview_type=interview_type,
            level=level,
            question_history=history_prompt,
            current_question=current_question,
            current_response=current_response
        )

        logger.debug(f"Evaluation prompt: {prompt}")

        try:
            result = self._invoke_model(prompt)
            content = result.get("content", "").strip()
            logger.debug(f"LLM response for evaluation: {content}")

            # Parse the LLM's decision from its response
            needs_followup = False
            followup_question = None

            lines = content.split('\n')
            for line in lines:
                if line.lower().startswith("follow-up needed:"):
                    needs_followup = "yes" in line.lower()
                elif line.lower().startswith("follow-up question:"):
                    followup_question = line.split(":", 1)[1].strip()
                    break

            if needs_followup and not followup_question:
                # If we couldn't extract a specific question but LLM wants a follow-up,
                # look for any line with a question mark
                for line in lines:
                    if "?" in line:
                        followup_question = line.strip()
                        break

            # If still no follow-up question, use a default
            if needs_followup and not followup_question:
                followup_question = "Can you elaborate more on your last answer?"

            logger.debug(f"Evaluation result: needs_followup={needs_followup}, followup_question={followup_question}")
            return needs_followup, followup_question

        except Exception as e:
            logger.error(f"Error evaluating response: {e}", exc_info=True)
            return False, None

    def _format_question_history(self, question_history: List[Dict[str, str]]) -> str:
        """Format the question history for the prompt."""
        formatted_history = ""
        for i, qa in enumerate(question_history, 1):
            formatted_history += f"Q{i}: {qa['question']}\n"
            formatted_history += f"A{i}: {qa['answer']}\n\n"
        return formatted_history.strip()

    def generate_interview_summary(self, interview_type: str, level: str,
                                   questions_and_responses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate a comprehensive summary of the interview.

        Args:
            interview_type: Type of interview (behavioral, technical, system_design)
            level: Experience level (entry, mid, senior)
            questions_and_responses: List of question-answer pairs from the interview

        Returns:
            Dictionary containing the summary sections
        """
        # Format questions and responses for the prompt
        formatted_qa = ""
        for i, qa in enumerate(questions_and_responses, 1):
            formatted_qa += f"Q{i}: {qa['question']}\n"
            formatted_qa += f"A{i}: {qa['answer']}\n"
            if qa.get('follow_ups'):
                for j, fu in enumerate(qa['follow_ups'], 1):
                    formatted_qa += f"  Follow-up {j}: {fu['question']}\n"
                    formatted_qa += f"  Response {j}: {fu['answer']}\n"
            formatted_qa += "\n"

        prompt = self.prompt_manager.format_prompt(
            "summary",
            interview_type=interview_type,
            level=level,
            questions_and_responses=formatted_qa
        )

        logger.debug(f"Summary generation prompt: {prompt}")

        result = self._invoke_model(
            prompt,
            max_tokens=1500  # Increase token limit for comprehensive summary
        )
        content = result.get("content", "").strip()
        logger.debug(f"LLM response for summary: {content}")

        # Parse the summary into sections
        sections = {
            "overall_assessment": "",
            "strengths": [],
            "improvement_areas": [],
            "examples": [],
            "meets_bar": "",
            "additional_comments": ""
        }

        current_section = None
        for line in content.split("\n"):
            line = line.strip()
            if not line:
                continue

            lower_line = line.lower()
            if "overall assessment" in lower_line:
                current_section = "overall_assessment"
                sections[current_section] = ""
            elif "strengths" in lower_line:
                current_section = "strengths"
            elif "areas for improvement" in lower_line:
                current_section = "improvement_areas"
            elif "key examples" in lower_line:
                current_section = "examples"
            elif "final decision" in lower_line:
                current_section = "meets_bar"
                sections[current_section] = line.split(":", 1)[1].strip() if ":" in line else line
            elif "additional comments" in lower_line:
                current_section = "additional_comments"
                sections[current_section] = ""
            elif current_section:
                if current_section == "overall_assessment":
                    sections[current_section] += line + " "
                elif current_section in ["strengths", "improvement_areas", "examples"]:
                    if line.startswith("-") or line[0].isdigit():
                        sections[current_section].append(line.lstrip("- ").strip())
                elif current_section == "additional_comments":
                    sections[current_section] += line + " "

        logger.debug(f"Parsed summary sections: {sections}")
        return sections

    def generate_coach_response(self, prompt: str) -> str:
        try:
            result = self._invoke_model(prompt, max_tokens=800)  # Adjust max_tokens as needed
            content = result.get("content", "").strip()
            return content
        except Exception as e:
            logger.error(f"Error generating coach response: {e}", exc_info=True)
            raise Exception(f"Failed to generate coach response: {str(e)}")

    def generate_resume_feedback(self, prompt: str) -> dict:
        """Generate feedback for a resume"""
        try:
            result = self._invoke_model(prompt, max_tokens=1500)
            content = result.get("content", "").strip()

            # Parse the structured feedback
            sections = {
                "overall_assessment": "",
                "strengths": [],
                "improvements": [],
                "refined_content": "",
                "additional_tips": []
            }

            current_section = None
            for line in content.split("\n"):
                line = line.strip()
                if not line:
                    continue

                lower_line = line.lower()
                if "overall assessment" in lower_line:
                    current_section = "overall_assessment"
                    sections[current_section] = ""
                elif "strengths" in lower_line:
                    current_section = "strengths"
                elif "improvements" in lower_line:
                    current_section = "improvements"
                elif "refined resume" in lower_line:
                    current_section = "refined_content"
                    sections[current_section] = ""
                elif "additional tips" in lower_line:
                    current_section = "additional_tips"
                elif current_section:
                    if current_section in ["strengths", "improvements", "additional_tips"]:
                        if line.startswith("-") or line[0].isdigit():
                            sections[current_section].append(line.lstrip("- ").strip())
                    else:
                        sections[current_section] += line + "\n"

            return sections

        except Exception as e:
            logger.error(f"Error generating resume feedback: {e}", exc_info=True)
            raise Exception(f"Failed to generate resume feedback: {str(e)}")