# Tailscale Manager — Integration Plan

> How to weave the expanded `TailscaleAPIClient` (~60 endpoints) into the Flet UI.

---

## Phase 1: Foundation

- [x] Pass shared `TailscaleAPIClient` instance from `app.py` to all views (default `None`)
- [x] Initialize API client from saved config in `app.py` (not ad-hoc inside views)
- [x] Make API credential management accessible from Settings view (not just ACLs)

## Phase 2: Enhance existing views

- [x] **Peers** — inline tag editing, route display, authorize/deauthorize, key-expiry toggle
- [x] **Dashboard** — API-powered stats (auth key count, user count, DNS summary, pending invites)

## Phase 3: New views

- [x] **Auth Keys** — `get_keys`, `create_auth_key`, `delete_key`
- [x] **DNS** — nameservers, preferences, search paths, split DNS (CRUD)
- [x] **Users** — list, roles, approve/suspend/restore

## Phase 4: Advanced views

- [x] **Webhooks** — list, create, edit, delete, test
- [x] **Audit Logs** — configuration audit logs, network flow logs
- [x] **Tailnet Settings** — view and edit
- [x] **Device Posture** — list integrations, view device attributes

---

## Navigation

Add new entries to `NAV_ITEMS` in `constants.py` as each view is built.
