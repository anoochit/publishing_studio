# Chapter 5: Building Multi-Agent-Like Systems in GenKit

While Chapter 4 explored building individual intelligent agents with GenKit, real-world AI applications often require more complex coordination. This chapter delves into how to construct "multi-agent-like systems" within GenKit by orchestrating multiple flows, implementing sequential and parallel workflows, designing loop-based refinement processes, and fostering collaborative patterns among different GenKit components.

## Section 5.1: Orchestrating Multiple GenKit Flows

At the core of building complex AI systems in GenKit is the ability to chain and combine individual flows. This multi-flow orchestration allows you to break down large problems into smaller, manageable, and reusable AI-powered components.

### Introduction to Multi-Flow Orchestration

Multi-flow orchestration involves creating a "master" flow that coordinates the execution of several "sub-flows." Each sub-flow can be a specialized agent or a module designed to handle a specific task (e.g., summarizing text, performing a calculation, or retrieving data). By orchestrating these, you build a more modular, scalable, and understandable system.

### Sequential Flow Execution

The most straightforward way to combine flows is through sequential execution, where one flow completes its task, and its output becomes the input for the next flow. GenKit's `run` function is central to this, allowing you to invoke another defined flow directly within your current flow.

### Passing Data Between Flows

Effective orchestration relies on clear communication between flows. This is achieved by carefully designing the `inputSchema` and `outputSchema` of each flow. The output of one flow should align with the input expected by the next, ensuring type-safe and predictable data exchange. GenKit's schema validation (Zod for TypeScript, Pydantic for Python) enforces these contracts.

### Error Handling in Chained Flows

When chaining flows, it's important to consider how errors propagate. If a sub-flow fails, the calling flow should be able to catch and handle that error gracefully. You can use standard language-level `try-catch` (TypeScript) or `try-except` (Python) blocks around `genkit.run` calls to manage these scenarios.

#### Example: Article Processing Flow

Let's create an `articleProcessingFlow` that sequentially uses a `summarizationAgentFlow` (from Chapter 4) to summarize an input article and then calculate metrics based on the original and summarized text.

**Node.js/TypeScript**

```typescript
// Node.js/TypeScript - Sequential Flow Execution
import { defineFlow, run } from '@genkit-ai/core';
import { z } from 'zod';
// Assume summarizationAgentFlow is defined as in Chapter 4
// For a runnable example, you'd import it from its file:
// import { summarizationAgentFlow } from './chapter_4_developing_intelligent_agents_with_genkit';

// Placeholder for summarizationAgentFlow if not imported
const summarizationAgentFlow = defineFlow(
  {
    name: 'summarizationAgentFlow',
    inputSchema: z.object({ text: z.string(), length: z.enum(['short', 'medium', 'long']) }),
    outputSchema: z.string(),
  },
  async (input) => {
    // Simplified for example; real implementation from Chapter 4
    return `Summary of (${input.length}): ${input.text.substring(0, 50)}...`;
  }
);

export const articleProcessingFlow = defineFlow(
  {
    name: 'articleProcessingFlow',
    inputSchema: z.object({
      articleText: z.string().describe('The full text of the article to process.'),
      summaryLength: z.enum(['short', 'medium', 'long']).default('medium').describe('Desired length of the summary.'),
    }),
    outputSchema: z.object({
      originalLength: z.number().describe('Length of the original article text.'),
      summary: z.string().describe('The generated summary.'),
      summaryLength: z.number().describe('Length of the generated summary text.'),
    }).describe('Processed article data including summary and lengths.'),
  },
  async (input) => {
    // Step 1: Count original article length
    const originalLength = input.articleText.length;

    // Step 2: Summarize the article using the summarization agent flow
    // The output of summarizationAgentFlow is directly used here.
    const summary = await run(
      summarizationAgentFlow, 
      { text: input.articleText, length: input.summaryLength }
    );

    // Step 3: Count summary length
    const summaryLength = summary.length;

    return {
      originalLength,
      summary,
      summaryLength,
    };
  }
);
```

**Python**

