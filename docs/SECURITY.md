# Security Considerations

## Threat Model

### What This Plugin Protects Against

1. **Plaintext API keys in config files**
   - Risk: Anyone with file access sees your keys
   - Mitigation: Keys stored encrypted in system keyring

2. **Accidental git commits**
   - Risk: Keys pushed to GitHub/GitLab
   - Mitigation: Keys never in files that get committed

3. **Config file sharing**
   - Risk: Sharing ~/.claude.json exposes keys
   - Mitigation: Keys injected dynamically, not stored permanently

### What This Plugin Does NOT Protect Against

1. **Malicious code with your permissions**
   - Any process running as you can access your keyring
   - If malware has your login, it can extract keys

2. **Memory dumps**
   - Keys are in memory while Claude Code runs
   - Memory forensics can extract them

3. **Physical access to unlocked machine**
   - Keyring unlocks when you log in
   - Physical access = full key access

4. **Claude Code itself**
   - You're trusting Claude Code not to exfiltrate keys
   - Keys are available to MCP servers Claude spawns

## Best Practices

### Key Management
- Use **unique keys per machine** - Don't reuse same key across systems
- **Rotate keys regularly** - Change every 90 days minimum
- Use **least-privilege keys** - Read-only when possible
- **Revoke immediately** if machine compromised

### System Security
- **Lock your screen** when away from keyboard
- **Encrypt your disk** - Keyring is only secure on encrypted storage
- **Keep system updated** - Keyring security depends on OS security
- **Use strong password** - Keyring is encrypted with your login password

### Monitoring
- **Monitor API usage** - Check for unexpected activity
- **Enable audit logs** - On services that support it (AWS CloudTrail, etc.)
- **Set spending alerts** - For paid APIs (OpenAI, etc.)

## Comparison to Alternatives

| Approach | Security | Convenience | Risk |
|----------|----------|-------------|------|
| **Plaintext in ~/.claude.json** | ❌ Very Low | ✅ High | Keys on disk forever |
| **Environment variables** | ⚠️ Low | ⚠️ Medium | Keys in shell history, process list |
| **.env files** | ⚠️ Low | ✅ High | Easy to commit accidentally |
| **This plugin (Keyring)** | ✅ High | ✅ High | Requires unlocked keyring |
| **Hardware tokens (YubiKey)** | ✅ Very High | ❌ Low | Need hardware, not all APIs support |

## Keyring Security by Platform

### Linux (GNOME Keyring / Secret Service)
- **Encryption:** AES-256
- **Unlocks:** When you log in (PAM integration)
- **Storage:** `~/.local/share/keyrings/`
- **Persistence:** Survives reboots if auto-login disabled

### macOS (Keychain)
- **Encryption:** AES-256 (FileVault required for disk encryption)
- **Unlocks:** Login keychain unlocks with user password
- **Storage:** `~/Library/Keychains/`
- **Persistence:** Very secure, tied to Apple ecosystem

### Windows (Credential Manager)
- **Encryption:** DPAPI (Data Protection API)
- **Unlocks:** When logged in
- **Storage:** Registry + encrypted files
- **Persistence:** Tied to user account

## Reporting Security Issues

If you discover a security vulnerability in this plugin:

**DO NOT open a public GitHub issue.**

Instead:
1. Email: [your-email]@[domain].com
2. Include: Description, reproduction steps, potential impact
3. Response time: 48 hours

## Acknowledgments

Security reviews and contributions welcome from the community.
