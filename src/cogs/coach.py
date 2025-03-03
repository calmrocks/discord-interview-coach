import discord
from discord.ext import commands
from ..providers.llm_provider import LLMProvider
from ..providers.prompt_manager import PromptManager

class InterviewCoach(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.llm_provider = LLMProvider()
        self.prompt_manager = PromptManager()

    @commands.command(name='coach')
    async def interview_coach(self, ctx, *, question: str):
        """
        Ask the interview coach for guidance on interview-related questions.
        Usage: !coach <your question>
        Example: !coach How should I answer "What's your greatest weakness?"
        """
        await ctx.send("Consulting the interview coach. Please wait...")

        try:
            prompt = self.prompt_manager.format_prompt("interview_coach", question=question)
            response = await self._get_coach_response(prompt)

            # Split the response into chunks if it's too long
            chunks = [response[i:i+1900] for i in range(0, len(response), 1900)]
            for chunk in chunks:
                await ctx.send(chunk)
        except Exception as e:
            await ctx.send(f"Sorry, I encountered an error while consulting the interview coach: {str(e)}")

    async def _get_coach_response(self, prompt: str) -> str:
        loop = self.bot.loop
        response = await loop.run_in_executor(None, self.llm_provider.generate_coach_response, prompt)
        return response

async def setup(bot):
    await bot.add_cog(InterviewCoach(bot))
