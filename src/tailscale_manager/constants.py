ROUTES = {
    "dashboard": "/",
    "peers": "/peers",
    "exit_nodes": "/exit-nodes",
    "serve": "/serve",
    "settings": "/settings",
    "acls": "/acls",
    "auth_keys": "/auth-keys",
    "dns": "/dns",
    "users": "/users",
    "webhooks": "/webhooks",
    "audit_logs": "/audit-logs",
    "tailnet_settings": "/tailnet-settings",
    "device_posture": "/device-posture",
}

NAV_ITEMS = [
    {"icon": "DASHBOARD", "label": "Dashboard", "route": ROUTES["dashboard"]},
    {"icon": "PEOPLE", "label": "Peers", "route": ROUTES["peers"]},
    {"icon": "EXIT_TO_APP", "label": "Exit Nodes", "route": ROUTES["exit_nodes"]},
    {"icon": "LAN", "label": "Serve / Funnel", "route": ROUTES["serve"]},
    {"icon": "KEY", "label": "Auth Keys", "route": ROUTES["auth_keys"]},
    {"icon": "DNS", "label": "DNS", "route": ROUTES["dns"]},
    {"icon": "LOCK", "label": "ACLs", "route": ROUTES["acls"]},
    {"icon": "PEOPLE", "label": "Users", "route": ROUTES["users"]},
    {"icon": "WEBHOOK", "label": "Webhooks", "route": ROUTES["webhooks"]},
    {"icon": "HISTORY", "label": "Audit Logs", "route": ROUTES["audit_logs"]},
    {"icon": "TUNE", "label": "Tailnet Settings", "route": ROUTES["tailnet_settings"]},
    {"icon": "SECURITY", "label": "Device Posture", "route": ROUTES["device_posture"]},
    {"icon": "SETTINGS", "label": "Settings", "route": ROUTES["settings"]},
]

STATUS_COLORS = {
    "online": "#4CAF50",
    "offline": "#F44336",
    "away": "#FF9800",
    "unknown": "#9E9E9E",
}
