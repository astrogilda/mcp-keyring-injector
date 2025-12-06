#!/usr/bin/env python3
"""
Claude Code MCP Credential Injector

Dynamically injects MCP server API credentials from system keyring into Claude Code
configuration at session start. Prevents storing API keys in config files.

Author: https://github.com/astrogilda
License: MIT

Problem Solved:
--------------
MCP servers spawned by Claude Code do not inherit environment variables from
SessionStart hooks. API keys must be in ~/.claude.json env sections, but storing
them there is a security risk. This hook solves the problem by:
  1. Reading API keys from system keyring (encrypted storage)
  2. Dynamically injecting them into ~/.claude.json at session start
  3. Removing them when the session ends (handled by Claude Code)

Usage:
------
1. Store API key in system keyring:

   Linux (GNOME Keyring):
   $ secret-tool store --label="GitHub API Token" service github account api-key

   macOS (Keychain):
   $ security add-generic-password -s github -a api-key -w

   Windows (PowerShell):
   > cmdkey /generic:github /user:api-key /pass

   Or use Python keyring library:
   $ python3 -c "import keyring; keyring.set_password('github', 'api-key', 'YOUR_API_KEY')"

2. Create ~/.claude/config/mcp-credentials.json:
   {
     "github": {
       "env_var": "GITHUB_TOKEN",
       "service": "github",
       "account": "api-key",
       "label": "GitHub API Token",
       "mcp_server": "github-mcp"
     }
   }

3. Enable hook in ~/.claude/settings.json:
   "hooks": {
     "SessionStart": [{
       "hooks": [{
         "type": "command",
         "command": "/path/to/inject-mcp-credentials.py",
         "timeout": 5
       }]
     }]
   }

Configuration Format:
--------------------
{
  "service-name": {
    "env_var": "ENV_VARIABLE_NAME",        # Environment variable to inject
    "service": "keyring-service-name",     # Keyring service name
    "account": "keyring-account-name",     # Keyring account name
    "label": "Human readable label",       # Display name for status messages
    "mcp_server": "mcp-server-name"        # MCP server in ~/.claude.json (optional)
  }
}

If "mcp_server" is omitted, defaults to "service-name".

Requirements:
------------
- Python keyring library (uv pip install keyring)
- System keyring (macOS Keychain, GNOME Keyring, Windows Credential Manager)
- Claude Code with MCP support
- Python 3.10+
"""

import json
import sys
from pathlib import Path
from typing import Any, Dict, Optional

try:
    import keyring
except ImportError:
    print(
        json.dumps(
            {
                "systemMessage": "ERROR: keyring library not installed. Run: uv pip install keyring"
            }
        )
    )
    sys.exit(1)


def get_key_from_keyring(service: str, account: str) -> Optional[str]:
    """
    Retrieve API key from system keyring (cross-platform).

    Uses Python keyring library which automatically detects and uses:
    - macOS: Keychain
    - Linux: GNOME Keyring, KWallet, or Secret Service API
    - Windows: Windows Credential Manager

    Args:
        service: Keyring service name
        account: Keyring account (username)

    Returns:
        API key if found, None otherwise
    """
    try:
        # keyring uses service as service_name and account as username
        password = keyring.get_password(service, account)
        return password if password else None
    except Exception:
        # Keyring backend not available or other error
        return None


def load_config() -> Dict[str, Dict[str, str]]:
    """Load MCP credentials configuration from JSON file."""
    config_path = Path.home() / ".claude" / "config" / "mcp-credentials.json"

    if not config_path.exists():
        return {}

    try:
        with open(config_path) as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(
            json.dumps(
                {
                    "systemMessage": f"WARNING: Failed to load mcp-credentials.json: {e}",
                }
            )
        )
        return {}


def load_claude_config() -> Optional[Dict[str, Any]]:
    """Load ~/.claude.json configuration."""
    config_path = Path.home() / ".claude.json"

    if not config_path.exists():
        return None

    try:
        with open(config_path) as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(
            json.dumps(
                {
                    "systemMessage": f"WARNING: Failed to load .claude.json: {e}",
                }
            )
        )
        return None


def save_claude_config(config: Dict[str, Any]) -> bool:
    """Save ~/.claude.json configuration."""
    config_path = Path.home() / ".claude.json"

    try:
        with open(config_path, "w") as f:
            json.dump(config, f, indent=2)
        return True
    except IOError as e:
        print(
            json.dumps(
                {
                    "systemMessage": f"WARNING: Failed to save .claude.json: {e}",
                }
            )
        )
        return False


def main() -> None:
    """Inject MCP API keys into ~/.claude.json MCP server env sections."""
    # Claude Code hook protocol requires reading stdin even if unused
    _ = json.loads(sys.stdin.read())

    # Load configurations
    cred_config = load_config()
    claude_config = load_claude_config()

    if not cred_config:
        # No MCP credentials configured
        return

    if not claude_config or "mcpServers" not in claude_config:
        print(
            json.dumps(
                {
                    "systemMessage": "WARNING: No MCP servers configured in ~/.claude.json",
                }
            )
        )
        return

    # Track results
    loaded = []
    failed = []
    modified = False

    # Process each configured service
    for service_name, service_config in cred_config.items():
        env_var = service_config.get("env_var")
        keyring_service = service_config.get("service")
        keyring_account = service_config.get("account")
        label = service_config.get("label", service_name)
        mcp_server = service_config.get("mcp_server", service_name)

        if not all([env_var, keyring_service, keyring_account]):
            failed.append(f"{label} (incomplete config)")
            continue

        # Check if MCP server exists in config
        if mcp_server not in claude_config["mcpServers"]:
            failed.append(f"{label} (MCP server '{mcp_server}' not found)")
            continue

        # Retrieve from keyring
        api_key = get_key_from_keyring(keyring_service, keyring_account)

        if api_key:
            # Inject into MCP server env section
            if "env" not in claude_config["mcpServers"][mcp_server]:
                claude_config["mcpServers"][mcp_server]["env"] = {}

            claude_config["mcpServers"][mcp_server]["env"][env_var] = api_key
            loaded.append(label)
            modified = True
        else:
            failed.append(f"{label} (not in keyring)")

    # Save modified config
    if modified:
        if not save_claude_config(claude_config):
            print(
                json.dumps(
                    {
                        "systemMessage": "ERROR: Failed to save MCP credentials to ~/.claude.json",
                    }
                )
            )
            return

    # Build status message
    messages = []
    if loaded:
        messages.append(f"Injected: {', '.join(loaded)}")
    if failed:
        messages.append(f"Failed: {', '.join(failed)}")

    if messages:
        output = {
            "systemMessage": f"MCP credentials - {' | '.join(messages)}",
        }
        print(json.dumps(output))


if __name__ == "__main__":
    main()
