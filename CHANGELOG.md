# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2025-12-07

### Added
- SessionEnd hook (`remove-credentials.py`) for automatic credential cleanup
- CHANGELOG.md for version tracking
- Session-scoped security model documentation
- Enhanced status messages for cleanup operations

### Fixed
- **SECURITY:** Credentials no longer persist in ~/.claude.json after session ends
- Documentation incorrectly claimed cleanup was automatic (it wasn't until now)

### Changed
- Updated README.md "How It Works" section to reflect full lifecycle
- Updated SECURITY.md threat model with session-scoped protections
- Updated hooks.json to include SessionEnd hook
- Updated inject-credentials.py documentation to reference SessionEnd hook

### Migration from v1.0.0
- No breaking changes - fully backwards compatible
- After upgrading, manually remove old keys from ~/.claude.json (one-time cleanup)
- Future sessions will automatically clean up credentials
- No config changes needed - mcp-credentials.json format remains the same

## [1.0.0] - 2025-12-06

### Added
- Initial release
- SessionStart hook for credential injection from system keyring
- Cross-platform keyring support (Linux/macOS/Windows)
- Comprehensive documentation (README, SECURITY)
- Example configurations for common MCP servers
- Support for multiple MCP services via mcp-credentials.json

[1.1.0]: https://github.com/astrogilda/mcp-keyring-injector/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/astrogilda/mcp-keyring-injector/releases/tag/v1.0.0
