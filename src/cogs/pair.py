from discord.ext import commands
import discord
import asyncio
import logging
from datetime import datetime, timedelta
from src.utils.question_loader import QuestionLoader
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class PairInterview(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.pending_pairs = {}  # Store pending pair requests
        self.active_interviews = {}  # Store active interview sessions
        self.question_loader = QuestionLoader()

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
        """Handle reactions to pair requests and question type selection"""
        if user.bot:
            return

        message = reaction.message
        # Handle pair request reactions
        if message.id in self.pending_pairs:
            if user == self.pending_pairs[message.id]['initiator']:
                return

            if str(reaction.emoji) == "✋":
                try:
                    # Create interview channels
                    await self._create_interview_channels(message, self.pending_pairs[message.id]['initiator'], user)

                    # Clean up the pair request
                    await message.delete()
                    del self.pending_pairs[message.id]

                except Exception as e:
                    logger.error(f"Error creating interview channels: {str(e)}", exc_info=True)
                    await message.channel.send("❌ An error occurred while creating the interview channels.")
            return

        # Handle question type selection
        category_id = message.channel.category_id
        if category_id in self.active_interviews:
            interview = self.active_interviews[category_id]
            if 'pending_selection' in interview and message.id == interview['pending_selection']['message_id']:
                # Check if this is one of our interview type emojis
                if str(reaction.emoji) in self.question_loader.INTERVIEW_TYPE_EMOJIS:
                    interview_type = self.question_loader.INTERVIEW_TYPE_EMOJIS[str(reaction.emoji)]

                    # Send difficulty selection
                    difficulty_embed = await self.question_loader.create_difficulty_selection_embed()
                    diff_msg = await message.channel.send(embed=difficulty_embed)

                    # Update pending selection
                    interview['pending_selection'] = {
                        'message_id': diff_msg.id,
                        'type': 'difficulty',
                        'interview_type': interview_type
                    }

                    # Add difficulty reactions
                    for emoji in self.question_loader.DIFFICULTY_EMOJIS:
                        await diff_msg.add_reaction(emoji)

                    # Delete the type selection message
                    await message.delete()

                # Handle difficulty selection
                elif str(reaction.emoji) in self.question_loader.DIFFICULTY_EMOJIS:
                    difficulty = self.question_loader.DIFFICULTY_EMOJIS[str(reaction.emoji)]
                    interview_type = interview['pending_selection']['interview_type']

                    # Delete the difficulty selection message
                    await message.delete()
                    del interview['pending_selection']

                    # Send question with selected type and difficulty
                    await self._send_question(message.channel, interview, interview_type, difficulty)

    async def _create_interview_channels(self, message, user1, user2):
        """Create a category with voice and text channels for the interview"""
        guild = message.guild
        category_name = f"Interview-{user1.name}-{user2.name}"

        try:
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
                'created_at': datetime.now(),
                'current_question': None,  # Track current question
                'asked_questions': set()    # Track asked questions
            }

            # Move users to voice channel if they're in a voice channel
            for user in [user1, user2]:
                try:
                    member = guild.get_member(user.id)
                    if member and member.voice and member.voice.channel:
                        await member.move_to(voice_channel)
                except Exception as e:
                    logger.error(f"Failed to move {user.name} to voice channel: {e}")

            # Send welcome message with instructions and mentions
            welcome_embed = discord.Embed(
                title="🎯 Interview Session Started",
                description=(
                    f"Welcome {user1.mention} and {user2.mention}!\n\n"
                    f"**Channels:**\n"
                    f"🎙️ Voice: {voice_channel.mention}\n"
                    f"💬 Text: {text_channel.mention}\n\n"
                    f"**Interview Commands:**\n"
                    f"`!question` - Get an interview question (will show type options)\n"
                    f"`!question <type>` - Get a specific type question\n"
                    f"  Types: technical, behavioral, system_design\n"
                    f"`!next` - Get next question of same type\n"
                    f"`!stop` - End the interview (5 minute countdown)\n"
                    f"`!extend` - Add 30 more minutes\n\n"
                    f"Example: `!question technical`\n\n"
                    f"This session will automatically end after 2 hours if not stopped."
                ),
                color=discord.Color.green()
            )

            # Send initial messages
            initial_msg = await text_channel.send(f"{user1.mention} {user2.mention} Your interview session is ready!")
            await text_channel.send(embed=welcome_embed)

            # Send voice channel join prompt
            voice_prompt = await text_channel.send(
                f"🎤 Click here to join the voice channel: {voice_channel.mention}\n"
                f"Please join the voice channel to begin your interview!"
            )

            # Send question type examples
            question_types_embed = discord.Embed(
                title="📚 Question Types Available",
                description=(
                    "**Technical Interview:**\n"
                    "• Algorithms and Data Structures\n"
                    "• Coding Problems\n"
                    "• Database Design\n\n"
                    "**System Design:**\n"
                    "• Architecture Design\n"
                    "• Scalability\n"
                    "• System Components\n\n"
                    "**Behavioral:**\n"
                    "• Past Experiences\n"
                    "• Leadership\n"
                    "• Problem Solving\n\n"
                    "Use `!question <type> <level>` to start!"
                ),
                color=discord.Color.blue()
            )
            await text_channel.send(embed=question_types_embed)

            return category, voice_channel, text_channel

        except Exception as e:
            logger.error(f"Error in creating interview channels: {e}")
            # Clean up if something goes wrong
            try:
                if 'category' in locals():
                    await category.delete()
            except:
                pass
            raise

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

            # Explicitly cleanup everything
            await self._cleanup_interview(category_id)
            logger.info(f"Interview session {category_id} stopped and cleaned up")

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

    @commands.command(name="question")
    async def get_interview_question(self, ctx, question_type: str = None):
        """Get a random interview question based on type"""
        try:
            # Check if this is an interview text channel
            category_id = ctx.channel.category_id
            if not category_id or category_id not in self.active_interviews:
                return

            interview = self.active_interviews[category_id]
            if ctx.author not in [interview['user1'], interview['user2']]:
                return

            # If type not specified, show available options
            if not question_type:
                # Send type selection
                type_embed = await self.question_loader.create_type_selection_embed()
                type_msg = await ctx.send(embed=type_embed)

                # Store the message for reaction handling
                interview['pending_selection'] = {
                    'message_id': type_msg.id
                }

                # Add reaction options
                for emoji in self.question_loader.get_interview_type_emojis():
                    await type_msg.add_reaction(emoji)
                return

            # If type is specified directly
            await self._send_question(ctx, interview, question_type.lower(), "medium")  # Default to medium difficulty

        except Exception as e:
            logger.error(f"Error getting interview question: {str(e)}", exc_info=True)
            await ctx.send("❌ An error occurred while getting the question.")

    async def _send_question(self, ctx, interview, question_type: str, level: str = "medium"):
        """Send a question for discussion"""
        question = await self.question_loader.get_random_question(question_type, level)
        if not question:
            await ctx.send("❌ No questions found for the specified type.")
            return

        # Store current question
        interview['current_question'] = question
        interview['asked_questions'].add(question.get('id', ''))

        # Create and send embed
        embed = await self.question_loader.create_question_embed(question_type, level, question)
        await ctx.send(embed=embed)

        # Send a follow-up message with instructions
        await ctx.send("💭 Discuss your answer in the voice channel. Use `!next` when you're ready for another question.")

    @commands.command(name="next")
    async def next_question(self, ctx):
        """Get the next question of the same type and level"""
        try:
            category_id = ctx.channel.category_id
            if not category_id or category_id not in self.active_interviews:
                return

            interview = self.active_interviews[category_id]
            if ctx.author not in [interview['user1'], interview['user2']]:
                return

            current_question = interview.get('current_question')
            if not current_question:
                await ctx.send("❌ No active question. Use `!question <type> <level>` to start.")
                return

            question_type = current_question.get('type')
            level = current_question.get('difficulty')

            # Get and send next question
            await self._send_question(ctx, interview, question_type, level)

        except Exception as e:
            logger.error(f"Error getting next question: {str(e)}", exc_info=True)
            await ctx.send("❌ An error occurred while getting the next question.")

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        """Track when users join/leave interview voice channels"""
        try:
            # Check if this is related to an interview voice channel
            for interview in self.active_interviews.values():
                if member in [interview['user1'], interview['user2']]:
                    voice_channel = interview['voice_channel']
                    text_channel = interview['text_channel']

                    # If user joined the interview voice channel
                    if after.channel and after.channel.id == voice_channel.id:
                        await text_channel.send(f"✅ {member.mention} joined the voice channel!")

                    # If user left the interview voice channel
                    elif before.channel and before.channel.id == voice_channel.id:
                        await text_channel.send(f"ℹ️ {member.mention} left the voice channel!")

                    break
        except Exception as e:
            logger.error(f"Error in voice state update handler: {e}")

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
            # Delete text channel first
            try:
                await interview['text_channel'].delete()
            except discord.NotFound:
                pass
            except Exception as e:
                logger.error(f"Error deleting text channel: {e}")

            # Delete voice channel
            try:
                await interview['voice_channel'].delete()
            except discord.NotFound:
                pass
            except Exception as e:
                logger.error(f"Error deleting voice channel: {e}")

            # Finally delete the category
            try:
                await interview['category'].delete()
            except discord.NotFound:
                pass
            except Exception as e:
                logger.error(f"Error deleting category: {e}")

            logger.info(f"Successfully cleaned up interview session {category_id}")
        except Exception as e:
            logger.error(f"Error in cleanup: {str(e)}")
        finally:
            # Always remove from active interviews
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
                        logger.info(f"Cleaning up old interview session {category_id}")
                        await self._cleanup_interview(category_id)

            except Exception as e:
                logger.error(f"Error in cleanup task: {str(e)}")

            await asyncio.sleep(300)  # Check every 5 minutes

async def setup(bot):
    cog = PairInterview(bot)
    await bot.add_cog(cog)
    bot.loop.create_task(cog.cleanup_old_sessions())