```python
# Python - Sequential Flow Execution
import genkit
from pydantic import BaseModel, Field
from typing import Literal

# Assume summarization_agent_flow is defined as in Chapter 4
# For a runnable example, you'd import it from its file:
# from chapter_4_developing_intelligent_agents_with_genkit import summarization_agent_flow

# Placeholder for summarization_agent_flow if not imported
@genkit.define_flow(name="summarizationAgentFlow", input_schema=BaseModel(text=str, length=Literal["short", "medium", "long"]), output_schema=str)
async def summarization_agent_flow(input: dict):
    # Simplified for example; real implementation from Chapter 4
    return f"Summary of ({input['length']}): {input['text'][:50]}..."

class ArticleProcessingInput(BaseModel):
    article_text: str = Field(description="The full text of the article to process.")
    summary_length: Literal["short", "medium", "long"] = Field(default="medium", description="Desired length of the summary.")

class ArticleProcessingOutput(BaseModel):
    original_length: int = Field(description="Length of the original article text.")
    summary: str = Field(description="The generated summary.")
    summary_length: int = Field(description="Length of the generated summary text.")

@genkit.define_flow(name="articleProcessingFlow", input_schema=ArticleProcessingInput, output_schema=ArticleProcessingOutput)
async def article_processing_flow(input: ArticleProcessingInput):
    # Step 1: Count original article length
    original_length = len(input.article_text)

    # Step 2: Summarize the article using the summarization agent flow
    # The output of summarization_agent_flow is directly used here.
    summary = await genkit.run(
        summarization_agent_flow, 
        input={"text": input.article_text, "length": input.summary_length}
    )

    # Step 3: Count summary length
    summary_length = len(summary)

    return ArticleProcessingOutput(
        original_length=original_length,
        summary=summary,
        summary_length=summary_length,
    )
```

This example clearly illustrates how `genkit.run` is used to invoke a sub-flow (`summarizationAgentFlow`) and how its output is seamlessly passed as data to subsequent steps within `articleProcessingFlow`. This modularity makes complex workflows easier to build, debug, and maintain.

## Section 5.2: Implementing Sequential and Parallel Workflows

Optimizing the execution of your GenKit flows is crucial for performance and responsiveness. You can design workflows to execute steps either sequentially or in parallel, depending on the dependencies between tasks.

### Sequential Workflows

As seen in Section 5.1, sequential workflows execute tasks one after another, where the output of a preceding task often serves as input for the next. This is suitable for tasks with strong dependencies.

### Parallel Workflows

