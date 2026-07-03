# Chapter 2: Core Concepts of GenKit: Flows, Models, and Prompts

**Target File Name:** `chapter_2_core_concepts_of_genkit_flows_models_and_prompts.md`

## Section 2.1: Understanding GenKit Flows

### Roadmap

- **Flow Definition Deep Dive:** Explain the `defineFlow` function, its parameters (name, inputSchema, outputSchema, run function).
- **Flow Steps and Observability:** Illustrate how individual operations within a flow (`run`, `generate`, `tool`) become traceable steps in the GenKit Developer UI.
- **Input and Output Schemas:** Importance of defining clear data structures using Zod (Node.js/TypeScript), Pydantic (Python), or equivalent for type safety and validation.
- **Error Handling within Flows:** Strategies for managing and reporting errors in AI workflows.

### Required Technical Concepts/APIs

- `genkit.defineFlow`
- `genkit.run` (for sub-flows or sequential operations)
- Input/Output schemas (e.g., Zod, Pydantic)

### Code Snippets

```typescript
// Node.js/TypeScript
import { defineFlow, run, generate } from '@genkit-ai/core';
import { gemini } from '@genkit-ai/vertexai';
import { z } from 'zod';

export const complexFlow = defineFlow(
  {
    name: 'complexFlow',
    inputSchema: z.object({
      topic: z.string(),
      length: z.number().int().min(100).max(1000),
    }),
    outputSchema: z.object({
      summary: z.string(),
      keywords: z.array(z.string()),
    }),
  },
  async (input) => {
    const brainstormResult = await run(
      () => generate({
        model: gemini,
        prompt: `Brainstorm ideas for a ${input.topic} article.`,
      }),
      'brainstormIdeas' // Step name for observability
    );

    const articleContent = await generate(
      {
        model: gemini,
        prompt: `Write a ${input.length} word article on ${input.topic} based on these ideas: ${brainstormResult.text()}.`,
      },
      'generateArticle'
    );

    const summaryAndKeywords = await generate({
      model: gemini,
      prompt: `Summarize the following article and extract 5 keywords:\n\n${articleContent.text()}`,
      output: { schema: z.object({ summary: z.string(), keywords: z.array(z.string()).max(5) }) },
    });

    return summaryAndKeywords.output();
  }
);
```

```python
# Python
import genkit
from genkit.models import gemini
from pydantic import BaseModel
from typing import List

class ComplexFlowInput(BaseModel):
    topic: str
    length: int

class ComplexFlowOutput(BaseModel):
    summary: str
    keywords: List[str]

@genkit.define_flow(name="complexFlow", input_schema=ComplexFlowInput, output_schema=ComplexFlowOutput)
async def complex_flow(input: ComplexFlowInput):
    brainstorm_result = await genkit.run(
        lambda: genkit.generate(
            model=gemini,
            prompt=f"Brainstorm ideas for a {input.topic} article.",
        ),
        "brainstormIdeas"
    )

    article_content = await genkit.generate(
        model=gemini,
        prompt=f"Write a {input.length} word article on {input.topic} based on these ideas: {brainstorm_result.text()}.
",
        name="generateArticle"
    )

    summary_and_keywords = await genkit.generate(
        model=gemini,
        prompt=f"Summarize the following article and extract 5 keywords:\n\n{article_content.text()}",
        output=ComplexFlowOutput,
        name="summaryAndKeywords"
    )
    return summary_and_keywords.output()
```

### Target Depth and Developer Instructions

- Provide a multi-step flow example to demonstrate the `run` function and how steps are visualized in the GenKit UI. Emphasize the importance of clear input/output schemas for data integrity. Use both TypeScript (Zod) and Python (Pydantic) examples.

## Section 2.2: Integrating Generative Models

### Roadmap

- **Model Configuration:** Explain `configureGenkit` for setting up various LLMs (Gemini, OpenAI, Anthropic).
- **Unified API:** Demonstrate how GenKit provides a consistent interface across different model providers.
- **Model Parameters:** Discuss common parameters like temperature, topK, topP, and their impact on generation.
- **Batching and Streaming:** Briefly introduce capabilities for optimized model interactions.

### Required Technical Concepts/APIs

- `genkit.configureGenkit`
- `genkit.generate`
- Model providers (e.g., `vertexai.gemini`, `openai.gpt35`, `anthropic.claude`)
- Model parameters (temperature, topK, topP).

### Code Snippets

```typescript
// Node.js/TypeScript - Configuring multiple models
import { configureGenkit } from '@genkit-ai/core';
import { geminiPro } from '@genkit-ai/vertexai';
import { openAI } from '@genkit-ai/openai';

configureGenkit({
  plugins: [
    vertexai(), // Configures Gemini Pro
    openAI({
      apiKey: process.env.OPENAI_API_KEY,
    }),
  ],
  // ... other configurations
});
```

```python
# Python - Configuring multiple models
import genkit
from genkit.plugins import vertexai, openai
import os

genkit.configure(
    plugins=[
        vertexai.vertexai_plugins(), # Configures Gemini Pro
        openai.openai_plugins(api_key=os.environ.get("OPENAI_API_KEY"))
    ]
)
```

### Target Depth and Developer Instructions

- Show how to configure and switch between different LLM providers using GenKit's unified API. Provide examples of setting model parameters. Explain the advantages of this abstraction. Use both TypeScript and Python examples.

## Section 2.3: Prompt Engineering with GenKit

### Roadmap

