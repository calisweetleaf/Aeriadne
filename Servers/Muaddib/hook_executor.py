#!/usr/bin/env python3
"""
Hook Executor — executes hooks from hooks_manifest.json.

Integrates with the Somnus-MCP gateway/state machine for auto-triggering. Hooks
are lifecycle/event signals into the Muad'Dib + tools cognition plane; they are
not a second server, second tool plane, or owner of neural/Q-table state.
"""

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional


class HookExecutor:
    def __init__(self, manifest_path: str = None):
        if manifest_path is None:
            manifest_path = os.getenv(
                "SOVEREIGN_HOOKS_MANIFEST",
                "/home/daeron/Somnus-MCP/hooks_manifest.json"
            )
        self.manifest_path = Path(manifest_path)
        self.manifest = None
        self.load_manifest()

    def load_manifest(self) -> Dict[str, Any]:
        """Load hooks manifest from JSON."""
        if not self.manifest_path.exists():
            raise FileNotFoundError(f"Hooks manifest not found: {self.manifest_path}")

        with open(self.manifest_path, 'r') as f:
            self.manifest = json.load(f)
        return self.manifest

    def get_hooks_for_event(self, event_type: str) -> List[Dict[str, Any]]:
        """Get all hooks for a given event type."""
        if not self.manifest or event_type not in self.manifest.get("hooks", {}):
            return []
        return self.manifest["hooks"][event_type]

    def execute_hook(
        self,
        hook: Dict[str, Any],
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """Execute a single hook."""
        command = hook.get("command", "")
        timeout = hook.get("timeout", 10)
        plugin_name = hook.get("plugin", "unknown")
        hook_name = hook.get("name", "unknown")

        # Expand environment variables
        command = os.path.expandvars(command)

        result = {
            "plugin": plugin_name,
            "name": hook_name,
            "command": command,
            "status": "pending",
            "returncode": None,
            "stdout": "",
            "stderr": "",
            "dry_run": dry_run
        }

        if dry_run:
            result["status"] = "dry_run"
            return result

        try:
            proc = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            result["status"] = "success" if proc.returncode == 0 else "failed"
            result["returncode"] = proc.returncode
            result["stdout"] = proc.stdout
            result["stderr"] = proc.stderr
        except subprocess.TimeoutExpired:
            result["status"] = "timeout"
            result["stderr"] = f"Hook timeout after {timeout}s"
        except Exception as e:
            result["status"] = "error"
            result["stderr"] = str(e)

        return result

    def execute_event_hooks(
        self,
        event_type: str,
        dry_run: bool = False,
        matcher: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Execute all hooks for an event type."""
        hooks = self.get_hooks_for_event(event_type)
        results = []

        for hook in hooks:
            # Skip if matcher doesn't match
            if matcher and hook.get("matcher") and matcher not in hook.get("matcher", ""):
                continue

            result = self.execute_hook(hook, dry_run=dry_run)
            results.append(result)

        return results

    def get_auto_trigger_rules(self) -> Dict[str, Any]:
        """Get auto-trigger rules from manifest."""
        return self.manifest.get("autoTriggerRules", {})


def main():
    """CLI interface for hook execution."""
    import argparse

    parser = argparse.ArgumentParser(description="Execute hooks from manifest")
    parser.add_argument("event_type", nargs="?", help="Event type (PreToolUse, PostToolUse, Stop, etc.)")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be executed")
    parser.add_argument("--manifest", help="Path to hooks manifest")
    parser.add_argument("--list", action="store_true", help="List all hooks")
    parser.add_argument("--list-events", action="store_true", help="List all event types")

    args = parser.parse_args()

    try:
        executor = HookExecutor(manifest_path=args.manifest)

        if args.list_events:
            print("Available events:")
            for event in executor.manifest.get("hooks", {}).keys():
                print(f"  - {event}")
            return 0

        if args.list:
            print("All hooks:")
            for event, hooks in executor.manifest.get("hooks", {}).items():
                print(f"\n{event}:")
                for hook in hooks:
                    print(f"  - {hook.get('plugin')}/{hook.get('name')}")
            return 0

        if not args.event_type:
            parser.print_help()
            return 1

        results = executor.execute_event_hooks(args.event_type, dry_run=args.dry_run)

        if not results:
            print(f"No hooks found for event: {args.event_type}")
            return 1

        print(json.dumps(results, indent=2))

        # Exit with error if any hook failed
        for result in results:
            if result["status"] not in ["success", "dry_run"]:
                return 1

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
