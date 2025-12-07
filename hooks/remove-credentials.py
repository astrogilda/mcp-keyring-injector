#!/usr/bin/env python3
"""
Claude Code MCP Credential Cleanup Hook

Removes MCP API credentials from ~/.claude.json at session end for security.
Companion to inject-credentials.py SessionStart hook.

Author: https://github.com/astrogilda
License: MIT

Security Model:
--------------
1. SessionStart: inject-credentials.py reads keys from keyring -> writes to ~/.claude.json
2. Session runs: MCP servers read from ~/.claude.json env sections
3. SessionEnd: THIS HOOK removes keys from ~/.claude.json -> keys only in keyring

This ensures API keys exist in config files ONLY while Claude Code is running.

Usage:
------
This hook is installed automatically by the mcp-keyring-injector plugin.

To enable manually, add to ~/.claude/settings.json:

"hooks": {
  "SessionEnd": [{
    "hooks": [{
      "type": "command",
      "command": "${CLAUDE_PLUGIN_ROOT}/hooks/remove-credentials.py",
      "timeout": 5
    }]
  }]
}

Configuration:
-------------
Reads from ~/.claude/config/mcp-credentials.json (same format as inject-credentials.py)
Removes the env_var from each configured MCP server's env section.

Example mcp-credentials.json:
{
  "github": {
    "env_var": "GITHUB_TOKEN",
    "service": "github",
    "account": "api-key",
    "label": "GitHub API Token",
    "mcp_server": "github-mcp"
  }
}

Requirements:
------------
- Claude Code with MCP support
- Python 3.10+
- Companion inject-credentials.py hook for SessionStart
"""

import json
import sys
from pathlib import Path
from typing import Any, Dict


def load_config() -> Dict[str, Dict[str, str]]:
    """Load MCP credentials configuration from JSON file."""
    config_path = Path.home() / ".claude" / "config" / "mcp-credentials.json"

    if not config_path.exists():
        return {}

    try:
        with open(config_path) as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}


def load_claude_config() -> Dict[str, Any] | None:
    """Load ~/.claude.json configuration."""
    config_path = Path.home() / ".claude.json"

    if not config_path.exists():
        return None

    try:
        with open(config_path) as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return None


def save_claude_config(config: Dict[str, Any]) -> bool:
    """Save ~/.claude.json configuration."""
    config_path = Path.home() / ".claude.json"

    try:
        with open(config_path, "w") as f:
            json.dump(config, f, indent=2)
        return True
    except IOError:
        return False


def format_status_message(
    removed: list[str], failed_to_save: bool = False
) -> Dict[str, Any]:
    """
    Format status message with success/failure categorization.

    Args:
        removed: List of service labels that were successfully cleaned up
        failed_to_save: Whether saving ~/.claude.json failed

    Returns:
        Hook response dict with decision and systemMessage
    """
    if failed_to_save:
        return {
            "decision": "approve",
            "systemMessage": (
                f"WARNING: MCP credentials cleanup - Removed {len(removed)} credential(s) "
                f"but failed to save ~/.claude.json\n"
                f"  Credentials may still be present in config file\n"
                f"  Manual cleanup may be required"
            ),
        }

    if removed:
        return {
            "decision": "approve",
            "systemMessage": f"Cleaned up {len(removed)} MCP credential(s): {', '.join(removed)}",
        }

    # Nothing to remove - this is normal and expected
    return {
        "decision": "approve",
        "systemMessage": "INFO: MCP credentials already clean (no credentials to remove)",
    }


def main() -> None:
    """Remove MCP API keys from ~/.claude.json MCP server env sections."""
    # Claude Code hook protocol requires reading stdin even if unused
    try:
        _ = json.loads(sys.stdin.read())
    except json.JSONDecodeError:
        pass

    # Load configurations
    cred_config = load_config()
    claude_config = load_claude_config()

    if not cred_config or not claude_config:
        # Nothing to clean up
        print(json.dumps({"decision": "approve"}))
        return

    if "mcpServers" not in claude_config:
        print(json.dumps({"decision": "approve"}))
        return

    # Track cleanup
    removed = []
    failed_to_save = False
    modified = False

    # Process each configured service
    for service_name, service_config in cred_config.items():
        env_var = service_config.get("env_var")
        label = service_config.get("label", service_name)
        mcp_server = service_config.get("mcp_server", service_name)

        if not env_var or mcp_server not in claude_config["mcpServers"]:
            continue

        # Remove env var if it exists
        mcp_config = claude_config["mcpServers"][mcp_server]
        if "env" in mcp_config and env_var in mcp_config["env"]:
            del mcp_config["env"][env_var]
            removed.append(label)
            modified = True

            # Clean up empty env dict
            if not mcp_config["env"]:
                del mcp_config["env"]

    # Save modified config
    if modified:
        if not save_claude_config(claude_config):
            failed_to_save = True

    # Build and output status message
    response = format_status_message(removed, failed_to_save)
    print(json.dumps(response))


if __name__ == "__main__":
    main()
