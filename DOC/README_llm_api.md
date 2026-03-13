# Using an LLM API with Python

This example shows how to connect to an LLM API using Python and the `openai` package, send a prompt, and print the model's response.

## What this program does

The script:

1. Imports the required Python modules.
2. Creates an API client.
3. Connects to a custom LLM server.
4. Sends a short chat conversation to the model.
5. Prints the model's answer.

## Example code

```python
import os
from openai import OpenAI

# Create an OpenAI client object.
# This object lets our Python program send requests to the LLM server.
client = OpenAI(
    # Read the API key from an environment variable instead of hardcoding it.
    # This is safer because secret keys should not be written directly in code.
    api_key=os.environ.get("OPENAI_API_KEY"),

    # The base URL tells the client which server to send requests to.
    # In this case, we are using a custom endpoint instead of the default OpenAI API server.
    base_url="https://ellm.nrp-nautilus.io/v1"
)

# Send a chat completion request to the model.
# This asks the model to generate a response based on the conversation below.
completion = client.chat.completions.create(
    # Choose which model to use.
    # You could switch this to another available model if needed.
    # https://nrp.ai/documentation/userdocs/ai/llm-managed/#:~:text=Available%20Models,-main
    model="gpt-oss",

    # The messages list represents the conversation history.
    messages=[
        {
            "role": "system",
            "content": "Talk like a pirate."
        },
        {
            "role": "user",
            "content": "How do I check if a Python object is an instance of a class?"
        },
    ],
)

# The response is stored in 'completion'.
# completion.choices is a list of possible answers from the model.
# We usually take the first one: choices[0]
# .message.content gives the actual text of the model's reply.
print(completion.choices[0].message.content)
```

## Requirements

* Python 3.8 or later
* The `openai` Python package installed

Install the package with:

```bash
pip install openai
```

## How to get your API key from the NRP portal

The token is created from the **NRP Create LLM tokens** page.

### Steps to create a token

1. Open the NRP LLM tokens page.
2. In the **Alias** field, enter a name for your token.

   * Example: `my-llm-token`
3. In the **Group** dropdown, select your group.
4. Click **Create new token for general LLM API access**.
5. Copy the generated token and store it securely.

### Important security note

Treat the token like a password.

* Do not share it in screenshots, slides, email, or public repositories.
* Do not hardcode it directly into Python files.
* If a token is accidentally exposed, delete it and create a new one.

## How to set your API key

Do **not** place your API key directly inside your code.

Instead, store the token in an environment variable named `OPENAI_API_KEY`.

### On macOS or Linux

```bash
export OPENAI_API_KEY="your_token_here"
```

### On Windows Command Prompt

```cmd
set OPENAI_API_KEY=your_token_here
```

### On Windows PowerShell

```powershell
$env:OPENAI_API_KEY="your_token_here"
```

After setting the environment variable, Python can read it using:

```python
api_key=os.environ.get("OPENAI_API_KEY")
```

## How to run the program

Save your Python code in a file such as `llm_api_example.py`, then run:

```bash
python llm_api_example.py
```

## Expected behavior

The program sends the user question to the model:

> How do I check if a Python object is an instance of a class?

Because the system message says `Talk like a pirate.`, the model will answer in a pirate style.

For example, the response might look something like:

```text
Arrr, ye can use isinstance(obj, MyClass) to check whether the object belongs to that class!
```

## Explanation of important parts

### `from openai import OpenAI`

This imports the `OpenAI` client class from the Python package.

### `client = OpenAI(...)`

This creates a client object used to communicate with the LLM server.

* `api_key=...` provides authentication.
* `base_url=...` tells the client which API server to use.

### `client.chat.completions.create(...)`

This sends a chat request to the model.

Important arguments:

* `model`: the model name to use
* `messages`: the conversation history

### Message roles

The `messages` list contains dictionaries with roles:

* `system`: gives instructions to the model
* `user`: contains the user's question
* `assistant`: used for previous model replies if continuing a conversation

## Why use a system message?

The system message helps control the model's behavior.

In this example:

```python
{"role": "system", "content": "Talk like a pirate."}
```

This changes the style of the response without changing the main question.

## Notes for students

* The model name must match one supported by your server.
* The `base_url` can point to a local server, school server, research server, or a hosted API.
* If `OPENAI_API_KEY` is missing, authentication may fail.
* If the server is unavailable, the request may return an error.

## Common errors

### 1. Missing API key

If `OPENAI_API_KEY` is not set, the client may fail to authenticate.

### 2. Wrong model name

If `gpt-oss` is not available on the server, the request may fail.

### 3. Wrong base URL

If the URL is incorrect, Python may not be able to connect to the server.

### 4. Package not installed

If you see an import error, install the package:

```bash
pip install openai
```

## Safer coding practice

Avoid writing code like this:

```python
api_key="your_secret_key"
```

That exposes private credentials in source files.

Using environment variables is safer and is the standard practice in software development.

