# GEMINI.md: Publishing Studio Context

## Project Overview

Publishing Studio is an autonomous multi-agent system built on the **Agent Developer Kit (ADK)**. It manages the complete lifecycle of technical book production, from market research and outlining to drafting, editing, marketing, and performance analytics.

### Architecture

The system follows a hierarchical orchestration model:

- **Root Orchestrator (`root_agent.yaml`)**: The "Executive Editor" that coordinates the end-to-end workflow.
- **Research Phase**: Gathers market intelligence and generates a technical outline.
- **Writing Phase**: Concurrently drafts front-end, back-end, and DevOps sections.
- **Editing Phase**: Refines drafts for clarity and technical accuracy.
- **Marketing Phase**: Generates launch strategies and social media assets.
- **Analytics Phase**: Forecasts performance and ROI.

### Core Technologies

- **Agent Developer Kit (ADK)**: Framework for multi-agent coordination.
- **Gemini 3.1 Pro**: The primary model for orchestration and content generation.
- **Python**: Custom tools for filesystem and shell interaction.
- **Markdown**: Used for all generated content (outlines, drafts, reports).

## Building and Running

### Prerequisites

- Python 3.10+
- [Agent Developer Kit (ADK)](https://google.github.io/adk-docs/)
- Google Gemini API Key (set in environment)

### Installation

```bash
pip install google-adk
```

### Running the Studio

To launch the interactive ADK web interface:

```bash
adk web
```

Or use the ADK CLI for specific prompts:

```bash
Research 'Modern Cloud Native Architecture' and draft an outline.
```

## Development Conventions

### Sandbox & Security

- **Strict Sandbox Policy**: All filesystem operations (read, write, execute) MUST be restricted to the `workspace/` directory.
- **Tool Resolution**: Use `agents.studio_tools` for all file and command operations. These tools automatically enforce the workspace boundary.

### Agent Configuration

- **YAML-Based**: Agents are defined in `.yaml` files in the `agents/` directory.
- **Hierarchical Delegation**: The `root_agent` handles high-level logic and delegates specialized tasks to sub-agents defined in `sub_agents`.
- **Tool Injection**: Tools are registered globally or per agent in the `tools` section of the YAML config.

### Workspace Structure

- `workspace/research/`: Market analysis and `outline.md`.
- `workspace/drafts/`: Raw manuscript chapters.
- `workspace/marketing/`: Promotional assets and launch plans.
- `workspace/analytics/`: ROI forecasts and performance metrics.

### Technical Standards

- **Iterative Drafting**: The `root_agent` uses a drafting loop to cross-reference existing files in `workspace/drafts/` with the `writing_plan.md`.
- **Consistency**: The `editing_agent` is responsible for unifying the tone and style across parallel-drafted chapters.