- **Crafting Effective Prompts:** Guidelines for clear, concise, and specific prompts.
- **Prompt Templates:** Using variables and conditional logic within prompts for dynamic content.
- **Model Configurations per Prompt:** Overriding default model parameters for specific `generate` calls.
- **Few-Shot Prompting:** Providing examples to guide LLM behavior.

### Required Technical Concepts/APIs

- `genkit.generate` `prompt` parameter.
- String interpolation/template literals.
- `genkit.configure` (for default model)

### Code Snippets

```typescript
// Node.js/TypeScript - Prompt template and model config override
import { generate } from '@genkit-ai/core';
import { gemini } from '@genkit-ai/vertexai';

async function generateCreativeStory(topic: string, characters: string[]) {
  const prompt = `Write a short, whimsical story about ${topic}. Include the following characters: ${characters.join(', ')}. The story should have a happy ending.`;
  const story = await generate({
    model: gemini,
    prompt: prompt,
    config: { temperature: 0.8, topK: 40 }, // Override default model config
  });
  return story.text();
}
```

```python
# Python - Prompt template and model config override
import genkit
from genkit.models import gemini

async def generate_creative_story(topic: str, characters: list[str]):
    prompt = f"Write a short, whimsical story about {topic}. Include the following characters: {', '.join(characters)}. The story should have a happy ending."
    story = await genkit.generate(
        model=gemini,
        prompt=prompt,
        config=genkit.GenerationConfig(temperature=0.8, top_k=40) # Override default model config
    )
    return story.text()
```

### Target Depth and Developer Instructions

- Provide practical examples of building flexible and effective prompts. Demonstrate how to use prompt templates and override model configurations for specific generation tasks. Explain the rationale behind prompt engineering techniques.

## Section 2.4: Structured Outputs

### Roadmap

- **The Need for Structured Data:** Why generating JSON or other structured formats is crucial for application integration.
- **Schema-Driven Generation:** Using input/output schemas to guide LLMs to produce desired data structures.
- **Output Parsers:** Techniques for robustly parsing LLM responses into structured data.
- **Example Use Cases:** Extracting entities, generating configuration files, data validation.

### Required Technical Concepts/APIs

- `genkit.generate` `output` parameter (with `schema`).
- Zod (Node.js/TypeScript), Pydantic (Python).

### Code Snippets

```typescript
// Node.js/TypeScript - Extracting structured data
import { generate } from '@genkit-ai/core';
import { gemini } from '@genkit-ai/vertexai';
import { z } from 'zod';

const movieSchema = z.object({
  title: z.string(),
  director: z.string(),
  year: z.number().int(),
  genres: z.array(z.string()),
});

async function extractMovieInfo(text: string) {
  const info = await generate({
    model: gemini,
    prompt: `Extract movie title, director, year, and genres from the following text:\n\n${text}`,
    output: { schema: movieSchema },
  });
  return info.output();
}
```

```python
# Python - Extracting structured data
import genkit
from genkit.models import gemini
from pydantic import BaseModel
from typing import List

class MovieInfo(BaseModel):
    title: str
    director: str
    year: int
    genres: List[str]

async def extract_movie_info(text: str):
    info = await genkit.generate(
        model=gemini,
        prompt=f"Extract movie title, director, year, and genres from the following text:\n\n{text}",
        output=MovieInfo,
    )
    return info.output()
```

### Target Depth and Developer Instructions

- Demonstrate how to reliably get structured output from LLMs using GenKit's schema capabilities. Provide clear examples for both TypeScript and Python. Discuss error handling for parsing failures.

## Section 2.5: Handling Multimodal Inputs and Outputs

### Roadmap

- **Introduction to Multimodality:** Explain the concept of combining different data types (text, images, video, audio) in AI interactions.
- **Multimodal Inputs:** How to pass image data (e.g., base64 encoded) along with text prompts to models like Gemini.
- **Multimodal Outputs (Image Generation):** Using models capable of generating images based on text prompts.
- **Use Cases:** Image description, visual question answering, creative content generation.

### Required Technical Concepts/APIs

- `genkit.generate` with `part` for multimodal content.
- Image encoding (e.g., base64).
- Multimodal models (e.g., Gemini 1.5, Imagen).

### Code Snippets

```typescript
// Node.js/TypeScript - Multimodal input with image
import { generate, part } from '@genkit-ai/core';
import { gemini } from '@genkit-ai/vertexai';
import * as fs from 'fs';

async function describeImage(imagePath: string, question: string) {
  const imageBytes = fs.readFileSync(imagePath).toString('base64');
  const response = await generate({
    model: gemini,
    prompt: [
      part({
        text: question,
      }),
      part({
        media: {
          contentType: 'image/jpeg',
          url: `data:image/jpeg;base64,${imageBytes}`,
        },
      }),
    ],
  });
  return response.text();
}
```

```python
# Python - Multimodal input with image
import genkit
from genkit.models import gemini
from genkit.core.types import Part
import base64

async def describe_image(image_path: str, question: str):
    with open(image_path, "rb") as image_file:
        image_bytes = base64.b64encode(image_file.read()).decode("utf-8")

    response = await genkit.generate(
        model=gemini,
        prompt=[
            Part(text=question),
            Part(media={"contentType": "image/jpeg", "url": f"data:image/jpeg;base64,{image_bytes}"})
        ],
    )
    return response.text()
```

### Target Depth and Developer Instructions

- Introduce the concept of multimodal AI and demonstrate how GenKit handles it. Provide practical examples of sending image data along with text prompts. Briefly mention models capable of generating images as output (even if full code isn't provided, describe the capability). Use both TypeScript and Python examples.
