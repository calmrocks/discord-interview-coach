from discord.ext import commands, tasks
from datetime import datetime, time
import logging
import pytz
import discord

logger = logging.getLogger(__name__)

class BaseScheduledTask:
    def __init__(self, bot):
        self.bot = bot
        self.timezone = pytz.timezone('UTC')
        self._last_run = None
        self.task_stats = {
            'runs': 0,
            'errors': 0,
            'last_error': None,
            'last_success': None
        }

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
        """Override this method to define when the task should run"""
        raise NotImplementedError

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