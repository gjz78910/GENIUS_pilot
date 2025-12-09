"""Stub for loading external data for the scheduling tool.

This module contains a placeholder function that can be extended to load
engineers, jobs and travel matrices from external sources such as JSON or
CSV files.  For the purposes of this MVP, data is hardcoded in the
`data` package and this loader returns ``None``.
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple


def load_data(file_path: str) -> Tuple[List[Any], List[Any], Dict[str, Dict[str, float]]]:
    """Load engineers, jobs and travel matrix from an external file.

    Parameters
    ----------
    file_path : str
        Path to the JSON or CSV file containing the data.

    Returns
    -------
    Tuple[List[Any], List[Any], Dict[str, Dict[str, float]]]
        The loaded engineers, jobs and travel matrix.  In this stub the
        return value is ``(None, None, None)``.

    Notes
    -----
    This is a stub and does not implement any functionality.  It exists so
    that participants in the experiment can practise feature development
    using AI coding assistants.
    """
    print(f"Data loader stub called. Attempted to load data from {file_path} but feature is not implemented.")
    return None, None, None  # type: ignore[return-value]