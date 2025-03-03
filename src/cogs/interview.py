from discord.ext import commands
import logging
import discord
from src.utils.embed_builder import EmbedBuilder
from ..services.interview_service import InterviewService


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

class Interview(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.embed_builder = EmbedBuilder()
        self.interview_service = InterviewService()
        self.pending_selection: Dict[int, Tuple[discord.Message, str]] = {}

    @commands.command(name='interview')
    async def start_interview(self, ctx):
        """
        Start a mock interview session.
        Usage: !interview
        The bot will guide you through selecting an interview type and difficulty.
        """
        if self.interview_service.get_session(ctx.author.id):
            await ctx.send("You already have an active interview session!")
            return

        try:
            await ctx.author.send("Welcome to Discord Interview Coach! Starting your session...")
            await ctx.send(f"{ctx.author.mention} Check your DMs to start the interview!")

            # Create selection embed
            embed = self.embed_builder.create_interview_type_selection()
            selection_msg = await ctx.author.send(embed=embed)

            # Store message and selection type
            self.pending_selection[ctx.author.id] = (selection_msg, "type")

            # Add reaction options
            reactions = ['💻', '👥', '📊']
            for reaction in reactions:
                await selection_msg.add_reaction(reaction)

        except discord.Forbidden:
            await ctx.send(
                f"{ctx.author.mention} I couldn't send you a DM. "
                "Please enable DMs from server members and try again!"
            )

    async def send_difficulty_selection(self, user: discord.User):
        """Send difficulty selection message"""
        embed = self.embed_builder.create_difficulty_selection()
        difficulty_msg = await user.send(embed=embed)

        # Store message and selection type
        self.pending_selection[user.id] = (difficulty_msg, "difficulty")

        # Add reaction options
        reactions = ['🟢', '🟡', '🔴']
        for reaction in reactions:
            await difficulty_msg.add_reaction(reaction)

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction: discord.Reaction, user: discord.User):
        """Handle interview type and difficulty selection"""
        if user.bot or user.id not in self.pending_selection:
            return

        selection_msg, selection_type = self.pending_selection[user.id]
        if reaction.message.id != selection_msg.id:
            return

        if selection_type == "type":
            # Handle interview type selection
            reaction_types = {
                '💻': 'technical',
                '👥': 'behavioral',
                '📊': 'system_design'
            }

            if str(reaction.emoji) in reaction_types:
                interview_type = reaction_types[str(reaction.emoji)]
                self.interview_service.create_session(user.id, interview_type)
                await selection_msg.delete()  # Clean up the selection message
                await self.send_difficulty_selection(user)

        elif selection_type == "difficulty":
            # Handle difficulty selection
            difficulty_levels = {
                '🟢': 'easy',
                '🟡': 'medium',
                '🔴': 'hard'
            }

            if str(reaction.emoji) in difficulty_levels:
                difficulty = difficulty_levels[str(reaction.emoji)]
                self.interview_service.set_difficulty(user.id, difficulty)
                await selection_msg.delete()  # Clean up the selection message
                del self.pending_selection[user.id]
                await self.start_interview_question(user)

    async def start_interview_question(self, user: discord.User):
        """Start the interview with the first question"""
        try:
            question_data = await self.interview_service.get_next_question(user.id)
            if question_data:
                session = self.interview_service.get_session(user.id)
                embed = self.embed_builder.create_question_embed(
                    session.interview_type,
                    session.difficulty,
                    question_data
                )
                await user.send("Great! Let's begin the interview.")
                await user.send(embed=embed)
            else:
                await user.send("Error: Could not get a question. Please try again.")
                self.interview_service.end_session(user.id)
        except Exception as e:
            await user.send(f"Error starting interview: {str(e)}")
            self.interview_service.end_session(user.id)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not isinstance(message.channel, discord.DMChannel):
            return

        session = self.interview_service.get_session(message.author.id)
        if not session or session.status != "waiting_for_answer":
            return

        async with message.channel.typing():
            try:
                logger.debug(f"Processing response for user {message.author.id}")
                await message.channel.send("Processing your response... Please wait.")
                result, continue_interview = await self.interview_service.process_response(
                    message.author.id,
                    message.content
                )
                logger.debug(f"Process response result: {result}, continue_interview: {continue_interview}")

                if continue_interview:
                    # Send follow-up question
                    if isinstance(result, dict) and 'question' in result:
                        follow_up_embed = self.embed_builder.create_question_embed(
                            session.interview_type,
                            session.difficulty,
                            {"question": result['question']}
                        )
                        await message.channel.send(embed=follow_up_embed)
                    else:
                        logger.error(f"Unexpected result format for follow-up: {result}")
                        await message.channel.send("An error occurred while processing your response. Please try again.")
                else:
                    # Send summary and end interview
                    if isinstance(result, dict) and 'content' in result:
                        summary = result['content']
                        summary_embed = self.create_summary_embed(summary)
                        await message.channel.send(embed=summary_embed)
                    else:
                        logger.error(f"Unexpected result format for summary: {result}")
                        await message.channel.send("An error occurred while generating the summary. The interview has ended.")
                    self.interview_service.end_session(message.author.id)

            except Exception as e:
                logger.error(f"Error processing response: {str(e)}", exc_info=True)
                await message.channel.send(f"Error processing response: {str(e)}")
                self.interview_service.end_session(message.author.id)

    @commands.command(name='active_interviews')
    async def check_active_interviews(self, ctx):
        """Check currently active interview sessions"""
        active_sessions = self.interview_service.get_active_sessions()
        if not active_sessions:
            await ctx.send("No active interview sessions.")
            return

        embed = self.embed_builder.create_active_sessions_embed(active_sessions)
        await ctx.send(embed=embed)

    def create_summary_embed(self, summary):
        embed = discord.Embed(title="Interview Summary", color=discord.Color.blue())

        # Overall Assessment
        embed.add_field(name="Overall Assessment", value=summary.get("overall_assessment", "N/A"), inline=False)

        # Strengths
        strengths = summary.get("strengths", [])
        strengths_text = "\n".join(f"• {strength}" for strength in strengths) if strengths else "N/A"
        embed.add_field(name="Strengths", value=strengths_text, inline=False)

        # Areas for Improvement
        improvements = summary.get("improvement_areas", [])
        improvements_text = "\n".join(f"• {improvement}" for improvement in improvements) if improvements else "N/A"
        embed.add_field(name="Areas for Improvement", value=improvements_text, inline=False)

        # Key Examples
        examples = summary.get("examples", [])
        examples_text = "\n".join(f"{i+1}. {example}" for i, example in enumerate(examples)) if examples else "N/A"
        embed.add_field(name="Key Examples", value=examples_text, inline=False)

        # Final Decision
        embed.add_field(name="Final Decision", value=summary.get("meets_bar", "N/A"), inline=False)

        # Additional Comments
        if "additional_comments" in summary:
            embed.add_field(name="Additional Comments", value=summary["additional_comments"], inline=False)

        return embed

async def setup(bot):
    await bot.add_cog(Interview(bot))