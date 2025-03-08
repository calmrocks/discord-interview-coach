import discord
from discord.ext import commands
import io
import PyPDF2
import docx
from ..services.resume_service import ResumeService
from src.utils.embed_builder import EmbedBuilder

class Resume(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.resume_service = ResumeService()
        self.embed_builder = EmbedBuilder()
        self.pending_resumes = {}  # Store user_id: waiting_for_resume
        self.supported_formats = ['.txt', '.doc', '.docx', '.pdf']

    @commands.command(name='resume')
    async def refine_resume(self, ctx):
        """
        Start a resume refinement session.
        Usage: !resume
        Upload your resume as a file (.txt, .doc, .docx, .pdf) or paste the text directly.
        """
        try:
            instructions = (
                "Welcome to the Resume Refinement service!\n\n"
                "Please either:\n"
                "1. Upload your resume as a file (supported formats: txt, doc, docx, pdf), or\n"
                "2. Paste your resume text directly\n\n"
                "I'll analyze it and provide detailed feedback and improvements."
            )
            await ctx.author.send(instructions)
            await ctx.send(f"{ctx.author.mention} Check your DMs to start the resume refinement process!")

            self.pending_resumes[ctx.author.id] = True

        except discord.Forbidden:
            await ctx.send(
                f"{ctx.author.mention} I couldn't send you a DM. "
                "Please enable DMs from server members and try again!"
            )

    async def extract_text_from_file(self, attachment) -> str:
        """Extract text from various file formats"""
        file_ext = attachment.filename[attachment.filename.rfind('.'):].lower()

        if file_ext not in self.supported_formats:
            raise ValueError(f"Unsupported file format. Supported formats: {', '.join(self.supported_formats)}")

        # Download the file
        file_data = io.BytesIO()
        await attachment.save(file_data)
        file_data.seek(0)

        try:
            if file_ext == '.txt':
                return file_data.read().decode('utf-8')

            elif file_ext == '.pdf':
                pdf_reader = PyPDF2.PdfReader(file_data)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
                return text

            elif file_ext in ['.doc', '.docx']:
                doc = docx.Document(file_data)
                return "\n".join([paragraph.text for paragraph in doc.paragraphs])

        except Exception as e:
            raise ValueError(f"Error reading file: {str(e)}")

    async def send_feedback_in_chunks(self, channel, feedback: dict):
        """Send feedback in chunks to handle Discord's message length limits"""
        # Send initial sections
        embed = self.embed_builder.create_resume_feedback_embed(feedback, include_refined=False)
        await channel.send(embed=embed)

        # Send refined resume in chunks if it exists
        refined_content = feedback.get("refined_content", "").strip()
        if refined_content:
            await channel.send("**Refined Resume:**")
            chunks = [refined_content[i:i+1994] for i in range(0, len(refined_content), 1994)]
            for chunk in chunks:
                await channel.send(f"```{chunk}```")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not isinstance(message.channel, discord.DMChannel):
            return

        if message.author.id in self.pending_resumes:
            async with message.channel.typing():
                try:
                    resume_text = ""

                    # Check for file attachment
                    if message.attachments:
                        attachment = message.attachments[0]
                        await message.channel.send("Processing your resume file... Please wait.")
                        resume_text = await self.extract_text_from_file(attachment)
                    else:
                        # Use message content as resume text
                        resume_text = message.content

                    if not resume_text.strip():
                        await message.channel.send("No resume content found. Please try again.")
                        return

                    await message.channel.send("Analyzing your resume... Please wait.")

                    # Get refinement feedback
                    feedback = await self.resume_service.analyze_resume(resume_text)

                    # Send feedback in chunks
                    await self.send_feedback_in_chunks(message.channel, feedback)

                    # Clean up
                    del self.pending_resumes[message.author.id]

                    # Ask if they want to save the refined version
                    await self.offer_download(message.channel, feedback.get("refined_content", ""))

                except ValueError as ve:
                    await message.channel.send(f"Error: {str(ve)}")
                except Exception as e:
                    await message.channel.send(f"Error processing resume: {str(e)}")
                    del self.pending_resumes[message.author.id]

    async def offer_download(self, channel, refined_content: str):
        """Offer to provide the refined resume as a downloadable file"""
        if not refined_content:
            return

        await channel.send("Would you like to download the refined resume as a file? React with 📥 to download.")
        msg = await channel.send("(This offer will expire in 60 seconds)")
        await msg.add_reaction("📥")

        def check(reaction, user):
            return not user.bot and str(reaction.emoji) == "📥" and reaction.message.id == msg.id

        try:
            await self.bot.wait_for('reaction_add', timeout=60.0, check=check)
            # Create and send file
            file = discord.File(
                io.StringIO(refined_content),
                filename="refined_resume.txt"
            )
            await channel.send("Here's your refined resume:", file=file)
        except TimeoutError:
            await msg.delete()
        except Exception as e:
            await channel.send(f"Error creating file: {str(e)}")

async def setup(bot):
    await bot.add_cog(Resume(bot))