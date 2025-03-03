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