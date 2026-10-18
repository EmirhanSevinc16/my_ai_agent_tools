import json


TOOLS = {}   # tool adı -> {"function": ..., "schema": ...}


def register_tool(function, schema):
    name = schema["function"]["name"]
    if name in TOOLS:
        raise ValueError(f"'{name}' zaten kayıtlı")
    TOOLS[name] = {"function": function, "schema": schema}


def get_function(name):
    return TOOLS[name]["function"]


def get_schema(name):
    return TOOLS[name]["schema"]


AGENTS = {}   # agent adı -> tool isimleri listesi


def define_agent(agent, tools):
    AGENTS[agent] = []
    grant(agent, *tools)


def grant(agent, *tool_names):
    for name in tool_names:
        if name not in TOOLS:
            raise KeyError(f"Rafta '{name}' diye bir tool yok")
        if name not in AGENTS[agent]:
            AGENTS[agent].append(name)


def revoke(agent, *tool_names):
    AGENTS[agent] = [n for n in AGENTS[agent] if n not in tool_names]


def get_schemas(agent):
    return [TOOLS[name]["schema"] for name in AGENTS[agent]]


def execute(agent, name, args):
    if name not in AGENTS[agent]:
        return f"Hata: '{name}' tool'u {agent} için tanımlı değil"
    try:
        if isinstance(args, str):
            args = json.loads(args or "{}")
        result = TOOLS[name]["function"](**args)
        if not isinstance(result, str):
            result = json.dumps(result, ensure_ascii=False)
        return result
    except Exception as e:
        return f"Hata ({name}): {type(e).__name__}: {e}"