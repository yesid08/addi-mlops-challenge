"""
Knowledge Base entry structure reference.

This file documents the schema that each topic in your Knowledge Base should follow.
The actual content — which topics to include, how many scenarios, what conditions —
is your design decision based on the stakeholder interviews.

See: source/adapters/utils/knowledge_base.py for the current (basic) implementation.
See: docs/stakeholder_interviews/ for the raw business requirements.
"""

# Each topic in the KB is a dict with this structure:
EXAMPLE_KB_STRUCTURE = {
    "TOPIC_NAME": {
        # Which graph node should handle questions about this topic.
        "responsible_agent": "handle_<agent_name>",

        # Brief description of when this topic applies.
        "contexto": "Description of the user's intent or situation.",

        # Example user questions that would trigger this topic.
        "pregunta": "Example question 1 / Example question 2",

        # Comma-separated keywords useful for classification.
        "keywords": "keyword1, keyword2, keyword3",

        # Detailed instructions for how the agent should respond.
        # This is where you encode business rules, edge cases, and behavior guidelines.
        "instrucciones": (
            "Detailed multi-sentence instructions. "
            "Include specific business rules from the stakeholder interviews. "
            "Cover edge cases and what to do when information is missing."
        ),

        # List of conditional scenarios. The agent should pick the one that matches
        # the user's current situation based on their data.
        "escenarios": [
            {
                "id": 1,
                "condicion": "Condition based on user_data fields (e.g., 'user has active orders')",
                "respuesta_sugerida": (
                    "Template response with {variable} placeholders "
                    "that get replaced with actual user data values."
                ),
            },
            # Add more scenarios for different conditions...
        ],

        # List of user_data field names needed for this topic.
        # Used with data_filter.py to pass only relevant data to the agent.
        "variables": ["field_name_1", "field_name_2"],
    },
}
