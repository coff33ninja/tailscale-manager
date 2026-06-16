# Tailscale Manager — Integration Plan

> How to weave the expanded `TailscaleAPIClient` (~60 endpoints) into the Flet UI.

---

## Phase 1: Foundation

- [ ] Pass shared `TailscaleAPIClient` instance from `app.py` to all views (default `None`)
- [ ] Initialize API client from saved config in `app.py` (not ad-hoc inside views)
- [ ] Make API credential management accessible from Settings view (not just ACLs)

## Phase 2: Enhance existing views

- [ ] **Peers** — inline tag editing, route display, authorize/deauthorize, key-expiry toggle
- [ ] **Dashboard** — API-powered stats (auth key count, user count, DNS summary, pending invites)

## Phase 3: New views

- [ ] **Auth Keys** — `get_keys`, `create_auth_key`, `delete_key`
- [ ] **DNS** — nameservers, preferences, search paths, split DNS (CRUD)
- [ ] **Users** — list, roles, approve/suspend/restore

## Phase 4: Advanced views

- [ ] **Webhooks** — list, create, edit, delete, test
- [ ] **Audit Logs** — configuration audit logs, network flow logs
- [ ] **Tailnet Settings** — view and edit
- [ ] **Device Posture** — list integrations, view device attributes

---

## Navigation

Add new entries to `NAV_ITEMS` in `constants.py` as each view is built.
