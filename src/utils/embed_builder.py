import discord

class EmbedBuilder:
    def create_interview_type_selection(self):
        embed = discord.Embed(
            title="Interview Type Selection",
            description="Please select the type of interview you'd like to practice:",
            color=discord.Color.blue()
        )
        embed.add_field(name="💻 Technical", value="Programming and technical questions", inline=False)
        embed.add_field(name="👥 Behavioral", value="Soft skills and past experiences", inline=False)
        embed.add_field(name="📊 System Design", value="Architecture and design questions", inline=False)
        return embed

    def create_difficulty_selection(self):
        embed = discord.Embed(
            title="Select Difficulty Level",
            description="Please choose the difficulty level for your interview:",
            color=discord.Color.blue()
        )
        embed.add_field(name="🟢 Entry Level", value="Basic questions suitable for beginners", inline=False)
        embed.add_field(name="🟡 Medium", value="Intermediate level questions", inline=False)
        embed.add_field(name="🔴 Hard", value="Advanced questions for experienced professionals", inline=False)
        return embed

    def create_question_embed(self, interview_type, difficulty, question_data):
        embed = discord.Embed(
            title=f"{interview_type.title()} Interview - {difficulty.title()} Level",
            description=question_data["question"],
            color=discord.Color.blue()
        )
        if "context" in question_data:
            embed.add_field(name="Context", value=question_data["context"], inline=False)
        return embed

    def create_summary_embed(self, summary):
        embed = discord.Embed(
            title="Interview Feedback",
            description=summary["overall_assessment"],
            color=discord.Color.green() if summary["meets_bar"] else discord.Color.orange()
        )
        if summary["strengths"]:
            embed.add_field(
                name="💪 Strengths",
                value="\n".join(f"• {s}" for s in summary["strengths"]),
                inline=False
            )
        if summary["improvement_areas"]:
            embed.add_field(
                name="🎯 Areas for Improvement",
                value="\n".join(f"• {i}" for i in summary["improvement_areas"]),
                inline=False
            )
        return embed

    def create_active_sessions_embed(self, active_sessions):
        embed = discord.Embed(
            title="Active Interview Sessions",
            color=discord.Color.blue()
        )
        for user_id, session in active_sessions:
            status = "🔄 Processing" if session.is_processing else "⏳ Waiting for response"
            embed.add_field(
                name=f"User: {user_id}",
                value=f"Type: {session.interview_type}\nDifficulty: {session.difficulty}\nStatus: {status}",
                inline=False
            )
        return embed


    def create_resume_feedback_embed(self, feedback: dict, include_refined: bool = True) -> discord.Embed:
        """Create an embed for resume feedback"""
        embed = discord.Embed(
            title="Resume Analysis Results",
            color=discord.Color.blue()
        )

        # Overall Assessment
        assessment = feedback.get("overall_assessment", "N/A")
        if len(assessment) > 1024:
            assessment = assessment[:1021] + "..."
        embed.add_field(
            name="Overall Assessment",
            value=assessment,
            inline=False
        )

        # Strengths
        strengths = feedback.get("strengths", [])
        strengths_text = "\n".join(f"• {strength}" for strength in strengths) or "N/A"
        if len(strengths_text) > 1024:
            strengths_text = strengths_text[:1021] + "..."
        embed.add_field(
            name="Strengths",
            value=strengths_text,
            inline=False
        )

        # Improvements
        improvements = feedback.get("improvements", [])
        improvements_text = "\n".join(f"• {improvement}" for improvement in improvements) or "N/A"
        if len(improvements_text) > 1024:
            improvements_text = improvements_text[:1021] + "..."
        embed.add_field(
            name="Suggested Improvements",
            value=improvements_text,
            inline=False
        )

        # Refined Resume (optional)
        if include_refined:
            refined_content = feedback.get("refined_content", "").strip()
            if refined_content:
                if len(refined_content) > 1024:
                    refined_content = refined_content[:1021] + "..."
                embed.add_field(
                    name="Refined Resume",
                    value=refined_content or "N/A",
                    inline=False
                )

        # Additional Tips
        tips = feedback.get("additional_tips", [])
        tips_text = "\n".join(f"• {tip}" for tip in tips) or "N/A"
        if len(tips_text) > 1024:
            tips_text = tips_text[:1021] + "..."
        embed.add_field(
            name="Additional Tips",
            value=tips_text,
            inline=False
        )

        return embed