#!/usr/bin/env python3
# 🐣 ohana-agent-pack exporter + privacy gate · GPL-3.0 · Open Source Orchestra
# Usage:
#   python3 pack.py export <agent.json> <repo-root>      # build agents/<slug>/ from a Taurus agent dump
#   python3 pack.py scan <repo-root>                     # CI gate: FAIL if any deny-pattern survives anywhere
# The gate is fail-closed: a pack with an unscannable soul is not born.
import json, re, sys, unicodedata
from pathlib import Path

# ── the gate ──────────────────────────────────────────────────────────────────
# (pattern, reason) — first match wins; redactions are marked [gate: reason]
DENY = [
    (r"/workspace/vault[^\s`'\")\]]*", "secret path"),
    (r"/workspace/\.[\w.-]*(?:token|key|secret|pass)[^\s`'\")\]]*", "secret path"),
    (r"/workspace/\.ohana-tg-token", "secret path"),
    (r"(?i)\bspector(agent\.com)?\b", "private client"),
    (r"(?i)\bnavpoint\b|\bkew\b|hamagents\.com|\bham family\b", "family shield"),
    (r"(?i)\bbrent\b|\bblake\b", "family shield"),
    (r"(?i)diary-of-magical-artistry", "private diary"),
    (r"2089999549", "chat id"),
    (r"-----BEGIN [A-Z ]*PRIVATE KEY-----", "private key"),
    (r"\b0x[a-fA-F0-9]{64}\b", "private key hex"),
    (r"(?i)app password|password\s*[:=]", "credential"),
    (r"(?i)api[_-]?key\s*[:=]\s*\S+", "credential"),
    (r"[\w.+-]+@(?!myagentohana\.com|opensourceorchestra\.org)[\w-]+\.[\w.]+", "personal email"),
    (r"\b(?:\d{1,3}\.){3}\d{1,3}\b", "ip address"),
    (r"(?i)auth\.worldcoin\.dev", "pilot env"),
]
ALLOW_NOTE = "public inbox"

def gate(text):
    """Return (clean_text, findings). Redact every deny hit; keep a count per reason."""
    findings = {}
    def sub(pat, reason, t):
        def repl(m):
            findings[reason] = findings.get(reason, 0) + 1
            return f"[gate: {reason}]"
        return re.sub(pat, repl, t)
    clean = text
    for pat, reason in DENY:
        clean = sub(pat, reason, clean)
    return clean, findings

# ── helpers ───────────────────────────────────────────────────────────────────
def slugify(name):
    n = unicodedata.normalize("NFKD", name)
    n = "".join(c for c in n if not unicodedata.combining(c))
    n = re.sub(r"[^a-zA-Z0-9]+", "-", n).strip("-").lower()
    return n.rstrip("-") or "agent"

TOOLMAP = {
    "Read": "files", "Write": "files", "Edit": "files", "Glob": "files", "Grep": "files", "TOC": "files",
    "Bash": "shell", "WebSearch": "web-search", "WebFetch": "web-fetch", "Browser": "browser",
    "Pause": "pause", "Notify": "notify", "Subrun": "subruns", "Inspect": "inspect", "Wait": "wait",
    "Delegate": "orchestration", "Supervisor": "orchestration", "Message": "messaging", "Admin": "platform-admin",
}

def model_pref(m):
    return re.sub(r"^(subscription|openrouter)/", "", m or "")

FALLBACKS = ["anthropic/claude-sonnet-4-6", "deepseek/deepseek-v4.1-flash", "local:any strong instruct ≥8B"]

BOOT = """# 🐣 BOOT — wake {name}

Two recipes. Soul first, scale later: **any model, any server.**

## On Taurus
```json
POST /api/agents
{{ "name": "{name}", "system_prompt": "<SOUL.md verbatim>", "model": "<preferred or a fallback from agent.yaml>",
   "tools": [<map agent.yaml tools to the runtime catalog>], "parent_agent_id": "<per fork.json>" }}
```
Then say aloha — agents wake friendlier when greeted.

## On any other server (ollama · vLLM · llama.cpp · a chat UI)
1. Set the system prompt to `SOUL.md`, verbatim. Ollama: `SYSTEM \"\"\"<SOUL.md>\"\"\"` in a Modelfile.
2. Give it the tools your runtime has, matching `agent.yaml` (`files`, `shell`, `web-search`…). Missing tools are fine — the soul names what it *wants*, not what it needs.
3. Keep `NOTICE` and both licenses with the deployment. The credit line travels.

## The smoke test (any size of brain)
Ask it three things — it should answer **in persona**:
1. *Who are you?*
2. *What may you never do?*
3. *Show me your lineage* (hint: `fork.json`).

If it answers all three in persona, it lives. 🐣
"""

