# Chapter 2: Core Concepts of GenKit: Flows, Models, and Prompts

In Chapter 1, we introduced GenKit and set up our development environment, culminating in a simple "Hello AI" flow. Building upon that foundation, this chapter dives deeper into the fundamental building blocks of GenKit: flows, models, and prompts. Mastering these core concepts is essential for constructing sophisticated AI-powered applications, enabling you to define complex workflows, integrate various generative models, and craft effective prompts to guide AI behavior.

## 2.1 Understanding GenKit Flows

GenKit flows are the heart of your AI application, providing a structured and observable way to define how your AI interacts with users, models, and tools. They represent a sequence of operations designed to achieve a specific AI-driven task.

### Flow Definition Deep Dive

A GenKit flow is defined using the `defineFlow` function (or `@genkit.define_flow` decorator in Python). This function requires several key parameters:

*   **`name`**: A unique identifier for your flow, used in the GenKit Developer UI for tracing and identification.
*   **`inputSchema`**: Defines the expected structure and types of the data that your flow will receive. This is crucial for input validation and type safety.
*   **`outputSchema`**: Defines the expected structure and types of the data that your flow will return. This ensures consistent and predictable outputs for downstream application logic.
*   **`run` function**: The core logic of your flow, an asynchronous function that takes the validated input and performs the AI operations.

Here's a conceptual overview of `defineFlow`:

```typescript
// Node.js/TypeScript
import { defineFlow } from '@genkit-ai/core';
import { z } from 'zod';

export const myFlow = defineFlow(
  {
    name: 'myFlow',
    inputSchema: z.object({ /* ... input properties ... */ }),
    outputSchema: z.string(),
  },
  async (input) => {
    // ... AI logic using input ...
    return "output";
  }
);
```

```python
# Python
import genkit
from pydantic import BaseModel

class MyFlowInput(BaseModel):
    # ... input properties ...
    pass

@genkit.define_flow(name="myFlow", input_schema=MyFlowInput, output_schema=str)
async def my_flow(input: MyFlowInput):
    # ... AI logic using input ...
    return "output"
```

### Flow Steps and Observability

One of GenKit's most powerful features is its built-in observability. When you execute operations within a flow, such as `genkit.run`, `genkit.generate`, or `genkit.tool` (which we'll cover in Chapter 3), GenKit automatically tracks these as distinct steps. These steps are then visualized in the GenKit Developer UI, providing a detailed trace of your flow's execution, including inputs, outputs, and any errors.

Using `genkit.run` allows you to define sub-steps or encapsulate logical units within your main flow, enhancing modularity and making your traces even more granular and understandable.

### Input and Output Schemas

Defining robust input and output schemas is a best practice for any application, and even more so for AI-powered ones. They serve several critical purposes:

*   **Type Safety:** Ensures that data conforms to expected types, preventing common programming errors.
*   **Validation:** Automatically validates incoming and outgoing data, catching malformed inputs early.
*   **Clear Contracts:** Provides a clear contract for what data a flow expects and what it will produce, improving developer collaboration and integration.
*   **LLM Guidance (for outputs):** As we'll see in Section 2.4, schemas can guide LLMs to produce structured outputs.

