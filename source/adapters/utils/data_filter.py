from typing import Dict, Any, List, Optional


MANDATORY_FIELDS = [
    "primer_nombre",
    "account_status",
    "orders",
]


def filter_user_data(
    user_data: Optional[Dict[str, Any]],
    relevant_fields: List[str],
) -> Dict[str, Any]:
    """
    Filter user_data to only include fields relevant to the current topic,
    plus mandatory base fields that are always needed.

    Args:
        user_data: Full user data dict from mock_data.
        relevant_fields: List of field names needed for this topic
                         (from the KB's "variables" list).

    Returns:
        Filtered dict with only the relevant fields.
    """
    if not user_data:
        return {}

    all_fields = set(MANDATORY_FIELDS)
    for field in relevant_fields:
        if field:
            all_fields.add(field)

    filtered = {}
    for field in all_fields:
        if field in user_data:
            filtered[field] = user_data[field]

    return filtered
