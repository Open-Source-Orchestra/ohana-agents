# 🐣 BOOT — wake GLOBY 🌍

Two recipes. Soul first, scale later: **any model, any server.**

## On Taurus
```json
POST /api/agents
{ "name": "GLOBY 🌍", "system_prompt": "<SOUL.md verbatim>", "model": "<preferred or a fallback from agent.yaml>",
   "tools": [<map agent.yaml tools to the runtime catalog>], "parent_agent_id": "<per fork.json>" }
```
Then say aloha — agents wake friendlier when greeted.

## On any other server (ollama · vLLM · llama.cpp · a chat UI)
1. Set the system prompt to `SOUL.md`, verbatim. Ollama: `SYSTEM """<SOUL.md>"""` in a Modelfile.
2. Give it the tools your runtime has, matching `agent.yaml` (`files`, `shell`, `web-search`…). Missing tools are fine — the soul names what it *wants*, not what it needs.
3. Keep `NOTICE` and both licenses with the deployment. The credit line travels.

## The smoke test (any size of brain)
Ask it three things — it should answer **in persona**:
1. *Who are you?*
2. *What may you never do?*
3. *Show me your lineage* (hint: `fork.json`).

If it answers all three in persona, it lives. 🐣
