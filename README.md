# AI Agent Tools

🌐 **English** | [Türkçe](README.tr.md)

A collection of reusable Python tools built to power AI agents (LLM-based agents). Each tool is defined both as a **Python function** and as an OpenAI-compatible **function calling schema**, so it can be used with NVIDIA, OpenAI, or any other API that supports the `tools` parameter.

## Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Tools Overview](#tools-overview)
- [Tool Details](#tool-details)
  - [read_file](#1-read_file)
  - [edit_file](#2-edit_file)
  - [web_search](#3-web_search)
  - [fetch_web_page](#4-fetch_web_page)
- [Helper Function: md_file_reading](#helper-function-md_file_reading)
- [Tool Map and Schemas](#tool-map-and-schemas)
- [Usage Example with an Agent](#usage-example-with-an-agent)
- [Security Notes](#security-notes)

## Features

- File reading and writing
- Web search via DuckDuckGo (no API key required)
- Fetching cleaned text content from web pages
- All errors are returned as **strings** instead of raising exceptions, so the agent can see the error and correct itself
- Easy integration into an agent loop via `TOOL_MAP` and `TOOL_SCHEMAS`

## Installation

```bash
git clone https://github.com/<username>/<repo-name>.git
cd <repo-name>
pip install requests beautifulsoup4 ddgs
```

Requirements:

| Package | Purpose |
|---------|---------|
| `requests` | Downloading web pages |
| `beautifulsoup4` | Parsing and cleaning HTML |
| `ddgs` | DuckDuckGo search |

Python 3.9 or higher is recommended.

## Tools Overview

| Tool | Description | Parameters | Return type |
|------|-------------|------------|-------------|
| `read_file` | Reads a text file | `path` | `str` |
| `edit_file` | Writes/overwrites a file with the given content | `path`, `content` | `str` |
| `web_search` | Searches the internet | `query`, `max_results` (optional) | `List[Dict]` |
| `fetch_web_page` | Fetches the text of a web page | `url` | `str` |

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

### 3. `web_search`

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

### 4. `fetch_web_page`

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

## Helper Function: `md_file_reading`

This is **not an agent tool** (it is not part of `TOOL_MAP` or `TOOL_SCHEMAS`); it is a helper function called directly from your code. Its typical use is loading system prompts or rule files from Markdown.

It reads a Markdown file and replaces the `{{ CURRENT_DATETIME }}` placeholder with the current date and time (in `%d %B %Y, %H:%M` format), so the agent knows the current time on every run.

**Example**

`rules.md`:

```markdown
You are a helpful assistant.
Current date and time: {{ CURRENT_DATETIME }}
```

Usage:

```python
system_prompt = md_file_reading("rules.md")
```

If the file is not found: `Hata: Kurallar dosyası (<md_file>) bulunamadı.`

## Tool Map and Schemas

The code provides two main structures:

- **`TOOL_MAP`**: A dictionary mapping tool names to Python functions. Used to execute tool calls coming from the model.
- **`TOOL_SCHEMAS`**: A list of JSON schemas sent to the model, defining each tool's name, description, and parameters.

```python
TOOL_MAP = {
    "read_file": read_file,
    "edit_file": edit_file,
    "web_search": web_search,
    "fetch_web_page": fetch_web_page,
}
```

To add a new tool:

1. Write the Python function.
2. Add it to `TOOL_MAP`.
3. Add its schema to the `TOOL_SCHEMAS` list.

## Usage Example with an Agent

A basic agent loop with an OpenAI-compatible API (e.g. NVIDIA API):

```python
import json
from openai import OpenAI

client = OpenAI(base_url="<API_BASE_URL>", api_key="<API_KEY>")
messages = [{"role": "user", "content": "Research the new features of Python 3.13."}]

while True:
    response = client.chat.completions.create(
        model="<MODEL_NAME>",
        messages=messages,
        tools=TOOL_SCHEMAS,
    )
    msg = response.choices[0].message
    messages.append(msg)

    if not msg.tool_calls:
        print(msg.content)
        break

    for call in msg.tool_calls:
        func = TOOL_MAP[call.function.name]
        args = json.loads(call.function.arguments)
        result = func(**args)
        messages.append({
            "role": "tool",
            "tool_call_id": call.id,
            "content": json.dumps(result, ensure_ascii=False),
        })
```

> Keep your API key in a `.env` file instead of hardcoding it, and add that file to `.gitignore`.

## Security Notes

- `read_file` and `edit_file` have **no path restrictions**. They give the agent read/write access to any file on the system. Consider restricting them to a specific working directory before running in untrusted environments.
- `fetch_web_page` and `web_search` bring in external content. That content may contain text that tries to steer the agent's behavior (prompt injection); treat content from the web as data, not as instructions.

## License

Add your license information here (e.g. MIT).