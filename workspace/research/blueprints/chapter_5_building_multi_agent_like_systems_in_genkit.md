# Chapter 5: Building Multi-Agent-Like Systems in GenKit
**Target File Name:** `chapter_5_building_multi_agent_like_systems_in_genkit.md`

## Section 5.1: Orchestrating Multiple GenKit Flows
### Roadmap:
- **Introduction to Multi-Flow Orchestration:** Explain the concept of chaining and combining individual GenKit flows to achieve larger, more complex tasks.
- **Sequential Flow Execution:** Demonstrate how to call one flow from another (`genkit.run` with a flow).
- **Passing Data Between Flows:** Techniques for structuring input and output schemas to facilitate data exchange.
- **Error Handling in Chained Flows:** Strategies for managing and propagating errors across multiple flows.

### Required Technical Concepts/APIs:
- `genkit.defineFlow`
- `genkit.run` (to invoke other flows)
- Input/Output schemas (Zod/Pydantic)

### Code Snippets:
```typescript
// Node.js/TypeScript - Sequential Flow Execution
import { defineFlow, run } from '@genkit-ai/core';
import { z } from 'zod';

// Assume summarizationAgentFlow is defined as in Chapter 4
// import { summarizationAgentFlow } from './chapter_4_agents';

export const articleProcessingFlow = defineFlow(
  {
    name: 'articleProcessingFlow',
    inputSchema: z.object({
      articleText: z.string(),
      summaryLength: z.enum(['short', 'medium', 'long']).default('medium'),
    }),
    outputSchema: z.object({
      originalLength: z.number(),
      summary: z.string(),
      summaryLength: z.number(),
    }),
  },
  async (input) => {
    // Step 1: Count original article length
    const originalLength = input.articleText.length;

    // Step 2: Summarize the article using the summarization agent flow
    const summary = await run(
      summarizationAgentFlow, // Call another defined flow
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
```python
# Python - Sequential Flow Execution
import genkit
from pydantic import BaseModel
from typing import Literal

# Assume summarization_agent_flow is defined as in Chapter 4
# from .chapter_4_agents import summarization_agent_flow

class ArticleProcessingInput(BaseModel):
    article_text: str
    summary_length: Literal["short", "medium", "long"] = "medium"

class ArticleProcessingOutput(BaseModel):
    original_length: int
    summary: str
    summary_length: int

