import json
import os

class PromptManager:
    def __init__(self, prompt_file="data/prompts.json"):
        self.prompt_file = prompt_file
        self.prompts = self._load_prompts()

    def _load_prompts(self):
        with open(self.prompt_file, 'r') as f:
            return json.load(f)

    def format_prompt(self, prompt_type, **kwargs):
        """Format a prompt template with the provided parameters"""
        if prompt_type not in self.prompts:
            raise ValueError(f"Unknown prompt type: {prompt_type}")

        prompt_data = self.prompts[prompt_type]
        template = prompt_data["template"]

        # Validate that all required parameters are provided
        for param in prompt_data["parameters"]:
            if param not in kwargs:
                raise ValueError(f"Missing parameter '{param}' for prompt '{prompt_type}'")

        # Format the template with the provided parameters
        return template.format(**kwargs)