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
        config = TASK_CONFIG.get(task_name, {})
        if not config.get('enabled', False):
            return False

        schedule = config.get('schedule', {})
        schedule_type = schedule.get('type')
        hours = schedule.get('hours', [])
        minute_window = schedule.get('minute_window', 60)
        interval = schedule.get('interval', 0)

        now = datetime.now(self.timezone)
        current_hour = now.hour
        current_minute = now.minute

        # Check if enough time has passed since last run (for interval-based tasks)
        if interval > 0:
            last_run = self.last_run.get(task_name)
            if last_run:
                time_since_last_run = (now - last_run).total_seconds() / 60
                if time_since_last_run < interval:
                    return False

        # Check if current time falls within the scheduled window
        if schedule_type == 'business_hours':
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
                return False

        else:
            return False

        # Check minute window
        if current_minute >= minute_window:
            return False

        # Update last run time
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