import discord
from discord.ext import commands
from ..services.resume_service import ResumeService
from src.utils.embed_builder import EmbedBuilder

class Resume(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.resume_service = ResumeService()
        self.embed_builder = EmbedBuilder()
        self.pending_resumes = {}  # Store user_id: resume_text

    @commands.command(name='resume')
    async def refine_resume(self, ctx):
        """
        Start a resume refinement session.
        Usage: !resume
        The bot will guide you through the resume refinement process in DMs.
        """
        try:
            # Send initial DM to user
            await ctx.author.send("Welcome to the Resume Refinement service! Please paste your resume text below.")
            await ctx.send(f"{ctx.author.mention} Check your DMs to start the resume refinement process!")

            self.pending_resumes[ctx.author.id] = True

        except discord.Forbidden:
            await ctx.send(
                f"{ctx.author.mention} I couldn't send you a DM. "
                "Please enable DMs from server members and try again!"
            )

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not isinstance(message.channel, discord.DMChannel):
            return

        if message.author.id in self.pending_resumes:
            async with message.channel.typing():
                try:
                    await message.channel.send("Analyzing your resume... Please wait.")

                    # Get refinement feedback
                    feedback = await self.resume_service.analyze_resume(message.content)

                    # Send feedback using embed
                    embed = self.embed_builder.create_resume_feedback_embed(feedback)
                    await message.channel.send(embed=embed)

                    # Clean up
                    del self.pending_resumes[message.author.id]

                except Exception as e:
                    await message.channel.send(f"Error processing resume: {str(e)}")
                    del self.pending_resumes[message.author.id]

async def setup(bot):
    await bot.add_cog(Resume(bot))