When tasks are independent of each other (i.e., the output of one isn't required for the input of another), they can be executed concurrently to save time. GenKit supports this using language-native concurrency primitives:

*   **Node.js/TypeScript:** `Promise.all` allows you to await multiple promises (which `genkit.run` and `genkit.generate` return) concurrently.
*   **Python:** `asyncio.gather` is used to run multiple awaitable objects (like `genkit.run` and `genkit.generate` calls) in parallel.

### When to Use Sequential vs. Parallel

*   **Sequential:** Use when tasks have strict data dependencies (e.g., summarize an article, then extract keywords from the summary).
*   **Parallel:** Use when tasks are independent and can be performed simultaneously to improve latency (e.g., summarize an article and generate keywords from the *original* article concurrently).

#### Example: Parallel Content Processing

Let's extend our content processing to perform summarization and keyword extraction from the *original* text in parallel.

**Node.js/TypeScript**

```typescript
// Node.js/TypeScript - Parallel Workflow
import { defineFlow, generate, run } from '@genkit-ai/core';
import { gemini } from '@genkit-ai/vertexai'; // Assuming Gemini is configured
import { z } from 'zod';

// Placeholder for summarizationAgentFlow if not imported from Chapter 4
const summarizationAgentFlow = defineFlow(
  {
    name: 'summarizationAgentFlow',
    inputSchema: z.object({ text: z.string(), length: z.enum(['short', 'medium', 'long']) }),
    outputSchema: z.string(),
  },
  async (input) => {
    // Simplified for example; real implementation from Chapter 4
    return `Summary of (${input.length}): ${input.text.substring(0, 50)}...`;
  }
);

export const parallelProcessingFlow = defineFlow(
  {
    name: 'parallelProcessingFlow',
    inputSchema: z.string().describe('The input text for parallel processing.'), // Input text
    outputSchema: z.object({
      summary: z.string().describe('The generated summary.'),
      keywords: z.array(z.string()).describe('Extracted keywords.'),
    }).describe('Output with summary and keywords from parallel processing.'),
  },
  async (text) => {
    // Execute summarization and keyword extraction in parallel
    const [summary, keywordsResponse] = await Promise.all([
      run(summarizationAgentFlow, { text, length: 'medium' }), // Summarize in parallel
      generate({ // Extract keywords in parallel (using a simple generate for demonstration)
        model: gemini,
        prompt: `Extract 5 key keywords from the following text:\n\n${text}`,
        output: { schema: z.array(z.string()).max(5) }, // Expect structured array of strings
      }),
    ]);

    return {
      summary: summary as string, 
      keywords: keywordsResponse.output() as string[], 
    };
  }
);
```

**Python**

```python
# Python - Parallel Workflow
import genkit
from genkit.models import gemini # Assuming Gemini is configured
import asyncio
from pydantic import BaseModel, Field
from typing import List, Literal

# Placeholder for summarization_agent_flow if not imported from Chapter 4
@genkit.define_flow(name="summarizationAgentFlow", input_schema=BaseModel(text=str, length=Literal["short", "medium", "long"]), output_schema=str)
async def summarization_agent_flow(input: dict):
    # Simplified for example; real implementation from Chapter 4
    return f"Summary of ({input['length']}): {input['text'][:50]}..."

class ParallelProcessingOutput(BaseModel):
    summary: str = Field(description="The generated summary.")
    keywords: List[str] = Field(description="Extracted keywords.")

@genkit.define_flow(name="parallelProcessingFlow", input_schema=str, output_schema=ParallelProcessingOutput)
async def parallel_processing_flow(text: str):
    # Execute summarization and keyword extraction in parallel
    summary_task = genkit.run(summarization_agent_flow, input={"text": text, "length": "medium"})
    keywords_task = genkit.generate(
        model=gemini,
        prompt=f"Extract 5 key keywords from the following text:\n\n{text}",
        output=List[str], # Expect a list of strings
    )

    summary, keywords_response = await asyncio.gather(summary_task, keywords_task)

    return ParallelProcessingOutput(
        summary=summary,
        keywords=keywords_response.output()
    )
```

By using `Promise.all` or `asyncio.gather`, both the summarization and keyword extraction tasks are initiated simultaneously. The `parallelProcessingFlow` then waits for both to complete before combining their results. This significantly reduces the total execution time compared to running them sequentially.

## Section 5.3: Loop-based Agent Designs

Some AI tasks, especially those involving refinement, planning, or exploration, benefit from iterative processes. Loop-based agent designs allow a GenKit flow to repeatedly execute a set of operations, incorporating feedback from previous iterations until a desired condition is met.

### Iterative Refinement

Iterative refinement is a powerful technique where an agent generates an initial output, then critically reviews and improves it over multiple cycles. This simulates a human-like process of drafting and editing, leading to higher-quality results.

### Implementing Feedback Loops

Feedback loops are central to iterative refinement. The output of one LLM call (e.g., a generated text) becomes the input for a subsequent LLM call that provides critique or suggestions for improvement. This feedback is then used to revise the original output in the next iteration.

### Stopping Conditions

Crucial to any loop-based design is a clear stopping condition to prevent infinite execution. This could be:

*   **Maximum Iterations:** A predefined limit on how many times the loop can run.
*   **Convergence Criteria:** Stopping when the output meets certain quality metrics or when feedback indicates "no more significant improvements needed."
*   **Time Limit:** A maximum execution time for the loop.

#### Example: Iterative Content Correction Flow

Let's build a flow that iteratively generates and refines a piece of content, using an LLM to provide feedback and then incorporating that feedback into subsequent revisions.

**Node.js/TypeScript**

```typescript
// Node.js/TypeScript - Loop-based Iterative Refinement
import { defineFlow, generate, Message, Role } from '@genkit-ai/core';
import { gemini } from '@genkit-ai/vertexai'; // Assuming Gemini is configured
import { z } from 'zod';

export const iterativeCorrectionFlow = defineFlow(
  {
    name: 'iterativeCorrectionFlow',
    inputSchema: z.object({
      initialPrompt: z.string().describe('The initial request for content generation.'),
      maxIterations: z.number().int().min(1).max(5).default(3).describe('Maximum number of correction iterations.'),
    }),
    outputSchema: z.string().describe('The final, refined content.'),
  },
  async (input) => {
    let currentResponse = '';
    let iteration = 0;
    let feedback = '';

    while (iteration < input.maxIterations) {
      iteration++;
      const messages: Message[] = [
        { role: Role.SYSTEM, content: 'You are an expert content creator. Generate text and then critically review it.' },
        { role: Role.USER, content: `Initial request: ${input.initialPrompt}` },
      ];

      if (currentResponse) {
        messages.push(
          { role: Role.MODEL, content: currentResponse },
          { role: Role.USER, content: `Review the previous response for clarity and accuracy. Provide constructive feedback (e.g., "Improve sentence structure", "Add more detail about X") and then revise the text based on that feedback. Previous feedback was: "${feedback}". If no significant issues, state "No significant issues found."` }
        );
      }

      const llmResponse = await generate({
        model: gemini,
        prompt: messages,
      });

      const fullText = llmResponse.text();
      
      // Simple heuristic for splitting feedback from revised content.
      // In a production system, you'd use structured output for robustness.
      const feedbackMarker = 'Feedback:';
      const revisedContentMarker = 'Revised Content:';

      if (fullText.includes(feedbackMarker) && fullText.includes(revisedContentMarker)) {
        feedback = fullText.substring(fullText.indexOf(feedbackMarker) + feedbackMarker.length, fullText.indexOf(revisedContentMarker)).trim();
        currentResponse = fullText.substring(fullText.indexOf(revisedContentMarker) + revisedContentMarker.length).trim();
      } else {
        // If no explicit markers, assume the whole response is the content for simplicity
        currentResponse = fullText;
        feedback = 'No specific feedback found in this turn.';
      }

      // Check for stopping conditions
      if (!feedback || feedback.toLowerCase().includes('no significant issues') || iteration === input.maxIterations) {
        break; // Exit loop if no more specific feedback or max iterations reached
      }
    }
    return currentResponse;
  }
);
```

**Python**

```python
# Python - Loop-based Iterative Refinement
import genkit
from genkit.models import gemini
from genkit.core.types import Message, Role
from pydantic import BaseModel, Field
from typing import List

class IterativeCorrectionInput(BaseModel):
    initial_prompt: str = Field(description="The initial request for content generation.")
    max_iterations: int = Field(default=3, ge=1, le=5, description="Maximum number of correction iterations.")

@genkit.define_flow(name="iterativeCorrectionFlow", input_schema=IterativeCorrectionInput, output_schema=str)
async def iterative_correction_flow(input: IterativeCorrectionInput):
    current_response = ""
    iteration = 0
    feedback = ""

    while iteration < input.max_iterations:
        iteration += 1
        messages: List[Message] = [
            Message(role=Role.SYSTEM, content='You are an expert content creator. Generate text and then critically review it.'),
            Message(role=Role.USER, content=f"Initial request: {input.initial_prompt}"),
        ]

        if current_response:
            messages.append(Message(role=Role.MODEL, content=current_response))
            messages.append(Message(role=Role.USER, content=f"Review the previous response for clarity and accuracy. Provide constructive feedback (e.g., \"Improve sentence structure\", \"Add more detail about X\") and then revise the text based on that feedback. Previous feedback was: \"{feedback}\". If no significant issues, state \"No significant issues found.\""))

        llm_response = await genkit.generate(
            model=gemini,
            prompt=messages,
        )

        full_text = llm_response.text()
        
        # Simple heuristic for splitting feedback from revised content
        # In a production system, you'd use structured output for robustness.
        feedback_marker = 'Feedback:'
        revised_content_marker = 'Revised Content:'

        if feedback_marker in full_text and revised_content_marker in full_text:
            feedback_start = full_text.find(feedback_marker) + len(feedback_marker)
            revised_content_start = full_text.find(revised_content_marker)
            feedback = full_text[feedback_start:revised_content_start].strip()
            current_response = full_text[revised_content_start + len(revised_content_marker):].strip()
        else:
            # If no explicit markers, assume the whole response is the content for simplicity
            current_response = full_text
            feedback = 'No specific feedback found in this turn.'

        # Check for stopping conditions
        if not feedback or "no significant issues" in feedback.lower() or iteration == input.max_iterations:
            break # Exit loop if no more specific feedback or max iterations reached

    return current_response
```

This `iterativeCorrectionFlow` demonstrates a self-correcting agent. It repeatedly calls the LLM, first for content generation, then for critique, and finally for revision, until a maximum number of iterations is reached or the LLM indicates no further improvements are needed. This pattern is invaluable for tasks requiring high-quality, polished outputs.

## Section 5.4: Collaboration Patterns

Moving beyond individual agent tasks, GenKit can be used to simulate collaboration between different AI components, enabling a division of labor for more complex problems. This section explores patterns for achieving this collaborative behavior.

### Simulating Agent Communication

In GenKit, "communication" between simulated agents primarily occurs through the passing of data between flows or through the results of tool invocations. The `outputSchema` of one flow becomes the `inputSchema` for another, allowing information to flow through the system.

### Supervisor/Worker Pattern

A common collaboration pattern is the "supervisor/worker" model. A main `supervisor` flow orchestrates the overall task, delegating specific sub-tasks to specialized `worker` flows. The supervisor collects results from the workers and synthesizes them into a final output.

### Sequential and Parallel Collaboration

Just like individual operations, collaborative tasks can be executed sequentially or in parallel:

*   **Sequential Collaboration:** Workers perform tasks in a defined order, with each worker building upon the output of the previous one.
*   **Parallel Collaboration:** Multiple workers independently tackle different aspects of a problem concurrently, and their results are later merged by a supervisor or aggregator flow.

#### Example: Research and Report Generation

Let's create a `supervisorReportFlow` that orchestrates a `researchAgentFlow` (a worker to gather information) and a `reportWriterFlow` (another worker to write a report) to generate a comprehensive document on a given topic.

**Node.js/TypeScript**

```typescript
// Node.js/TypeScript - Supervisor/Worker Pattern
import { defineFlow, generate, run } from '@genkit-ai/core';
import { gemini } from '@genkit-ai/vertexai'; // Assuming Gemini is configured
import { z } from 'zod';

// Worker Flow 1: Research Agent
export const researchAgentFlow = defineFlow(
  {
    name: 'researchAgentFlow',
    inputSchema: z.string().describe('The topic to research.'),
    outputSchema: z.string().describe('A summary of research findings.'),
  },
  async (topic) => {
    // Simulate complex research, potentially involving RAG or web search tools
    const researchResult = await generate({
      model: gemini,
      prompt: `Conduct thorough research on the topic: "${topic}". Provide a concise yet comprehensive summary of the key findings, important dates, and notable figures. Ensure accuracy and objectivity.`,
      config: { temperature: 0.4 },
    });
    return researchResult.text();
  }
);

// Worker Flow 2: Report Writer
export const reportWriterFlow = defineFlow(
  {
    name: 'reportWriterFlow',
    inputSchema: z.object({
      topic: z.string().describe('The topic of the report.'),
      researchFindings: z.string().describe('The research findings to base the report on.'),
    }),
    outputSchema: z.string().describe('The generated detailed report.'),
  },
  async (input) => {
    const report = await generate({
      model: gemini,
      prompt: `Based on the following research findings about "${input.topic}", write a detailed, well-structured, and informative report. Include an introduction, main body (incorporating findings), and a conclusion. Research Findings:\n\n${input.researchFindings}`,
      config: { temperature: 0.6 },
    });
    return report.text();
  }
);

// Supervisor Flow: Orchestrates research and report writing
export const supervisorReportFlow = defineFlow(
  {
    name: 'supervisorReportFlow',
    inputSchema: z.string().describe('The main topic for which to generate a report.'), // Main topic
    outputSchema: z.string().describe('The final comprehensive report.'),
  },
  async (topic) => {
    // Step 1: Supervisor delegates research to the researchAgentFlow
    console.log(`Supervisor: Delegating research for "${topic}"...`);
    const researchFindings = await run(researchAgentFlow, topic);
    console.log('Supervisor: Research complete.');

    // Step 2: Supervisor delegates report writing to the reportWriterFlow
    console.log('Supervisor: Delegating report writing...');
    const finalReport = await run(reportWriterFlow, { topic, researchFindings });
    console.log('Supervisor: Report writing complete.');

    return finalReport;
  }
);
```

**Python**

```python
# Python - Supervisor/Worker Pattern
import genkit
from genkit.models import gemini # Assuming Gemini is configured
from pydantic import BaseModel, Field

# Worker Flow 1: Research Agent
@genkit.define_flow(name="researchAgentFlow", input_schema=str, output_schema=str)
async def research_agent_flow(topic: str):
    # Simulate complex research, potentially involving RAG or web search tools
    research_result = await genkit.generate(
        model=gemini,
        prompt=f'Conduct thorough research on the topic: "{topic}". Provide a concise yet comprehensive summary of the key findings, important dates, and notable figures. Ensure accuracy and objectivity.',
        config=genkit.GenerationConfig(temperature=0.4),
    )
    return research_result.text()

# Worker Flow 2: Report Writer
class ReportWriterInput(BaseModel):
    topic: str = Field(description="The topic of the report.")
    research_findings: str = Field(description="The research findings to base the report on.")

@genkit.define_flow(name="reportWriterFlow", input_schema=ReportWriterInput, output_schema=str)
async def report_writer_flow(input: ReportWriterInput):
    report = await genkit.generate(
        model=gemini,
        prompt=f'Based on the following research findings about "{input.topic}", write a detailed, well-structured, and informative report. Include an introduction, main body (incorporating findings), and a conclusion. Research Findings:\n\n{input.research_findings}',
        config=genkit.GenerationConfig(temperature=0.6),
    )
    return report.text()

# Supervisor Flow: Orchestrates research and report writing
@genkit.define_flow(name="supervisorReportFlow", input_schema=str, output_schema=str)
async def supervisor_report_flow(topic: str):
    # Step 1: Supervisor delegates research to the research_agent_flow
    print(f"Supervisor: Delegating research for \"{topic}\"..." )
    research_findings = await genkit.run(research_agent_flow, input=topic)
    print("Supervisor: Research complete.")

    # Step 2: Supervisor delegates report writing to the report_writer_flow
    print("Supervisor: Delegating report writing...")
    final_report = await genkit.run(report_writer_flow, input=ReportWriterInput(topic=topic, research_findings=research_findings))
    print("Supervisor: Report writing complete.")

    return final_report
```

This `supervisorReportFlow` acts as a central orchestrator, demonstrating how a complex task (report generation) can be broken down and delegated to specialized GenKit flows. The explicit `run` calls highlight the sequential nature of this collaboration, where research must be completed before report writing can begin. The clear input/output schemas of each flow ensure the seamless transfer of information between these "collaborating agents."

## Section 5.5: Use Case Deep Dive: Dynamic Content Generator

To solidify our understanding of building multi-agent-like systems, let's construct a comprehensive "Dynamic Content Generator" flow. This agent will combine several techniques learned in previous chapters—multi-flow orchestration, parallel execution, tools, and structured outputs—to create rich content (articles or social media posts) complete with summaries, keywords, and even conceptual image suggestions.

### Breakdown into Sub-Tasks/Sub-Agents

We'll break down the dynamic content generation into several stages, each potentially handled by a dedicated GenKit flow or tool:

1.  **Research & Keyword Extraction:** Gather initial information and identify key terms. (Can be done in parallel for efficiency).
2.  **Content Generation:** Draft the main article or social media post.
3.  **Summarization:** Create a concise summary of the generated content.
4.  **Image Generation (Conceptual):** Suggest or generate an image to accompany the content.

### Design the Overall Orchestration Flow

The `dynamicContentGeneratorFlow` will act as the orchestrator, managing the dependencies and data flow between these stages.

**Node.js/TypeScript**

```typescript
// Node.js/TypeScript - Dynamic Content Generator Flow
import { defineFlow, generate, defineTool, run } from '@genkit-ai/core';
import { gemini } from '@genkit-ai/vertexai'; // Assuming Gemini is configured
import { z } from 'zod';

// Re-using or defining conceptual flows/tools from previous chapters/sections:
// - researchAgentFlow (from 5.4)
// - summarizationAgentFlow (from 4.2)

// Placeholder for an image generation tool (conceptual)
export const imageGeneratorTool = defineTool(
  {
    name: 'imageGenerator',
    description: 'Generates an image URL based on a textual description.',
    inputSchema: z.object({
      description: z.string().describe('A textual description for the image to be generated.'),
    }),
    outputSchema: z.string().describe('URL of the generated image.'), // URL or base64 of the image
  },
  async (input) => {
    console.log(`Simulating image generation for: "${input.description}"`);
    // In a real scenario, this would call an external image generation API (e.g., DALL-E, Imagen)
    return `https://example.com/generated-image-${Date.now()}.png`;
  }
);

