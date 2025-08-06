#!/usr/bin/env python3
"""
Main entry point for the Finance Agent.
This imports the v3.5 implementation which includes structured data lookup.
"""

from agent.main_v3_5 import *

# Re-export all public symbols
__all__ = ['FinanceAgent', 'main']
