# Quick Start Guide

Get your Personal Agent up and running in 5 minutes!

## Step 1: Get a Gemini API Key

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy your API key

## Step 2: Install

```bash
cd personal-agent
./scripts/install.sh
```

This will:
- Check Python version (requires 3.10+)
- Install all dependencies
- Create a `.env` file

## Step 3: Configure

Edit the `.env` file and add your API key:

```bash
nano .env  # or use your preferred editor
```

Add:
```
GEMINI_API_KEY=your_actual_api_key_here
```

## Step 4: Run

Choose your preferred interface:

### Option A: Terminal (Interactive CLI)

```bash
python -m src.terminal.cli
```

Try these commands:
- Type naturally to chat with your agent
- `/interests add machine learning` - Add an interest
- `/discover` - Find interesting content
- `/status` - View statistics
- `/help` - See all commands

### Option B: Web Interface

```bash
python -m src.web.app
```

Then open: http://localhost:8000

### Option C: Background Daemon

```bash
python -m src.daemon.service
```

The daemon will:
- Discover content every 30 minutes
- Analyze your preferences periodically
- Run in the background continuously

## Next Steps

### Personalize Your Agent

1. Add your interests:
```bash
# In CLI:
/interests add artificial intelligence
/interests add programming
/interests add space exploration

# Or via web UI - use the sidebar
```

2. Have some conversations to build context

3. Ask the agent to understand you better:
```bash
/understand
```

### Advanced Usage

**Single commands without interactive mode:**
```bash
# Send a single message
python -m src.terminal.cli chat "What's new in AI?"

# Discover content
python -m src.terminal.cli discover --limit 10
```

**Run with custom settings:**
```bash
# Web UI on different port
WEB_PORT=3000 python -m src.web.app

# Daemon with faster checks
python -m src.daemon.service --check-interval 15
```

**Multiple users:**
```bash
python -m src.terminal.cli --user-id alice
python -m src.terminal.cli --user-id bob
```

## Troubleshooting

### "Module not found"
```bash
pip install -r requirements.txt
```

### "API key not found"
Make sure `.env` exists and contains `GEMINI_API_KEY=...`

### "Permission denied"
```bash
chmod -R u+w data/
```

## What's Next?

- Check out the full [README.md](README.md) for detailed documentation
- Explore the API endpoints (see README)
- Customize content discovery in `src/agent/content.py`
- Add new LLM providers in `src/llm/`
- Create custom commands in `src/terminal/cli.py`

## Tips

1. **Be specific about your interests** - The more specific you are, the better content the agent can discover

2. **Use the `/understand` command regularly** - This helps the agent learn your preferences

3. **Run the daemon in the background** - Let it discover content while you work

4. **Try the web UI for convenience** - Great for quick interactions and managing interests

5. **Check the logs** - If something isn't working, logs will show what's happening

## Common Use Cases

### Content Curator
```bash
# Add your interests
/interests add rust programming
/interests add web development
/interests add devops

# Let the daemon discover content
python -m src.daemon.service &

# Check discovered content later
/discover
```

### AI Assistant
```bash
# Just chat naturally
python -m src.terminal.cli

> How can I optimize my Python code?
> What are the best practices for async programming?
> Explain how transformers work in AI
```

### Research Helper
```bash
# Add research topics
/interests add quantum computing
/interests add machine learning papers

# Ask for summaries
> Summarize recent developments in quantum computing
> Find papers about transformer architectures
```

Enjoy your Personal Agent!
