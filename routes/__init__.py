"""Routes Package.

Provides Flask Blueprints for API JSON endpoints and Dashboard HTML views.
"""

from routes.api import api_bp
from routes.views import views_bp

__all__ = ["api_bp", "views_bp"]
