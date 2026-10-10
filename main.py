"""Starta spelet:   .venv/bin/python main.py

Större eller mindre fönster (mindre = snabbare):
    .venv/bin/python main.py 1280x720
    .venv/bin/python main.py 960x540
"""
import os
import sys

if len(sys.argv) > 1 and 'x' in sys.argv[1]:
    os.environ['MARS_STORLEK'] = sys.argv[1]

from spel import app      # noqa: E402

app.run()
