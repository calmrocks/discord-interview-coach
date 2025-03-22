from discord.ext import commands, tasks
import discord
import asyncio
from datetime import datetime, time
from ...utils.task_scheduler import BaseScheduledTask
from ...config.task_config import TASK_CONFIG
from .games.truth_dare import TruthDare
from .games.word_guess import WordGuess
import logging


logger = logging.getLogger(__name__)

AVAILABLE_GAMES = {
    "truth-or-dare": TruthDare,
    "word-guess": WordGuess
}

class GameSelectView(discord.ui.View):
    def __init__(self, cog):
        super().__init__()
        self.cog = cog
        self.add_game_buttons()

    def add_game_buttons(self):
        for game_id, game_class in AVAILABLE_GAMES.items():
            button = discord.ui.Button(
                label=game_class.GAME_NAME,  # Use class variable
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

            # Check if player already joined
            if interaction.user in invite['players']:
                await interaction.response.send_message(
                    "You've already joined this game!",
                    ephemeral=True
                )
                return

            # Add the player to the set of players
            invite['players'].add(interaction.user)

            # Get min_players from game class
            temp_game = game_class(self.cog.bot, [], interaction.guild)
            min_players = temp_game.min_players

            # Update the original message
            players_text = "\n".join([f"• {player.display_name}" for player in invite['players']])
            embed = interaction.message.embeds[0]
            embed.add_field(
                name=f"Players ({len(invite['players'])}/{min_players}):",
                value=players_text,
                inline=False
            )
            await invite['message'].edit(embed=embed)

            # Tell them they've joined
            await interaction.response.send_message(
                f"You've joined the game! ({len(invite['players'])}/{min_players} players)\n"
                f"Waiting for {min_players - len(invite['players'])} more players...",
                ephemeral=True
            )

            # If we have enough players, start the game
            if len(invite['players']) >= min_players:
                await self.cog.handle_game_start(message_id, game_class)

        return callback

class GameInvites(commands.Cog, BaseScheduledTask):
    def __init__(self, bot):
        commands.Cog.__init__(self)
        BaseScheduledTask.__init__(self, bot)
        self.task_loop = self.create_task_loop()
        self.task_loop.start()
        self.active_invites = {}
        self.active_games = {}
        self.game_channels = {}

    def cog_unload(self):
        self.task_loop.cancel()

    async def create_game_invite(self, channel, initiator=None):
        """Create a game invite that can be used by both scheduled and manual starts"""
        logger.info(f"Creating game invite in channel: {channel.name}")

        embed = discord.Embed(
            title="🎮 Let's Play a Game!",
            description=(
                "Choose a game to play!\n"
                "Invite expires in 60 seconds."
            ),
            color=discord.Color.blue()
        )

        # Create temporary instances to access properties
        for game_id, game_class in AVAILABLE_GAMES.items():
            logger.info(f"Processing game: {game_id}")
            try:
                # Create a temporary instance to access the properties
                temp_game = game_class(self.bot, [], channel.guild)
                # Get the values from the properties
                game_name = str(temp_game.name)
                game_desc = str(temp_game.description)
                min_players = temp_game.min_players

                logger.info(f"Adding game to embed: {game_name}")
                embed.add_field(
                    name=f"{game_name} (Needs {min_players} players)",
                    value=game_desc,
                    inline=False
                )
            except Exception as e:
                logger.error(f"Error processing game {game_id}: {e}")
                continue

        if initiator:
            embed.add_field(
                name="Players (1/?):",  # Remove hardcoded player count
                value=f"• {initiator.display_name}",
                inline=False
            )
            embed.set_footer(text=f"Started by {initiator.name}")
        else:
            embed.add_field(
                name="Players (0/?):",  # Remove hardcoded player count
                value="Waiting for players...",
                inline=False
            )
            embed.set_footer(text="Scheduled game invite")

        try:
            view = GameSelectView(self)
            message = await channel.send(embed=embed, view=view)

            self.active_invites[message.id] = {
                'message': message,
                'players': set(),
                'timeout': 60,
                'initiator': initiator
            }

            await self.schedule_invite_cleanup(message.id)
            return message

        except Exception as e:
            logger.error(f"Error sending game invite: {e}", exc_info=True)
            raise

    async def schedule_invite_cleanup(self, message_id):
        """Schedule cleanup of inactive invites"""
        await asyncio.sleep(60)  # Wait for 1 minute
        invite = self.active_invites.get(message_id)
        if invite:
            message = invite['message']
            for component in message.components:
                for button in component.children:
                    game_id = button.custom_id.replace('game_', '')
                    if game_id in AVAILABLE_GAMES:
                        game_class = AVAILABLE_GAMES[game_id]
                        temp_game = game_class(self.bot, [], message.guild)
                        min_players = temp_game.min_players
                        if len(invite['players']) < min_players:
                            await message.edit(content="Not enough players joined. Game cancelled.", view=None)
                            del self.active_invites[message_id]
                            return

    async def execute(self):
        """Send scheduled game invites"""
        logger.info("Executing scheduled game invites")

        # Get channels from config
        config = TASK_CONFIG.get('gameinvites', {})
        channel_ids = config.get('channel_ids', [])  # Changed from game_channels to channel_ids

        logger.info(f"Found {len(channel_ids)} configured channels for game invites")

        for channel_id in channel_ids:
            channel = self.bot.get_channel(channel_id)
            if channel:
                logger.info(f"Creating scheduled game invite in channel {channel.name} ({channel_id})")
                try:
                    await self.create_game_invite(channel)
                except Exception as e:
                    logger.error(f"Error creating game invite in channel {channel.name} ({channel_id}): {e}")
            else:
                logger.warning(f"Could not find channel with ID {channel_id}")

    @commands.command(name="startgame")
    async def start_game(self, ctx):
        """Start a new game manually"""
        await self.create_game_invite(ctx.channel, ctx.author)

    async def handle_game_start(self, message_id, game_class):
        """Handle game start when enough players join"""
        invite = self.active_invites.get(message_id)
        if not invite:
            return

        temp_game = game_class(self.bot, [], invite['message'].guild)
        min_players = temp_game.min_players

        if len(invite['players']) >= min_players:
            try:
                # Create and start the game
                game = game_class(self.bot, list(invite['players']), invite['message'].guild)
                channel = await game.setup_channel()
                self.active_games[channel.id] = game

                # Notify players
                player_mentions = " ".join(player.mention for player in invite['players'])
                await channel.send(
                    f"Game starting! Welcome {player_mentions}\n"
                    f"This channel will be deleted {game.cleanup_timeout} seconds after the game ends."
                )

                await game.start_game()

                # Clean up the invite
                await invite['message'].edit(
                    content=f"Game started in {channel.mention}!",
                    view=None
                )
                del self.active_invites[message_id]

            except Exception as e:
                logger.error(f"Error starting game: {e}")
                await invite['message'].edit(
                    content="An error occurred while starting the game.",
                    view=None
                )
                del self.active_invites[message_id]

async def setup(bot):
    await bot.add_cog(GameInvites(bot))