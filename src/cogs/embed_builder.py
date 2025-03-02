import discord
from datetime import datetime
from typing import Dict, Any

class EmbedBuilder:
    """Builds Discord embeds for different parts of the interview"""

    def create_welcome_embed(self) -> discord.Embed:
        """Create the welcome embed with interview type selection"""
        embed = discord.Embed(
            title="Welcome to Mock Interview Bot!",
            description="Please select an interview type by reacting to this message:",
            color=discord.Color.blue(),
            timestamp=datetime.now()
        )

        embed.add_field(
            name="💻 Technical/Coding Interview",
            value="Algorithmic and coding questions",
            inline=False
        )

        embed.add_field(
            name="🏗️ System Design Interview",
            value="Design scalable systems and architecture",
            inline=False
        )

        embed.add_field(
            name="🗣️ Behavioral Interview",
            value="Questions about your past experiences and soft skills",
            inline=False
        )

        embed.set_footer(text="React with the emoji for your selected interview type")
        return embed

    def create_level_selection_embed(self, interview_type: str) -> discord.Embed:
        """Create embed for selecting experience level"""
        title_map = {
            "technical": "Technical Interview",
            "system_design": "System Design Interview",
            "behavioral": "Behavioral Interview"
        }

        embed = discord.Embed(
            title=f"{title_map.get(interview_type, interview_type)} Selected",
            description="Please select your experience level:",
            color=discord.Color.green(),
            timestamp=datetime.now()
        )

        embed.add_field(
            name="🥉 Entry Level",
            value="0-2 years of experience",
            inline=False
        )

        embed.add_field(
            name="🥈 Mid Level",
            value="3-5 years of experience",
            inline=False
        )

        embed.add_field(
            name="🥇 Senior Level",
            value="6+ years of experience",
            inline=False
        )

        embed.set_footer(text="React with the emoji for your experience level")
        return embed

    def create_question_embed(self, question: str) -> discord.Embed:
        """Create embed for an interview question"""
        embed = discord.Embed(
            title="Interview Question",
            description=question,
            color=discord.Color.gold(),
            timestamp=datetime.now()
        )

        embed.set_footer(text="Type your answer in the thread")
        return embed

    def create_followup_embed(self, question: str) -> discord.Embed:
        """Create embed for a follow-up question"""
        embed = discord.Embed(
            title="Follow-up Question",
            description=question,
            color=discord.Color.purple(),
            timestamp=datetime.now()
        )

        embed.set_footer(text="Type your answer in the thread")
        return embed

    def create_summary_embed(self, summary: Dict[str, Any]) -> discord.Embed:
        """Create the interview summary embed"""
        # Determine color based on meets_bar
        color = discord.Color.green() if summary.get("meets_bar") else discord.Color.orange()

        embed = discord.Embed(
            title="Interview Feedback Summary",
            description=summary.get("overall_assessment", "Interview completed"),
            color=color,
            timestamp=datetime.now()
        )

        # Add strengths
        strengths = summary.get("strengths", [])
        if strengths:
            embed.add_field(
                name="💪 Strengths",
                value="\n".join(f"• {strength}" for strength in strengths[:3]),
                inline=False
            )

        # Add improvement areas
        improvements = summary.get("improvement_areas", [])
        if improvements:
            embed.add_field(
                name="🔍 Areas for Improvement",
                value="\n".join(f"• {area}" for area in improvements[:3]),
                inline=False
            )

        # Add specific examples if available
        examples = summary.get("examples", [])
        if examples:
            embed.add_field(
                name="📝 Key Observations",
                value="\n".join(f"• {example}" for example in examples[:2]),
                inline=False
            )

        # Final assessment
        result = "Meets Bar ✅" if summary.get("meets_bar") else "Does Not Meet Bar ❌"
        embed.add_field(
            name="Final Assessment",
            value=result,
            inline=False
        )

        embed.set_footer(text="Thank you for using Mock Interview Bot!")
        return embed