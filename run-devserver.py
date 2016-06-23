#!/usr/bin/env python
"""Starts the Flask app in debug mode.

Do not use in production.
"""
from bot.webapp import goldstarsapp

if __name__ == "__main__":
    goldstarsapp.debug = True
    goldstarsapp.run(port=8042, host='0.0.0.0', processes=2)
