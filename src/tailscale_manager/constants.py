ROUTES = {
    "dashboard": "/",
    "peers": "/peers",
    "exit_nodes": "/exit-nodes",
    "serve": "/serve",
    "settings": "/settings",
    "acls": "/acls",
}

NAV_ITEMS = [
    {"icon": "DASHBOARD", "label": "Dashboard", "route": ROUTES["dashboard"]},
    {"icon": "PEOPLE", "label": "Peers", "route": ROUTES["peers"]},
    {"icon": "EXIT_TO_APP", "label": "Exit Nodes", "route": ROUTES["exit_nodes"]},
    {"icon": "LAN", "label": "Serve / Funnel", "route": ROUTES["serve"]},
    {"icon": "LOCK", "label": "ACLs", "route": ROUTES["acls"]},
    {"icon": "SETTINGS", "label": "Settings", "route": ROUTES["settings"]},
]

STATUS_COLORS = {
    "online": "#4CAF50",
    "offline": "#F44336",
    "away": "#FF9800",
    "unknown": "#9E9E9E",
}
