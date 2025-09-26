import sys
sys.path.append('..')  # So we can import app.py
from app import app as application

# Vercel will use this as the entry point for the Python serverless function
# This file must be named index.py for Vercel's default routing
