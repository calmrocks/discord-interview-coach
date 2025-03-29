from discord.ext import commands, tasks
from datetime import datetime, time
import logging
import pytz
from zoneinfo import ZoneInfo
from tzlocal import get_localzone
import discord
from ..config.task_config import TASK_CONFIG

logger = logging.getLogger(__name__)

class BaseScheduledTask:
    def __init__(self, bot):
        self.bot = bot
        self.timezone = get_localzone()
        self._last_run = None
        self.task_stats = {
            'runs': 0,
            'errors': 0,
            'last_error': None,
            'last_success': None
        }
        self.last_run = {}
        self._register_status_command()

    def create_task_loop(self):
        """Create the task loop with configured interval"""
        task_name = self.__class__.__name__.lower()
        logger.info(f"[{task_name}] Loading task config")
        logger.info(f"[{task_name}] Available configs: {TASK_CONFIG.keys()}")

        config = TASK_CONFIG.get(task_name, {})
        logger.info(f"[{task_name}] Loaded config: {config}")

        loop_minutes = config.get('loop_minutes', 30)  # Default to 30 minutes if not specified
        logger.info(f"Creating task loop for {task_name} with {loop_minutes} minute interval")

        @tasks.loop(minutes=loop_minutes)
        async def task_loop():  # Remove 'self' parameter here
            logger.info(f"Task loop executing for {task_name}")
            await self.safe_execute()  # 'self' is available from closure

        @task_loop.before_loop
        async def before_task_loop():  # Remove 'self' parameter here
            logger.info(f"Waiting for bot to be ready before starting {task_name}")
            await self.bot.wait_until_ready()
            logger.info(f"Bot is ready, {task_name} task can start")

        return task_loop

    def _register_status_command(self):
        """Register status command with a unique name based on the subclass"""
        # Get the subclass name and convert to lowercase for command name
        command_name = f"status_{self.__class__.__name__.lower()}"

        @commands.command(name=command_name)
        @commands.is_owner()
        async def status(ctx):
            """Show task statistics"""
            embed = discord.Embed(
                title=f"Task Status: {self.__class__.__name__}",
                color=discord.Color.blue()
            )
            embed.add_field(name="Total Runs", value=self.task_stats['runs'])
            embed.add_field(name="Total Errors", value=self.task_stats['errors'])

            if self.task_stats['last_success']:
                embed.add_field(
                    name="Last Success",
                    value=self.task_stats['last_success'].strftime('%Y-%m-%d %H:%M:%S'),
                    inline=False
                )

            if self.task_stats['last_error']:
                time, error = self.task_stats['last_error']
                embed.add_field(
                    name="Last Error",
                    value=f"{time.strftime('%Y-%m-%d %H:%M:%S')}\n{error}",
                    inline=False
                )

            await ctx.send(embed=embed)

        # Add the command to the class
        setattr(self, command_name, status)

        # Add the command to the bot commands
        self.bot.add_command(status)

    def should_run(self) -> bool:
        """Common logic for determining if a task should run based on configuration"""
        task_name = self.__class__.__name__.lower()
        logger.info(f"Checking should_run for {task_name}")

        config = TASK_CONFIG.get(task_name, {})
        if not config.get('enabled', False):
            logger.info(f"[{task_name}] Task is not enabled in config")
            return False

        schedule = config.get('schedule', {})
        schedule_type = schedule.get('type')
        hours = schedule.get('hours', [])
        minute_window = schedule.get('minute_window', 60)
        interval = schedule.get('interval', 0)

        now = datetime.now(self.timezone)
        current_hour = now.hour
        current_minute = now.minute

        logger.info(f"""
        [{task_name}] Schedule check details:
        - Current time: {now}
        - Schedule type: {schedule_type}
        - Target hours: {hours}
        - Current hour: {current_hour}
        - Current minute: {current_minute}
        - Minute window: {minute_window}
        - Interval: {interval}
        """)

        # Check if enough time has passed since last run (for interval-based tasks)
        if interval > 0:
            last_run = self.last_run.get(task_name)
            if last_run:
                time_since_last_run = (now - last_run).total_seconds() / 60
                logger.info(f"[{task_name}] Time since last run: {time_since_last_run} minutes")
                if time_since_last_run < interval:
                    logger.info(f"[{task_name}] Not enough time passed since last run")
                    return False

        # Check if current time falls within the scheduled window
        if schedule_type == 'all_hours':
            # Always return True for 'all_hours', but still respect the interval
            pass
        elif schedule_type == 'business_hours':
            if len(hours) != 2:
                return False
            start_hour, end_hour = hours
            if not (start_hour <= current_hour < end_hour):
                return False
        elif schedule_type == 'daily':
            if len(hours) != 1:
                return False
            if current_hour != hours[0]:
                return False
        elif schedule_type == 'specific_hours':
            if current_hour not in hours:
                logger.info(f"[{task_name}] Current hour {current_hour} not in target hours {hours}")
                return False
        else:
            return False

        # Check minute window (skip for 'all_hours')
        if schedule_type != 'all_hours' and current_minute >= minute_window:
            logger.info(f"[{task_name}] Current minute {current_minute} outside window {minute_window}")
            return False

        # Update last run time
        logger.info(f"[{task_name}] All checks passed - task should run")
        self.last_run[task_name] = now
        return True

    async def execute(self):
        """Override this method to define what the task does"""
        raise NotImplementedError

    def is_business_hours(self) -> bool:
        """Check if current time is within business hours"""
        now = datetime.now(self.timezone)
        return 9 <= now.hour < 17 and now.weekday() < 5

    async def safe_execute(self):
        """Safely execute the task with error handling"""
        try:
            if self.should_run():
                await self.execute()
                self.task_stats['runs'] += 1
                self.task_stats['last_success'] = datetime.now(self.timezone)
        except Exception as e:
            self.task_stats['errors'] += 1
            self.task_stats['last_error'] = (datetime.now(self.timezone), str(e))
            logger.error(f"Error in {self.__class__.__name__}: {e}", exc_info=True)

    def create_status_embed(self) -> discord.Embed:
        """Create status embed for the task"""
        embed = discord.Embed(
            title=f"Task Status: {self.__class__.__name__}",
            color=discord.Color.blue()
        )
        embed.add_field(name="Total Runs", value=self.task_stats['runs'])
        embed.add_field(name="Total Errors", value=self.task_stats['errors'])

        if self.task_stats['last_success']:
            embed.add_field(
                name="Last Success",
                value=self.task_stats['last_success'].strftime('%Y-%m-%d %H:%M:%S'),
                inline=False
            )

        if self.task_stats['last_error']:
            time, error = self.task_stats['last_error']
            embed.add_field(
                name="Last Error",
                value=f"{time.strftime('%Y-%m-%d %H:%M:%S')}\n{error}",
                inline=False
            )

        return embed