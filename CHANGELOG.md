# Changelog

All notable changes to fastapi-sse-events will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2026-03-04

### Added
- Comprehensive documentation website with interactive examples
- CHANGELOG.md for tracking version history
- Enhanced PyPI metadata and project URLs
- Professional README.md with complete usage examples
- Support for Python 3.10, 3.11, and 3.12
- Type hints marker (`py.typed`) for IDE support
- Improved error handling in SSE event listeners
- Better debugging console logs in frontend examples

### Changed
- Updated project structure to match industry standards
- Reorganized examples for better clarity
- Enhanced pyproject.toml with detailed classifiers
- Improved package exports in `__init__.py`
- Updated author information and repository links

### Fixed
- JavaScript regex escaping issues in HTML string context
- SSE event parsing in browser EventSource
- Syntax errors in frontend event handlers
- Event listener attachment and routing

## [0.1.0] - 2025-01-15

### Added
- Initial release of fastapi-sse-events
- Server-Sent Events (SSE) support for FastAPI
- Redis Pub/Sub backend for horizontal scaling
- Decorator-based API for easy integration
- Topic-based event routing
- Authorization hooks for secure subscriptions
- Heartbeat support for connection keepalive
- Comprehensive test suite
- Examples for CRM, quickstart, and production deployment

### Features
- `SSEApp` - Simplified FastAPI application with SSE support
- `EventBroker` - Core event publishing and subscription engine
- `@publish_event` - Decorator for automatic event publishing
- `@subscribe_to_events` - Decorator for SSE endpoint creation
- `TopicBuilder` - Helper for constructing topic strings
- `MetricsCollector` - Built-in metrics for monitoring
- Health check endpoints

### Documentation
- Comprehensive README with usage examples
- API reference documentation
- Deployment guide for production
- Client integration examples (JavaScript, React)

---

## Release Types

- **Major** (x.0.0): Breaking changes, major new features
- **Minor** (0.x.0): New features, backward compatible
- **Patch** (0.0.x): Bug fixes, minor improvements

## Links

- [PyPI Package](https://pypi.org/project/fastapi-sse-events/)
- [GitHub Repository](https://github.com/bhadri01/fastapi_sse_events)
- [Documentation](https://bhadri01.github.io/fastapi_sse_events)
- [Issue Tracker](https://github.com/bhadri01/fastapi_sse_events/issues)