export const dynamicContentGeneratorFlow = defineFlow(
  {
    name: 'dynamicContentGeneratorFlow',
    inputSchema: z.object({
      topic: z.string().describe('The main topic for content generation.'),
      audience: z.string().optional().describe('The target audience for the content.'),
      format: z.enum(['article', 'social_post']).default('article').describe('Desired content format.'),
    }),
    outputSchema: z.object({
      content: z.string().describe('The main generated content.'),
      summary: z.string().describe('A summary of the content.'),
      keywords: z.array(z.string()).describe('Extracted keywords.'),
      imageUrl: z.string().optional().describe('Optional URL of a generated image.'),
    }).describe('Comprehensive output of the dynamic content generator.'),
  },
  async (input) => {
    // Stage 1: Research and Keyword Extraction (Parallel Execution)
    console.log('Starting parallel research and keyword extraction...');
    const [researchFindings, keywordsResponse] = await Promise.all([
      run(researchAgentFlow, input.topic), // Run research concurrently
      generate({
        model: gemini,
        prompt: `Extract 5-7 relevant keywords (comma-separated) for a ${input.format} about "${input.topic}" for ${input.audience || 'a general audience'}.`,
        output: { schema: z.array(z.string()).max(7) },
      }),
    ]);
    const keywords = keywordsResponse.output() as string[];
    console.log('Research and keywords extracted.');

    // Stage 2: Content Generation (Conditional based on format)
    let generatedContent = '';
    console.log(`Generating content in "${input.format}" format...`);
    if (input.format === 'article') {
      const articlePrompt = `Write a detailed and engaging article about "${input.topic}" for ${input.audience || 'a general audience'} based on these findings: ${researchFindings}. Incorporate these keywords naturally: ${keywords.join(', ')}.`;
      const articleResponse = await generate({ model: gemini, prompt: articlePrompt, config: { temperature: 0.7 } });
      generatedContent = articleResponse.text();
    } else if (input.format === 'social_post') {
      const socialPostPrompt = `Create a catchy and shareable social media post (max 280 characters) about "${input.topic}" for ${input.audience || 'a general audience'} based on these findings: ${researchFindings}. Use relevant hashtags from: ${keywords.join(', ')}.`;
      const socialPostResponse = await generate({ model: gemini, prompt: socialPostPrompt, config: { temperature: 0.8 } });
      generatedContent = socialPostResponse.text();
    }
    console.log('Main content generated.');

    // Stage 3: Summarization
    console.log('Generating summary...');
    const summary = await run(summarizationAgentFlow, { text: generatedContent, length: 'short' });
    console.log('Summary generated.');

    // Stage 4: Image Generation (Conditional)
    let imageUrl: string | undefined;
    if (input.format === 'article') { // Only generate image for articles in this example
      console.log('Generating image description and image...');
      const imageDescriptionPrompt = `Generate a concise, descriptive phrase for an image that would perfectly accompany an article about "${input.topic}" for ${input.audience || 'a general audience'}.`;
      const imageDescriptionResponse = await generate({ model: gemini, prompt: imageDescriptionPrompt, config: { temperature: 0.6 } });
      const imageDescription = imageDescriptionResponse.text();

      imageUrl = await imageGeneratorTool.run({ description: imageDescription });
      console.log('Image generated.');
    }

    return {
      content: generatedContent,
      summary: summary as string,
      keywords,
      imageUrl,
    };
  }
);
```

**Python**

```python
# Python - Dynamic Content Generator Flow
import genkit
from genkit.models import gemini # Assuming Gemini is configured
from pydantic import BaseModel, Field
from typing import List, Literal, Optional
import asyncio
import time

