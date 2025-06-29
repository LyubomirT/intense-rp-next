"""
Core module for Intense RP API

This module contains the foundational components for state management,
configuration, and core business logic.
"""

from .state_manager import StateManager, get_state_manager, reset_state_manager, StateEvent, StateChange


__all__ = [
    'StateManager',
    'get_state_manager', 
    'reset_state_manager',
    'StateEvent',
    'StateChange'
]