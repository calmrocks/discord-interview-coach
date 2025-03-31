from discord.ext import commands
import discord
import asyncio
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class PairInterview(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.pending_pairs = {}  # Store pending pair requests
        self.active_interviews = {}  # Store active interview sessions

    @commands.command(name="pair")
    async def pair_interview(self, ctx):
        """Start a pair interview request"""
        try:
            # Check if user already has a pending request or active interview
            if self._is_user_busy(ctx.author.id):
                await ctx.send("❌ You already have a pending or active interview session!")
                return

            embed = discord.Embed(
                title="🤝 Pair Interview Request",
                description=f"{ctx.author.mention} is looking for a pair interview partner!\n\n"
                            f"React with ✋ to join this interview.\n"
                            f"This request will expire in 5 minutes.",
                color=discord.Color.blue()
            )

            message = await ctx.send(embed=embed)
            await message.add_reaction("✋")

            # Store the pair request
            self.pending_pairs[message.id] = {
                'initiator': ctx.author,
                'message': message,
                'created_at': datetime.now()
            }

            # Wait for 5 minutes then clean up if no one joined
            await asyncio.sleep(300)
            if message.id in self.pending_pairs:
                await message.delete()
                del self.pending_pairs[message.id]
                try:
                    await ctx.send(f"⏰ Pair interview request from {ctx.author.mention} has expired.")
                except:
                    pass

        except Exception as e:
            logger.error(f"Error creating pair request: {str(e)}", exc_info=True)
            await ctx.send("❌ An error occurred while creating the pair request.")

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        """Handle reactions to pair requests"""
        if user.bot:
            return

        message = reaction.message
        if message.id not in self.pending_pairs:
            return

        pair_info = self.pending_pairs[message.id]
        if user == pair_info['initiator']:
            return

        if str(reaction.emoji) == "✋":
            try:
                # Create interview category and channels
                await self._create_interview_channels(message, pair_info['initiator'], user)

                # Clean up the pair request
                await message.delete()
                del self.pending_pairs[message.id]

            except Exception as e:
                logger.error(f"Error creating interview channels: {str(e)}", exc_info=True)
                await message.channel.send("❌ An error occurred while creating the interview channels.")

    async def _create_interview_channels(self, message, user1, user2):
        """Create a category with voice and text channels for the interview"""
        guild = message.guild
        category_name = f"Interview-{user1.name}-{user2.name}"

        # Set up permissions for the category
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            user1: discord.PermissionOverwrite(view_channel=True, connect=True, speak=True),
            user2: discord.PermissionOverwrite(view_channel=True, connect=True, speak=True),
            guild.me: discord.PermissionOverwrite(view_channel=True, manage_channels=True)
        }

        # Create category
        category = await guild.create_category(category_name, overwrites=overwrites)

        # Create voice channel
        voice_channel = await category.create_voice_channel(
            "🎙️interview-voice",
            user_limit=2
        )

        # Create text channel
        text_channel = await category.create_text_channel("📝interview-chat")

        # Store interview session info
        self.active_interviews[category.id] = {
            'category': category,
            'voice_channel': voice_channel,
            'text_channel': text_channel,
            'user1': user1,
            'user2': user2,
            'created_at': datetime.now()
        }

        # Send welcome message with instructions
        welcome_embed = discord.Embed(
            title="🎯 Interview Session Started",
            description=(
                f"Welcome {user1.mention} and {user2.mention}!\n\n"
                f"**Voice Channel:** {voice_channel.mention}\n"
                f"**Text Channel:** {text_channel.mention}\n\n"
                f"**Commands:**\n"
                f"`!stop` - End the interview (5 minute countdown)\n"
                f"`!extend` - Add 30 more minutes\n\n"
                f"This session will automatically end after 2 hours if not stopped."
            ),
            color=discord.Color.green()
        )
        await text_channel.send(embed=welcome_embed)

    @commands.command(name="stop")
    async def stop_interview(self, ctx):
        """Stop an active interview"""
        try:
            # Check if this is an interview text channel
            category_id = ctx.channel.category_id
            if not category_id or category_id not in self.active_interviews:
                return

            interview = self.active_interviews[category_id]
            if ctx.author not in [interview['user1'], interview['user2']]:
                return

            embed = discord.Embed(
                title="🛑 Interview Ending",
                description="This interview session will end in 5 minutes.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)

            # Wait 5 minutes
            await asyncio.sleep(300)

            # Delete the category and all channels
            await self._cleanup_interview(category_id)

        except Exception as e:
            logger.error(f"Error stopping interview: {str(e)}", exc_info=True)
            await ctx.send("❌ An error occurred while stopping the interview.")

    @commands.command(name="extend")
    async def extend_interview(self, ctx):
        """Extend the interview time by 30 minutes"""
        try:
            category_id = ctx.channel.category_id
            if not category_id or category_id not in self.active_interviews:
                return

            interview = self.active_interviews[category_id]
            if ctx.author not in [interview['user1'], interview['user2']]:
                return

            interview['created_at'] = datetime.now()  # Reset the timer
            await ctx.send("✅ Interview time extended by 30 minutes!")

        except Exception as e:
            logger.error(f"Error extending interview: {str(e)}", exc_info=True)
            await ctx.send("❌ An error occurred while extending the interview.")

    def _is_user_busy(self, user_id):
        """Check if user has pending or active interviews"""
        # Check pending requests
        for pair_info in self.pending_pairs.values():
            if user_id in [pair_info['initiator'].id]:
                return True

        # Check active interviews
        for interview in self.active_interviews.values():
            if user_id in [interview['user1'].id, interview['user2'].id]:
                return True

        return False

    async def _cleanup_interview(self, category_id):
        """Clean up an interview session"""
        if category_id not in self.active_interviews:
            return

        interview = self.active_interviews[category_id]
        try:
            await interview['category'].delete()
        except:
            pass

        del self.active_interviews[category_id]

    async def cleanup_old_sessions(self):
        """Cleanup old sessions periodically"""
        while True:
            try:
                current_time = datetime.now()

                # Clean up old pending requests
                for message_id, pair_info in list(self.pending_pairs.items()):
                    if (current_time - pair_info['created_at']) > timedelta(minutes=5):
                        try:
                            await pair_info['message'].delete()
                        except:
                            pass
                        del self.pending_pairs[message_id]

                # Clean up old interview sessions
                for category_id, interview in list(self.active_interviews.items()):
                    if (current_time - interview['created_at']) > timedelta(hours=2):
                        await self._cleanup_interview(category_id)

            except Exception as e:
                logger.error(f"Error in cleanup task: {str(e)}")

            await asyncio.sleep(300)  # Check every 5 minutes

async def setup(bot):
    cog = PairInterview(bot)
    await bot.add_cog(cog)
    bot.loop.create_task(cog.cleanup_old_sessions())