# Re-using or defining conceptual flows/tools from previous chapters/sections:
# from chapter_4_developing_intelligent_agents_with_genkit import summarization_agent_flow
# from chapter_5_building_multi_agent_like_systems_in_genkit import research_agent_flow

# Placeholder for summarization_agent_flow if not imported
@genkit.define_flow(name="summarizationAgentFlow", input_schema=BaseModel(text=str, length=Literal["short", "medium", "long"]), output_schema=str)
async def summarization_agent_flow(input: dict):
    return f"Summary of ({input['length']}): {input['text'][:50]}..."

# Placeholder for research_agent_flow if not imported
@genkit.define_flow(name="researchAgentFlow", input_schema=str, output_schema=str)
async def research_agent_flow(topic: str):
    return f'Simulated research findings for "{topic}". Key points: Point 1, Point 2.'

# Placeholder for an image generation tool (conceptual)
@genkit.define_tool(name="imageGenerator", description="Generates an image URL based on a textual description.")
def image_generator_tool(description: str) -> str:
    print(f"Simulating image generation for: {description}")
    # In a real scenario, this would call an external image generation API (e.g., DALL-E, Imagen)
    return f"https://example.com/generated-image-{int(time.time())}.png"

class DynamicContentInput(BaseModel):
    topic: str = Field(description="The main topic for content generation.")
    audience: Optional[str] = Field(None, description="The target audience for the content.")
    format: Literal["article", "social_post"] = Field("article", description="Desired content format.")

