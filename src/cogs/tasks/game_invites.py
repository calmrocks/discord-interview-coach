from discord.ext import commands, tasks
import discord
import asyncio
from datetime import datetime, time
from ...utils.task_scheduler import BaseScheduledTask
from ...config.task_config import TASK_CONFIG
from .games import AVAILABLE_GAMES
from .games.game_config import GAME_CONFIGS
import logging


logger = logging.getLogger(__name__)

class GameSelectView(discord.ui.View):
    def __init__(self, cog):
        super().__init__(timeout=60)
        self.cog = cog
        self.bot = cog.bot  # Add this line to get the bot instance
        logger.debug("Initializing GameSelectView")
        self.add_game_buttons()

    def add_game_buttons(self):
        logger.debug("Adding game buttons to view")
        for game_id, game_class in AVAILABLE_GAMES.items():
            logger.debug(f"Adding button for game: {game_id}")
            try:
                temp_game = game_class(self.bot, [], None)  # Now self.bot will be available
                button = discord.ui.Button(
                    label=temp_game.name,
                    custom_id=f"game_{game_id}",
                    style=discord.ButtonStyle.primary
                )
                button.callback = self.create_callback(game_class)
                self.add_item(button)
                logger.debug(f"Successfully added button for {game_id}")
            except Exception as e:
                logger.error(f"Error adding button for {game_id}: {e}", exc_info=True)

    def create_callback(self, game_class):
        async def callback(interaction: discord.Interaction):
            logger.info("=== Game Button Callback Started ===")
            logger.info(f"Game clicked: {game_class.__name__}")
            logger.info(f"User clicked: {interaction.user}")

            message_id = interaction.message.id
            logger.info(f"Message ID: {message_id}")

            invite = self.cog.active_invites.get(message_id)
            if not invite:
                logger.warning(f"No invite found for message ID: {message_id}")
                await interaction.response.send_message(
                    "This game invite has expired.",
                    ephemeral=True
                )
                return

            logger.info(f"Current players in invite: {len(invite['players'])}")
            logger.info(f"Players: {[p.name for p in invite['players']]}")

            temp_game = game_class(self.bot, [], interaction.guild)  # Using self.bot here
            logger.info(f"Game requirements - Min: {temp_game.min_players}, Max: {temp_game.max_players}")

            # Add player
            invite['players'].add(interaction.user)
            current_players = len(invite['players'])
            logger.info(f"After adding player - Total players: {current_players}")
            logger.info(f"Updated players list: {[p.name for p in invite['players']]}")

            await interaction.response.send_message(
                f"You've joined the game! ({current_players}/{temp_game.max_players} players)",
                ephemeral=True
            )
            logger.info("Sent join confirmation message")

            # Check if we have enough players
            logger.info(f"Checking if can start game: Current={current_players}, Required={temp_game.min_players}")
            if current_players >= temp_game.min_players:
                logger.info("=== Starting Game Process ===")
                try:
                    logger.info("Calling handle_game_start")
                    await self.cog.handle_game_start(message_id, game_class)
                    logger.info("handle_game_start completed")
                except Exception as e:
                    logger.error(f"Error in handle_game_start: {e}", exc_info=True)
            else:
                logger.info("Not enough players to start game yet")

            logger.info("=== Game Button Callback Completed ===")

        return callback