GenKit leverages popular schema validation libraries: [Zod](https://zod.dev/) for Node.js/TypeScript and [Pydantic](https://docs.pydantic.dev/latest/) for Python.

### Error Handling within Flows

Robust error handling is crucial for reliable AI applications. Within GenKit flows, you can use standard language-specific error handling mechanisms (e.g., `try...catch` in TypeScript, `try...except` in Python). GenKit's observability UI will automatically log any unhandled exceptions, making it easier to diagnose issues. For more structured error reporting, you can define specific error outputs in your `outputSchema` or use custom error types.

Here's a multi-step flow example demonstrating `genkit.run` for observability and schema usage:

```typescript
// Node.js/TypeScript
import { defineFlow, run, generate } from '@genkit-ai/core';
import { gemini } from '@genkit-ai/vertexai'; // Make sure Vertex AI is configured
import { z } from 'zod';

export const complexFlow = defineFlow(
  {
    name: 'complexFlow',
    inputSchema: z.object({
      topic: z.string().describe('The topic for the article.'),
      length: z.number().int().min(100).max(1000).describe('Desired length of the article in words.'),
    }).describe('Input for generating a complex article.'),
    outputSchema: z.object({
      summary: z.string().describe('A summary of the generated article.'),
      keywords: z.array(z.string()).max(5).describe('Up to 5 keywords from the article.'),
    }).describe('Output containing the article summary and keywords.'),
  },
  async (input) => {
    // Step 1: Brainstorm ideas for the article
    const brainstormResult = await run(
      async () => {
        const llmResponse = await generate({
          model: gemini,
          prompt: `Brainstorm detailed ideas and a brief outline for a ${input.topic} article.`,
        });
        return llmResponse.text();
      },
      'brainstormIdeas' // Step name for observability
    );

    // Step 2: Generate the full article content
    const articleContent = await generate(
      {
        model: gemini,
        prompt: `Write a ${input.length} word article on ${input.topic} based on these ideas: ${brainstormResult}. Focus on clarity and engagement.`,
      },
      'generateArticle' // Step name for observability
    );

    // Step 3: Summarize and extract keywords from the article
    const summaryAndKeywords = await generate({
      model: gemini,
      prompt: `Summarize the following article and extract exactly 5 relevant keywords:\n\n${articleContent.text()}`,
      output: { schema: z.object({ summary: z.string(), keywords: z.array(z.string()).max(5) }) },
      name: 'extractSummaryAndKeywords' // Step name for observability
    });

    return summaryAndKeywords.output();
  }
);
```

```python
# Python
import genkit
from genkit.models import gemini # Make sure Gemini is configured
from pydantic import BaseModel, Field
from typing import List

class ComplexFlowInput(BaseModel):
    topic: str = Field(description="The topic for the article.")
    length: int = Field(ge=100, le=1000, description="Desired length of the article in words.")

class ComplexFlowOutput(BaseModel):
    summary: str = Field(description="A summary of the generated article.")
    keywords: List[str] = Field(max_items=5, description="Up to 5 keywords from the article.")

@genkit.define_flow(name="complexFlow", input_schema=ComplexFlowInput, output_schema=ComplexFlowOutput)
async def complex_flow(input: ComplexFlowInput):
    # Step 1: Brainstorm ideas for the article
    brainstorm_result = await genkit.run(
        lambda: genkit.generate(
            model=gemini,
            prompt=f"Brainstorm detailed ideas and a brief outline for a {input.topic} article.",
        ),
        "brainstormIdeas" # Step name for observability
    )

    # Step 2: Generate the full article content
    article_content = await genkit.generate(
        model=gemini,
        prompt=f"Write a {input.length} word article on {input.topic} based on these ideas: {brainstorm_result.text()}. Focus on clarity and engagement.",
        name="generateArticle" # Step name for observability
    )

    # Step 3: Summarize and extract keywords from the article
    summary_and_keywords = await genkit.generate(
        model=gemini,
        prompt=f"Summarize the following article and extract exactly 5 relevant keywords:\n\n{article_content.text()}",
        output=ComplexFlowOutput, # Use Pydantic model for structured output
        name="extractSummaryAndKeywords" # Step name for observability
    )
    return summary_and_keywords.output()
```

When you run `complexFlow` and observe it in the GenKit Developer UI, you will see three distinct steps: `brainstormIdeas`, `generateArticle`, and `extractSummaryAndKeywords`, each with its own inputs and outputs. This granular tracing is invaluable for understanding and debugging your AI logic.

## 2.2 Integrating Generative Models

GenKit offers a unified approach to interacting with various generative AI models, abstracting away the differences in their APIs. This allows you to easily switch between models or use multiple models within the same application.

### Model Configuration

Before using any generative model, you need to configure GenKit to know about it. This is typically done using `genkit.configureGenkit` (TypeScript) or `genkit.configure` (Python) within your `genkit-config.ts` or `genkit_config.py` file. You pass `plugins` that correspond to different model providers.

For example, to configure Google Gemini (via Vertex AI) and OpenAI GPT models:

```typescript
// Node.js/TypeScript - genkit-config.ts
import { configureGenkit } from '@genkit-ai/core';
import { vertexai } from '@genkit-ai/vertexai';
import { openAI } from '@genkit-ai/openai';

export default configureGenkit({
  plugins: [
    vertexai(), // Configures Google Gemini Pro and other Vertex AI models
    openAI({
      apiKey: process.env.OPENAI_API_KEY, // Ensure OPENAI_API_KEY is set in your environment
    }),
  ],
  // ... other configurations like flow definitions, retrievers, evaluators
});
```

```python
# Python - genkit_config.py
import genkit
from genkit.plugins import vertexai, openai
import os

genkit.configure(
    plugins=[
        vertexai.vertexai_plugins(), # Configures Google Gemini Pro and other Vertex AI models
        openai.openai_plugins(api_key=os.environ.get("OPENAI_API_KEY")) # Ensure OPENAI_API_KEY is set
    ]
)
```

After configuration, you can import and use the models in your flows, for example, `gemini` from `@genkit-ai/vertexai` or `gpt35` from `@genkit-ai/openai`.

### Unified API

GenKit provides a consistent `generate` function that works across all integrated models. This means the core syntax for making an LLM call remains the same, regardless of whether you're using Gemini, GPT, or Claude.

```typescript
// Node.js/TypeScript - Using different models with the same API
import { generate } from '@genkit-ai/core';
import { gemini } from '@genkit-ai/vertexai';
import { gpt35 } from '@genkit-ai/openai';

async function getResponse(modelChoice: 'gemini' | 'gpt', promptText: string) {
  const model = modelChoice === 'gemini' ? gemini : gpt35; // Dynamically select model
  const llmResponse = await generate({
    model: model,
    prompt: promptText,
  });
  return llmResponse.text();
}
```

```python
# Python - Using different models with the same API
import genkit
from genkit.models import gemini, gpt35 # Assuming both are configured

async def get_response(model_choice: str, prompt_text: str):
    model = gemini if model_choice == "gemini" else gpt35 # Dynamically select model
    llm_response = await genkit.generate(
        model=model,
        prompt=prompt_text,
    )
    return llm_response.text()
```

This abstraction greatly simplifies multi-model strategies, A/B testing, and switching model providers without rewriting core logic.

### Model Parameters

Generative models expose various parameters that control their behavior and the nature of their outputs. Common parameters include:

*   **`temperature`**: Controls the randomness of the output. Higher values (e.g., 0.8) make the output more creative and diverse, while lower values (e.g., 0.2) make it more deterministic and focused.
*   **`topK`**: Limits the number of highest probability tokens to consider for the next token prediction. A lower `topK` restricts the model to more common words.
*   **`topP`**: Filters tokens based on their cumulative probability. The model considers the smallest set of tokens whose cumulative probability exceeds `topP`. This is often used in conjunction with `temperature`.

You can set these parameters globally during `configureGenkit` or override them for individual `generate` calls using the `config` parameter.

### Batching and Streaming

GenKit also supports advanced interaction patterns with models:

*   **Batching**: For certain models and providers, you can send multiple prompts in a single request to optimize latency and cost. While not always directly exposed as a `generate` parameter, GenKit's underlying model integrations might leverage this where available.
*   **Streaming**: For long responses, GenKit can stream tokens as they are generated by the LLM, providing a more responsive user experience. This is typically enabled by specifying a streaming option in the `generate` call or model configuration.

## 2.3 Prompt Engineering with GenKit

Prompt engineering is the art and science of crafting inputs (prompts) to generative models to achieve desired outputs. Effective prompt engineering is critical for guiding LLMs, especially in the context of building reliable AI agents.

### Crafting Effective Prompts

General guidelines for effective prompts include:

*   **Clarity and Conciseness:** Be direct and avoid ambiguity. Every word matters.
*   **Specificity:** Provide clear instructions, constraints, and examples.
*   **Role-Playing:** Assign a persona to the LLM (e.g., "You are a helpful assistant...").
*   **Delimiters:** Use clear delimiters (e.g., triple backticks ```` ``` ````, XML tags `<instruction>`) to separate instructions from content.
*   **Format Requirements:** Explicitly state the desired output format (e.g., "Return a JSON object").

### Prompt Templates

In real-world applications, prompts often need to be dynamic, incorporating user input or data from other parts of your flow. GenKit leverages standard string interpolation techniques to create prompt templates. You can inject variables directly into your prompt strings.

### Model Configurations per Prompt

While you can set default model configurations globally, it's often necessary to fine-tune generation parameters for specific tasks within a flow. You can override these defaults for individual `genkit.generate` calls using the `config` parameter.

### Few-Shot Prompting

Few-shot prompting involves providing a few examples of input-output pairs within your prompt to demonstrate the desired behavior. This can significantly improve the model's ability to follow complex instructions or mimic a specific style.

Here's an example combining prompt templating and model configuration override:

```typescript
// Node.js/TypeScript - Prompt template and model config override
import { generate } from '@genkit-ai/core';
import { gemini } from '@genkit-ai/vertexai';
import { z } from 'zod';

export const creativeStoryFlow = defineFlow(
  {
    name: 'creativeStoryFlow',
    inputSchema: z.object({
      topic: z.string().describe('The main topic of the story.'),
      characters: z.array(z.string()).min(1).describe('A list of characters to include.'),
    }),
    outputSchema: z.string().describe('A whimsical story.'),
  },
  async (input) => {
    const prompt = `Write a short, whimsical story about ${input.topic}. Include the following characters: ${input.characters.join(', ')}. The story should have a happy ending and be no more than 200 words.`;
    const story = await generate({
      model: gemini,
      prompt: prompt,
      config: { temperature: 0.8, topK: 40 }, // Override default model config for creativity
    });
    return story.text();
  }
);
```

```python
# Python - Prompt template and model config override
import genkit
from genkit.models import gemini
from pydantic import BaseModel
from typing import List

class CreativeStoryInput(BaseModel):
    topic: str = Field(description="The main topic of the story.")
    characters: List[str] = Field(min_items=1, description="A list of characters to include.")

@genkit.define_flow(name="creativeStoryFlow", input_schema=CreativeStoryInput, output_schema=str)
async def creative_story_flow(input: CreativeStoryInput):
    prompt = f"Write a short, whimsical story about {input.topic}. Include the following characters: {', '.join(input.characters)}. The story should have a happy ending and be no more than 200 words."
    story = await genkit.generate(
        model=gemini,
        prompt=prompt,
        config=genkit.GenerationConfig(temperature=0.8, top_k=40) # Override default model config
    )
    return story.text()
```

## 2.4 Structured Outputs

While LLMs are excellent at generating free-form text, many application integrations require structured data (e.g., JSON, XML). GenKit simplifies the process of guiding LLMs to produce well-formed, type-safe structured outputs.

### The Need for Structured Data

Generating JSON or other structured formats from LLMs is crucial for several reasons:

*   **Application Integration:** Easily parseable data allows your application to consume LLM outputs programmatically without complex regex or heuristics.
*   **Data Validation:** Structured output can be validated against a schema, ensuring data integrity.
*   **Reduced Post-Processing:** Minimizes the need for extensive post-processing logic to extract information from free-form text.
*   **Reliability:** Increases the reliability of AI-powered features by ensuring predictable data formats.

### Schema-Driven Generation

GenKit allows you to provide an `output.schema` parameter in your `genkit.generate` calls. When you do this, GenKit instructs the LLM to format its response according to the provided schema. The framework handles the underlying prompt engineering to guide the model, and often includes retry mechanisms if the initial output doesn't conform to the schema.

### Output Parsers

When a schema is provided, GenKit automatically attempts to parse the LLM's response into the specified structured format. If the parsing is successful, the result is directly accessible via the `.output()` method on the generation response. If parsing fails, GenKit provides mechanisms to inspect the raw response and potential errors.

### Example Use Cases

*   **Extracting Entities:** Extracting names, dates, locations, or product details from unstructured text.
*   **Generating Configuration Files:** Creating JSON or YAML configuration based on natural language instructions.
*   **Data Validation:** Ensuring that user-provided text conforms to specific data constraints by having the LLM transform and validate it.

Here's how to extract structured movie information:

```typescript
// Node.js/TypeScript - Extracting structured data
import { defineFlow, generate } from '@genkit-ai/core';
import { gemini } from '@genkit-ai/vertexai';
import { z } from 'zod';

const movieSchema = z.object({
  title: z.string().describe('The title of the movie.'),
  director: z.string().describe('The director of the movie.'),
  year: z.number().int().describe('The release year of the movie.'),
  genres: z.array(z.string()).describe('A list of genres the movie belongs to.'),
}).describe('Schema for extracting movie information.');

export const extractMovieInfoFlow = defineFlow(
  {
    name: 'extractMovieInfoFlow',
    inputSchema: z.string().describe('Text containing movie information.'),
    outputSchema: movieSchema,
  },
  async (text) => {
    const info = await generate({
      model: gemini,
      prompt: `Extract the movie title, director, year, and up to 3 genres from the following text and return as a JSON object matching the provided schema.\n\nText: ${text}`,
      output: { schema: movieSchema },
    });
    return info.output(); // Returns a typed object conforming to movieSchema
  }
);
```

```python
# Python - Extracting structured data
import genkit
from genkit.models import gemini
from pydantic import BaseModel, Field
from typing import List

class MovieInfo(BaseModel):
    title: str = Field(description="The title of the movie.")
    director: str = Field(description="The director of the movie.")
    year: int = Field(description="The release year of the movie.")
    genres: List[str] = Field(description="A list of genres the movie belongs to.", max_items=3)

@genkit.define_flow(name="extractMovieInfoFlow", input_schema=str, output_schema=MovieInfo)
async def extract_movie_info_flow(text: str):
    info = await genkit.generate(
        model=gemini,
        prompt=f"Extract the movie title, director, year, and up to 3 genres from the following text and return as a JSON object matching the provided schema.\n\nText: {text}",
        output=MovieInfo, # Use Pydantic model for structured output
    )
    return info.output() # Returns a typed object conforming to MovieInfo
```

## 2.5 Handling Multimodal Inputs and Outputs

Modern generative AI models are increasingly multimodal, meaning they can process and generate content across different modalities like text, images, and soon, audio and video. GenKit provides capabilities to leverage these multimodal models.

### Introduction to Multimodality

Multimodality in AI refers to the ability of models to understand and interact with information presented in more than one format simultaneously. For instance, a multimodal model can take an image and a text question about it, then generate a text answer.

### Multimodal Inputs

Some models, like Google's Gemini, can accept both text and image data as input within a single prompt. In GenKit, you can construct a prompt with multiple `part` objects, where each part represents a different modality. For images, you typically provide the image data as a base64-encoded string or a URL.

### Multimodal Outputs (Image Generation)

While this chapter primarily focuses on text generation, it's worth noting that some generative models (e.g., Google's Imagen) can also produce images based on text prompts. GenKit supports integrating with such models, allowing your flows to output generated visual content. The pattern would generally involve calling a `generate` function with an image generation model and receiving an image output (e.g., a URL or base64 encoded image).

### Use Cases

Multimodal AI opens up a new array of possibilities:

*   **Image Description:** Asking an AI to describe the content of an image.
*   **Visual Question Answering (VQA):** Posing specific questions about elements within an image.
*   **Creative Content Generation:** Generating images from text prompts, or generating text that describes a given image.
*   **Document Analysis:** Analyzing scanned documents that contain both text and visual layouts.

Here's how to send multimodal input (text and image) to a model like Gemini:

```typescript
// Node.js/TypeScript - Multimodal input with image
import { defineFlow, generate, part } from '@genkit-ai/core';
import { gemini } from '@genkit-ai/vertexai'; // Ensure Vertex AI is configured
import * as fs from 'fs';
import { z } from 'zod';

export const describeImageFlow = defineFlow(
  {
    name: 'describeImageFlow',
    inputSchema: z.object({
      imagePath: z.string().describe('Path to the image file.'),
      question: z.string().describe('Question about the image.'),
    }),
    outputSchema: z.string().describe('AI's answer to the question about the image.'),
  },
  async (input) => {
    const imageBytes = fs.readFileSync(input.imagePath).toString('base64');
    const response = await generate({
      model: gemini,
      prompt: [
        part({
          text: input.question,
        }),
        part({
          media: {
            contentType: 'image/jpeg', // Adjust based on your image type
            url: `data:image/jpeg;base64,${imageBytes}`,
          },
        }),
      ],
    });
    return response.text();
  }
);
```

```python
# Python - Multimodal input with image
import genkit
from genkit.models import gemini # Ensure Gemini is configured
from genkit.core.types import Part, MessageData
import base64
from pydantic import BaseModel, Field

class DescribeImageInput(BaseModel):
    image_path: str = Field(description="Path to the image file.")
    question: str = Field(description="Question about the image.")

@genkit.define_flow(name="describeImageFlow", input_schema=DescribeImageInput, output_schema=str)
async def describe_image_flow(input: DescribeImageInput):
    with open(input.image_path, "rb") as image_file:
        image_bytes = base64.b64encode(image_file.read()).decode("utf-8")

    response = await genkit.generate(
        model=gemini,
        prompt=[
            Part(text=input.question),
            Part(media=MessageData(contentType="image/jpeg", url=f"data:image/jpeg;base64,{image_bytes}")) # Adjust content type
        ],
    )
    return response.text()
```

This chapter has laid the groundwork for understanding how GenKit orchestrates AI interactions through flows, integrates with diverse models, and leverages prompt engineering for precise control. We've also explored how to extract structured data and work with multimodal inputs, setting the stage for building even more intelligent and interactive AI applications with GenKit. In the next chapter, we will expand on these capabilities by introducing tools and Retrieval-Augmented Generation (RAG) to empower our AI with external knowledge and actions.
