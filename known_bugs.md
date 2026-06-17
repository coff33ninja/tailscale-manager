# Known Bugs & Issues

## Security

| Severity | Issue | Location |
|----------|-------|----------|
| Medium | API key stored in **plaintext** at `%APPDATA%\tailscale-manager\.env` — no encryption, no DPAPI, no keyring integration | `config.py:21-31` |
| ~~Low~~ **FIXED** | ~~`config.save()` writes API key to `os.environ`, leaking it to all child processes~~ | ~~`config.py:32-33`~~ Removed in 2026-06-17 audit |
| ~~Low~~ **FIXED** | ~~ACL view sends user-entered JSON directly — no schema validation, no dry-run guard~~ | ~~`acls.py:168-174`~~ Added `validate_acl()` call before `set_acl()` in 2026-06-17 audit |
| ~~Low~~ **FIXED** | ~~HuJSON comment stripper mangles string literals~~ | ~~`api_client.py:8-25`~~ Rewrote with string-aware state machine in 2026-06-17 audit |

## Bugs

| Severity | Issue | Location |
|----------|-------|----------|
| ~~High~~ **FIXED** | ~~Crash in Serve/Funnel view: `_render_funnel([])` → `[].routes` `AttributeError`~~ | ~~`serve_funnel.py:82-83`~~ `_render_funnel(ServeConfig())` since 2026-06-17 |
| ~~Medium~~ **FIXED** | ~~Exit Node toggle clobbers all settings: `cli.up(exit_node=ip)` with defaults~~ | ~~`exit_nodes.py:115-122`~~ `TailscaleCLI.up()` uses `Optional[bool] = None` since 2026-06-17 |
| ~~Medium~~ **FIXED** | ~~Same issue for disable: `cli.up()` with zero arguments resets everything~~ | ~~`exit_nodes.py:124-130`~~ Same fix — no flags passed unless explicitly set |
| ~~Low~~ **FIXED** | ~~`_request()` catches `Exception` broadly; fallback parse failure goes unhandled~~ | ~~`api_client.py:50-54`~~ Wrapped in try/except raising `TailscaleAPIError` since 2026-06-17 |
| ~~Low~~ **FIXED** | ~~`ServeConfig.from_json()` hardcodes TCP port 443~~ | ~~`tailscale_cli.py:64`~~ Now iterates all TCP ports since 2026-06-17 |

## Code Quality

| Issue | Location | Status |
|-------|----------|--------|
| ~~No tests exist~~ | ~~entire project~~ | **FALSE** — 52 tests in `tests/test_api_client.py` |
| ~~`validate_acl` dead re-raise~~ | ~~`api_client.py:72-77`~~ | **FIXED** — removed no-op handler |
| ~~Funnel errors silently swallowed~~ | ~~`serve_funnel.py:82`~~ | **FIXED** — added `_render_funnel_error()` |
| ~~`config.py` environment leakage~~ | ~~`config.py:32-33`~~ | **FIXED** — removed `os.environ` writes |
| ~~`DashboardView.load()` full tree rebuild~~ | ~~`dashboard.py:94-99`~~ | **FIXED** — uses content ref, only dynamic column rebuilt |
| ~~Hardcoded Windows path~~ | ~~`tailscale_cli.py:192-194`~~ | **FIXED** — added `Program Files (x86)` candidate |
| ~~`httpx` is transitive only~~ | ~~`pyproject.toml:7-10`~~ | **FALSE** — declared as `httpx>=0.28.0` |
| ~~`pyproject.toml` vs `.python-version` mismatch~~ | ~~`pyproject.toml:6` vs `.python-version`~~ | **FIXED** — synced to `3.10` |
| ~~`ROUTES` dict unused~~ | ~~`constants.py:1-8`~~ | **FALSE** — used by `NAV_ITEMS` and `app.py` |
| ~~`status_card.py` widget unused~~ | ~~`status_card.py` vs `dashboard.py:31-43`~~ | **FALSE** — imported and used in `dashboard.py` |

## Dependencies

| Package | Declared | Resolved | Notes |
|---------|----------|----------|-------|
| `flet` | `>=0.25.0` | `0.85.3` | Fine |
| `python-dotenv` | `>=1.0.0` | `1.2.2` | Fine |
| `httpx` | `>=0.28.0` | `0.28.1` | Fine — declared in `pyproject.toml:35` |

---

## Audit (2026-06-17) — Status of previously reported items

| Status | Original Entry | Notes |
|--------|----------------|-------|
| **FIXED** | High — Crash in Serve/Funnel view: `_render_funnel([])` → `[].routes` `AttributeError` | Changed to `_render_funnel(ServeConfig())` |
| **FIXED** | Medium — Exit Node toggle clobbers all settings via `cli.up(exit_node=ip)` defaults | `TailscaleCLI.up()` now uses `Optional[bool] = None` — only explicitly passed flags are emitted |
| **FIXED** | Medium — Same issue for disable: `cli.up()` resets everything | With `None` defaults, `up()` with no args emits `["up"]` only, preserving current settings |
| **FIXED** | Code Quality — `validate_acl` dead re-raise in `api_client.py` | Removed no-op `try/except TailscaleAPIError as e: raise e` |
| **FIXED** | Low — `ServeConfig.from_json()` hardcodes `["TCP"]["443"]` | Now iterates all TCP ports |
| **FIXED** | Low — `TailscaleAPIClient._request()` catches `Exception` broadly; fallback parse failure goes unhandled | Wrapped fallback in try/except that raises `TailscaleAPIError` |
| **FIXED** | Low — HuJSON comment stripper mangles string literals | Rewrote with proper string-aware state machine |
| **FIXED** | Code Quality — Funnel errors silently swallowed (inconsistent UX) | Added `_render_funnel_error()` — funnel now shows error UI like serve |
| **FIXED** | Code Quality — `config.py` environment leakage (`save()` writes to `os.environ`) | Removed `os.environ` writes from `save()` |
| **FIXED** | Code Quality — `DashboardView.load()` rebuilds full control tree on every refresh | Uses content ref; only the dynamic content column is rebuilt |
| **FIXED** | Code Quality — Hardcoded Windows path misses `Program Files (x86)` | Added `Program Files (x86)` candidate path |
| **FIXED** | Code Quality — `pyproject.toml` vs `.python-version` mismatch | Synced `.python-version` to `3.10` |
| **FIXED** | Low — ACL view no schema validation / no dry-run guard before `set_acl()` | Added `validate_acl()` call with warnings shown before save |
| **FALSE** | Code Quality — "No tests exist" | 52 integration tests exist in `tests/test_api_client.py` with `conftest.py` |
| **FALSE** | Code Quality — "`constants.py:ROUTES` dict defined but unused" | `ROUTES` is used by `NAV_ITEMS` (same file) and imported in `app.py` for view routing |
| **FALSE** | Code Quality — "`status_card.py` widget defined but unused" | Imported and used as `status_card(...)` throughout `dashboard.py` |
| **FALSE** | Dependencies — "`httpx` not declared" / "transitive dep" | Explicitly declared as `httpx>=0.28.0` in `pyproject.toml:35` |
| **STALE** | Various line-number references across all entries | Code has been modified since the bug doc was written; line numbers have shifted |
| **OPEN** | Medium — API key stored in plaintext at `%APPDATA%\tailscale-manager\.env` | No OS-specific secret storage (DPAPI/Keychain/keyring) implemented — requires platform-level integration |
