# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Vocode is an open-source library for building voice-based LLM applications. It provides abstractions for creating real-time streaming conversations and deploying voice agents to phone calls, Zoom meetings, and other platforms.

## Essential Development Commands

```bash
# Install dependencies
poetry install

# Run tests
make test

# Lint code (required before commits)
make lint        # Lint all files
make lint_diff   # Lint only changed files

# Type checking (required)
make typecheck      # Check all modules
make typecheck_diff # Check only changed files

# Run examples
make chat                    # Interactive chat agent
make streaming_conversation  # Streaming conversation demo
make turn_based_conversation # Turn-based conversation demo

# Install pre-commit hooks (recommended)
poetry run pre-commit install
```

## Architecture Overview

Vocode conversations consist of five core components that work together:

1. **Transcriber**: Converts speech to text (Deepgram, AssemblyAI, Google, Azure, etc.)
2. **Agent**: Processes text and generates responses (OpenAI, Anthropic, LangChain, etc.)
3. **Synthesizer**: Converts text to speech (ElevenLabs, Azure, Google, Play.ht, etc.)
4. **Input Device**: Captures audio (microphone, phone, file)
5. **Output Device**: Plays audio (speaker, phone, WebSocket)

### Key Directories

- `vocode/streaming/`: Real-time streaming conversation implementation
  - `streaming/agent/`: LLM agent implementations
  - `streaming/synthesizer/`: TTS implementations
  - `streaming/transcriber/`: STT implementations
  - `streaming/telephony/`: Phone call support (Twilio, Vonage)
- `vocode/turn_based/`: Turn-based conversation implementation
- `apps/`: Example applications showcasing different use cases

### Important Patterns

- **Abstract Factory Pattern**: All components (agents, synthesizers, transcribers) use factories for instantiation
- **Pydantic Models**: Configuration is done via strongly-typed Pydantic models (see `vocode/streaming/models/`)
- **Async Workers**: Components communicate via async workers and queues
- **Events System**: Conversation flow managed by events (see `EventsManager`)

## Code Style Requirements

- **Formatting**: Use Black with 100-character line length
- **Type Annotations**: Required for all public functions and methods
- **Imports**: Use absolute imports from `vocode` package
- **Async**: Use `async`/`await` for all I/O operations
- **Error Handling**: Use Sentry integration for error tracking

## Testing

- Tests use pytest with async support
- Fixtures available in `tests/fixtures/`
- Mock external services rather than making real API calls
- Run individual tests with: `pytest tests/path/to/test_file.py::test_function_name`

## Common Tasks

When implementing new components:
1. Create a Pydantic config model in the appropriate `models/` directory
2. Inherit from the appropriate base class (BaseAgent, BaseSynthesizer, etc.)
3. Implement abstract methods
4. Add factory support if needed
5. Write tests using existing fixtures