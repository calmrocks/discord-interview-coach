from .base_game import BaseGame
from src.config.game_config import GAME_CONFIGS
import discord
import random
import logging
import asyncio
from typing import Dict, Set, List

logger = logging.getLogger(__name__)

class MirrorMatch(BaseGame):
    def __init__(self, bot, players, guild):
        super().__init__(bot, players, guild)
        self._config = GAME_CONFIGS['mirror_match']

        # Game state
        self.trendsetter = None
        self.trendsetter_answers = {}
        self.player_answers = {}
        self.scores = {player.id: 0 for player in players}
        self.current_questions = []
        self.game_phase = 'setup'  # setup, trendsetter, followers, ended

    async def start_game(self):
        """Initialize and start the Mirror Match game"""
        await super().start_game()

        # Select random trendsetter
        self.trendsetter = random.choice(self.players)
        self.current_questions = random.sample(self._config['questions'], 10)

        # Announce game start and roles
        await self.channel.send(
            "🎮 **Mirror Match Started!**\n\n"
            f"👑 **Trendsetter**: {self.trendsetter.mention}\n"
            f"👥 **Followers**: {', '.join(p.mention for p in self.players if p != self.trendsetter)}\n\n"
            "The Trendsetter will answer some questions, and Followers will try to match their answers!"
        )

        # Start the game phases
        await self.trendsetter_phase()

    async def trendsetter_phase(self):
        """Handle the trendsetter's question phase"""
        self.game_phase = 'trendsetter'

        await self.channel.send(
            f"{self.trendsetter.mention}, you are the Trendsetter!\n"
            "I'll send you 10 questions in DMs. Please answer them honestly!"
        )

        try:
            # Send questions to trendsetter via DM
            dm_channel = await self.trendsetter.create_dm()

            for i, question in enumerate(self.current_questions, 1):
                # Create and send question embed
                embed = discord.Embed(
                    title=f"Question {i}/10",
                    description=question['question'],
                    color=discord.Color.blue()
                )

                # Create button view for options
                view = OptionView(question['options'])
                question_msg = await dm_channel.send(embed=embed, view=view)

                # Wait for trendsetter's answer
                try:
                    await view.wait()
                    if view.selected_option is None:
                        await self.channel.send("Game cancelled - Trendsetter didn't respond in time!")
                        return await self.end_game(forced=True)

                    self.trendsetter_answers[i] = view.selected_option
                    await question_msg.edit(
                        embed=embed.add_field(name="Your answer", value=view.selected_option),
                        view=None
                    )
                except asyncio.TimeoutError:
                    await self.channel.send("Game cancelled - Trendsetter didn't respond in time!")
                    return await self.end_game(forced=True)

            await self.channel.send("Trendsetter has completed their answers! Moving to the Followers phase...")
            await self.followers_phase()

        except discord.Forbidden:
            await self.channel.send(
                "Unable to send DM to Trendsetter. Please enable DMs and try again!"
            )
            return await self.end_game(forced=True)

    async def followers_phase(self):
        """Handle the followers' question phase"""
        self.game_phase = 'followers'

        followers = [p for p in self.players if p != self.trendsetter]

        await self.channel.send(
            "🎯 **Followers Phase Started!**\n"
            "Each follower will receive the same questions in DMs.\n"
            "Try to match what you think the Trendsetter answered!"
        )

        for follower in followers:
            self.player_answers[follower.id] = {}

            try:
                dm_channel = await follower.create_dm()
                await dm_channel.send(
                    "Your turn! Answer these questions as you think the Trendsetter did!"
                )

                for i, question in enumerate(self.current_questions, 1):
                    # Create and send question embed
                    embed = discord.Embed(
                        title=f"Question {i}/10",
                        description=question['question'],
                        color=discord.Color.green()
                    )

                    view = OptionView(question['options'])
                    question_msg = await dm_channel.send(embed=embed, view=view)

                    try:
                        await view.wait()
                        if view.selected_option is None:
                            await self.channel.send(f"{follower.mention} didn't respond in time!")
                            continue

                        self.player_answers[follower.id][i] = view.selected_option
                        await question_msg.edit(
                            embed=embed.add_field(name="Your answer", value=view.selected_option),
                            view=None
                        )
                    except asyncio.TimeoutError:
                        await self.channel.send(f"{follower.mention} didn't respond in time!")
                        continue

                await dm_channel.send("You've completed all questions! Wait for others to finish...")

            except discord.Forbidden:
                await self.channel.send(
                    f"Unable to send DM to {follower.mention}. Please enable DMs!"
                )
                continue

        await self.calculate_scores()

    async def calculate_scores(self):
        """Calculate and display the final scores"""
        self.game_phase = 'ended'

        # Calculate scores for each player
        followers = [p for p in self.players if p != self.trendsetter]

        for follower in followers:
            correct_answers = 0
            follower_answers = self.player_answers.get(follower.id, {})

            for question_num, trendsetter_answer in self.trendsetter_answers.items():
                if follower_answers.get(question_num) == trendsetter_answer:
                    correct_answers += 1
                    self.scores[follower.id] += self._config['scoring']['correct_match']

            # Add bonus points if applicable
            if correct_answers >= self._config['scoring']['bonus_threshold']:
                self.scores[follower.id] += 1
                bonus_awarded = True
            else:
                bonus_awarded = False

            # Send individual results to each player
            try:
                dm_channel = await follower.create_dm()
                embed = discord.Embed(
                    title="Your Results",
                    description=f"You matched {correct_answers}/10 answers!",
                    color=discord.Color.blue()
                )
                embed.add_field(
                    name="Points Earned",
                    value=f"{self.scores[follower.id]} points" + (" (including bonus!)" if bonus_awarded else "")
                )
                await dm_channel.send(embed=embed)
            except discord.Forbidden:
                pass

        # Display final leaderboard
        await self.show_leaderboard()

    async def show_leaderboard(self):
        """Display the final leaderboard and trendsetter's answers"""
        embed = discord.Embed(
            title="🏆 Mirror Match Results",
            description="Here's how well everyone did at matching the Trendsetter!",
            color=discord.Color.gold()
        )

        # Sort players by score
        sorted_scores = sorted(
            [(player, self.scores[player.id]) for player in self.players if player != self.trendsetter],
            key=lambda x: x[1],
            reverse=True
        )

        # Add leaderboard to embed
        leaderboard = "\n".join(
            f"{idx+1}. {player.name}: {score} points"
            for idx, (player, score) in enumerate(sorted_scores)
        )
        embed.add_field(name="📊 Leaderboard", value=leaderboard or "No scores", inline=False)

        # Add Trendsetter's answers
        trendsetter_answers = "\n".join(
            f"Q{q}: {ans}" for q, ans in self.trendsetter_answers.items()
        )
        embed.add_field(
            name=f"👑 {self.trendsetter.name}'s Answers",
            value=trendsetter_answers,
            inline=False
        )

        await self.channel.send(embed=embed)

        # End the game
        await self.end_game()

    async def end_game(self, forced=False):
        """End the game and clean up"""
        if not forced:
            await self.channel.send(
                "Thanks for playing Mirror Match!\n"
                f"This channel will be deleted in {self.cleanup_timeout} seconds."
            )

        await super().end_game(forced=forced)

class OptionView(discord.ui.View):
    def __init__(self, options: List[str]):
        super().__init__(timeout=30.0)
        self.selected_option = None

        # Create a button for each option
        for option in options:
            self.add_item(OptionButton(option, self))

class OptionButton(discord.ui.Button):
    def __init__(self, option: str, view: OptionView):
        super().__init__(
            label=option,
            style=discord.ButtonStyle.primary
        )
        self.option = option
        self.parent_view = view

    async def callback(self, interaction: discord.Interaction):
        self.parent_view.selected_option = self.option
        await interaction.response.send_message(f"You selected: {self.option}", ephemeral=True)
        self.parent_view.stop()