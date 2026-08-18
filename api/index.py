"""Vercel Serverless Function entrypoint module.

Exposes the Flask application instance for serverless deployments on Vercel.
"""

from typing import Any

from app import app

# Vercel Serverless Function Entrypoint
app: Any = app
