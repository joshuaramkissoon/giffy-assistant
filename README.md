# Giffy 🦒

Giffy is a voice assistant leveraging speech-to-text, text-to-speech, and generative agents for lively, engaging chats. It also exposes an interface that can be used to interact with any generative agent as if it were human (i.e. via speech) and benefits from the continuous extension of supported tools.

## Getting Started

These instructions will help you set up and run the Giffy on your local machine.

### Prerequisites

Before you begin, make sure you have the following installed:

- Python 3.6 or higher
- `pip`

### Installing

Clone the repository to your local machine:

```bash
git clone https://github.com/joshuaramkissoon/giffy-assistant.git
cd giffy-assistant
```

Install the requirements using `pip install -r requirements.txt`

### API Keys

You will need to obtain API keys for the following services (likely to be extended when new tools are introduced):

* [**OpenAI**](https://platform.openai.com/docs/api-reference/introduction): For GPT-based models
* [**SerpAPI**](https://serpapi.com/): For search queries
* [**Eleven Labs**](https://beta.elevenlabs.io/speech-synthesis): For Text-to-Speech functionality

Once you have the API keys, create a `.env` file in the project root directory with the following content:

```env
OPENAI_API_KEY=your_openai_api_key
SERP_API_KEY=your_serpapi_api_key
ELEVENLABS_API_KEY=your_elevenlabs_api_key
```

## Quick Usage

To start the Giffy Assistant, run the following command:

```bash
python3 giffy.py
```

Press `c` to start recording your voice, `s` to stop recording, and `x` to cancel a recording. Press `q` to let Giffy take a break (closes assistant object).

## The `Agent` Class

The `Agent` class serves as the base class for custom generative agents. By deriving your own agent class from `Agent`, you can interact with many different agents in a convenient way using speech. `GiffyAssistant` can work with any custom generative agent, as long as it implements the `ask()` method.

### `Agent` Interface

The `Agent` interface is defined below:

```python
class Agent:
    def ask(self, input: str) -> str:
        # Implementation of the method that processes the input and returns a response
        response = ...
        return response
```

An example of a trivial custom agent:

```python
class MyCustomAgent(Agent):
    def ask(self, input: str) -> str:
        # Your custom implementation of generating a response
        response = "Hello, I'm your custom agent!"
        return response
```

## The `GiffyAssistant` Class 

### Creating a `GiffyAssistant`

This is the core component of the Giffy voice assistant, responsible for managing the conversation flow and interactions with the user. Any custom agent implementing [`Agent`](#the-agent-class) can be used to power Giffy. This agent can be as simple as a wrapper around a standard LLM like GPT-4 or as involved as a generative agent with access to tools (like [BabyAGI](https://github.com/yoheinakajima/babyagi)).

Here's a simple example of how to use the `GiffyAssistant` class:

```python
from giffy import GiffyAssistant, Agent

# Create an instance of your custom agent
my_agent = MyCustomAgent()

# Initialize the assistant with your custom agent
giffy = GiffyAssistant(agent=my_agent)
```

In this example, we've defined a dummy custom agent by extending the `Agent` class and implementing the `ask()` method. We then create an instance of our custom agent and pass it to the `GiffyAssistant` when initializing it.

### Interacting with Giffy

You can interact with Giffy in two ways:

* **Single-prompt**: Get the response to a single prompt using `ask()`. Explicit call to `ask()` required by user to ask a follow up question.
* **Live conversation**: Have a real-time chat with Giffy using `start()`. Will loop until stopped by user pressing the `q` key.

Giffy responds to the user using synthesized speech in both cases.

```python
giffy.ask("Hi there!") # Get single prompt response
# Output synthesized speech: "Hello, I am your custom agent!"

giffy.start() # Start real-time chat
# Keep conversation alive until 'q' pressed
```

#### Live Conversation

Live conversation allows for seamless interactions with agents; after receiving a response from the agent, the user is prompted to start capturing more audio and can use the following controls:

|     Action     | Key  | Description                                                   |
|--------------|:----:|---------------------------------------------------------------|
| Capture Audio  |  c   | Start capturing audio for GiffyAssistant to process          |
| Stop Audio     |  s   | Stop capturing audio and let GiffyAssistant process the input|
| Cancel Audio   |  x   | Cancel the current audio capture without processing           |
| Quit Giffy     |  q   | Exit GiffyAssistant and end the conversation                 |
