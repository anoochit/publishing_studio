# Publishing Studio: Agentic Instruction Context

Publishing Studio is an autonomous multi-agent system built on the **Agent Developer Kit (ADK)** for technical book production. This document provides critical architectural context and development standards.

## 🏗️ Project Overview

- **Core Technology**: Python 3.10+, Google Gemini API, [Agent Developer Kit (ADK)](https://google.github.io/adk-docs/).
- **Primary Model**: `gemini-3.1-pro-preview` (configured in `agents/root_agent.yaml`).
- **Goal**: End-to-end automation of technical publishing: Research → Writing → Editing → Marketing → Analytics.

## 🛠️ Architecture & Orchestration

The system uses a hierarchical model with specialized agents defined in `agents/*.yaml`.

### Orchestration Tiers

1. **Root Orchestrator (`root_agent.yaml`)**: Acts as the "Executive Editor." Coordinates the end-to-end lifecycle.
2. **Phase Agents**:
    - `research_agent.yaml` (**Sequential**): `research_gatherer` → `research_processor`.
    - `writing_phase.yaml` (**Parallel**): Concurrent drafting by `writer_front_end`, `writer_back_end`, and `writer_devops`.
    - `editing_agent.yaml`: Refinement and technical accuracy check.
    - `marketing_agent.yaml` (**Sequential**): `market_trend_researcher` → `marketing_strategist`.
    - `analytics_agent.yaml` (**Sequential**): `market_stats_gatherer` → `performance_analyst`.

### Custom Tools (`agents/studio_tools.py`)

- `read_file(path)`: Securely reads from the `workspace/` sandbox.
- `write_file(path, content)`: Writes content within the `workspace/` sandbox.
- `execute_command(command)`: Runs shell commands (e.g., tests, builds) inside the `workspace/` directory.

## 🛡️ Development & Safety Conventions

- **Sandbox Policy**: **CRITICAL**. All file operations (read/write/execute) MUST be performed within the `workspace/` directory. The `studio_tools.py` module enforces this via path resolution and security checks.
- **Agent Configuration**: New agents or behavioral changes should be defined in the YAML configs under `agents/`.
- **Context Flow**: Ensure the output of one phase (e.g., the research outline) is passed as context to the next phase (e.g., the writing agents).

## 🚀 Key Commands

- **Install Dependencies**: `pip install google-adk`
- **Run the Studio**: `adk run agents --input "Your book topic here"`
- **Format Tools**: `black agents/studio_tools.py` (standard Python formatting)

## 📁 Directory Structure

- `agents/`: Contains all agent YAML configurations and Python tool definitions.
- `workspace/`: The runtime sandbox where research, drafts, and assets are stored.
  - `workspace/research/`: Market intelligence and outlines.
  - `workspace/drafts/`: Manuscript drafts.
  - `workspace/marketing/`: Promotional assets and plans.
  - `workspace/analytics/`: Performance forecasts.
