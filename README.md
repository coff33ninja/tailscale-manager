# Tailscale Manager

A full-featured cross-platform desktop GUI for managing [Tailscale](https://tailscale.com) mesh VPN networks, built with [Flet](https://flet.dev) (Python → Flutter). Monitor your tailnet, manage peers, configure DNS and Auth Keys, edit ACL policies, manage webhooks and users, and toggle connection settings — all from a native-looking dark-theme interface.

![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Platform](https://img.shields.io/badge/platform-windows%20%7C%20macos%20%7C%20linux-lightgrey)
![Flet](https://img.shields.io/badge/built%20with-Flet-00897B)
![GitHub stars](https://img.shields.io/github/stars/coff33ninja/tailscale-manager?style=social)

## Features

### Works without API key (CLI-powered)
- **Dashboard** — overview of connection status, device info, IPs, version, peer stats, and health warnings
- **Peers** — browse all tailnet devices with online/offline sections, search, ACL allowances viewer (tags/users/groups/autogroups/CIDRs), exit-node badge, relay info, latency, last-seen, and port-scan service discovery
- **Exit Nodes** — view and enable/disable exit nodes
- **Serve / Funnel** — manage Tailscale Serve and Funnel routes
- **Quick actions** — connect/disconnect with one click

### Requires API key (Tailscale v2 HTTP API)
- **Auth Keys** — list, create (reusable/ephemeral/preauthorized with tag assignment), and revoke keys
- **DNS** — 4-tab management: nameservers (add/remove), MagicDNS toggle, search paths, and split DNS routes (domain → nameservers)
- **ACLs** — view and edit ACL policies (HuJSON) via the API, with full allowance resolution per peer; uses the shared API client and calls `reconfigure()` when credentials change
- **Users** — list users with avatar, role, and status badges; suspend and restore (owner-protected)
- **Webhooks** — list, create, test, rotate secret, and delete webhook endpoints for tailnet events
- **Audit Logs** — date-range searchable configuration audit log viewer
- **Tailnet Settings** — view/edit tailnet-level settings via a full JSON editor (monospace, syntax-validated)
- **Device Posture** — list, create, and delete MDM/compliance posture integrations

### Enhanced existing views
- **Dashboard** — background-fetches auth key count, active user count, and MagicDNS status displayed as a third stat row
- **Peers** — inline tag editor (comma-separated input dialog), display advertising routes per device, authorize/deauthorize toggle, and key-expiry action button
- **Peer tiles** (`widgets/peer_tile.py`) — shows tags as colored chips, route count badge, and action buttons for authorized status, key expiry, and tag editing
- **Settings** — API credential section with Tailscale API key and tailnet ID fields; saves to config and calls `reconfigure()` on the shared client so all views pick up credentials without restarting

## Screenshots

*(Add screenshots here)*

## Requirements

- Windows (primary target), macOS, or Linux
- [Tailscale](https://tailscale.com/download) installed and logged in (`tailscale status` must work)
- Python 3.10+
- (Optional) A [Tailscale API key](https://login.tailscale.com/admin/settings/keys) for admin features

## Getting Started

### One-click launcher (Windows)

Double-click `run.bat` — it will automatically install `uv` (if missing), sync dependencies, and launch the app.

### Manual

```bash
# Install uv (https://docs.astral.sh/uv/)
# Then:
uv sync
uv run python -m tailscale_manager
```

### First-time setup

1. Launch the app — basic status works without configuration
2. For admin features, go to **Settings** and enter:
   - **Tailscale API key** — create at https://login.tailscale.com/admin/settings/keys (read/write)
   - **Tailnet ID** — your tailnet name (e.g. `your-tailnet.ts.net`)

Keys are stored in `%APPDATA%\tailscale-manager\.env` and are never sent anywhere except to the Tailscale API.

## Building a Standalone Executable

### Windows (one-click)

Run `build.bat` — it syncs dependencies, then runs `flet pack` to produce:

```
dist\tailscale-manager\tailscale-manager.exe
```

Launch the exe from that directory (double-click or run `dist\tailscale-manager\tailscale-manager.exe`). Do **not** move or run the exe outside its folder — it needs the `_internal/` directory next to it.

### Debugging build issues

If the exe crashes silently, rebuild with console output enabled:

```bash
.venv\Scripts\flet.exe pack pack.py -n "tailscale-manager" --distpath dist --onedir --hidden-import "tailscale_manager" -y
```

Console errors (missing imports, runtime tracebacks) will appear in the terminal window.

### Manual build

```bash
uv sync
.venv\Scripts\flet.exe pack pack.py ^
    -n "tailscale-manager" ^
    --product-name "Tailscale Manager" ^
    --distpath dist ^
    --onedir ^
    --hidden-import "tailscale_manager" ^
    -y
```

## Project Structure

```
tailscale-manager/
├── run.bat                  # Windows launcher
├── pyproject.toml           # Project config + dependencies
├── .env.example             # API key template
├── .gitignore
├── known_bugs.md            # Known issues & audit findings
├── README.md
└── src/
    └── tailscale_manager/
        ├── __init__.py      # Entry point (run function)
        ├── __main__.py      # python -m support
        ├── app.py           # Flet app shell, nav rail, routing, shared API client
        ├── tailscale_cli.py # Tailscale CLI wrapper
        ├── api_client.py    # Tailscale v2 API client (~60 endpoints)
        ├── config.py        # API key / tailnet config storage
        ├── constants.py     # Nav items, status colors, routes
        ├── views/
        │   ├── dashboard.py      # Status overview + API stats
        │   ├── peers.py          # Device list + tags/routes/auth actions
        │   ├── exit_nodes.py     # Exit node toggle
        │   ├── serve_funnel.py   # Serve/Funnel route management
        │   ├── acls.py           # ACL policy editor
        │   ├── settings.py       # Connection + API credential management
        │   ├── auth_keys.py      # Auth key CRUD
        │   ├── dns.py            # 4-tab DNS configuration
        │   ├── users.py          # User list + suspend/restore
        │   ├── webhooks.py       # Webhook endpoints CRUD
        │   ├── audit_logs.py     # Configuration audit log viewer
        │   ├── tailnet_settings.py  # Tailnet settings JSON editor
        │   └── device_posture.py    # Posture integrations CRUD
        └── widgets/
            ├── status_card.py
            └── peer_tile.py     # Peer tile with tags, routes, action buttons
```

## API Key Storage

Checked in order:
1. Environment variables `TAILSCALE_API_KEY` / `TAILSCALE_TAILNET`
2. `%APPDATA%\tailscale-manager\.env` (or `~/.config/tailscale-manager/.env` on Linux/macOS)
3. Project root `.env`

A shared `TailscaleAPIClient` instance is created once in `app.py` and passed to all 12 view constructors. The client was rewritten to cover ~60 Tailscale v2 endpoints (devices, DNS, ACLs, auth keys, users, webhooks, tailnet settings, posture, and audit logs) with proper URL building, error handling, `b'null'` body normalization, and a `reconfigure()` method so credential updates apply to all views at runtime without restarting. Views that need API access fall back to an ad-hoc client if the shared instance is unauthenticated.

## Testing

```bash
# Run non-destructive integration tests (uses mock server):
uv run pytest -m "not write_op" -v

# Run all tests including write operations (needs real API key):
uv run pytest -v
```

52 integration tests cover the API client with both happy-path and edge-case scenarios (404s, invalid IDs, string boundaries, etc.).

## Known Issues

See [known_bugs.md](known_bugs.md) for a full list of known bugs, security concerns, and code quality issues.

## License

MIT

## Disclaimer

This project is not affiliated with or endorsed by Tailscale Inc. It is an independent open-source tool that wraps the official `tailscale` CLI and API.
