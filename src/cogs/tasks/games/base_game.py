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
        overwrites = {
            self.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            self.guild.me: discord.PermissionOverwrite(read_messages=True)
        }

        # Add permissions for players
        for player in self.players:
            overwrites[player] = discord.PermissionOverwrite(read_messages=True)

        channel_name = f"{self.name}-{datetime.now().strftime('%Y%m%d-%H%M')}"
        logger.info(f"Creating game channel: {channel_name}")

        try:
            self.channel = await self.guild.create_text_channel(
                channel_name,
                overwrites=overwrites
            )
            logger.info(f"Successfully created game channel: {self.channel.name}")
            return self.channel
        except Exception as e:
            logger.error(f"Error creating game channel: {e}")
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

class GameSelectView(discord.ui.View):
    def __init__(self, cog):
        super().__init__()
        self.cog = cog
        self.add_game_buttons()

    def add_game_buttons(self):
        for game_id, game_class in AVAILABLE_GAMES.items():
            # Create a temporary instance to get the name
            temp_game = game_class(self.bot, [], self.cog.bot.guilds[0])
            button_label = str(temp_game.name)  # Convert to string

            button = discord.ui.Button(
                label=button_label,  # Use the string value
                custom_id=f"game_{game_id}",
                style=discord.ButtonStyle.primary
            )
            button.callback = self.create_callback(game_class)
            self.add_item(button)

    def create_callback(self, game_class):
        async def callback(interaction: discord.Interaction):
            message_id = interaction.message.id
            invite = self.cog.active_invites.get(message_id)

            if not invite:
                await interaction.response.send_message(
                    "This game invite has expired.",
                    ephemeral=True
                )
                return

            invite['players'].add(interaction.user)
            await interaction.response.send_message(
                f"You've joined the game! ({len(invite['players'])}/3 players)",
                ephemeral=True
            )

            if len(invite['players']) >= 3:
                await self.cog.handle_game_start(message_id, game_class)

        return callback