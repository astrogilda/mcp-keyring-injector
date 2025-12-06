# MCP Keyring Injector

Securely inject MCP server API credentials from your system keyring into Claude Code configuration at session start. No more API keys in config files!

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

## The Problem

MCP servers in Claude Code require API keys in their environment configuration (`~/.claude.json`). Storing API keys in config files is a security risk:
- Keys are in plaintext on disk
- Easy to accidentally commit to git
- Shared across all projects
- Hard to rotate without editing configs

## The Solution

This plugin solves the problem by:
1. Storing API keys in your **system keyring** (encrypted)
2. **Dynamically injecting** them into `~/.claude.json` when Claude Code starts
3. **Automatically removing** them when the session ends
4. Working **cross-platform** (Linux, macOS, Windows)

## Features

- **Secure**: Keys stored encrypted in system keyring
- **Cross-platform**: Works on Linux (GNOME Keyring), macOS (Keychain), Windows (Credential Manager)
- **Automatic**: Runs on every Claude Code session start
- **Flexible**: Configure multiple MCP services from one file
- **Zero overhead**: Adds <100ms to session startup

## Installation

### 1. Install the plugin

```bash
# Via Claude Code plugin system
/plugin marketplace add astrogilda/claude-plugins
/plugin install mcp-keyring-injector

# Or manually
git clone https://github.com/astrogilda/mcp-keyring-injector.git ~/Documents/mcp-keyring-injector
```

### 2. Install Python dependencies

```bash
uv pip install keyring
```

### 3. Store your first API key

Choose your platform:

**Linux (GNOME Keyring):**
```bash
python3 -c "import keyring; keyring.set_password('github', 'api-key', 'YOUR_API_KEY')"
```

**macOS (Keychain):**
```bash
security add-generic-password -s github -a api-key -w YOUR_API_KEY
```

**Windows (PowerShell):**
```powershell
cmdkey /generic:github /user:api-key /pass:YOUR_API_KEY
```

### 4. Configure MCP credentials

Create `~/.claude/config/mcp-credentials.json`:

```json
{
  "github": {
    "env_var": "GITHUB_TOKEN",
    "service": "github",
    "account": "api-key",
    "label": "GitHub API Token",
    "mcp_server": "github-mcp"
  }
}
```

See `examples/mcp-credentials.json` for more examples.

### 5. Verify it works

Restart Claude Code. You should see:
```
MCP credentials - Injected: GitHub API Token
```

Check your GitHub MCP tools are now available!

## Configuration

### Config File Format

`~/.claude/config/mcp-credentials.json`:

```json
{
  "service-name": {
    "env_var": "ENVIRONMENT_VARIABLE_NAME",
    "service": "keyring-service-name",
    "account": "keyring-account-name",
    "label": "Human Readable Label",
    "mcp_server": "mcp-server-name-in-claude.json"
  }
}
```

**Fields:**
- `env_var`: Environment variable the MCP server expects (e.g., `GITHUB_TOKEN`)
- `service`: Keyring service name (how you stored the key)
- `account`: Keyring account/username (how you stored the key)
- `label`: Display name in status messages
- `mcp_server`: MCP server name from `~/.claude.json` (defaults to service-name if omitted)

### Adding Multiple Services

```json
{
  "github": {
    "env_var": "GITHUB_TOKEN",
    "service": "github",
    "account": "api-key",
    "label": "GitHub API Token",
    "mcp_server": "github-mcp"
  },
  "openai": {
    "env_var": "OPENAI_API_KEY",
    "service": "openai",
    "account": "api-key",
    "label": "OpenAI API Key",
    "mcp_server": "openai-mcp"
  }
}
```

## How It Works

```
Claude Code Session Start
         ↓
SessionStart hook triggered
         ↓
Read ~/.claude/config/mcp-credentials.json
         ↓
For each service:
  ├─ Retrieve API key from system keyring
  ├─ Inject into ~/.claude.json MCP server env
  └─ Report success/failure
         ↓
Claude Code continues startup
         ↓
MCP servers start with injected credentials
```

## Security Considerations

### What This Protects Against
- ✅ API keys in plaintext config files
- ✅ Accidental git commits of secrets
- ✅ Unauthorized file access (keyring requires user authentication)

### What This Doesn't Protect Against
- ❌ Malicious code with your user permissions (can access keyring)
- ❌ Physical access to unlocked machine
- ❌ Memory dumps while Claude Code is running

### Best Practices
1. Use unique API keys per machine
2. Rotate keys regularly
3. Use least-privilege API keys (read-only when possible)
4. Don't share `~/.claude/config/mcp-credentials.json` (it's not secret, but lists your services)

## Troubleshooting

### "MCP credentials - Failed: X (not in keyring)"

The key isn't stored in your system keyring.

**Solution:**
```bash
python3 -c "import keyring; keyring.set_password('service', 'account', 'YOUR_KEY')"
```

### "MCP credentials - Failed: X (MCP server 'Y' not found)"

The MCP server name doesn't match what's in `~/.claude.json`.

**Solution:** Check your MCP server name:
```bash
jq '.mcpServers | keys' ~/.claude.json
```

Update `mcp_server` field in config to match.

### "ERROR: keyring library not installed"

Python keyring library is missing.

**Solution:**
```bash
uv pip install keyring
```

### Hook runs but tools still unavailable

Check MCP server logs:
```bash
ls ~/.cache/claude-cli-nodejs/*/mcp-logs-*/
cat ~/.cache/claude-cli-nodejs/*/mcp-logs-github-mcp/*.txt
```

Look for errors about missing API keys.

## Development

### Project Structure
```
claude-mcp-credentials/
├── .claude-plugin/
│   └── plugin.json          # Plugin metadata
├── hooks/
│   └── inject-credentials.py  # SessionStart hook
├── examples/
│   └── mcp-credentials.json   # Example config
├── docs/
│   └── SECURITY.md            # Security considerations
├── README.md
└── LICENSE
```

### Testing Locally

```bash
# Test the hook directly
echo '{}' | ~/Documents/claude-mcp-credentials/hooks/inject-credentials.py

# Check if keys were injected
jq '.mcpServers."github-mcp".env' ~/.claude.json
```

### Contributing

Contributions welcome! Please:
1. Fork the repo
2. Create a feature branch
3. Add tests for new functionality
4. Ensure code passes black + ruff
5. Submit PR with clear description

## License

MIT License - see LICENSE file for details.

## Credits

Created by [@astrogilda](https://github.com/astrogilda)

Uses the excellent [keyring](https://github.com/jaraco/keyring) library by Jason R. Coombs.

## Links

- [Claude Code Documentation](https://docs.anthropic.com/en/docs/claude-code)
- [MCP Protocol](https://modelcontextprotocol.io/)
- [Python Keyring Library](https://github.com/jaraco/keyring)
