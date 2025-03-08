import discord
from discord.ext import commands
from datetime import datetime, timedelta
import asyncio
from ..utils.embed_builder import EmbedBuilder

class PairInterview(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.embed_builder = EmbedBuilder()
        self.active_requests = {}  # Store active pair interview requests
        self.active_pairs = {}  # Store active interview pairs

    @commands.command(name='pair')
    async def pair_interview(self, ctx):
        """
        Start a paired mock interview session.
        Usage: !pair
        Find a partner for a mock interview practice session.
        """
        if ctx.author.id in self.active_requests:
            await ctx.send("You already have an active pair interview request!")
            return

        # Create interview type selection
        embed = self.embed_builder.create_interview_type_selection()
        selection_msg = await ctx.send(
            f"{ctx.author.mention} Please select the type of interview you want to practice:",
            embed=embed
        )

        # Add reaction options
        reactions = ['💻', '👥', '📊']  # Technical, Behavioral, System Design
        for reaction in reactions:
            await selection_msg.add_reaction(reaction)

        try:
            # Wait for user's interview type selection
            reaction, user = await self.bot.wait_for(
                'reaction_add',
                timeout=30.0,
                check=lambda r, u: u == ctx.author and str(r.emoji) in reactions
            )

            interview_type = {
                '💻': 'technical',
                '👥': 'behavioral',
                '📊': 'system_design'
            }[str(reaction.emoji)]

            # Create level selection
            level_embed = discord.Embed(
                title="Select Experience Level",
                description="🟢 Entry Level\n🟡 Mid Level\n🔴 Senior Level",
                color=discord.Color.blue()
            )
            level_msg = await ctx.send(
                f"{ctx.author.mention} Please select your experience level:",
                embed=level_embed
            )

            # Add reaction options for level
            level_reactions = ['🟢', '🟡', '🔴']
            for reaction in level_reactions:
                await level_msg.add_reaction(reaction)

            # Wait for user's level selection
            reaction, user = await self.bot.wait_for(
                'reaction_add',
                timeout=30.0,
                check=lambda r, u: u == ctx.author and str(r.emoji) in level_reactions
            )

            level = {
                '🟢': 'entry',
                '🟡': 'mid',
                '🔴': 'senior'
            }[str(reaction.emoji)]

            # Create and send pair request
            await self.create_pair_request(ctx, interview_type, level)

        except asyncio.TimeoutError:
            await ctx.send(f"{ctx.author.mention} Interview setup timed out. Please try again!")
        finally:
            try:
                await selection_msg.delete()
                await level_msg.delete()
            except:
                pass

    async def create_pair_request(self, ctx, interview_type: str, level: str):
        """Create and send a pair interview request"""
        expiration_time = datetime.utcnow() + timedelta(minutes=30)

        embed = discord.Embed(
            title="Mock Interview Partner Needed! 🤝",
            description=(
                f"**Type:** {interview_type.title()} Interview\n"
                f"**Level:** {level.title()} Level\n"
                f"**Requester:** {ctx.author.name}\n\n"
                "React with ✋ to volunteer as the interviewer!\n\n"
                f"This request will expire in 30 minutes ({expiration_time.strftime('%H:%M')} UTC)"
            ),
            color=discord.Color.green()
        )
        embed.add_field(
            name="How it works",
            value=(
                "1. Volunteer by reacting with ✋\n"
                "2. Both participants will be paired in a private channel\n"
                "3. Bot will provide interview questions and guidelines\n"
                "4. Take turns interviewing each other"
            )
        )

        request_msg = await ctx.send(embed=embed)
        await request_msg.add_reaction("✋")

        # Store the request details
        self.active_requests[ctx.author.id] = {
            "message": request_msg,
            "type": interview_type,
            "level": level,
            "channel": ctx.channel,
            "expiration": expiration_time
        }

        # Start expiration timer
        self.bot.loop.create_task(self.expire_request(ctx.author.id, request_msg, expiration_time))

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction: discord.Reaction, user: discord.User):
        """Handle volunteer reactions for pair interviews"""
        if user.bot or str(reaction.emoji) != "✋":
            return

        # Find the corresponding request
        requester_id = None
        for rid, request in self.active_requests.items():
            if request["message"].id == reaction.message.id:
                requester_id = rid
                break

        if not requester_id or user.id == requester_id:
            return

        request_data = self.active_requests[requester_id]

        # Create private channel for the pair
        try:
            # Create private channel
            overwrites = {
                reaction.message.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                reaction.message.guild.me: discord.PermissionOverwrite(read_messages=True),
                reaction.message.guild.get_member(requester_id): discord.PermissionOverwrite(read_messages=True),
                user: discord.PermissionOverwrite(read_messages=True)
            }

            channel_name = f"mock-interview-{requester_id}-{user.id}"
            private_channel = await reaction.message.guild.create_text_channel(
                channel_name,
                overwrites=overwrites,
                category=reaction.message.channel.category
            )

            # Send initial instructions
            await self.send_interview_instructions(
                private_channel,
                request_data["type"],
                request_data["level"],
                reaction.message.guild.get_member(requester_id),
                user
            )

            # Clean up the request
            await request_data["message"].delete()
            del self.active_requests[requester_id]

            # Store the active pair
            self.active_pairs[private_channel.id] = {
                "requester": requester_id,
                "volunteer": user.id,
                "type": request_data["type"],
                "level": request_data["level"],
                "start_time": datetime.utcnow()
            }

        except Exception as e:
            await request_data["channel"].send(
                f"Error creating interview channel: {str(e)}\n"
                "Please try again or contact an administrator."
            )

    async def send_interview_instructions(self, channel, interview_type: str, level: str, requester: discord.Member, volunteer: discord.Member):
        """Send instructions and initial questions to the private channel"""
        welcome_embed = discord.Embed(
            title="Mock Interview Session Started! 🎯",
            description=(
                f"Welcome to your paired mock interview session!\n\n"
                f"**Type:** {interview_type.title()}\n"
                f"**Level:** {level.title()}\n"
                f"**Participants:**\n"
                f"• {requester.mention}\n"
                f"• {volunteer.mention}\n\n"
                "Please decide who will be the interviewer first."
            ),
            color=discord.Color.blue()
        )

        # Add commands section
        welcome_embed.add_field(
            name="Available Commands",
            value=(
                "`!next` - Get the next interview question\n"
                "`!switch` - Switch interviewer/interviewee roles\n"
                "`!end` - End the interview session\n"
                "`!feedback` - Provide feedback to your partner"
            ),
            inline=False
        )

        # Add guidelines
        welcome_embed.add_field(
            name="Guidelines",
            value=(
                "1. Be respectful and professional\n"
                "2. Provide constructive feedback\n"
                "3. Stay in character (interviewer/interviewee)\n"
                "4. Take notes for feedback\n"
                "5. Each person should practice both roles"
            ),
            inline=False
        )

        await channel.send(embed=welcome_embed)

        # Send first question
        question = self.get_practice_question(interview_type, level)
        question_embed = discord.Embed(
            title="First Interview Question",
            description=question,
            color=discord.Color.green()
        )
        await channel.send(embed=question_embed)

    async def expire_request(self, user_id: int, message: discord.Message, expiration_time: datetime):
        """Handle request expiration"""
        await discord.utils.sleep_until(expiration_time)

        if user_id in self.active_requests:
            try:
                await message.delete()
            except:
                pass
            del self.active_requests[user_id]

    @commands.command(name='next')
    async def next_question(self, ctx):
        """Get the next interview question"""
        if ctx.channel.id not in self.active_pairs:
            return

        pair_data = self.active_pairs[ctx.channel.id]
        question = self.get_practice_question(pair_data["type"], pair_data["level"])

        embed = discord.Embed(
            title="Next Interview Question",
            description=question,
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

    @commands.command(name='switch')
    async def switch_roles(self, ctx):
        """Switch interviewer/interviewee roles"""
        if ctx.channel.id not in self.active_pairs:
            return

        embed = discord.Embed(
            title="Switching Roles! 🔄",
            description=(
                "Time to switch roles!\n\n"
                "Previous interviewer is now the interviewee.\n"
                "Previous interviewee is now the interviewer.\n\n"
                "Use `!next` to get a new question for this round."
            ),
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed)

    @commands.command(name='end')
    async def end_session(self, ctx):
        """End the interview session"""
        if ctx.channel.id not in self.active_pairs:
            return

        embed = discord.Embed(
            title="Interview Session Ended",
            description=(
                "This mock interview session has ended.\n"
                "Please use `!feedback` to provide feedback to your partner.\n"
                "The channel will be deleted in 5 minutes after feedback is shared."
            ),
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)

        # Schedule channel deletion
        self.bot.loop.create_task(self.delete_interview_channel(ctx.channel, 300))  # 300 seconds = 5 minutes
        del self.active_pairs[ctx.channel.id]

    async def delete_interview_channel(self, channel: discord.TextChannel, delay: int):
        """Delete the interview channel after a delay"""
        await asyncio.sleep(delay)
        try:
            await channel.delete()
        except:
            pass

    def get_practice_question(self, interview_type: str, level: str) -> str:
        """Get a practice question from the question provider"""
        # You can reuse your existing question provider here
        return "Sample question for now - integrate with your question provider"

async def setup(bot):
    await bot.add_cog(PairInterview(bot))