# Known Bugs & Issues

## Security

| Severity | Issue | Location |
|----------|-------|----------|
| Medium | API key stored in **plaintext** at `%APPDATA%\tailscale-manager\.env` — no encryption, no DPAPI, no keyring integration | `config.py:21-31` |
| Low | `config.save()` writes API key to `os.environ`, leaking it to all child processes (including `tailscale` subprocess calls that don't need it) | `config.py:32-33` |
| Low | ACL view sends user-entered JSON directly to Tailscale API after only `json.loads()` parsing — no schema validation, no dry-run guard before `set_acl()` | `acls.py:168-174` |
| Low | HuJSON comment stripper (`_strip_hujson`) mangles string literals containing `//`, `/*`, or `#` before sending to API | `api_client.py:8-25` |

## Bugs

| Severity | Issue | Location |
|----------|-------|----------|
| **High** | **Crash in Serve/Funnel view**: if `funnel_status()` fails, error handler calls `_render_funnel([])` which calls `_build_route_list([], "funnel")` → `[].routes` raises `AttributeError` | `serve_funnel.py:82-83` → `serve_funnel.py:89-90` |
| Medium | **Exit Node toggle clobbers all settings**: `exit_nodes.py:118` calls `self.cli.up(exit_node=ip)` with defaults, overwriting user's `accept_dns`, `ssh`, `advertise_routes` preferences from Settings view | `exit_nodes.py:115-122` |
| Medium | **Same issue for disable**: `exit_nodes.py:126` calls `self.cli.up()` with zero arguments, resetting everything to defaults | `exit_nodes.py:124-130` |
| Low | `TailscaleAPIClient._request()` catches `Exception` broadly (line 52); if `_strip_hujson` + re-parse fails, exception goes unhandled | `api_client.py:50-54` |
| Low | `ServeConfig.from_json()` hardcodes TCP port lookup as `["TCP"]["443"]` — silently produces empty routes if port or key name differs | `tailscale_cli.py:64` |

## Code Quality

| Issue | Location |
|-------|----------|
| No tests exist — zero test files, no `pytest`, no test configuration | entire project |
| `validate_acl` has dead re-raise — `except TailscaleAPIError as e: raise e` is a no-op | `api_client.py:72-77` |
| Funnel errors silently swallowed — serve errors are shown to user, funnel errors just show empty list (inconsistent UX) | `serve_funnel.py:82` |
| `config.py` environment leakage — `save()` writes to `os.environ` (process-global mutable state) | `config.py:32-33` |
| `DashboardView.load()` rebuilds full control tree on every refresh — inefficient, causes flickering; should update values in-place | `dashboard.py:94-99` |
| Hardcoded Windows path in `get_tailscale_path()` — misses `Program Files (x86)` and custom installs | `tailscale_cli.py:192-194` |
| `httpx` used directly but only a transitive dependency — if `flet` drops `httpx`, `api_client.py` breaks | `pyproject.toml:7-10` |
| `pyproject.toml` says `>=3.10`, `.python-version` says `3.14` — misleading minimum version claim | `pyproject.toml:6` vs `.python-version` |
| `constants.py:ROUTES` dict defined but unused — routes are hardcoded in `app.py:40-47` and `NAV_ITEMS` | `constants.py:1-8` |
| `status_card.py` widget defined but unused — dashboard creates its own inline cards instead of using this widget | `status_card.py` vs `dashboard.py:31-43` |

## Dependencies

| Package | Declared | Resolved | Notes |
|---------|----------|----------|-------|
| `flet` | `>=0.25.0` | `0.85.3` | Fine |
| `python-dotenv` | `>=1.0.0` | `1.2.2` | Fine |
| `httpx` | **not declared** | `0.28.1` (transitive via flet) | Should be explicit |
