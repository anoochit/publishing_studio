# Publishing Studio: User Guide & Example Prompts

Welcome to the **Publishing Studio**, an autonomous multi-agent system for technical book production.

## How to Use

The **Root Agent** is your primary point of contact. You can give it high-level instructions, and it will orchestrate the research, planning, drafting, and marketing phases.

### 🚀 Full Lifecycle Prompts

Use these prompts to run the entire studio from start to finish.

* **"I want to publish a technical book about 'Mastering Kubernetes for Edge Computing'. Run the full studio lifecycle."**
* **"Topic: 'The Art of Writing Clean Python with Gemini API'. Execute the complete Publishing Studio protocol, including research, a full drafting loop, and a marketing plan."**
* **"Transform my idea for 'Next.js 15: The Complete Guide' into a published product. Start with market research and follow through to the performance forecast."**

### 🔍 Research & Planning Only

Use these if you only want to see the initial strategy before committing to a full draft.

* **"Research the 'Rust for WebAssembly' market and generate a 10-chapter technical outline in `research/outline.md`."**
* **"Create a technical Table of Contents and a `writing_plan.md` checklist for a book titled 'Distributed Systems in Go'."**

### ✍️ Targeted Drafting

Use these to focus on specific parts of the book.

* **"Based on the existing `research/outline.md`, draft Chapter 1 and Chapter 2 using the writing sub-agents. Update the progress in `writing_plan.md`."**
* **"I need a deep dive into 'Security in Microservices'. Draft a comprehensive chapter for this and save it to `drafts/`."**

### 📢 Marketing & Analytics

Use these to generate promotional materials for a finished or drafted book.

* **"Read the `research/outline.md` for my book and create a 5-day launch strategy and social media hooks in the `marketing/` folder."**
* **"Based on current market trends and my book outline, provide a performance forecast and sales analytics report."**

## Workspace Structure

All assets are saved in the `workspace/` directory:
* `research/`: Market analysis and the technical `outline.md`.
* `drafts/`: The actual manuscript chapters.
* `marketing/`: Launch strategies, social media posts, and blog drafts.
* `analytics/`: Sales forecasts and performance reports.
