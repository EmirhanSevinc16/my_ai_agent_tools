# AI Agent Tools

🌐 **English** | [Türkçe](README_tr.md)

A small toolkit for building AI agents (LLM-based agents) that work in different roles. You define each tool **once**, give every agent only the tools its job needs, and run any agent with a single call. Each tool exists as a **Python function** together with an OpenAI-compatible **function calling schema**, so it can be used with NVIDIA, OpenAI, or any other API that supports the `tools` parameter.

## Table of Contents

- [Features](#features)
- [Project Structure](#project-structure)
- [Installation](#installation)
- [How It Works](#how-it-works)
- [Tools Overview](#tools-overview)
- [Tool Details](#tool-details)
  - [read_file](#1-read_file)
  - [edit_file](#2-edit_file)
  - [create_file](#3-create_file)
  - [web_search](#4-web_search)
  - [fetch_web_page](#5-fetch_web_page)
- [Registry API](#registry-api)
- [Agent Profiles](#agent-profiles)
- [Running an Agent](#running-an-agent)
- [Adding a New Tool](#adding-a-new-tool)
- [Helpers: md_file_reading](#helpers-md_file_reading)
- [Security Notes](#security-notes)
- [License](#license)

## Features

- **Define once:** every tool is registered a single time, and its function and schema always stay together
- **Role-based agents:** each agent only sees, and can only run, the tools it was granted (for example `code_agent` and `web_researcher`)
- **Easy to grow:** give an agent a new tool by adding one name to its profile, without touching the tool's code
- **Ready-made loop:** `run_agent` for one-off tasks and `run_turn` for multi-turn chats with memory
- **Safe execution:** tool calls that are not allowed for the agent are refused before anything runs
- All errors are returned as **strings** instead of raising exceptions, so the agent can see the error and correct itself
- File reading and writing, web search via DuckDuckGo (no API key required), and cleaned text extraction from web pages

## Project Structure

```
my_agent_tools/
├── registry.py            # tool registry, agent profiles, execute
├── tools_and_schemas.py   # tool functions and their schemas (registered on import)
├── agents.py              # agent profiles: which agent gets which tools
├── runner.py              # run_agent / run_turn loop
├── helpers.py             # helper functions for your own code (not agent tools)
└── pyproject.toml
```

## Installation

```bash
git clone https://github.com/<username>/<repo-name>.git
cd <repo-name>
pip install -e .
```

The `-e` (editable) flag makes Python use the cloned folder directly, so new tools and profile changes are visible in every project without reinstalling. This also installs the dependencies:

| Package | Purpose |
|---------|---------|
| `requests` | Downloading web pages |
| `beautifulsoup4` | Parsing and cleaning HTML |
| `ddgs` | DuckDuckGo search |

The examples below also use an OpenAI-compatible client (`pip install openai`). The package itself does not depend on it.

**Without installing:** install the three packages above manually and add the folder to Python's path:

```python
import sys
sys.path.insert(0, "/path/to/<repo-name>")
```

Python 3.9 or higher is recommended.

## How It Works

The toolkit has three layers:

1. **Registry** (`registry.py`, `tools_and_schemas.py`): every tool is a "card" holding a function and its schema. Cards are registered once with `register_tool` and stored in the `TOOLS` dictionary.
2. **Agent profiles** (`agents.py`): a profile is just a list of tool **names**. Profiles are stored in the `AGENTS` dictionary and point to the cards in the registry.
3. **Runner** (`runner.py`): when an agent runs, only the schemas from its profile are sent to the model. Every tool call coming back from the model is checked against that profile before it is executed.

Tools register themselves when `tools_and_schemas` is imported. `agents.py` imports it, so importing `agents` in your program is enough to load everything.

## Tools Overview

| Tool | Description | Parameters | Return type |
|------|-------------|------------|-------------|
| `read_file` | Reads a text file | `path` | `str` |
| `edit_file` | Writes/overwrites a file with the given content | `path`, `content` | `str` |
| `create_file` | Creates a new file with optional content (fails if already exists) | `path`, `content` (optional) | `str` |
| `web_search` | Searches the internet | `query`, `max_results` (optional) | `List[Dict]` |
| `fetch_web_page` | Fetches the text of a web page | `url` | `str` |

When a tool runs through `execute`, results that are not strings (such as the list from `web_search`) are converted to a JSON string before being sent back to the model.

## Tool Details

### 1. `read_file`

Reads the text file at the given path as UTF-8 and returns its content. Used by the agent to inspect project files, code files, or notes.

**Parameters**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `path` | `string` | Yes | Path of the file to read |

**Returns**

- On success: the full content of the file (`str`)
- If the file does not exist: `Hata: Dosya bulunamadı: <path>`
- On any other error: `Hata: Dosya okunurken bir sorun oluştu: <error>`

**Example**

```python
read_file("main.py")
```

---

### 2. `edit_file`

**Completely overwrites** the given file with the provided content. Creates the file if it does not exist. Used by the agent to create and update code or text files.

> ⚠️ This tool does not perform partial edits; it replaces the entire file content with `content`. To edit a file, first read its current content with `read_file`, then send the **full** updated content.

**Parameters**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `path` | `string` | Yes | Path of the file to edit |
| `content` | `string` | Yes | New content to write to the file (code or text) |

**Returns**

- On success: `Başarılı: Dosya güncellendi (<path>)`
- On error: `Hata: Dosya güncellenirken bir sorun oluştu: <error>`

**Example**

```python
edit_file("notes.txt", "New content goes here")
```

---

### 3. `create_file`

Creates a new Python or text file at the given path and optionally writes initial content. Automatically creates any missing parent directories (`os.makedirs`).

> 🛡️ **Overwrite Protection:** Unlike `edit_file`, if the target file already exists, it does not overwrite it; instead, it returns an error message prompting the model or user to use `edit_file` for updating existing files.

**Parameters**

| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `path` | `string` | Yes | – | Path and name of the file to create (e.g. `script.py` or `notes.txt`) |
| `content` | `string` | No | `""` | Initial content to write to the file (code or text). Can be left empty |

**Returns**

- On success: `Başarılı: Dosya oluşturuldu (<path>)`
- If file already exists: `Hata: Dosya zaten mevcut: <path>. Mevcut bir dosyayı güncellemek veya üzerine yazmak için 'edit_file' kullanın.`
- On any other error: `Hata: Dosya oluşturulurken bir sorun oluştu: <error>`

**Example**

```python
create_file("src/utils.py", "def hello():\n    print('Hello World')")
```

---

### 4. `web_search`

Searches the internet via DuckDuckGo. Used to find up-to-date information, news, and websites. Returns a title, URL, and short snippet for each result.

**Parameters**

| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `query` | `string` | Yes | – | Search term or question |
| `max_results` | `integer` | No | `5` | Maximum number of results to return |

**Returns**

A list of dictionaries:

```json
[
  {
    "title": "Page title",
    "url": "https://example.com/page",
    "snippet": "A short summary of the page..."
  }
]
```

If an error occurs during the search: `[{"error": "Arama sırasında hata oluştu: <error>"}]`

**Example**

```python
web_search("what is python asyncio", max_results=3)
```

---

### 5. `fetch_web_page`

Downloads the web page at the given URL, extracts its text content from the HTML, and cleans it. Ideal for reading the detailed content of a result found with `web_search`.

**How it works**

1. Downloads the page with a browser-like `User-Agent` (timeout: 10 seconds).
2. Removes `<script>`, `<style>`, `<header>`, `<footer>`, and `<nav>` tags.
3. Strips empty lines.
4. Truncates the result to the **first 4000 characters** to limit token usage.

**Parameters**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `url` | `string` | Yes | Full URL of the page to read |

**Returns**

- On success: the cleaned page text (up to 4000 characters)
- On error: `Sayfa içeriği çekilirken hata oluştu: <error>`

**Example**

```python
fetch_web_page("https://docs.python.org/3/library/asyncio.html")
```

> Content loaded dynamically via JavaScript cannot be fetched with this tool; only the HTML returned by the server is processed.

## Registry API

All of these live in `registry.py`:

| Function | Description |
|----------|-------------|
| `register_tool(function, schema)` | Adds a tool to the registry. The name is read from the schema. Raises `ValueError` if the name is already registered |
| `define_agent(agent, tools)` | Creates an agent profile (or resets an existing one) from a list of tool names. Raises `KeyError` if a name is not registered |
| `grant(agent, *tool_names)` | Adds tools to an existing profile |
| `revoke(agent, *tool_names)` | Removes tools from a profile |
| `get_schemas(agent)` | Returns the schemas to send to the model (the `tools=` parameter) |
| `execute(agent, name, args)` | Runs a tool call for an agent. `args` can be a dict or a JSON string. Always returns a string |
| `get_function(name)`, `get_schema(name)` | Look up a registered tool's function or schema directly |

`execute` never raises. If the agent is not allowed to use the tool it returns `Hata: '<name>' tool'u <agent> için tanımlı değil`, and if the tool itself fails it returns `Hata (<name>): <ErrorType>: <message>`. The model sees these messages and can correct itself.

## Agent Profiles

Profiles are defined in `agents.py`, which is the file you edit most often:

```python
import tools_and_schemas   # loads the tools into the registry
from registry import define_agent

define_agent("code_agent", tools=["read_file", "edit_file", "create_file"])
define_agent("web_researcher", tools=["web_search", "fetch_web_page", "create_file", "edit_file", "read_file"])
```

To give an agent a tool it was missing, add the tool's name to its list. To change a profile only while the program is running, use `grant` and `revoke`:

```python
import registry

registry.grant("web_researcher", "read_file")
registry.revoke("web_researcher", "read_file")
```

> `grant` and `revoke` only affect the running program. For a permanent change, edit `agents.py`.

## Running an Agent

`run_agent` runs a single task and returns the final answer. The `client` and `model` are passed in from outside, so the package never stores API keys and the same agents work with any OpenAI-compatible API:

```python
import os
from openai import OpenAI

import agents                      # loads tools and agent profiles
from runner import run_agent

client = OpenAI(base_url="<API_BASE_URL>", api_key=os.environ["<API_KEY_ENV_VAR>"])

answer = run_agent(
    agent="web_researcher",
    task="Research the new features of Python 3.13.",
    client=client,
    model="<MODEL_NAME>",
)
print(answer)
```

For a multi-turn chat that remembers the conversation, keep a `messages` list and call `run_turn` for each user message. It updates the list in place:

```python
from helpers import md_file_reading
from runner import run_turn

messages = [{"role": "system", "content": md_file_reading("code_agent.md")}]

while True:
    user_input = input("You > ")
    if user_input.strip().lower() == "quit":
        break
    messages.append({"role": "user", "content": user_input})
    print(run_turn("code_agent", messages, client, "<MODEL_NAME>"))
```

**Parameters**

| Name | Description |
|------|-------------|
| `agent` | Name of the agent profile to run |
| `client`, `model` | An OpenAI-compatible client and the model name |
| `max_turns` | Maximum number of model calls per request (default `10`). Prevents endless tool loops. If it is exceeded, an error message is returned |
| `on_tool_call` | Optional callback `(name, arguments)` called before each tool runs, useful for printing progress in your own interface (`run_turn` only) |
| `system_prompt` | Optional system prompt (`run_agent` only) |

Give each agent its own system prompt (for example one Markdown file per agent). The profile decides which tools an agent has, and the prompt tells it its role.

## Adding a New Tool

1. In `tools_and_schemas.py`, write the function and register it with its schema:

```python
def word_count(text: str) -> str:
    """Counts the words in the given text."""
    return str(len(text.split()))


register_tool(
    word_count,
    {
        "type": "function",
        "function": {
            "name": "word_count",
            "description": "Counts the words in the given text.",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Text to count the words of"},
                },
                "required": ["text"],
            },
        },
    },
)
```

2. In `agents.py`, add `"word_count"` to the profile of every agent that should use it.

There is no second list to update: the function and its schema are registered together, so they cannot get out of sync.

## Helpers: `md_file_reading`

`helpers.py` holds functions that are **not agent tools**: they are never registered, the model cannot see them, and they are called directly from your own code.

`md_file_reading` reads a Markdown file and replaces the `{{ CURRENT_DATETIME }}` placeholder with the current date and time (in `%d %B %Y, %H:%M` format). Its typical use is loading a system prompt, so the agent knows the current time on every run.

**Example**

`code_agent.md`:

```markdown
You are a helpful coding assistant.
Current date and time: {{ CURRENT_DATETIME }}
```

Usage:

```python
system_prompt = md_file_reading("code_agent.md")
```

## Security Notes

- `read_file`, `edit_file`, and `create_file` have **no path restrictions**. They give the agent read/write/creation access to any file on the system. Consider restricting them to a specific working directory before running in untrusted environments.
- The permission check in `execute` only works as well as your profiles. Give powerful tools (such as `edit_file`, `create_file`) only to the agents that need them, and always by explicit name.
- `fetch_web_page` and `web_search` bring in external content. That content may contain text that tries to steer the agent's behavior (prompt injection); treat content from the web as data, not as instructions.
- Keep your API key in a `.env` file instead of hardcoding it, and add that file to `.gitignore`.

## License

Add your license information here (e.g. MIT).