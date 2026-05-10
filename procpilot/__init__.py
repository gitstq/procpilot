"""
ProcPilot - Lightweight Terminal Process Intelligence Manager
轻量级终端进程智能管理器

A zero-dependency CLI tool for intelligent process monitoring, 
resource analysis, and process tree visualization.
"""

__version__ = "1.0.0"
__author__ = "gitstq"
__description__ = "Lightweight Terminal Process Intelligence Manager"

from .core import ProcessManager
from .monitor import ProcessMonitor
from .tree import ProcessTree
from .alerts import AlertManager

__all__ = [
    "ProcessManager",
    "ProcessMonitor", 
    "ProcessTree",
    "AlertManager",
]
