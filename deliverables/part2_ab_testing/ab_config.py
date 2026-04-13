"""A/B experiment configuration — read from environment variables at startup.

Environment variables:
  AB_TREATMENT_TRAFFIC_PCT  int 0-100, default 50.
                            Percentage of users routed to Version B (treatment).
                            Set to 0 to disable the experiment (all traffic → A).
                            Change without redeploying: update the env var and restart.
  AB_EXPERIMENT_SALT        str, default "emporyum-ab-v1".
                            Mixed with user_id before hashing.
                            Change to re-randomize user bucket assignments (new experiment).
"""

from pydantic_settings import BaseSettings


class ABSettings(BaseSettings):
    ab_treatment_traffic_pct: int = 50
    ab_experiment_salt: str = "emporyum-ab-v1"

    # Read from actual env vars only (not .env file) so these settings can be
    # changed at deploy time without touching application secrets.
    # Extra fields from the process environment are silently ignored.
    model_config = {"extra": "ignore"}


ab_settings = ABSettings()
