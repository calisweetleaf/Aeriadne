#!/usr/bin/env python3
"""Non-destructive Grok Build setup diagnostic.

The script avoids printing secret values. It reads config files, checks syntax,
reports discovered sections, and highlights common setup mistakes from the
uploaded xAI docs.
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

try:
    import tomllib  # Python 3.11+
except Exception:  # pragma: no cover
    tomllib = None

SECRET_RE = re.compile(r"(KEY|TOKEN|SECRET|PASSWORD|PASS|AUTH|CREDENTIAL|DSN)", re.I)
KNOWN_GLOBAL_TOP = {
    "cli", "models", "ui", "features", "session", "tools", "toolset", "auth",
    "grok_com_config", "model", "endpoints", "mcp_servers", "memory", "subagents",
    "skills", "plugins", "compat", "telemetry", "permission", "marketplace",
}
PROJECT_ALLOWED_TOP = {"mcp_servers", "permission"}
AGENT_RULE_NAMES = ["Agents.md", "Claude.md", "CLAUDE.md", "CLAUDE.local.md", "AGENT.md", "AGENTS.md"]


def redact_value(key: str, value: str | None) -> str:
    if value is None:
        return "<unset>"
    if SECRET_RE.search(key):
        if not value:
            return "<empty>"
        return f"<redacted:{len(value)} chars>"
    return value


def run(cmd: list[str], timeout: float = 5.0) -> dict[str, Any]:
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return {
            "ok": proc.returncode == 0,
            "returncode": proc.returncode,
            "stdout": proc.stdout.strip(),
            "stderr": proc.stderr.strip(),
        }
    except FileNotFoundError:
        return {"ok": False, "error": "not found"}
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": f"timed out after {timeout}s"}


def load_toml(path: Path) -> dict[str, Any]:
    result: dict[str, Any] = {"path": str(path), "exists": path.exists()}
    if not path.exists():
        return result
    if tomllib is None:
        result["warning"] = "Python tomllib unavailable, syntax not checked"
        return result
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
        result["valid"] = True
        result["top_level_sections"] = sorted(data.keys())
        result["data"] = data
    except Exception as exc:
        result["valid"] = False
        result["error"] = str(exc)
    return result


def summarize_mcp(data: dict[str, Any]) -> list[dict[str, Any]]:
    servers = data.get("mcp_servers") if isinstance(data, dict) else None
    if not isinstance(servers, dict):
        return []
    out: list[dict[str, Any]] = []
    for name, cfg in sorted(servers.items()):
        if not isinstance(cfg, dict):
            out.append({"name": name, "error": "server config is not a table"})
            continue
        transport = "http" if cfg.get("url") else "stdio" if cfg.get("command") else "unknown"
        item = {
            "name": name,
            "transport": transport,
            "enabled": cfg.get("enabled", True),
            "has_env": isinstance(cfg.get("env"), dict),
            "has_headers": isinstance(cfg.get("headers"), dict),
            "startup_timeout_sec": cfg.get("startup_timeout_sec"),
            "tool_timeout_sec": cfg.get("tool_timeout_sec"),
        }
        if transport == "http":
            item["url"] = cfg.get("url")
        elif transport == "stdio":
            item["command"] = cfg.get("command")
            item["args_count"] = len(cfg.get("args", [])) if isinstance(cfg.get("args"), list) else 0
        out.append(item)
    return out


def find_project_rules(project: Path) -> list[str]:
    found = []
    cur = project.resolve()
    candidates = [cur]
    # Walk upward until git root if present, otherwise just cwd.
    root = cur
    while True:
        if (root / ".git").exists():
            break
        if root.parent == root:
            root = cur
            break
        root = root.parent
    if root != cur:
        parts = []
        p = cur
        while True:
            parts.append(p)
            if p == root:
                break
            p = p.parent
        candidates = list(reversed(parts))
    for d in candidates:
        for name in AGENT_RULE_NAMES:
            p = d / name
            if p.exists():
                found.append(str(p))
                break
        rules_dir = d / ".grok" / "rules"
        if rules_dir.exists():
            found.extend(str(x) for x in sorted(rules_dir.glob("*.md")))
    return found


def collect(args: argparse.Namespace) -> dict[str, Any]:
    project = Path(args.project).expanduser().resolve()
    home = Path(os.environ.get("GROK_HOME", "~/.grok")).expanduser()
    grok_path = shutil.which("grok")
    env_keys = [k for k in sorted(os.environ) if k == "XAI_API_KEY" or k.startswith("GROK_") or k.startswith("XAI_")]

    global_config = load_toml(home / "config.toml")
    pager_config = load_toml(home / "pager.toml")
    project_config = load_toml(project / ".grok" / "config.toml")

    warnings: list[str] = []
    if global_config.get("valid"):
        unknown = sorted(set(global_config.get("top_level_sections", [])) - KNOWN_GLOBAL_TOP)
        if unknown:
            warnings.append(f"Unknown top-level sections in global config: {', '.join(unknown)}")
    if project_config.get("valid"):
        invalid = sorted(set(project_config.get("top_level_sections", [])) - PROJECT_ALLOWED_TOP)
        if invalid:
            warnings.append("Project .grok/config.toml is expected to contain [mcp_servers] and optionally [permission]; found global-only or unknown sections: " + ", ".join(invalid))

    if os.environ.get("XAI_API_KEY"):
        warnings.append("XAI_API_KEY is set and takes precedence over browser/OIDC/external auth credentials.")

    report: dict[str, Any] = {
        "system": {
            "platform": platform.platform(),
            "python": sys.version.split()[0],
            "shell": os.environ.get("SHELL") or os.environ.get("COMSPEC"),
            "cwd": str(Path.cwd()),
            "project": str(project),
            "grok_home": str(home),
        },
        "grok_binary": {
            "path": grok_path,
            "version": run([grok_path, "--version"]) if grok_path else {"ok": False, "error": "grok not found on PATH"},
        },
        "environment": {k: redact_value(k, os.environ.get(k)) for k in env_keys},
        "files": {
            "global_config": {k: v for k, v in global_config.items() if k != "data"},
            "pager_config": {k: v for k, v in pager_config.items() if k != "data"},
            "auth_json_exists": (home / "auth.json").exists(),
            "sessions_dir_exists": (home / "sessions").exists(),
            "memory_dir_exists": (home / "memory").exists(),
            "logs_dir_exists": (home / "logs").exists(),
            "user_skills_dir_exists": (home / "skills").exists(),
            "user_plugins_dir_exists": (home / "plugins").exists(),
            "user_agents_dir_exists": (home / "agents").exists(),
            "user_hooks_dir_exists": (home / "hooks").exists(),
            "project_config": {k: v for k, v in project_config.items() if k != "data"},
            "project_rules": find_project_rules(project),
            "project_grok_dirs": [str(p) for p in sorted((project / ".grok").glob("*"))] if (project / ".grok").exists() else [],
        },
        "mcp_servers": {
            "global": summarize_mcp(global_config.get("data", {})),
            "project": summarize_mcp(project_config.get("data", {})),
        },
        "warnings": warnings,
        "suggested_next_checks": [
            "Run `grok inspect` to verify discovered rules, skills, plugins, hooks, and MCP servers.",
            "Run `grok mcp list --json` if MCP servers are configured.",
            "Run `GROK_LOG_FILE=1 GROK_LOG_FILTER=debug grok -p \"hello\" --output-format json` for debug logs.",
        ],
    }

    if args.run_inspect and grok_path:
        report["grok_inspect"] = run([grok_path, "inspect", "--json"], timeout=args.inspect_timeout)
    return report


def print_markdown(report: dict[str, Any]) -> None:
    print("# Grok Build Doctor Report")
    print()
    sysinfo = report["system"]
    print(f"- Platform: `{sysinfo['platform']}`")
    print(f"- Project: `{sysinfo['project']}`")
    print(f"- Grok home: `{sysinfo['grok_home']}`")
    print(f"- Grok binary: `{report['grok_binary']['path'] or 'not found'}`")
    ver = report["grok_binary"]["version"]
    if ver.get("ok"):
        print(f"- Grok version: `{ver.get('stdout') or ver.get('stderr')}`")
    else:
        print(f"- Grok version check: `{ver.get('error') or ver.get('stderr') or 'failed'}`")
    print()

    print("## Environment")
    env = report.get("environment", {})
    if env:
        for k, v in env.items():
            print(f"- `{k}` = `{v}`")
    else:
        print("- No GROK_/XAI_ environment variables detected.")
    print()

    print("## Files")
    files = report["files"]
    for label in ["global_config", "pager_config", "project_config"]:
        item = files[label]
        status = "exists" if item.get("exists") else "missing"
        extra = ""
        if item.get("exists"):
            extra = ", valid TOML" if item.get("valid") else f", invalid TOML: {item.get('error', 'unknown error')}"
            if item.get("top_level_sections"):
                extra += ", sections: " + ", ".join(item["top_level_sections"])
        print(f"- {label}: `{item.get('path')}`: {status}{extra}")
    for key in ["auth_json_exists", "sessions_dir_exists", "memory_dir_exists", "logs_dir_exists", "user_skills_dir_exists", "user_plugins_dir_exists", "user_agents_dir_exists", "user_hooks_dir_exists"]:
        print(f"- {key}: `{files[key]}`")
    if files["project_rules"]:
        print("- Project rules:")
        for p in files["project_rules"]:
            print(f"  - `{p}`")
    print()

    print("## MCP servers")
    for scope in ["global", "project"]:
        servers = report["mcp_servers"][scope]
        print(f"### {scope}")
        if not servers:
            print("- none")
        for s in servers:
            bits = [f"transport={s.get('transport')}", f"enabled={s.get('enabled')}"]
            if s.get("url"):
                bits.append(f"url={s['url']}")
            if s.get("command"):
                bits.append(f"command={s['command']}")
                bits.append(f"args_count={s.get('args_count')}")
            if s.get("has_env"):
                bits.append("has_env=true")
            if s.get("has_headers"):
                bits.append("has_headers=true")
            print(f"- `{s.get('name')}`: " + ", ".join(bits))
    print()

    if report.get("warnings"):
        print("## Warnings")
        for w in report["warnings"]:
            print(f"- {w}")
        print()

    print("## Suggested next checks")
    for item in report["suggested_next_checks"]:
        print(f"- {item}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit Grok Build CLI setup without printing secrets.")
    parser.add_argument("--project", default=".", help="Project directory to inspect. Default: current directory.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of Markdown.")
    parser.add_argument("--run-inspect", action="store_true", help="Also run `grok inspect --json`. Disabled by default to avoid surprises.")
    parser.add_argument("--inspect-timeout", type=float, default=15.0, help="Timeout for `grok inspect --json` when --run-inspect is used.")
    args = parser.parse_args()
    report = collect(args)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_markdown(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