class DynamicContentOutput(BaseModel):
    content: str = Field(description="The main generated content.")
    summary: str = Field(description="A summary of the content.")
    keywords: List[str] = Field(description="Extracted keywords.")
    image_url: Optional[str] = Field(None, description="Optional URL of a generated image.")

@genkit.define_flow(name="dynamicContentGeneratorFlow", input_schema=DynamicContentInput, output_schema=DynamicContentOutput)
async def dynamic_content_generator_flow(input: DynamicContentInput):
    # Stage 1: Research and Keyword Extraction (Parallel Execution)
    print('Starting parallel research and keyword extraction...')
    research_task = genkit.run(research_agent_flow, input=input.topic)
    keywords_task = genkit.generate(
        model=gemini,
        prompt=f'Extract 5-7 relevant keywords (comma-separated) for a {input.format} about "{input.topic}" for {input.audience or "a general audience"}.',
        output=List[str],
    )
    research_findings, keywords_response = await asyncio.gather(research_task, keywords_task)
    keywords = keywords_response.output()
    print('Research and keywords extracted.')

    # Stage 2: Content Generation (Conditional based on format)
    generated_content = ''
    print(f'Generating content in "{input.format}" format...')
    if input.format == 'article':
        article_prompt = f'Write a detailed and engaging article about "{input.topic}" for {input.audience or "a general audience"} based on these findings: {research_findings}. Incorporate these keywords naturally: {", ".join(keywords)}.'
        article_response = await genkit.generate(model=gemini, prompt=article_prompt, config=genkit.GenerationConfig(temperature=0.7))
        generated_content = article_response.text()
    elif input.format == 'social_post':
        social_post_prompt = f'Create a catchy and shareable social media post (max 280 characters) about "{input.topic}" for {input.audience or "a general audience"} based on these findings: {research_findings}. Use relevant hashtags from: {", ".join(keywords)}.'
        social_post_response = await genkit.generate(model=gemini, prompt=social_post_prompt, config=genkit.GenerationConfig(temperature=0.8))
        generated_content = social_post_response.text()
    print('Main content generated.')

    # Stage 3: Summarization
    print('Generating summary...')
    summary = await genkit.run(summarization_agent_flow, input={"text": generated_content, "length": "short"})
    print('Summary generated.')

    # Stage 4: Image Generation (Conditional)
    image_url: Optional[str] = None
    if input.format == 'article': # Only generate image for articles in this example
        print('Generating image description and image...')
        image_description_prompt = f'Generate a concise, descriptive phrase for an image that would perfectly accompany an article about "{input.topic}" for {input.audience or "a general audience"}.'
        image_description_response = await genkit.generate(model=gemini, prompt=image_description_prompt, config=genkit.GenerationConfig(temperature=0.6))
        image_description = image_description_response.text()

        image_url = image_generator_tool(description=image_description) # Directly call tool
        print('Image generated.')

    return DynamicContentOutput(
        content=generated_content,
        summary=summary,
        keywords=keywords,
        image_url=image_url,
    )