@genkit.define_flow(name="articleProcessingFlow", input_schema=ArticleProcessingInput, output_schema=ArticleProcessingOutput)
async def article_processing_flow(input: ArticleProcessingInput):
    # Step 1: Count original article length
    original_length = len(input.article_text)

    # Step 2: Summarize the article using the summarization agent flow
    summary = await genkit.run(
        summarization_agent_flow, # Call another defined flow
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

### Target Depth and Developer Instructions:
- Provide a clear example of one flow calling another using `genkit.run`. Emphasize how input and output schemas facilitate data transfer and maintain type safety. Explain the benefits for modularity and reusability. Use both TypeScript and Python examples.

## Section 5.2: Implementing Sequential and Parallel Workflows
### Roadmap:
- **Sequential Workflows:** Reiterate and expand on chaining flows/operations in a strict order.
- **Parallel Workflows:** Introduce the concept of executing multiple operations or flows concurrently.
- **`Promise.all` (Node.js/TypeScript) / `asyncio.gather` (Python):** Demonstrate how to run multiple `genkit.run` or `genkit.generate` calls in parallel.
- **When to Use Sequential vs. Parallel:** Discuss performance implications and decision criteria.

### Required Technical Concepts/APIs:
- `genkit.run`
- `genkit.generate`
- `Promise.all` (TypeScript/Node.js)
- `asyncio.gather` (Python)

### Code Snippets:
```typescript
// Node.js/TypeScript - Parallel Workflow
import { defineFlow, generate, run } from '@genkit-ai/core';
import { gemini } from '@genkit-ai/vertexai';
import { z } from 'zod';

// Assume summarizationAgentFlow and keywordExtractionAgentFlow (a new simple flow)
// export const keywordExtractionAgentFlow = defineFlow(...)
// import { summarizationAgentFlow } from './chapter_4_agents';

export const parallelProcessingFlow = defineFlow(
  {
    name: 'parallelProcessingFlow',
    inputSchema: z.string(), // Input text
    outputSchema: z.object({
      summary: z.string(),
      keywords: z.array(z.string()),
    }),
  },
  async (text) => {
    const [summary, keywordsResponse] = await Promise.all([
      run(summarizationAgentFlow, { text, length: 'medium' }), // Summarize in parallel
      generate({ // Extract keywords in parallel (using a simple generate for demonstration)
        model: gemini,
        prompt: `Extract 5 key keywords from the following text:\n\n${text}`,
        output: { schema: z.array(z.string()).max(5) },
      }),
    ]);

    return {
      summary: summary as string, // Cast as summarizationAgentFlow returns string
      keywords: keywordsResponse.output() as string[], // Cast output of structured generation
    };
  }
);
```
```python
# Python - Parallel Workflow
import genkit
from genkit.models import gemini
import asyncio
from pydantic import BaseModel
from typing import List

# Assume summarization_agent_flow is defined as in Chapter 4
# from .chapter_4_agents import summarization_agent_flow

class ParallelProcessingOutput(BaseModel):
    summary: str
    keywords: List[str]

@genkit.define_flow(name="parallelProcessingFlow", input_schema=str, output_schema=ParallelProcessingOutput)
async def parallel_processing_flow(text: str):
    summary_task = genkit.run(summarization_agent_flow, input={"text": text, "length": "medium"})
    keywords_task = genkit.generate(
        model=gemini,
        prompt=f"Extract 5 key keywords from the following text:\n\n{text}",
        output=List[str],
    )

    summary, keywords = await asyncio.gather(summary_task, keywords_task)

    return ParallelProcessingOutput(
        summary=summary,
        keywords=keywords.output()
    )
```

### Target Depth and Developer Instructions:
- Provide a clear example of using `Promise.all` (JS/TS) or `asyncio.gather` (Python) to run multiple GenKit operations/flows concurrently. Explain the syntax and how to handle the results. Discuss when parallel execution is beneficial for performance and responsiveness. Use both TypeScript and Python examples.

## Section 5.3: Loop-based Agent Designs
### Roadmap:
- **Iterative Refinement:** Explain how agents can use loops to refine outputs, perform multi-step reasoning, or explore options.
- **Implementing Feedback Loops:** Designing flows where the output of one step informs the input of a subsequent, repeated step.
- **Stopping Conditions:** Crucial aspects of defining exit criteria for loops to prevent infinite execution.
- **Example: Iterative Content Generation/Correction:** An agent that generates content and then self-critiques/corrects it in a loop.

### Required Technical Concepts/APIs:
- `genkit.defineFlow`
- `genkit.generate` (for generation and critique)
- Conditional logic within flows (`if/else`, `while`)

### Code Snippets:
```typescript
// Node.js/TypeScript - Loop-based Iterative Refinement
import { defineFlow, generate, Message, Role } from '@genkit-ai/core';
import { gemini } from '@genkit-ai/vertexai';
import { z } from 'zod';

export const iterativeCorrectionFlow = defineFlow(
  {
    name: 'iterativeCorrectionFlow',
    inputSchema: z.object({
      initialPrompt: z.string(),
      maxIterations: z.number().int().min(1).max(5).default(3),
    }),
    outputSchema: z.string(),
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
          { role: Role.USER, content: `Review the previous response for clarity and accuracy. Provide constructive feedback and then revise the text based on that feedback. Previous feedback: ${feedback}` }
        );
      }

      const llmResponse = await generate({
        model: gemini,
        prompt: messages,
      });

      const fullText = llmResponse.text();
      // Simple heuristic for splitting feedback from revised content
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

      if (!feedback || feedback.includes('no significant issues') || iteration === input.maxIterations) {
        break; // Exit loop if no more specific feedback or max iterations reached
      }
    }
    return currentResponse;
  }
);
```
```python
# Python - Loop-based Iterative Refinement
import genkit
from genkit.models import gemini
from genkit.core.types import Message, Role
from pydantic import BaseModel
from typing import List

class IterativeCorrectionInput(BaseModel):
    initial_prompt: str
    max_iterations: int = 3 # Default to 3 iterations

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
            messages.append(Message(role=Role.USER, content=f"Review the previous response for clarity and accuracy. Provide constructive feedback and then revise the text based on that feedback. Previous feedback: {feedback}"))

        llm_response = await genkit.generate(
            model=gemini,
            prompt=messages,
        )

        full_text = llm_response.text()
        
        # Simple heuristic for splitting feedback from revised content
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


        if not feedback or "no significant issues" in feedback.lower() or iteration == input.max_iterations:
            break # Exit loop if no more specific feedback or max iterations reached

    return current_response
```

### Target Depth and Developer Instructions:
- Provide a concrete example of a loop-based flow for iterative refinement, such as self-correction in content generation. Explain how `while` loops are used and the importance of a clear stopping condition. Demonstrate how to build the prompt dynamically within the loop to include previous outputs and feedback. Use both TypeScript and Python examples.

## Section 5.4: Collaboration Patterns
### Roadmap:
- **Simulating Agent Communication:** How to pass information between different GenKit flows or tools to simulate collaborative behavior.
- **Supervisor/Worker Pattern:** Designing a main flow (supervisor) that delegates tasks to specialized sub-flows (workers).
- **Sequential Collaboration:** Agents working in a predefined order, each building on the output of the previous one.
- **Parallel Collaboration:** Agents working on different parts of a problem concurrently, with results being merged.
- **Example: Research and Report Generation:** A flow where one "agent" researches a topic, and another "agent" writes a report based on the research.

### Required Technical Concepts/APIs:
- `genkit.defineFlow`
- `genkit.run` (for invoking sub-flows)
- Input/Output schemas for clear interfaces.
- `genkit.generate` (for LLM-driven decision making and content creation)

### Code Snippets:
```typescript
// Node.js/TypeScript - Supervisor/Worker Pattern
import { defineFlow, generate, run } from '@genkit-ai/core';
import { gemini } from '@genkit-ai/vertexai';
import { z } from 'zod';

// Assume a simple researchAgentFlow
export const researchAgentFlow = defineFlow(
  {
    name: 'researchAgentFlow',
    inputSchema: z.string(), // Research topic
    outputSchema: z.string(), // Research summary/findings
  },
  async (topic) => {
    // Simulate complex research, perhaps involving RAG or web search in a real scenario
    const researchResult = await generate({
      model: gemini,
      prompt: `Conduct research on the topic: "${topic}". Provide a concise summary of key findings.`,
    });
    return researchResult.text();
  }
);

// Assume a simple reportWriterFlow
export const reportWriterFlow = defineFlow(
  {
    name: 'reportWriterFlow',
    inputSchema: z.object({
      topic: z.string(),
      researchFindings: z.string(),
    }),
    outputSchema: z.string(), // Generated report
  },
  async (input) => {
    const report = await generate({
      model: gemini,
      prompt: `Based on the following research findings about "${input.topic}", write a detailed report:\n\nResearch Findings:\n${input.researchFindings}`,
    });
    return report.text();
  }
);

export const supervisorReportFlow = defineFlow(
  {
    name: 'supervisorReportFlow',
    inputSchema: z.string(), // Main topic
    outputSchema: z.string(), // Final comprehensive report
  },
  async (topic) => {
    // Supervisor delegates research to the researchAgentFlow
    const researchFindings = await run(researchAgentFlow, topic);

    // Supervisor delegates report writing to the reportWriterFlow
    const finalReport = await run(reportWriterFlow, { topic, researchFindings });

    return finalReport;
  }
);
```
```python
# Python - Supervisor/Worker Pattern
import genkit
from genkit.models import gemini
from pydantic import BaseModel

# Assume a simple research_agent_flow
@genkit.define_flow(name="researchAgentFlow", input_schema=str, output_schema=str)
async def research_agent_flow(topic: str):
    # Simulate complex research
    research_result = await genkit.generate(
        model=gemini,
        prompt=f'Conduct research on the topic: "{topic}". Provide a concise summary of key findings.',
    )
    return research_result.text()

# Assume a simple report_writer_flow
class ReportWriterInput(BaseModel):
    topic: str
    research_findings: str

@genkit.define_flow(name="reportWriterFlow", input_schema=ReportWriterInput, output_schema=str)
async def report_writer_flow(input: ReportWriterInput):
    report = await genkit.generate(
        model=gemini,
        prompt=f'Based on the following research findings about "{input.topic}", write a detailed report:\n\nResearch Findings:\n{input.research_findings}',
    )
    return report.text()

@genkit.define_flow(name="supervisorReportFlow", input_schema=str, output_schema=str)
async def supervisor_report_flow(topic: str):
    # Supervisor delegates research to the research_agent_flow
    research_findings = await genkit.run(research_agent_flow, input=topic)

    # Supervisor delegates report writing to the report_writer_flow
    final_report = await genkit.run(report_writer_flow, input=ReportWriterInput(topic=topic, research_findings=research_findings))

    return final_report
```

### Target Depth and Developer Instructions:
- Provide a full, runnable example demonstrating a supervisor flow orchestrating two worker flows (e.g., a research agent and a report writing agent). Explain how data flows between these collaborative entities. Discuss the benefits of this modular approach for complex tasks. Use both TypeScript and Python examples.

## Section 5.5: Use Case Deep Dive
### Roadmap:
- **Choose a Complex Multi-Stage Agent:** Select one of the suggested use cases (e.g., an intelligent travel planner, a dynamic content generator).
- **Breakdown into Sub-Tasks/Sub-Agents:** Deconstruct the complex problem into manageable GenKit flows and tools.
- **Design the Overall Orchestration Flow:** Map out how the various sub-flows and tools will interact.
- **Implement Key Components:** Provide code snippets for the most illustrative parts of the multi-stage agent.
- **Demonstrate End-to-End Execution:** Explain how the entire system works together.

### Required Technical Concepts/APIs:
- All concepts from previous sections: `defineFlow`, `defineTool`, `generate`, `run`, `defineRetriever`, schemas, advanced prompting, parallel execution.

### Code Snippets:
```typescript
// Node.js/TypeScript - Conceptual outline for a dynamic content generator

// Assume existing flows/tools:
// - summarizationAgentFlow (from Chapter 4)
// - researchAgentFlow (from 5.4)
// - keywordExtractionAgentFlow (simplified: uses generate for keywords)
// - imageGeneratorTool (new, conceptual tool for image generation)

// Placeholder for an image generation tool (conceptual)
export const imageGeneratorTool = defineTool(
  {
    name: 'imageGenerator',
    description: 'Generates an image based on a textual description.',
    inputSchema: z.object({
      description: z.string(),
    }),
    outputSchema: z.string(), // URL or base64 of the image
  },
  async (input) => {
    console.log(`Generating image for: ${input.description}`);
    // In a real scenario, this would call an image generation API (e.g., DALL-E, Imagen)
    return `https://example.com/generated-image-${Date.now()}.png`;
  }
);


