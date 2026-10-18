import tools_and_schemas
from registry import define_agent

define_agent("code_agent", tools=["read_file", "edit_file"])
define_agent("web_researcher", tools=["web_search", "fetch_web_page"])