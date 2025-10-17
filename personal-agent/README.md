# Personal Agent

A personal AI agent that acts as your co-pilot, understanding your needs and finding interesting content for you.

## Features

- **Multi-Interface**: Terminal CLI and Web UI for flexible interaction
- **Background Service**: Runs continuously to monitor and discover content
- **Extensible LLM Support**: Abstraction layer for easy model swapping (currently supports Google Gemini)
- **Personalized**: Learns your preferences over time through conversation history
- **Content Discovery**: Automatically finds interesting content based on your interests
- **Memory Management**: Maintains conversation context and user interactions
- **User Profiles**: Persistent storage of preferences and learning patterns

## Quick Start

The easiest way to get started:

```bash
./scripts/install.sh   # Install dependencies and setup
./scripts/run.sh       # Interactive launcher
```

Or use Make:

```bash
make setup    # One-time setup
make run-cli  # Or run-web, or run-daemon
```

## Manual Setup

### Prerequisites

- Python 3.10 or higher
- Google Gemini API key ([Get one here](https://makersuite.google.com/app/apikey))

### Installation

1. Clone or download this repository

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file from the example:
```bash
cp .env.example .env
```

4. Add your Gemini API key to `.env`:
```env
GEMINI_API_KEY=your_actual_api_key_here
```

5. Create the data directory:
```bash
mkdir -p data
```

## Usage

### 1. Terminal Interface (CLI)

Interactive command-line interface with rich formatting:

```bash
python -m src.terminal.cli
```

**Available commands:**
- `/help` - Show available commands
- `/status` - View agent status and statistics
- `/discover [limit]` - Discover interesting content
- `/interests` - Manage your interests
- `/interests add <interest>` - Add a new interest
- `/interests remove <interest>` - Remove an interest
- `/understand` - Analyze your interactions for better personalization
- `/exit` - Exit the agent

**Single message mode:**
```bash
python -m src.terminal.cli chat "What's interesting in AI today?"
```

**Discover content:**
```bash
python -m src.terminal.cli discover --limit 10
```

### 2. Web UI

Modern web interface with real-time chat:

```bash
python -m src.web.app
```

Then open your browser to: http://localhost:8000

**Features:**
- Real-time chat interface
- Interest management
- Status dashboard
- Content discovery
- Responsive design

### 3. Background Daemon

Runs continuously in the background, discovering content at regular intervals:

```bash
python -m src.daemon.service --check-interval 30
```

**Options:**
- `--user-id` - User ID (default: "default")
- `--data-dir` - Data directory (default: "./data")
- `--check-interval` - Check interval in minutes (default: 30)
- `--log-level` - Logging level (default: "INFO")

**Run as systemd service:**
```bash
sudo cp scripts/personal-agent.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable personal-agent
sudo systemctl start personal-agent
```

View logs:
```bash
sudo journalctl -u personal-agent -f
```

## Project Structure

```
personal-agent/
├── src/
│   ├── agent/          # Core agent logic
│   ├── llm/            # LLM abstraction layer
│   ├── terminal/       # Terminal interface
│   ├── web/            # Web UI backend
│   └── daemon/         # Background service
├── tests/              # Unit tests
├── config/             # Configuration files
└── data/               # User data and preferences
```

## Architecture

The project uses a modular architecture with clear separation of concerns:

### LLM Abstraction Layer (`src/llm/`)

Provides a unified interface for different AI models:

- **BaseLLM**: Abstract base class defining the LLM interface
- **GeminiLLM**: Google Gemini implementation
- **LLMFactory**: Factory pattern for creating LLM instances
- **Easy to extend**: Just implement BaseLLM for new providers

Example:
```python
from src.llm import LLMFactory, LLMConfig, ModelProvider

config = LLMConfig(
    provider=ModelProvider.GEMINI,
    model_name="gemini-pro",
    api_key="your-api-key",
)

async with LLMFactory.create(config) as llm:
    response = await llm.generate("Hello, how are you?")
    print(response.content)
```

### Agent Core (`src/agent/`)

Main business logic and intelligence:

- **AgentBrain**: Orchestrates all agent functionality
- **UserProfile**: Manages user preferences and learning
- **ContentDiscovery**: Finds and ranks interesting content
- **MemoryManager**: Handles conversation history and context

### Interfaces

**Terminal (`src/terminal/`)**: Rich CLI with commands and interactive chat
**Web (`src/web/`)**: FastAPI backend with REST API and WebSocket support

### Background Service (`src/daemon/`)

Continuous operation with scheduled tasks:
- Periodic content discovery
- User behavior analysis
- Preference updates

## API Reference

### REST API Endpoints

When running the web UI, the following endpoints are available:

**Chat:**
- `POST /api/chat` - Send a message
  ```json
  {"message": "Hello", "user_id": "default"}
  ```

**Content Discovery:**
- `POST /api/discover` - Discover content
  ```json
  {"user_id": "default", "limit": 10}
  ```

**Status:**
- `GET /api/status/{user_id}` - Get agent status

**Interests:**
- `GET /api/interests/{user_id}` - Get interests
- `POST /api/interests/add` - Add interest
- `POST /api/interests/remove` - Remove interest

**WebSocket:**
- `WS /ws/chat/{user_id}` - Real-time chat

## Extending the Agent

### Adding a New LLM Provider

1. Create a new class inheriting from `BaseLLM`:

```python
from src.llm.base import BaseLLM, LLMResponse

class MyLLM(BaseLLM):
    async def initialize(self):
        # Setup your LLM client
        pass

    async def generate(self, prompt, system_prompt=None, **kwargs):
        # Implement generation logic
        return LLMResponse(...)
```

2. Register it with the factory:

```python
from src.llm import LLMFactory, ModelProvider

LLMFactory.register_provider(ModelProvider.MY_LLM, MyLLM)
```

### Customizing Content Discovery

Modify `src/agent/content.py` to integrate with:
- HackerNews API
- Reddit API
- Twitter API
- RSS feeds
- Custom sources

### Adding Custom Commands

Edit `src/terminal/cli.py` to add new slash commands:

```python
async def handle_command(self, command: str):
    if cmd == "/mycommand":
        # Your custom logic
        pass
```

## Configuration

All settings are in `config/settings.py` and can be overridden via environment variables:

- `GEMINI_API_KEY` - Required: Your Gemini API key
- `DEFAULT_MODEL` - Model to use (default: "gemini-pro")
- `TEMPERATURE` - LLM temperature (default: 0.7)
- `MAX_TOKENS` - Max response tokens (default: 2048)
- `WEB_HOST` - Web server host (default: "0.0.0.0")
- `WEB_PORT` - Web server port (default: 8000)
- `CHECK_INTERVAL_MINUTES` - Daemon check interval (default: 30)

## Development

### Running Tests

```bash
make test
# or
pytest tests/ -v
```

### Code Formatting

```bash
black src/
ruff check src/
```

### Project Structure

```
personal-agent/
├── src/
│   ├── agent/              # Core agent logic
│   │   ├── brain.py        # Main orchestrator
│   │   ├── profile.py      # User profiles
│   │   ├── content.py      # Content discovery
│   │   └── memory.py       # Memory management
│   ├── llm/                # LLM abstraction
│   │   ├── base.py         # Base classes
│   │   ├── gemini.py       # Gemini implementation
│   │   └── factory.py      # Factory pattern
│   ├── terminal/           # CLI interface
│   │   └── cli.py          # Terminal commands
│   ├── web/                # Web interface
│   │   ├── app.py          # FastAPI app
│   │   └── static/         # Frontend assets
│   └── daemon/             # Background service
│       └── service.py      # Daemon logic
├── config/                 # Configuration
│   └── settings.py         # Settings management
├── scripts/                # Utility scripts
├── tests/                  # Unit tests
├── data/                   # User data (created at runtime)
├── requirements.txt        # Python dependencies
├── pyproject.toml          # Project metadata
├── Makefile               # Build commands
└── README.md              # This file
```

## Troubleshooting

### "Module not found" errors

Make sure you're in the project root directory and have installed dependencies:
```bash
pip install -r requirements.txt
```

### API Key Issues

Verify your `.env` file contains a valid `GEMINI_API_KEY`:
```bash
cat .env | grep GEMINI_API_KEY
```

### Permission Errors

If running the daemon, ensure the data directory is writable:
```bash
chmod -R u+w data/
```

## Contributing

Contributions are welcome! Areas for improvement:

- Additional LLM providers (OpenAI, Anthropic, etc.)
- More content sources (HackerNews, Reddit, etc.)
- Enhanced UI/UX
- Better content ranking algorithms
- Mobile app interface
- Voice interface

## License

MIT License - See LICENSE file for details

## Acknowledgments

Built with:
- Google Gemini for AI capabilities
- FastAPI for the web backend
- Rich for terminal UI
- APScheduler for background tasks
