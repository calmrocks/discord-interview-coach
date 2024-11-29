from discord.ext import commands
import discord
from typing import Dict, Optional
from ..utils.question_loader import QuestionBank
from ..utils.feedback import FeedbackGenerator


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
        self.pending_selection: Dict[int, discord.Message] = {}  # Store user_id: selection_message
        self.question_bank = QuestionBank()
        self.feedback_generator = FeedbackGenerator()
        self.current_questions = {}  # Store current question for each user

        # Load questions when the cog is initialized
        try:
            self.question_bank.load_questions()
        except Exception as e:
            print(f"Error loading questions: {e}")

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

            # Create and send selection embed
            embed = discord.Embed(
                title="Interview Type Selection",
                description="Please select the type of interview you'd like to practice:",
                color=discord.Color.blue()
            )
            embed.add_field(name="💻 Technical", value="Programming and technical questions", inline=False)
            embed.add_field(name="👥 Behavioral", value="Soft skills and past experiences", inline=False)
            embed.add_field(name="📊 System Design", value="Architecture and design questions", inline=False)

            selection_msg = await ctx.author.send(embed=embed)

            # Store the selection message for later reference
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

    @commands.command(name='next')
    async def next_question(self, ctx):
        """Get the next interview question"""
        print(f"Next command received from {ctx.author.name}")  # Debug print


        # Check if this is in DM
        if not isinstance(ctx.channel, discord.DMChannel):
            await ctx.send("Please use this command in our DM chat!")
            return

        if ctx.author.id not in self.active_sessions:
            print(f"No active session for {ctx.author.name}")  # Debug print
            await ctx.send("You don't have an active interview session! Use `!interview` to start one.")
            return

        session = self.active_sessions[ctx.author.id]
        print(f"Found session for {ctx.author.name}, type: {session.interview_type}")  # Debug print

        question = self.question_bank.get_random_question(session.interview_type)

        if question:
            print(f"Sending question: {question.question}")  # Debug print

            # Store the current question
            self.current_questions[ctx.author.id] = question

            embed = discord.Embed(
                title=f"Question #{session.current_question + 1}",
                description=question.question,
                color=discord.Color.blue()
            )

            if question.follow_up:
                embed.add_field(
                    name="Follow-up",
                    value=question.follow_up,
                    inline=False
                )

            await ctx.send(embed=embed)
            session.current_question += 1
        else:
            print(f"No questions found for type: {session.interview_type}")  # Debug print
            await ctx.send("No questions available for this interview type!")

    @commands.command(name='answer')
    async def submit_answer(self, ctx, *, answer: str):
        """Submit your answer for evaluation"""
        if not isinstance(ctx.channel, discord.DMChannel):
            await ctx.send("Please use this command in our DM chat!")
            return

        if ctx.author.id not in self.active_sessions:
            await ctx.send("You don't have an active interview session!")
            return

        if ctx.author.id not in self.current_questions:
            await ctx.send("No current question to answer! Use !next to get a question first.")
            return

        # Send typing indicator while generating feedback
        async with ctx.typing():
            current_question = self.current_questions[ctx.author.id]
            feedback = await self.feedback_generator.generate_feedback(
                current_question.question,
                answer
            )

            if "error" in feedback:
                await ctx.send("Sorry, I couldn't generate feedback at this time.")
                return

            # Split feedback into multiple embeds
            # First embed: Bar Assessment and Strengths
            embed1 = discord.Embed(
                title="Answer Evaluation (1/2)",
                color=discord.Color.blue() if feedback["bar_assessment"] == "Meeting the Bar"
                else discord.Color.green() if feedback["bar_assessment"] == "Raising the Bar"
                else discord.Color.red()
            )

            embed1.add_field(
                name="Bar Assessment",
                value=feedback["bar_assessment"],
                inline=False
            )

            embed1.add_field(
                name="Key Strengths",
                value="\n".join(f"• {s}" for s in feedback["strengths"])[:1024],
                inline=False
            )

            # Second embed: Improvements and Follow-up
            embed2 = discord.Embed(
                title="Answer Evaluation (2/2)",
                color=embed1.color
            )

            # Split long better answer into chunks if needed
            better_answer = feedback["better_answer"]
            if len(better_answer) > 1024:
                chunks = [better_answer[i:i+1024] for i in range(0, len(better_answer), 1024)]
                for i, chunk in enumerate(chunks):
                    embed2.add_field(
                        name=f"Suggested Better Answer (Part {i+1})",
                        value=chunk,
                        inline=False
                    )
            else:
                embed2.add_field(
                    name="Suggested Better Answer",
                    value=better_answer,
                    inline=False
                )

            embed2.add_field(
                name="Areas for Improvement",
                value="\n".join(f"• {i}" for i in feedback["improvements"])[:1024],
                inline=False
            )

            embed2.add_field(
                name="Follow-up Questions",
                value="\n".join(f"• {q}" for q in feedback["follow_up"])[:1024],
                inline=False
            )

            # Send both embeds
            await ctx.send(embed=embed1)
            await ctx.send(embed=embed2)

            # Clear the current question
            del self.current_questions[ctx.author.id]

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction: discord.Reaction, user: discord.User):
        """Handle interview type selection"""
        # Ignore bot's own reactions
        if user.bot:
            return

        # Check if this is a pending selection message
        if user.id in self.pending_selection:
            selection_msg = self.pending_selection[user.id]
            if reaction.message.id == selection_msg.id:
                interview_type = None

                # Map reactions to interview types
                reaction_types = {
                    '💻': 'technical',
                    '👥': 'behavioral',
                    '📊': 'system_design'
                }

                if str(reaction.emoji) in reaction_types:
                    interview_type = reaction_types[str(reaction.emoji)]

                    # Create new interview session
                    self.active_sessions[user.id] = InterviewSession(
                        user_id=user.id,
                        interview_type=interview_type
                    )

                    # Clean up pending selection
                    del self.pending_selection[user.id]

                    # Send confirmation and first question
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
        # Here we'll add the first question in the next implementation
        await user.send("Ready to start? Type `!next` for your first question!")

    @commands.command(name='end')
    async def end_interview(self, ctx):
        """End the current interview session"""
        if ctx.author.id in self.active_sessions:
            del self.active_sessions[ctx.author.id]
            await ctx.send("Interview session ended. Thank you for practicing!")
        else:
            await ctx.send("You don't have an active interview session.")

    @commands.command(name='status')
    async def check_status(self, ctx):
        """Check your current interview session status"""
        if ctx.author.id in self.active_sessions:
            session = self.active_sessions[ctx.author.id]
            embed = discord.Embed(
                title="Interview Session Status",
                color=discord.Color.blue()
            )
            embed.add_field(name="Type", value=session.interview_type, inline=True)
            embed.add_field(name="Questions Asked", value=session.current_question, inline=True)
            embed.add_field(name="Status", value=session.status, inline=True)
            await ctx.send(embed=embed)
        else:
            await ctx.send("You don't have an active interview session.")

    @commands.command(name='debug')
    @commands.is_owner()  # Only bot owner can use this
    async def debug_sessions(self, ctx):
        """Debug command to check active sessions"""
        sessions_info = "\n".join([
            f"User ID: {user_id}, Type: {session.interview_type}, Questions: {session.current_question}"
            for user_id, session in self.active_sessions.items()
        ])
        await ctx.send(f"Active sessions:\n{sessions_info if sessions_info else 'No active sessions'}")

    @commands.command(name='questions')
    @commands.is_owner()  # Only bot owner can use this
    async def check_questions(self, ctx):
        """Debug command to check loaded questions"""
        questions_info = "\n".join([
            f"Type: {qtype}, Count: {len(questions)}"
            for qtype, questions in self.question_bank.questions.items()
        ])
        await ctx.send(f"Loaded questions:\n{questions_info if questions_info else 'No questions loaded'}")

async def setup(bot):
    await bot.add_cog(Interview(bot))