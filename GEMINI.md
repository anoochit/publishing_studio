# Publishing Studio Agent System

A multi-agent orchestration system built with the [Agent Developer Kit (ADK)](https://github.com/google/adk-python) designed to automate the lifecycle of technical publishing—from research and drafting to editing and marketing.

## Project Overview

The system functions as a virtual "Publishing Studio" where a central orchestrator coordinates specialized AI agents. It is built using Gemini models and follows a hierarchical delegation pattern to ensure high-quality, market-ready technical content.

### Core Architecture

- **Orchestration Layer**: The `root_agent` (Senior Executive Editor) manages the end-to-end process and delegates tasks to specialized sub-agents.
- **Specialist Layer**:
    - **`research_agent`**: Conducts market analysis, competitor research, and technical outlining.
    - **`writing_agent`**: Transforms outlines into detailed technical chapters with code blocks and pedagogical sidebars.
    - **`editing_agent`**: Enforces style guides (e.g., Google Developer Documentation Style Guide), ensures technical consistency, and performs quality control.
    - **`marketing_agent`**: Develops promotional strategies and assets.
    - **`analytics_agent`**: Provides data-driven insights and performance metrics.

## Key Files and Directories

- `publishing_studio_agent/`: Contains all agent configurations and logic.
    - `root_agent.yaml`: The main entry point and orchestrator config.
    - `*_agent.yaml`: Individual specialist configurations.
    - `studio_tools.py`: Python tool definitions for filesystem access and command execution.
- `drafts/`: Default output directory for manuscript chapters.
- `analytics/`: Directory for data insights and reports.
- `marketing/`: Directory for promotional assets and strategies.

## Development Conventions

- **Agent Configuration**: Agents are defined in YAML following the ADK `AgentConfig` schema.
- **Tooling**: Custom tools are defined in `publishing_studio_agent/studio_tools.py`. They prioritize safe filesystem operations (`read_file`, `write_file`) and controlled command execution (`execute_command`).
- **File Organization**:
    - Research assets -> `research/` (managed by `research_agent`)
    - Drafts -> `drafts/` (managed by `writing_agent`)
    - Edited content -> `analyst/` (managed by `editing_agent`)

## Running the System

This project requires the Agent Developer Kit (ADK) to be installed.

### Prerequisites
- Python 3.10+
- ADK installed: `pip install google-adk`
- Valid Gemini API Key configured in your environment.

### Execution
To start the orchestration process:
```bash
adk run publishing_studio_agent/root_agent.yaml
```

*Note: The root agent is designed to interact with the local filesystem. Ensure it has the necessary permissions in the project root.*
