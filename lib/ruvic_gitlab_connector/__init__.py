"""Conector Ruvic para GitLab (issues, comentarios en Merge Requests, pipelines)."""

from .client import GitLabClient
from .config import ENV_PREFIX, GitLabConfig
from .exceptions import (
    GitLabAuthError,
    GitLabConnectorError,
    GitLabDataError,
    GitLabNetworkError,
)
from .logging_utils import setup_logging

__all__ = [
    "ENV_PREFIX",
    "GitLabAuthError",
    "GitLabClient",
    "GitLabConfig",
    "GitLabConnectorError",
    "GitLabDataError",
    "GitLabNetworkError",
    "setup_logging",
]

__version__ = "1.0.0"
