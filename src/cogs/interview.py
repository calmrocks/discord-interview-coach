from discord.ext import commands
import discord
from typing import Dict, Optional
from .embed_builder import EmbedBuilder
from ..providers.question_provider import QuestionProvider
from ..providers.llm_provider import LLMProvider

class InterviewSession:
    def __init__(self, user_id: int, interview_type: str):
        self.user_id = user_id
        self.interview_type = interview_type
        self.current_question = None
        self.status = "active"  # possible states: "active", "waiting_for_answer", "completed"
        self.start_time = discord.utils.utcnow()

class Interview(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_sessions: Dict[int, InterviewSession] = {}
        self.pending_selection: Dict[int, discord.Message] = {}
        self.embed_builder = EmbedBuilder()
        self.question_provider = QuestionProvider()
        self.llm_provider = LLMProvider()

    @commands.command(name='interview')
    async def start_interview(self, ctx):
        """Start a new interview session"""
        if ctx.author.id in self.active_sessions:
            await ctx.send("You already have an active interview session!")
            return

        try:
            # Send initial DM
            await ctx.author.send("Welcome to Discord Interview Coach! Starting your session...")

            # Send confirmation in the server
            await ctx.send(f"{ctx.author.mention} Check your DMs to start the interview!")

            # Create selection embed
            embed = discord.Embed(
                title="Interview Type Selection",
                description="Please select the type of interview you'd like to practice:",
                color=discord.Color.blue()
            )
            embed.add_field(name="💻 Technical", value="Programming and technical questions", inline=False)
            embed.add_field(name="👥 Behavioral", value="Soft skills and past experiences", inline=False)
            embed.add_field(name="📊 System Design", value="Architecture and design questions", inline=False)

            # Send and store the selection message
            selection_msg = await ctx.author.send(embed=embed)
            self.pending_selection[ctx.author.id] = selection_msg

            # Add reaction options
            reactions = ['💻', '👥', '📊']
            for reaction in reactions:
                await selection_msg.add_reaction(reaction)

        except discord.Forbidden:
            await ctx.send(
                f"{ctx.author.mention} I couldn't send you a DM. "
                "Please enable DMs from server members and try again!"
            )

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction: discord.Reaction, user: discord.User):
        """Handle interview type selection"""
        if user.bot:
            return

        if user.id in self.pending_selection:
            selection_msg = self.pending_selection[user.id]
            if reaction.message.id == selection_msg.id:
                reaction_types = {
                    '💻': 'technical',
                    '👥': 'behavioral',
                    '📊': 'system_design'
                }

                if str(reaction.emoji) in reaction_types:
                    interview_type = reaction_types[str(reaction.emoji)]

                    # Create new interview session
                    session = InterviewSession(user.id, interview_type)
                    self.active_sessions[user.id] = session

                    # Clean up pending selection
                    del self.pending_selection[user.id]

                    # Start the interview immediately
                    await self.start_interview_question(user)

    async def start_interview_question(self, user: discord.User):
        """Send the first question to the user"""
        session = self.active_sessions[user.id]

        try:
            # Get a random question
            question_data = self.question_provider.get_random_question(
                session.interview_type,
                "medium"
            )

            # Store the current question
            session.current_question = question_data
            session.status = "waiting_for_answer"

            # Create and send question embed
            embed = discord.Embed(
                title="Interview Question",
                description=question_data["question"],
                color=discord.Color.blue()
            )

            if "context" in question_data:
                embed.add_field(name="Context", value=question_data["context"], inline=False)

            embed.add_field(
                name="Instructions",
                value="Type your answer when you're ready. Take your time to think it through!",
                inline=False
            )

            await user.send(embed=embed)

        except Exception as e:
            await user.send(f"Error getting question: {str(e)}")
            session.status = "completed"
            del self.active_sessions[user.id]

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Handle user answers during interview"""
        # Ignore messages from bots or non-DM channels
        if message.author.bot or not isinstance(message.channel, discord.DMChannel):
            return

        # Check if user has an active session waiting for answer
        if message.author.id in self.active_sessions:
            session = self.active_sessions[message.author.id]

            if session.status == "waiting_for_answer":
                # Process the answer
                async with message.channel.typing():
                    try:
                        # Evaluate the response using LLM
                        needs_followup, followup_question = self.llm_provider.evaluate_response(
                            session.current_question["question"],
                            message.content
                        )

                        # Generate interview summary
                        summary = self.llm_provider.generate_interview_summary(
                            session.interview_type,
                            "medium",
                            [{
                                "question": session.current_question["question"],
                                "answer": message.content
                            }]
                        )

                        # Create and send feedback embed
                        feedback_embed = discord.Embed(
                            title="Interview Feedback",
                            description=summary["overall_assessment"],
                            color=discord.Color.green() if summary["meets_bar"] else discord.Color.orange()
                        )

                        if summary["strengths"]:
                            feedback_embed.add_field(
                                name="💪 Strengths",
                                value="\n".join(f"• {s}" for s in summary["strengths"]),
                                inline=False
                            )

                        if summary["improvement_areas"]:
                            feedback_embed.add_field(
                                name="🎯 Areas for Improvement",
                                value="\n".join(f"• {i}" for i in summary["improvement_areas"]),
                                inline=False
                            )

                        await message.channel.send(embed=feedback_embed)

                        # Send closing message
                        closing_embed = discord.Embed(
                            title="Interview Complete",
                            description="Thank you for participating! Use `!interview` to start another session.",
                            color=discord.Color.blue()
                        )
                        await message.channel.send(embed=closing_embed)

                        # Clean up session
                        session.status = "completed"
                        del self.active_sessions[message.author.id]

                    except Exception as e:
                        await message.channel.send(f"Error evaluating answer: {str(e)}")
                        session.status = "completed"
                        del self.active_sessions[message.author.id]

async def setup(bot):
    await bot.add_cog(Interview(bot))