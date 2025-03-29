from discord.ext import commands, tasks
import discord
import asyncio
from datetime import datetime, time
from ...utils.task_scheduler import BaseScheduledTask
from ...config.task_config import TASK_CONFIG
from ...config.game_config import GAME_CONFIGS
from .games import AVAILABLE_GAMES
import logging
import asyncio

logger = logging.getLogger(__name__)

class GameSelectView(discord.ui.View):
    def __init__(self, cog):
        timeout = GAME_CONFIGS['general']['join_timeout']
        super().__init__(timeout=timeout)
        self.cog = cog
        self.bot = cog.bot
        logger.debug(f"Initializing GameSelectView with {timeout}s timeout")
        self.add_game_buttons()

    def add_game_buttons(self):
        logger.debug("Adding game buttons to view")
        for game_id, game_class in AVAILABLE_GAMES.items():
            logger.debug(f"Adding button for game: {game_id}")
            try:
                temp_game = game_class(self.bot, [], None)
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

            # Store the selected game class if not already stored
            if not invite.get('selected_game'):
                invite['selected_game'] = game_class
                invite['start_time'] = datetime.now()

            temp_game = game_class(self.bot, [], interaction.guild)
            current_players = len(invite['players'])

            # First check if we've reached max players (including current player if they haven't joined)
            if current_players >= temp_game.max_players:
                await interaction.response.send_message(
                    "This game is already full!",
                    ephemeral=True
                )
                # Start the game if we just reached max players
                if current_players == temp_game.max_players:
                    logger.info("Maximum players reached - starting game immediately")
                    if invite.get('cleanup_task'):
                        invite['cleanup_task'].cancel()
                    try:
                        await self.cog.handle_game_start(message_id, game_class)
                        logger.info("Game started successfully")
                    except Exception as e:
                        logger.error(f"Error in handle_game_start: {e}", exc_info=True)
                return

            # Now check if player is already in the game
            if interaction.user in invite['players']:
                await interaction.response.send_message(
                    "You've already joined this game!",
                    ephemeral=True
                )
                return

            # Add player
            invite['players'].add(interaction.user)
            current_players = len(invite['players'])
            logger.info(f"After adding player - Total players: {current_players}")
            logger.info(f"Updated players list: {[p.name for p in invite['players']]}")

            # Check if max players reached after adding new player
            if current_players >= temp_game.max_players:
                await interaction.response.send_message(
                    "Maximum players reached! Starting game...",
                    ephemeral=True
                )
                logger.info("Maximum players reached - starting game immediately")

                # Cancel the cleanup task
                if invite.get('cleanup_task'):
                    invite['cleanup_task'].cancel()

                # Start the game immediately
                try:
                    await self.cog.handle_game_start(message_id, game_class)
                    logger.info("Game started successfully")
                    return
                except Exception as e:
                    logger.error(f"Error in handle_game_start: {e}", exc_info=True)
                    return

            # If not max players, show waiting message
            players_needed = temp_game.min_players - current_players
            timeout = GAME_CONFIGS['general']['join_timeout']
            if players_needed > 0:
                await interaction.response.send_message(
                    f"You've joined! Need {players_needed} more player(s) to start.\n"
                    f"Current: {current_players}/{temp_game.max_players} players\n"
                    f"Game will start in {timeout} seconds if minimum players is reached.",
                    ephemeral=True
                )
            else:
                await interaction.response.send_message(
                    f"You've joined! ({current_players}/{temp_game.max_players} players)\n"
                    f"Game will start in {timeout} seconds!",
                    ephemeral=True
                )

            logger.info("=== Game Button Callback Completed ===")

        return callback