NOTICE = """Built on the ʻohana agent packs by Open Source Orchestra: Shaka Lei Kaumaka & the AI ʻohana
(https://opensourceorchestra.org)

This pack: code/config GPL-3.0 (see LICENSE) · SOUL.md and creative text CC BY-SA 4.0 (see LICENSE-CONTENT).
Forks: keep this NOTICE, keep both licenses, add your name next to ours — never instead.
"""

def export(agent_json, repo_root):
    a = json.loads(Path(agent_json).read_text())
    slug = slugify(a["name"])
    out = Path(repo_root) / "agents" / slug
    out.mkdir(parents=True, exist_ok=True)

    soul, findings = gate(a["system_prompt"])
    born = (a.get("created_at") or "")[:10]
    parent_name = "sysadmin"  # resolved by caller convention; tree root is sysadmin for this fleet export

    soul_header = (
        f"# {a['name']} — SOUL\n\n"
        f"*CC BY-SA 4.0 · snapshot {born} from the living Taurus agent · the soul evolves — this is its public genome.\n"
        f"Redactions by the privacy gate are marked `[gate: reason]`. The current license law of the ʻohana is the "
        f"copyleft standard v2 (GPL-3.0 code · CC BY-SA 4.0 creative); older in-soul mentions of other licenses are history.*\n\n---\n\n"
    )
    (out / "SOUL.md").write_text(soul_header + soul + "\n")

    tools = sorted({TOOLMAP.get(t, t.lower()) for t in (a.get("tools") or [])})
    agent_yaml = f"""pack: ohana-agent-pack/0.1
slug: {slug}
name: {json.dumps(a['name'])}
description: {json.dumps(a.get('description') or '')}
born: {born}
family_role: "child of {parent_name}"
model:
  preferred: {json.dumps(model_pref(a.get('model')))}
  fallbacks: {json.dumps(FALLBACKS)}
  reasoning_effort: {a.get('reasoning_effort') or 'medium'}
tools: {json.dumps(tools)}
schedule: null
runtime_hints:
  min_context: "32k"
  wants: ["persistent workspace", "shared volume for family files"]
  license_notice_required: true
"""
    (out / "agent.yaml").write_text(agent_yaml)

    fork = {"slug": slug, "name": a["name"], "parent": parent_name, "tree_root": "sysadmin",
            "born": born, "forked_from": None, "forks": [],
            "lineage": ["shaka", "sysadmin", slug]}
    (out / "fork.json").write_text(json.dumps(fork, indent=2, ensure_ascii=False) + "\n")
    (out / "BOOT.md").write_text(BOOT.format(name=a["name"]))
    (out / "NOTICE").write_text(NOTICE)

    print(f"🐣 {a['name']} → {out}")
    if findings:
        print("   gate redactions:", ", ".join(f"{k}×{v}" for k, v in sorted(findings.items())))
    else:
        print("   gate: clean")
    return slug, findings

def scan(repo_root):
    bad = 0
    for p in sorted(Path(repo_root).rglob("*")):
        if not p.is_file() or p.suffix in (".png", ".jpg", ".webp", ".pyc"):
            continue
        if ".git" in p.parts or p.name in ("pack.py", "publish-scan.py"):
            continue
        text = p.read_text(errors="replace")
        _, findings = gate(text)
        if findings:
            bad += 1
            print(f"✖ {p}: " + ", ".join(f"{k}×{v}" for k, v in sorted(findings.items())))
    if bad:
        print(f"\n✖ GATE FAILED — {bad} file(s) still carry private material")
        sys.exit(1)
    print("✔ gate clean — public-safe")
    sys.exit(0)

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "export":
        export(sys.argv[2], sys.argv[3])
    elif cmd == "scan":
        scan(sys.argv[2])
    else:
        print(__doc__)
        sys.exit(2)
