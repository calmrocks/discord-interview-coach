import logging
from discord.ext import commands
from discord import Embed, Status
from datetime import datetime, timedelta
import asyncio
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

    async def execute(self):
        """Send daily check-in to online subscribed users"""
        current_date = datetime.now().date()
        current_time = datetime.now()

        logger.info(f"Starting daily check-in execution for {len(self.test_user_ids)} users")

        for user_id in self.test_user_ids:
            try:
                user_id = str(user_id)
                logger.info(f"Processing user_id: {user_id}")

                user = self.bot.get_user(int(user_id))
                if not user:
                    logger.warning(f"User with ID {user_id} not found")
                    continue

                member = self.find_member(user_id)
                if not member or member.status == Status.offline:
                    logger.info(f"User {user.name} (ID: {user_id}) is offline or not found in any shared guild")
                    continue

                user_profile = await self.data_provider.get_user_profile(user_id)
                logger.debug(f"User profile for {user_id}: {user_profile}")

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

                try:
                    reaction, _ = await self.bot.wait_for(
                        'reaction_add',
                        timeout=300,
                        check=lambda r, u: u.id == int(user_id) and str(r.emoji)[0] in "123456"
                    )

                    # Get fresh user profile before modifications
                    user_profile = await self.data_provider.get_user_profile(user_id)

                    # Update coins
                    user_profile['total_coins'] += 50
                    await self.data_provider.save_user_profile(user_profile)

                    # Update streak
                    streak = await self.update_user_streak(user_id)

                    # Update last check-in date
                    user_profile = await self.data_provider.get_user_profile(user_id)
                    user_profile['last_check_in_date'] = current_date.isoformat()
                    await self.data_provider.save_user_profile(user_profile)

                    logger.info(f"Updated streak for user {user_id}: {streak}")
                    await self.send_streak_message(user, user_id, streak, "Daily Check-in")

                    self.sent_messages[user_id] = current_time
                    logger.info(f"User {user.name} (ID: {user_id}) responded to check-in")

                except asyncio.TimeoutError:
                    await user.send("You didn't respond to the check-in. No worries, we'll check in with you later!")
                    logger.info(f"User {user.name} (ID: {user_id}) did not respond to check-in")

            except Exception as e:
                logger.error(f"Error processing user {user_id}: {str(e)}", exc_info=True)
                continue

        logger.info("Completed daily check-in execution")

    def find_member(self, user_id):
        for guild in self.bot.guilds:
            member = guild.get_member(int(user_id))
            if member:
                return member
        return None

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
        user_id = str(user_id)
        user_profile = await self.data_provider.get_user_profile(user_id)
        user_profile['total_coins'] += points
        logger.info(f"Added {points} points to user {user_id}. New total: {user_profile['total_coins']}")
        await self.data_provider.save_user_profile(user_profile)
        return user_profile['total_coins']

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
        logger.info(f"Updated streak for user {user_id}: {user_profile['current_streak']}")

        return user_profile['current_streak']['count']

    async def generate_streak_message(self, user_id: str, streak: int):
        user_id = str(user_id)
        user_profile = await self.data_provider.get_user_profile(user_id)
        level_config = await self.data_provider.get_level_config()

        logger.debug(f"User profile for streak message: {user_profile}")
        logger.debug(f"Level config: {level_config}")

        current_level = next(level for level in level_config['levels'] if level['coins_required'] <= user_profile['total_coins'])
        next_level = next((level for level in level_config['levels'] if level['coins_required'] > user_profile['total_coins']), None)

        daily_reward = current_level['daily_reward']
        next_reward = next_level['daily_reward'] if next_level else daily_reward

        total_levels = len(level_config['levels'])

        if next_level:
            progress = user_profile['total_coins'] - current_level['coins_required']
            total_for_next_level = next_level['coins_required'] - current_level['coins_required']
            progress_percentage = min(progress / total_for_next_level, 1)
            filled_squares = int(progress_percentage * 6)
            progress_bar = f"{'🟩' * filled_squares}{'🟥' * (6 - filled_squares)}"
        else:
            progress_bar = "🟩🟩🟩🟩🟩🟩"  # Max level reached

        logger.debug(f"Progress bar calculation: progress={progress}, total_for_next_level={total_for_next_level}, percentage={progress_percentage}, filled_squares={filled_squares}")

        message = f"""
🔥 Current Streak: {streak} day{'s' if streak != 1 else ''}
💰 Total Coins: {user_profile['total_coins']}
🏆 Current Level: {current_level['level']}/{total_levels} ({current_level['title']})
🎁 Daily Reward: {daily_reward} 🪙
📊 Progress to Next Level:
{progress_bar}
🚀 Next Level Reward: {next_reward} 🪙 daily
"""
        if streak % 7 == 0:  # Upgrade every week
            message += f"""
🎉 You upgraded the daily reward! 
New daily reward: {daily_reward} 🪙
"""
        logger.debug(f"Generated streak message for user {user_id}: {message}")
        return message

    async def send_streak_message(self, user, user_id: str, streak: int, context: str):
        streak_message = await self.generate_streak_message(user_id, streak)
        embed = Embed(title=f"Your Streak Information ({context})", description=streak_message, color=0x00ff00)
        await user.send(embed=embed)
        logger.info(f"Sent streak message to user {user_id} for {context}")

    @commands.command(name="streak")
    async def show_streak(self, ctx):
        """Show the current streak and level information for the user."""
        user_id = str(ctx.author.id)
        user_profile = await self.data_provider.get_user_profile(user_id)
        streak = user_profile['current_streak']['count']
        logger.info(f"User {user_id} requested streak information. user_profile: {user_profile}")
        logger.info(f"User {user_id} requested streak information. Current streak: {streak}")
        await self.send_streak_message(ctx.author, user_id, streak, "Command")

async def setup(bot):
    await bot.add_cog(RandomQuestions(bot))