export const dynamicContentGeneratorFlow = defineFlow(
  {
    name: 'dynamicContentGeneratorFlow',
    inputSchema: z.object({
      topic: z.string(),
      audience: z.string().optional(),
      format: z.enum(['article', 'social_post']).default('article'),
    }),
    outputSchema: z.object({
      content: z.string(),
      summary: z.string(),
      keywords: z.array(z.string()),
      imageUrl: z.string().optional(),
    }),
  },
  async (input) => {
    // Stage 1: Research and Keyword Extraction (Parallel)
    const [researchFindings, keywordsResponse] = await Promise.all([
      run(researchAgentFlow, input.topic),
      generate({
        model: gemini,
        prompt: `Extract 5-7 relevant keywords for a ${input.format} about "${input.topic}" for ${input.audience || 'a general audience'}.`,
        output: { schema: z.array(z.string()).max(7) },
      }),
    ]);
    const keywords = keywordsResponse.output() as string[];

    // Stage 2: Content Generation
    let generatedContent = '';
    if (input.format === 'article') {
      const articlePrompt = `Write a detailed article about "${input.topic}" for ${input.audience || 'a general audience'} based on these findings: ${researchFindings}. Incorporate these keywords: ${keywords.join(', ')}.`;
      const articleResponse = await generate({ model: gemini, prompt: articlePrompt });
      generatedContent = articleResponse.text();
    } else if (input.format === 'social_post') {
      const socialPostPrompt = `Create a catchy social media post about "${input.topic}" for ${input.audience || 'a general audience'} based on these findings: ${researchFindings}. Use relevant hashtags from: ${keywords.join(', ')}.`;
      const socialPostResponse = await generate({ model: gemini, prompt: socialPostPrompt });
      generatedContent = socialPostResponse.text();
    }

    // Stage 3: Summarization
    const summary = await run(summarizationAgentFlow, { text: generatedContent, length: 'short' });

    // Stage 4: Image Generation (Conditional)
    let imageUrl: string | undefined;
    if (input.format === 'article') { // Only generate image for articles for this example
      const imageDescriptionPrompt = `Generate a concise, descriptive phrase for an image that would accompany an article about "${input.topic}" for ${input.audience || 'a general audience'}.`;
      const imageDescriptionResponse = await generate({ model: gemini, prompt: imageDescriptionPrompt });
      const imageDescription = imageDescriptionResponse.text();

      imageUrl = await imageGeneratorTool.run({ description: imageDescription });
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
```python
# Python - Conceptual outline for a dynamic content generator
import genkit
from genkit.models import gemini
from pydantic import BaseModel
from typing import List, Literal, Optional
import asyncio

# Assume existing flows/tools:
# - summarization_agent_flow (from Chapter 4)
# - research_agent_flow (from 5.4)
# - image_generator_tool (new, conceptual tool for image generation)

# Placeholder for an image generation tool (conceptual)
@genkit.define_tool(name="imageGenerator", description="Generates an image based on a textual description.")
def image_generator_tool(description: str) -> str:
    print(f"Generating image for: {description}")
    # In a real scenario, this would call an image generation API (e.g., DALL-E, Imagen)
    import time
    return f"https://example.com/generated-image-{int(time.time())}.png"

class DynamicContentInput(BaseModel):
    topic: str
    audience: Optional[str] = None
    format: Literal["article", "social_post"] = "article"

class DynamicContentOutput(BaseModel):
    content: str
    summary: str
    keywords: List[str]
    image_url: Optional[str] = None

@genkit.define_flow(name="dynamicContentGeneratorFlow", input_schema=DynamicContentInput, output_schema=DynamicContentOutput)
async def dynamic_content_generator_flow(input: DynamicContentInput):
    # Stage 1: Research and Keyword Extraction (Parallel)
    research_task = genkit.run(research_agent_flow, input=input.topic)
    keywords_task = genkit.generate(
        model=gemini,
        prompt=f'Extract 5-7 relevant keywords for a {input.format} about "{input.topic}" for {input.audience or "a general audience"}.',
        output=List[str],
    )
    research_findings, keywords_response = await asyncio.gather(research_task, keywords_task)
    keywords = keywords_response.output()

    # Stage 2: Content Generation
    generated_content = ''
    if input.format == 'article':
        article_prompt = f'Write a detailed article about "{input.topic}" for {input.audience or "a general audience"} based on these findings: {research_findings}. Incorporate these keywords: {", ".join(keywords)}.'
        article_response = await genkit.generate(model=gemini, prompt=article_prompt)
        generated_content = article_response.text()
    elif input.format == 'social_post':
        social_post_prompt = f'Create a catchy social media post about "{input.topic}" for {input.audience or "a general audience"} based on these findings: {research_findings}. Use relevant hashtags from: {", ".join(keywords)}.'
        social_post_response = await genkit.generate(model=gemini, prompt=social_post_prompt)
        generated_content = social_post_response.text()

    # Stage 3: Summarization
    summary = await genkit.run(summarization_agent_flow, input={"text": generated_content, "length": "short"})

    # Stage 4: Image Generation (Conditional)
    image_url: Optional[str] = None
    if input.format == 'article': # Only generate image for articles for this example
        image_description_prompt = f'Generate a concise, descriptive phrase for an image that would accompany an article about "{input.topic}" for {input.audience or "a general audience"}.'
        image_description_response = await genkit.generate(model=gemini, prompt=image_description_prompt)
        image_description = image_description_response.text()

        image_url = image_generator_tool(description=image_description) # Directly call tool

    return DynamicContentOutput(
        content=generated_content,
        summary=summary,
        keywords=keywords,
        image_url=image_url,
    )
```

### Target Depth and Developer Instructions:
- Provide a detailed, end-to-end example of a complex multi-stage agent (e.g., dynamic content generator). Show how to integrate all previously learned concepts: chaining flows, parallel execution, using tools, and leveraging LLMs for various steps. Emphasize modularity and clear data flow between stages. Use both TypeScript and Python. Clearly mark conceptual or simplified parts that would be more complex in a production environment.