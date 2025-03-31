from typing import Optional, Dict, Any
import discord
from pathlib import Path
import logging
from ..providers.question_provider import QuestionProvider

logger = logging.getLogger(__name__)

class QuestionLoader:
    def __init__(self):
        self.question_provider = QuestionProvider()

    INTERVIEW_TYPE_EMOJIS = {
        '💻': 'technical',
        '👥': 'behavioral',
        '📊': 'system_design'
    }

    DIFFICULTY_EMOJIS = {
        '🟢': 'easy',
        '🟡': 'medium',
        '🔴': 'hard'
    }

    @classmethod
    def get_interview_type_emojis(cls) -> list:
        """Get list of interview type emojis"""
        return list(cls.INTERVIEW_TYPE_EMOJIS.keys())

    @classmethod
    def get_difficulty_emojis(cls) -> list:
        """Get list of difficulty emojis"""
        return list(cls.DIFFICULTY_EMOJIS.keys())

    async def create_type_selection_embed(self) -> discord.Embed:
        """Create interview type selection embed"""
        embed = discord.Embed(
            title="Interview Type Selection",
            description="Choose the type of interview you'd like to practice:",
            color=discord.Color.blue()
        )
        embed.add_field(
            name="Options",
            value=(
                "💻 Technical Interview\n"
                "👥 Behavioral Interview\n"
                "📊 System Design Interview"
            ),
            inline=False
        )
        return embed

    async def create_difficulty_selection_embed(self) -> discord.Embed:
        """Create difficulty selection embed"""
        embed = discord.Embed(
            title="Difficulty Selection",
            description="Choose the difficulty level:",
            color=discord.Color.blue()
        )
        embed.add_field(
            name="Options",
            value=(
                "🟢 Easy\n"
                "🟡 Medium\n"
                "🔴 Hard"
            ),
            inline=False
        )
        return embed

    async def create_question_embed(self, interview_type: str, difficulty: str, question_data: Dict[str, Any]) -> discord.Embed:
        """Create question embed for free-form answers"""
        embed = discord.Embed(
            title=f"{interview_type.title()} Interview Question ({difficulty.title()})",
            description=question_data['question'],
            color=discord.Color.green()
        )

        if 'topics' in question_data:
            embed.add_field(
                name="📌 Related Topics",
                value=", ".join(question_data['topics']),
                inline=False
            )

        embed.set_footer(text="Discuss your answer in the voice channel. Use !next when ready for another question.")

        return embed

    async def get_random_question(self, interview_type: str, difficulty: str = "medium") -> Optional[Dict[str, Any]]:
        """Get a random question from the question bank"""
        try:
            return self.question_provider.get_random_question(interview_type, difficulty)
        except Exception as e:
            logger.error(f"Error getting random question: {e}")
            return None

    @classmethod
    def get_interview_type_from_reaction(cls, emoji: str) -> Optional[str]:
        """Convert reaction emoji to interview type"""
        return cls.INTERVIEW_TYPE_EMOJIS.get(emoji)

    @classmethod
    def get_difficulty_from_reaction(cls, emoji: str) -> Optional[str]:
        """Convert reaction emoji to difficulty level"""
        return cls.DIFFICULTY_EMOJIS.get(emoji)
