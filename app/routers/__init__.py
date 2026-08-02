# ==========================================================
# app/routers/__init__.py
# Routers Package Initialization
# ==========================================================

from . import ai_engine
from . import alerts
from . import analytics
from . import auth
from . import congestion
from . import dashboard
from . import detect
from . import heatmap
from . import profile
from . import recommendation
from . import reports
from . import users

__all__ = [
    "ai_engine",
    "alerts",
    "analytics",
    "auth",
    "congestion",
    "dashboard",
    "detect",
    "heatmap",
    "profile",
    "recommendation",
    "reports",
    "users",
]