class GameInvites(commands.Cog, BaseScheduledTask):
    def __init__(self, bot):
        self.bot = bot
        self.active_invites = {}
        self.active_games = {}

    def cog_unload(self):
        self.task_loop.cancel()

    async def create_game_invite(self, channel, initiator=None):
        """Create a game invite"""
        logger.info(f"Creating game invite in channel: {channel.name}")

        try:
            embed = discord.Embed(
                title="🎮 Let's Play a Game!",
                description="Choose a game to play!\nInvite expires in 60 seconds.",
                color=discord.Color.blue()
            )

            # Process each game
            for game_id, game_class in AVAILABLE_GAMES.items():
                logger.info(f"Processing game: {game_id}")
                try:
                    temp_game = game_class(self.bot, [], channel.guild)
                    embed.add_field(
                        name=f"{temp_game.name} (Needs {temp_game.min_players} to {temp_game.max_players} players)",
                        value=temp_game.description,
                        inline=False
                    )
                except Exception as e:
                    logger.error(f"Error processing game {game_id}: {e}", exc_info=True)
                    continue

            view = GameSelectView(self)
            message = await channel.send(embed=embed, view=view)

            self.active_invites[message.id] = {
                'message': message,
                'players': set([initiator]) if initiator else set(),
                'channel': channel,
                'selected_game': None  # Add this to track selected game
            }

            await self.schedule_invite_cleanup(message.id)
            return message

        except Exception as e:
            logger.error(f"Error in create_game_invite: {e}", exc_info=True)
            await channel.send("Error creating game invite. Please try again.")
            raise

    async def schedule_invite_cleanup(self, message_id):
        """Schedule cleanup of inactive invites"""
        logger.debug(f"Starting cleanup schedule for message ID: {message_id}")
        await asyncio.sleep(60)

        logger.debug(f"Checking invite for message ID: {message_id}")
        invite = self.active_invites.get(message_id)
        if invite:
            message = invite['message']
            try:
                selected_game = invite.get('selected_game')
                if selected_game:
                    player_count = len(invite['players'])
                    temp_game = selected_game(self.bot, [], message.guild)

                    logger.info(f"Checking player count for {selected_game.__name__}: {player_count} players")

                    if player_count < temp_game.min_players:
                        logger.info(f"Not enough players for {selected_game.__name__}. Need at least {temp_game.min_players}, got {player_count}")
                        await message.edit(
                            content=f"Not enough players joined. Need at least {temp_game.min_players} players. Game cancelled.",
                            view=None
                        )
                    elif player_count > temp_game.max_players:
                        logger.info(f"Too many players for {selected_game.__name__}. Maximum is {temp_game.max_players}, got {player_count}")
                        await message.edit(
                            content=f"Too many players joined. Maximum is {temp_game.max_players} players. Game cancelled.",
                            view=None
                        )
                else:
                    logger.info("No game was selected. Cancelling invite.")
                    await message.edit(content="No game was selected. Invite cancelled.", view=None)

                del self.active_invites[message_id]

            except Exception as e:
                logger.error(f"Error in cleanup: {e}", exc_info=True)
                await message.edit(content="Error occurred. Game cancelled.", view=None)
                del self.active_invites[message_id]

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
        logger.info("=== Handle Game Start ===")
        invite = self.active_invites.get(message_id)
        if not invite:
            logger.warning(f"No invite found for message {message_id}")
            return

        try:
            # Create and start the game
            game = game_class(self.bot, list(invite['players']), invite['channel'].guild)
            channel = await game.setup_channel()

            # Store the game in active_games
            self.active_games[channel.id] = game

            # Notify players
            player_mentions = " ".join(player.mention for player in invite['players'])
            await channel.send(
                f"Game starting! Welcome {player_mentions}\n"
                f"Use `!stop` to end the game early.\n"
                f"This channel will be deleted {game.cleanup_timeout} seconds after the game ends."
            )

            # Start the game
            await game.start_game()

            # Update original message
            await invite['message'].edit(
                content=f"Game started in {channel.mention}!",
                view=None
            )

            logger.info(f"Successfully started game in channel {channel.id}")

        except Exception as e:
            logger.error(f"Error starting game: {e}", exc_info=True)
            await invite['message'].edit(
                content="An error occurred while starting the game.",
                view=None
            )
            raise

    @commands.command(name="stop")
    async def stop_game(self, ctx):
        """Stop the current game in this channel"""
        logger.info(f"Stop command received in channel {ctx.channel.name}")

        # Check if this is a game channel
        if not ctx.channel.name.startswith(('truth-or-dare-', 'word-guess-')):
            logger.info(f"Stop command used in non-game channel: {ctx.channel.name}")
            await ctx.send("This command can only be used in game channels!")
            return

        # Check if there's an active game in this channel
        game = self.active_games.get(ctx.channel.id)
        if not game:
            logger.warning(f"No active game found in channel {ctx.channel.id}")
            await ctx.send("No active game found in this channel!")
            return

        # Check if the user is a player in the game
        if ctx.author not in game.players:
            logger.warning(f"Non-player {ctx.author} tried to stop the game")
            await ctx.send("Only players can stop the game!")
            return

        try:
            logger.info(f"Stopping game in channel {ctx.channel.id}")
            await game.stop_game()
            del self.active_games[ctx.channel.id]
            await ctx.send("Game stopped. This channel will be deleted soon.")
        except Exception as e:
            logger.error(f"Error stopping game: {e}", exc_info=True)
            await ctx.send("An error occurred while stopping the game!")

async def setup(bot):
    await bot.add_cog(GameInvites(bot))