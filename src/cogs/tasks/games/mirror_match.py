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
        self.game_phase = 'setup'

    async def start_game(self):
        """Initialize and start the Mirror Match game"""
        await super().start_game()

        # Select random trendsetter
        self.trendsetter = random.choice(self.players)
        self.current_questions = random.sample(
            self._config['questions'],
            self._config['num_questions']
        )

        # Create and send welcome embed with instructions
        welcome_embed = discord.Embed(
            title="🎮 Welcome to Mirror Match!",
            description="Test how well you can predict others' preferences!",
            color=discord.Color.blue()
        )

        # Add game roles section
        welcome_embed.add_field(
            name="👑 Roles",
            value=(
                f"**Trendsetter**: {self.trendsetter.mention}\n"
                f"**Followers**: {', '.join(p.mention for p in self.players if p != self.trendsetter)}"
            ),
            inline=False
        )

        # Add how to play section
        welcome_embed.add_field(
            name="📋 How to Play",
            value=(
                f"1️⃣ The Trendsetter will receive {self._config['num_questions']} questions in DMs\n"
                "2️⃣ They must answer honestly about their preferences\n"
                "3️⃣ Then, Followers will receive the same questions\n"
                "4️⃣ Followers try to match what they think the Trendsetter answered\n"
                "5️⃣ Get points for each correct match!"
            ),
            inline=False
        )

        # Add scoring section
        welcome_embed.add_field(
            name="🎯 Scoring",
            value=(
                f"• +{self._config['scoring']['correct_match']} point for each correct match\n"
                f"• Bonus {self._config['scoring']['bonus_points']} points for getting "
                f"{self._config['scoring']['bonus_threshold']}+ matches!\n"
                "• Final scores will be revealed at the end"
            ),
            inline=False
        )

        # Add important notes
        welcome_embed.add_field(
            name="⚠️ Important Notes",
            value=(
                "• Make sure your DMs are enabled\n"
                f"• Each question has a {self._config['question_timeout']}-second time limit\n"
                "• Have fun and try to think like the Trendsetter!"
            ),
            inline=False
        )

        await self.channel.send(embed=welcome_embed)
        await self.trendsetter_phase()

    async def trendsetter_phase(self):
        """Handle the trendsetter's question phase"""
        self.game_phase = 'trendsetter'
        self.messages_to_clean = [] # Track messages to clean up later

        if self._config['use_dm_for_trendsetter']:
            await self._trendsetter_dm_phase()
        else:
            await self._trendsetter_channel_phase()

    async def _trendsetter_dm_phase(self):
        """Handle trendsetter questions through DMs"""
        await self.channel.send(
            f"{self.trendsetter.mention}, you are the Trendsetter!\n"
            "I'll send you questions in DMs. Please answer them honestly!"
        )

        try:
            dm_channel = await self.trendsetter.create_dm()
            await self._process_trendsetter_questions(dm_channel)
        except discord.Forbidden:
            await self.channel.send(
                "Unable to send DM to Trendsetter. Please enable DMs and try again!"
            )
            return await self.end_game(forced=True)

    async def _trendsetter_channel_phase(self):
        """Handle trendsetter questions in the game channel"""
        intro_msg = await self.channel.send(
            f"{self.trendsetter.mention}, you are the Trendsetter!\n"
            "Answer these questions honestly in this channel.\n"
            "Other players, please don't scroll up to see the answers during your turn!"
        )
        self.messages_to_clean.append(intro_msg)

        await self._process_trendsetter_questions(self.channel)

        # Announce cleanup
        cleanup_msg = await self.channel.send(
            f"Trendsetter phase complete! Cleaning up messages in {self._config['cleanup_delay']} seconds..."
        )
        self.messages_to_clean.append(cleanup_msg)

        # Wait before cleaning
        await asyncio.sleep(self._config['cleanup_delay'])

        # Clean up all messages
        try:
            await self.channel.delete_messages(self.messages_to_clean)
        except (discord.HTTPException, discord.NotFound) as e:
            logger.error(f"Error cleaning up messages: {e}")
            # If bulk delete fails, try individual deletion
            for msg in self.messages_to_clean:
                try:
                    await msg.delete()
                except:
                    pass

        # Start followers phase
        await self.channel.send("Starting Followers phase...")
        await self.followers_phase()

    async def _process_trendsetter_questions(self, channel):
        """Process trendsetter questions in the specified channel"""
        for i, question in enumerate(self.current_questions, 1):
            embed = discord.Embed(
                title=f"Question {i}/{self._config['num_questions']}",
                description=question['question'],
                color=discord.Color.blue()
            )

            view = OptionView(question['options'], self._config['question_timeout'])
            question_msg = await channel.send(embed=embed, view=view)

            if not self._config['use_dm_for_trendsetter']:
                self.messages_to_clean.append(question_msg)

            try:
                await view.wait()
                if view.selected_option is None:
                    await self.channel.send("Game cancelled - Trendsetter didn't respond in time!")
                    return await self.end_game(forced=True)

                self.trendsetter_answers[i] = view.selected_option

                # Update message with answer
                embed.add_field(name="Your answer", value=view.selected_option)
                await question_msg.edit(embed=embed, view=None)

                # If in channel, add confirmation message
                if not self._config['use_dm_for_trendsetter']:
                    confirm_msg = await channel.send(f"Answer {i} recorded!")
                    self.messages_to_clean.append(confirm_msg)

            except asyncio.TimeoutError:
                await self.channel.send("Game cancelled - Trendsetter didn't respond in time!")
                return await self.end_game(forced=True)

        completion_msg = await channel.send("All questions answered! Moving to next phase...")
        if not self._config['use_dm_for_trendsetter']:
            self.messages_to_clean.append(completion_msg)

    async def followers_phase(self):
        """Handle the followers' question phase"""
        self.game_phase = 'followers'

        followers = [p for p in self.players if p != self.trendsetter]

        await self.channel.send(
            "🎯 **Followers Phase Started!**\n"
            "Each follower will receive the same questions in DMs.\n"
            f"You have {self._config['question_timeout']} seconds to answer each question.\n"
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
                    embed = discord.Embed(
                        title=f"Question {i}/{self._config['num_questions']}",
                        description=question['question'],
                        color=discord.Color.green()
                    )

                    view = OptionView(question['options'], self._config['question_timeout'])
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
                        await self.channel.send(f"{follower.mention} didn't respond in time for question {i}!")
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
            bonus_awarded = False
            if correct_answers >= self._config['scoring']['bonus_threshold']:
                self.scores[follower.id] += self._config['scoring']['bonus_points']
                bonus_awarded = True

            # Send individual results to each player
            try:
                dm_channel = await follower.create_dm()
                embed = discord.Embed(
                    title="Your Results",
                    description=(
                        f"You matched {correct_answers}/{self._config['num_questions']} answers!\n"
                        f"Base points: {correct_answers * self._config['scoring']['correct_match']}\n"
                        f"Bonus points: {self._config['scoring']['bonus_points'] if bonus_awarded else 0}\n"
                        f"Total points: {self.scores[follower.id]}"
                    ),
                    color=discord.Color.blue()
                )
                await dm_channel.send(embed=embed)
            except discord.Forbidden:
                logger.warning(f"Could not send results DM to {follower.name}")

        # Display final leaderboard
        await self.show_leaderboard()

    async def show_leaderboard(self):
        """Display the final leaderboard and trendsetter's answers"""
        embed = discord.Embed(
            title="🏆 Mirror Match Results",
            description=(
                "Game Over! Here's how well everyone did at matching "
                f"{self.trendsetter.name}'s preferences!"
            ),
            color=discord.Color.gold()
        )

        # Sort players by score
        sorted_scores = sorted(
            [(player, self.scores[player.id]) for player in self.players if player != self.trendsetter],
            key=lambda x: x[1],
            reverse=True
        )

        # Add leaderboard to embed
        leaderboard_text = ""
        for idx, (player, score) in enumerate(sorted_scores, 1):
            medal = "🥇" if idx == 1 else "🥈" if idx == 2 else "🥉" if idx == 3 else "➖"
            bonus = score >= self._config['scoring']['bonus_threshold']
            leaderboard_text += f"{medal} {player.name}: {score} points {' ⭐' if bonus else ''}\n"

        embed.add_field(
            name="📊 Final Scores",
            value=leaderboard_text or "No scores available",
            inline=False
        )

        # Add Trendsetter's answers
        answers_text = ""
        for q_num, answer in self.trendsetter_answers.items():
            question = self.current_questions[q_num - 1]['question']
            answers_text += f"Q{q_num}: {question}\n➡️ {answer}\n\n"

        embed.add_field(
            name=f"👑 {self.trendsetter.name}'s Answers",
            value=answers_text,
            inline=False
        )

        await self.channel.send(embed=embed)

        # End the game
        await self.end_game()

class OptionView(discord.ui.View):
    def __init__(self, options: List[str], timeout: int):
        super().__init__(timeout=timeout)
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