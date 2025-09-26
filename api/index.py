
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import app as application

# Vercel will use this as the entry point for the Python serverless function
# This file must be named index.py for Vercel's default routing
