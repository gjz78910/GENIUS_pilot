"""Reporting and data-loading features."""

from .report import generate_report  # noqa: F401
from .data_loader import load_data  # noqa: F401

__all__ = ["generate_report", "load_data"]
