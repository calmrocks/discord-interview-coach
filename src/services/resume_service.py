from ..providers.llm_provider import LLMProvider
from ..providers.prompt_manager import PromptManager

class ResumeService:
    def __init__(self):
        self.llm_provider = LLMProvider()
        self.prompt_manager = PromptManager()

    async def analyze_resume(self, resume_text: str) -> dict:
        """Analyze the resume and provide recommendations"""
        prompt = self.prompt_manager.format_prompt(
            "resume_analysis",
            resume_text=resume_text
        )

        try:
            result = self.llm_provider.generate_resume_feedback(prompt)
            return result
        except Exception as e:
            raise Exception(f"Failed to analyze resume: {str(e)}")