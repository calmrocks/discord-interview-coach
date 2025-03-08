import discord
from discord.ext import commands, tasks
import random
from datetime import datetime, time
import logging
from ..providers.question_provider import QuestionProvider
from ..config.bot_config import TEST_USER_IDS

logger = logging.getLogger(__name__)

class RandomQuestion(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.question_provider = QuestionProvider()
        self.test_user_ids = TEST_USER_IDS
        self.last_question_times = {}  # Track last question time for each user
        self.random_question_task.start()

    def cog_unload(self):
        self.random_question_task.cancel()

    @tasks.loop(minutes=30)  # Check every 30 minutes
    async def random_question_task(self):
        """Background task to send random questions"""
        logger.info("Checking for random question")
        now = datetime.now()

        # Only send between 9 AM and 5 PM
        if not (9 <= now.hour < 17):
            return

        # Only send on weekdays (Monday = 0, Sunday = 6)
        if now.weekday() >= 5:
            return

        for user_id in self.test_user_ids:
            try:
                # Check if enough time has passed for this user
                last_time = self.last_question_times.get(user_id)
                if last_time and (now - last_time).total_seconds() < 14400:  # 4 hours
                    continue

                # Get user
                user = self.bot.get_user(user_id)
                if not user:
                    logger.warning(f"Test user {user_id} not found")
                    continue

                # Check if user is online (if they're in a mutual server)
                member = discord.utils.find(lambda m: m.id == user_id, self.bot.get_all_members())
                if member and member.status == discord.Status.offline:
                    logger.info(f"Skipping offline user {user_id}")
                    continue

                # Randomly select question type and difficulty
                question_type = random.choice(['technical', 'behavioral'])
                difficulty = random.choice(['easy', 'medium', 'hard'])

                # Get random question
                question = self.question_provider.get_random_question(
                    question_type,
                    difficulty
                )

                # Create embed
                embed = discord.Embed(
                    title=f"Practice Question ({question_type.title()})",
                    description=question['question'],
                    color=discord.Color.blue()
                )
                embed.add_field(name="Difficulty", value=difficulty.title())

                # Send question
                await user.send("Here's a practice interview question!", embed=embed)
                self.last_question_times[user_id] = now
                logger.info(f"Sent question to test user {user_id}")

            except Exception as e:
                logger.error(f"Error sending random question to user {user_id}: {e}")

    @random_question_task.before_loop
    async def before_random_question_task(self):
        """Wait until bot is ready before starting the task"""
        await self.bot.wait_until_ready()

    @commands.command(name='testquestion')
    async def test_question(self, ctx):
        """Manually trigger a test question"""
        if ctx.author.id not in self.test_user_ids:
            return

        try:
            question_type = random.choice(['technical', 'behavioral'])
            difficulty = random.choice(['easy', 'medium', 'hard'])

            question = self.question_provider.get_random_question(
                question_type,
                difficulty
            )

            embed = discord.Embed(
                title=f"Practice Question ({question_type.title()})",
                description=question['question'],
                color=discord.Color.blue()
            )
            embed.add_field(name="Difficulty", value=difficulty.title())

            await ctx.author.send("Here's a practice interview question!", embed=embed)
            self.last_question_times[ctx.author.id] = datetime.now()
            logger.info(f"Sent test question to user {ctx.author.id}")

        except Exception as e:
            logger.error(f"Error sending test question: {e}")
            await ctx.send("Error sending test question.")

    @commands.command(name='listusers')
    @commands.is_owner()  # Only bot owner can use this command
    async def list_test_users(self, ctx):
        """List all test users and their last question times"""
        embed = discord.Embed(title="Test Users", color=discord.Color.blue())

        for user_id in self.test_user_ids:
            user = self.bot.get_user(user_id)
            last_time = self.last_question_times.get(user_id)

            user_info = f"Last question: {last_time.strftime('%Y-%m-%d %H:%M') if last_time else 'Never'}"
            if user:
                embed.add_field(
                    name=f"{user.name}#{user.discriminator}",
                    value=user_info,
                    inline=False
                )
            else:
                embed.add_field(
                    name=f"Unknown User ({user_id})",
                    value=user_info,
                    inline=False
                )

        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(RandomQuestion(bot))