class GameInvites(commands.Cog, BaseScheduledTask):
    def __init__(self, bot):
        self.bot = bot
        self.active_invites = {}
        self.active_games = {}

    def cog_unload(self):
        # Cancel all active tasks
        for invite in self.active_invites.values():
            if invite.get('cleanup_task'):
                invite['cleanup_task'].cancel()

    async def create_game_invite(self, channel, initiator=None):
        """Create a game invite"""
        logger.info(f"Creating game invite in channel: {channel.name}")

        try:
            timeout = GAME_CONFIGS['general']['join_timeout']
            embed = discord.Embed(
                title="🎮 Let's Play a Game!",
                description=f"Choose a game to play!\nInvite expires in {timeout} seconds.",
                color=discord.Color.blue()
            )

            # Process each game
            for game_id, game_class in AVAILABLE_GAMES.items():
                logger.debug(f"Processing game: {game_id}")
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

            # Initialize invite data
            self.active_invites[message.id] = {
                'message': message,
                'players': set([initiator]) if initiator else set(),
                'channel': channel,
                'selected_game': None,
                'start_time': None,
                'cleanup_task': None
            }

            # Schedule cleanup
            cleanup_task = self.bot.loop.create_task(self.check_invite_status(message.id))
            self.active_invites[message.id]['cleanup_task'] = cleanup_task

            return message

        except Exception as e:
            logger.error(f"Error in create_game_invite: {e}", exc_info=True)
            await channel.send("Error creating game invite. Please try again.")
            raise

    async def check_invite_status(self, message_id):
        """Check invite status after 60 seconds"""
        timeout = GAME_CONFIGS['general']['join_timeout']
        await asyncio.sleep(timeout)  # Wait 60 seconds

        invite = self.active_invites.get(message_id)
        if not invite:
            return

        # If game hasn't started yet
        if not invite.get('game'):
            message = invite['message']
            selected_game = invite.get('selected_game')
            current_players = len(invite['players'])

            try:
                if not selected_game:
                    await message.edit(content="No game was selected. Invite cancelled.", view=None)
                else:
                    temp_game = selected_game(self.bot, [], message.guild)
                    if current_players >= temp_game.min_players:
                        # Start the game if we have enough players
                        await self.handle_game_start(message_id, selected_game)
                        return
                    else:
                        await message.edit(
                            content=f"Not enough players joined. Need at least {temp_game.min_players} players. Game cancelled.",
                            view=None
                        )
            except Exception as e:
                logger.error(f"Error in check_invite_status: {e}", exc_info=True)
                await message.edit(content="Error occurred. Game cancelled.", view=None)

            # Clean up the invite
            del self.active_invites[message_id]

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

            # Clean up the invite
            del self.active_invites[message_id]

            logger.info(f"Successfully started game in channel {channel.id}")

        except Exception as e:
            logger.error(f"Error starting game: {e}", exc_info=True)
            await invite['message'].edit(
                content="An error occurred while starting the game.",
                view=None
            )
            raise

    @commands.command(name="startgame")
    async def start_game(self, ctx):
        """Start a new game manually"""
        await self.create_game_invite(ctx.channel, ctx.author)

    @commands.command(name="stop")
    async def stop_game(self, ctx):
        """Stop the current game in this channel"""
        logger.info(f"Stop command received in channel {ctx.channel.name}")

        game = self.active_games.get(ctx.channel.id)
        if not game:
            logger.warning(f"No active game found in channel {ctx.channel.id}")
            try:
                await ctx.send("No active game found in this channel!")
            except discord.NotFound:
                pass
            return

        if ctx.author not in game.players:
            logger.warning(f"Non-player {ctx.author} tried to stop the game")
            try:
                await ctx.send("Only players can stop the game!")
            except discord.NotFound:
                pass
            return

        try:
            logger.info(f"Stopping game in channel {ctx.channel.id}")
            # Send message before stopping the game
            try:
                await ctx.send("Game stopped. This channel will be deleted soon.")
            except discord.NotFound:
                pass

            # Stop the game and clean up
            await game.stop_game()
            if ctx.channel.id in self.active_games:
                del self.active_games[ctx.channel.id]

        except Exception as e:
            logger.error(f"Error stopping game: {e}", exc_info=True)
            try:
                await ctx.send("An error occurred while stopping the game!")
            except discord.NotFound:
                pass

    async def execute(self):
        """Send scheduled game invites"""
        logger.info("Executing scheduled game invites")
        config = TASK_CONFIG.get('gameinvites', {})
        channel_ids = config.get('channel_ids', [])

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

async def setup(bot):
    await bot.add_cog(GameInvites(bot))
