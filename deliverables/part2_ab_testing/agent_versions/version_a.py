"""Version A — control agent (unchanged from source/).

This module is a thin re-export so that the A/B router can reference both
versions through a symmetric interface.  No logic is duplicated here.
"""

from source.adapters.chains.general_chain import (  # noqa: F401
    get_general_chain as get_control_chain,
)
from source.application.graph import workflow as workflow_a  # noqa: F401

__all__ = ["get_control_chain", "workflow_a"]
