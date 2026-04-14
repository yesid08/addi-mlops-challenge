"""Runtime A/B experiment configuration endpoints.

Allows operators to change the traffic split and salt without redeploying.
Overrides are process-local and reset to env-var defaults on restart.

Endpoints:
    GET    /ab/config  — Read current effective config (override or env var).
    POST   /ab/config  — Set a runtime override for traffic_pct and/or salt.
    DELETE /ab/config  — Clear overrides, revert to env-var defaults.
"""

import logging
from typing import Literal

from fastapi import APIRouter, Request

from app.schemas import ABConfigRequest, ABConfigResponse
from deliverables.part2_ab_testing.ab_config import ab_settings

router = APIRouter(tags=["ab-testing"])
logger = logging.getLogger(__name__)


def _build_response(request: Request) -> ABConfigResponse:
    """Build an ABConfigResponse reflecting the current effective configuration."""
    store = request.app.state.ab_config_store
    override_pct = store.get_pct()
    override_salt = store.get_salt()

    effective_pct = override_pct if override_pct is not None else ab_settings.ab_treatment_traffic_pct
    effective_salt = override_salt if override_salt is not None else ab_settings.ab_experiment_salt
    source: Literal["override", "env_var"] = (
        "override" if (override_pct is not None or override_salt is not None) else "env_var"
    )

    return ABConfigResponse(
        traffic_pct=effective_pct,
        salt=effective_salt,
        source=source,
    )


@router.get("/ab/config", response_model=ABConfigResponse)
async def get_ab_config(request: Request) -> ABConfigResponse:
    """Return the current effective A/B experiment configuration."""
    return _build_response(request)


@router.post("/ab/config", response_model=ABConfigResponse)
async def set_ab_config(request: Request, body: ABConfigRequest) -> ABConfigResponse:
    """Override the A/B traffic split at runtime.

    - Set ``traffic_pct=0`` to route all traffic to variant A (kill-switch).
    - Set ``traffic_pct=100`` to route all traffic to variant B.
    - Change ``salt`` to re-randomize user bucket assignments (new experiment).
    """
    store = request.app.state.ab_config_store
    store.set_override(pct=body.traffic_pct, salt=body.salt)

    logger.info(
        "AB config override set | traffic_pct=%s | salt=%s | correlation_id=%s",
        body.traffic_pct,
        body.salt,
        request.state.correlation_id,
    )

    return _build_response(request)


@router.delete("/ab/config", response_model=ABConfigResponse)
async def reset_ab_config(request: Request) -> ABConfigResponse:
    """Clear runtime overrides and revert to env-var defaults."""
    request.app.state.ab_config_store.clear()

    logger.info(
        "AB config override cleared | correlation_id=%s",
        request.state.correlation_id,
    )

    return _build_response(request)
