from datetime import datetime, timedelta
import discord
from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)

class BaseGame(ABC):
    def __init__(self, bot, players, guild):
        self.bot = bot
        self.players = players
        self.guild = guild
        self.channel = None
        self.start_time = None
        self.is_active = False
        self.cleanup_timeout = 300  # 5 minutes default

    @property
    @abstractmethod
    def name(self) -> str:
        """Game name"""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Game description"""
        pass

    @property
    @abstractmethod
    def min_players(self) -> int:
        """Minimum number of players"""
        pass

    async def setup_channel(self):
        """Create and set up game channel"""
        logger.info("=== Setting up game channel ===")
        logger.info(f"Creating channel for game: {self.name}")
        logger.info(f"Number of players: {len(self.players)}")

        overwrites = {
            self.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            self.guild.me: discord.PermissionOverwrite(read_messages=True)
        }

        # Add permissions for players
        for player in self.players:
            logger.info(f"Adding permissions for player: {player.name}")
            overwrites[player] = discord.PermissionOverwrite(read_messages=True)

        channel_name = f"{self.name}-{datetime.now().strftime('%Y%m%d-%H%M')}"
        logger.info(f"Creating channel with name: {channel_name}")

        try:
            self.channel = await self.guild.create_text_channel(
                channel_name,
                overwrites=overwrites
            )
            logger.info(f"Successfully created channel: {self.channel.name} ({self.channel.id})")
            return self.channel
        except Exception as e:
            logger.error(f"Error creating game channel: {e}", exc_info=True)
            raise

    @abstractmethod
    async def start_game(self):
        """Start the game"""
        self.start_time = datetime.now()
        self.is_active = True

    @abstractmethod
    async def end_game(self):
        """End the game"""
        self.is_active = False
        await self.schedule_cleanup()

    async def schedule_cleanup(self):
        """Schedule channel cleanup"""
        logger.info(f"Scheduling cleanup for channel {self.channel.name} in {self.cleanup_timeout} seconds")
        await discord.utils.sleep_until(
            datetime.now() + timedelta(seconds=self.cleanup_timeout)
        )
        if self.channel:
            try:
                await self.channel.delete()
                logger.info(f"Successfully deleted channel {self.channel.name}")
            except Exception as e:
                logger.error(f"Error deleting channel: {e}")

