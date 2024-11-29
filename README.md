# Discord Interview Coach

A Discord bot that helps users practice interview questions with AI-powered feedback. The bot supports technical, behavioral, and system design interviews in a private, 1-on-1 setting.

## Features

- 🎯 Multiple interview types (Technical, Behavioral, System Design)
- 💬 Private 1:1 interview sessions
- 🤖 AI-powered feedback using Amazon Bedrock
- 📊 Detailed evaluation with specific improvements
- 🔄 Follow-up questions for deeper discussion

## Prerequisites

- Python 3.8 or higher
- Discord Bot Token
- AWS Account with Bedrock access
- AWS CLI configured with appropriate permissions

## Setup

1. Clone the repository
```bash
git clone https://github.com/yourusername/discord-interview-coach.git
cd discord-interview-coach
```

2. Install dependencies

```
pip install -r requirements.txt
```

3. Create .env file in the root directory

```bash
# Discord Bot Token (Required)
DISCORD_TOKEN=your_discord_bot_token

# AWS Credentials (Required for AI feedback)
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_REGION=your_aws_region

# Bot Configuration (Optional)
COMMAND_PREFIX=!
```

## Creating a Discord Bot

1. Visit [Discord Developer Portal](https://discord.com/developers/applications)
2. Click "New Application"
    - Give your bot a name (e.g., "Interview Coach")
    - Accept the Developer Terms of Service

3. Configure Bot Settings
    - Navigate to the "Bot" tab in the left sidebar
    - Click "Add Bot"
    - Click "Yes, do it!" to confirm

4. Set Bot Permissions
    - Under "Privileged Gateway Intents", enable:
        - ✅ MESSAGE CONTENT INTENT
        - ✅ SERVER MEMBERS INTENT
        - ✅ PRESENCE INTENT

5. Get Your Bot Token
    - Click "Reset Token" and confirm
    - Copy the token
    - Add it to your `.env` file:
      ```env
      DISCORD_TOKEN=your_token_here
      ```

6. Invite Bot to Your Server
    - Go to "OAuth2" → "URL Generator"
    - Select scopes:
        - ✅ bot
        - ✅ applications.commands
    - Select bot permissions:
        - ✅ Send Messages
        - ✅ Read Messages/View Channels
        - ✅ Add Reactions
    - Copy and open the generated URL
    - Select your server and authorize

## Running the Bot

```
python run.py
```


