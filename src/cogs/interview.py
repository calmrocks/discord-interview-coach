from discord.ext import commands
import discord
from typing import Dict, Optional
from .embed_builder import EmbedBuilder  # Adjust import path as needed

class InterviewSession:
    def __init__(self, user_id: int, interview_type: str):
        self.user_id = user_id
        self.interview_type = interview_type
        self.current_question = 0
        self.answers = []
        self.status = "active"
        self.start_time = discord.utils.utcnow()

class Interview(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_sessions: Dict[int, InterviewSession] = {}
        self.pending_selection: Dict[int, discord.Message] = {}
        self.embed_builder = EmbedBuilder()
        self.current_questions = {}

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

            # Debug print
            print(f"Stored selection message ID: {selection_msg.id} for user {ctx.author.id}")

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
        # Debug print
        print(f"Reaction detected: {reaction.emoji} from user: {user.name}")

        # Ignore bot's own reactions
        if user.bot:
            return

        # Debug print
        print(f"Pending selections: {self.pending_selection}")
        print(f"User ID in pending: {user.id in self.pending_selection}")

        # Check if this is a pending selection message
        if user.id in self.pending_selection:
            selection_msg = self.pending_selection[user.id]

            # Debug print
            print(f"Selection msg ID: {selection_msg.id}")
            print(f"Reaction msg ID: {reaction.message.id}")

            if reaction.message.id == selection_msg.id:
                # Map reactions to interview types
                reaction_types = {
                    '💻': 'technical',
                    '👥': 'behavioral',
                    '📊': 'system_design'
                }

                if str(reaction.emoji) in reaction_types:
                    interview_type = reaction_types[str(reaction.emoji)]

                    # Debug print
                    print(f"Selected interview type: {interview_type}")

                    # Create new interview session
                    self.active_sessions[user.id] = InterviewSession(
                        user_id=user.id,
                        interview_type=interview_type
                    )

                    # Clean up pending selection
                    del self.pending_selection[user.id]

                    # Send confirmation and instructions
                    await self.send_interview_start_message(user, interview_type)

    async def send_interview_start_message(self, user: discord.User, interview_type: str):
        """Send the interview start message and instructions"""
        type_names = {
            'technical': 'Technical Interview',
            'behavioral': 'Behavioral Interview',
            'system_design': 'System Design Interview'
        }

        embed = discord.Embed(
            title=f"Starting {type_names[interview_type]}",
            description="Great choice! Let's begin your interview practice.",
            color=discord.Color.green()
        )

        embed.add_field(
            name="Instructions",
            value=(
                "• Take your time to think before answering\n"
                "• Type your answers as you would speak them\n"
                "• Use `!next` for the next question\n"
                "• Use `!end` to end the interview\n"
                "• Use `!pause` to pause the interview"
            ),
            inline=False
        )

        await user.send(embed=embed)
        await user.send("Ready to start? Type `!next` for your first question!")

async def setup(bot):
    await bot.add_cog(Interview(bot))