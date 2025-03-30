from discord.ext import commands
from discord import Embed
from discord import Status
from datetime import datetime, timedelta
import asyncio
import logging
from ...utils.task_scheduler import BaseScheduledTask
from ...config.task_config import TASK_CONFIG
from ...providers.data_provider import DataProvider

logger = logging.getLogger(__name__)

class RandomQuestions(commands.Cog, BaseScheduledTask):
    def __init__(self, bot):
        commands.Cog.__init__(self)
        BaseScheduledTask.__init__(self, bot)
        self.task_loop = self.create_task_loop()
        self.task_loop.start()
        self.data_provider = DataProvider()
        self.test_user_ids = TASK_CONFIG['randomquestions']['test_user_ids']
        self.allow_multiple_daily = TASK_CONFIG['randomquestions'].get('allow_multiple_daily', False)
        self.sent_messages = {}

    def cog_unload(self):
        self.task_loop.cancel()

    def get_task_config(self):
        return TASK_CONFIG['randomquestions']

    async def execute(self):
        """Send daily check-in to online subscribed users"""
        current_date = datetime.now().date()
        current_time = datetime.now()

        for user_id in self.test_user_ids:
            user = self.bot.get_user(int(user_id))
            if not user:
                logger.warning(f"User with ID {user_id} not found")
                continue

            # Check if user is a member of any guild the bot is in
            member = None
            for guild in self.bot.guilds:
                member = guild.get_member(int(user_id))
                if member:
                    break

            # If we couldn't find the member or they're offline, skip
            if not member or member.status == Status.offline:
                logger.info(f"User {user.name} (ID: {user_id}) is offline or not found in any shared guild")
                continue

            user_profile = await self.data_provider.get_user_profile(user_id)

            if not self.allow_multiple_daily and user_profile.get('last_check_in_date') == current_date.isoformat():
                logger.info(f"User {user.name} (ID: {user_id}) already received a check-in today")
                continue

            if self.allow_multiple_daily:
                last_sent = self.sent_messages.get(user_id)
                if last_sent and (current_time - last_sent) < timedelta(hours=1):
                    logger.info(f"Skipping user {user.name} (ID: {user_id}) due to recent message")
                    continue

            logger.info(f"Sending check-in to user {user.name} (ID: {user_id})")
            message = await self.ask_daily_question(user)

            def check(reaction, reactor):
                return reactor.id == int(user_id) and str(reaction.emoji)[0] in "123456"

            try:
                reaction, _ = await self.bot.wait_for('reaction_add', timeout=300, check=check)
                await self.add_points(user_id, 50)
                streak = await self.update_user_streak(user_id)
                streak_message = await self.generate_streak_message(user_id, streak)
                await user.send(streak_message)

                user_profile['last_check_in_date'] = current_date.isoformat()
                await self.data_provider.save_user_profile(user_profile)

                self.sent_messages[user_id] = current_time
                logger.info(f"User {user.name} (ID: {user_id}) responded to check-in")

            except asyncio.TimeoutError:
                await user.send("You didn't respond to the check-in. No worries, we'll check in with you later!")
                logger.info(f"User {user.name} (ID: {user_id}) did not respond to check-in")

    async def ask_daily_question(self, user):
        question = "What positive step did you take for your SDE career today? 🚀"
        options = [
            "👨‍💻 Practiced coding",
            "🏗️ Learned about system design",
            "✅ Completed work tasks efficiently",
            "⏰ Improved time management",
            "📚 Studied a new technology",
            "🤝 Collaborated on a project"
        ]

        message = await user.send(f"{question}\n\n" + "\n".join(f"{i+1}. {option}" for i, option in enumerate(options)))

        for i in range(len(options)):
            await message.add_reaction(f"{i+1}\N{COMBINING ENCLOSING KEYCAP}")

        return message

    async def add_points(self, user_id: str, points: int):
        user_profile = await self.data_provider.get_user_profile(user_id)
        user_profile['total_coins'] += points
        await self.data_provider.save_user_profile(user_profile)

    async def update_user_streak(self, user_id: str):
        user_profile = await self.data_provider.get_user_profile(user_id)

        current_date = datetime.now().date()
        last_activity_date = datetime.fromisoformat(user_profile['current_streak']['last_activity_date']).date()

        if current_date == last_activity_date + timedelta(days=1):
            user_profile['current_streak']['count'] += 1
        elif current_date > last_activity_date:
            user_profile['current_streak']['count'] = 1

        user_profile['current_streak']['last_activity_date'] = current_date.isoformat()

        await self.data_provider.save_user_profile(user_profile)

        return user_profile['current_streak']['count']

    async def generate_streak_message(self, user_id: str, streak: int):
        user_profile = await self.data_provider.get_user_profile(user_id)
        level_config = await self.data_provider.get_level_config()

        current_level = next(level for level in level_config['levels'] if level['coins_required'] <= user_profile['total_coins'])
        next_level = next((level for level in level_config['levels'] if level['coins_required'] > user_profile['total_coins']), None)

        daily_reward = current_level['daily_reward']
        next_reward = next_level['daily_reward'] if next_level else daily_reward

        progress = min(user_profile['total_coins'] - current_level['coins_required'], 6)
        progress_bar = f"{progress}{'🟩' * progress}{'🟥' * (6 - progress)}{next_level['coins_required'] - current_level['coins_required'] if next_level else ''}"

        message = f"""
🔥 Streak: {streak}
Current: {daily_reward} 🪙 daily
Next: {next_reward} 🪙 daily
{progress_bar}
You extended your streak! 
Current streak: {streak}
Reward: {daily_reward} 🪙
Type !streak for more information.
"""
        if streak % 7 == 0:  # Upgrade every week
            message += f"""
You upgraded the daily reward! 
Current streak: {streak}
Reward: {daily_reward - 20} -> {daily_reward} 🪙
"""

        return message

    @commands.command(name="streak")
    async def show_streak(self, ctx):
        """Show the current streak and level information for the user."""
        user_id = str(ctx.author.id)
        user_profile = await self.data_provider.get_user_profile(user_id)
        streak = user_profile['current_streak']['count']

        streak_message = await self.generate_streak_message(user_id, streak)

        # Create an embed for a nicer looking message
        embed = Embed(title="Your Streak Information", description=streak_message, color=0x00ff00)

        await ctx.send(embed=embed)

    async def generate_streak_message(self, user_id: str, streak: int):
        user_profile = await self.data_provider.get_user_profile(user_id)
        level_config = await self.data_provider.get_level_config()

        current_level = next(level for level in level_config['levels'] if level['coins_required'] <= user_profile['total_coins'])
        next_level = next((level for level in level_config['levels'] if level['coins_required'] > user_profile['total_coins']), None)

        daily_reward = current_level['daily_reward']
        next_reward = next_level['daily_reward'] if next_level else daily_reward

        progress = min(user_profile['total_coins'] - current_level['coins_required'], 6)
        total_levels = len(level_config['levels'])
        progress_bar = f"{progress}{'🟩' * progress}{'🟥' * (6 - progress)}{next_level['coins_required'] - current_level['coins_required'] if next_level else ''}"

        message = f"""
🔥 Current Streak: {streak} day{'s' if streak != 1 else ''}
💰 Total Coins: {user_profile['total_coins']}
🏆 Current Level: {current_level['level']}/{total_levels} ({current_level['title']})
🎁 Daily Reward: {daily_reward} 🪙
📊 Progress to Next Level:
{progress_bar}
🚀 Next Level Reward: {next_reward} 🪙 daily
"""
        return message

async def setup(bot):
    await bot.add_cog(RandomQuestions(bot))