```

This `dynamicContentGeneratorFlow` orchestrates several GenKit components to produce a complex output. It leverages:

*   **Parallel execution** (`asyncio.gather` / `Promise.all`) for independent tasks like research and keyword extraction.
*   **Sequential execution** (`genkit.run`) to ensure content is generated before summarization.
*   **Conditional logic** to tailor content generation and image generation based on the desired `format`.
*   **Custom tools** (`imageGeneratorTool`) to extend capabilities beyond LLM text generation.
*   **Structured outputs** for keywords and the final content object.

This robust example demonstrates how to build a powerful multi-stage agent using GenKit's flexible and observable architecture. By combining these patterns, you can create highly capable AI systems that automate complex workflows and generate rich, context-aware content.

## Summary

This chapter significantly expanded our understanding of building advanced AI applications with GenKit by focusing on multi-agent-like systems. We learned how to orchestrate multiple GenKit flows, employing both sequential and parallel execution patterns for efficiency. We explored loop-based designs for iterative refinement and feedback, crucial for tasks requiring high-quality, self-corrected outputs. Furthermore, we examined collaboration patterns, demonstrating how different flows can act as specialized "workers" under a "supervisor" flow. Finally, the use case deep dive into a Dynamic Content Generator showcased the integration of all these concepts into a single, powerful multi-stage agent. With these advanced orchestration techniques, you are now well-equipped to design and implement highly modular, scalable, and intelligent AI systems using GenKit.
