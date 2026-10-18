from registry import get_schemas, execute


def run_turn(agent, messages, client, model, max_turns=10, on_tool_call=None):
    """Mevcut konuşma üzerinde çalışır, modelin son cevabını döndürür.
    messages listesi yerinde güncellenir, böylece hafıza korunur."""
    for _ in range(max_turns):
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            tools=get_schemas(agent),
        )
        message = response.choices[0].message
        messages.append(message)

        if not message.tool_calls:
            return message.content

        for call in message.tool_calls:
            if on_tool_call:
                on_tool_call(call.function.name, call.function.arguments)
            result = execute(agent, call.function.name, call.function.arguments)
            messages.append({
                "role": "tool",
                "tool_call_id": call.id,
                "content": result,
            })

    return "Hata: max_turns aşıldı, agent cevabı tamamlayamadı."


def run_agent(agent, task, client, model, system_prompt=None, max_turns=10):
    """Tek seferlik görev için: sohbet gerekmeyen durumlarda kullanılır."""
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": task})
    return run_turn(agent, messages, client, model, max_turns)