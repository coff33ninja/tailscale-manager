# Tailscale Manager

A full-featured desktop GUI for managing Tailscale networks, built with [Flet](https://flet.dev).

![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

## Features

- **Dashboard** — overview of connection status, device info, IPs, version, peer stats, and health warnings
- **Peers** — browse all tailnet devices with online/offline status, search, and filtering
- **Exit Nodes** — view and enable/disable exit nodes
- **Serve / Funnel** — manage Tailscale Serve and Funnel routes
- **ACLs** — view and edit ACL policies (HuJSON) via the Tailscale API v2
- **Settings** — configure Tailscale API key and tailnet ID, toggle SSH and subnet routing
- **Quick actions** — connect/disconnect with one click

## Screenshots

*(Add screenshots here)*

## Requirements

- Windows (primary target), macOS, or Linux
- [Tailscale](https://tailscale.com/download) installed and logged in (`tailscale status` must work)
- Python 3.10+
- (Optional) A [Tailscale API key](https://login.tailscale.com/admin/settings/keys) for ACL management

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
2. For ACL management, go to **Settings** and enter:
   - **Tailscale API key** — create at https://login.tailscale.com/admin/settings/keys (read/write)
   - **Tailnet ID** — your tailnet name (e.g. `your-tailnet.ts.net`)

Keys are stored in `%APPDATA%\tailscale-manager\.env` and are never sent anywhere except to the Tailscale API.

## Project Structure

```
tailscale-manager/
├── run.bat                  # Windows launcher
├── pyproject.toml           # Project config + dependencies
├── .env.example             # API key template
├── .gitignore
├── README.md
└── src/
    └── tailscale_manager/
        ├── __init__.py      # Entry point (run function)
        ├── __main__.py      # python -m support
        ├── app.py           # Flet app shell, nav rail, routing
        ├── tailscale_cli.py # Tailscale CLI wrapper
        ├── api_client.py    # Tailscale v2 API client (ACLs)
        ├── config.py        # API key / tailnet config storage
        ├── constants.py     # Nav items, status colors
        ├── views/
        │   ├── dashboard.py
        │   ├── peers.py
        │   ├── exit_nodes.py
        │   ├── serve_funnel.py
        │   ├── acls.py
        │   └── settings.py
        └── widgets/
            ├── status_card.py
            └── peer_tile.py
```

## API Key Storage

Checked in order:
1. Environment variables `TAILSCALE_API_KEY` / `TAILSCALE_TAILNET`
2. `%APPDATA%\tailscale-manager\.env` (or `~/.config/tailscale-manager/.env` on Linux/macOS)
3. Project root `.env`

## Known Issues

See [known_bugs.md](known_bugs.md) for a full list of known bugs, security concerns, and code quality issues.

## License

MIT

## Disclaimer

This project is not affiliated with or endorsed by Tailscale Inc. It is an independent open-source tool that wraps the official `tailscale` CLI and API.
