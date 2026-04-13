"""
Knowledge Base for the Emporyum Tech assistant.

Basic implementation with 7 topics extracted from stakeholder interviews.
Structure reference: source/examples/example_kb_entry.py
"""

SCENARIO_KNOWLEDGE_BASE: dict = {
    "SALUDO": {
        "responsible_agent": "handle_general",
        "contexto": "El usuario saluda.",
        "instrucciones": "Saludar amablemente.",
        "escenarios": [
            {
                "id": 1,
                "condicion": "Siempre",
                "respuesta_sugerida": "Hola! En que puedo ayudarte?",
            },
        ],
        "variables": ["primer_nombre", "orders"],
    },
    "PEDIDOS": {
        "responsible_agent": "handle_general",
        "contexto": "Preguntas sobre pedidos y envios.",
        "instrucciones": "Dar informacion del pedido.",
        "escenarios": [
            {
                "id": 1,
                "condicion": "Tiene pedidos",
                "respuesta_sugerida": "Aqui esta la info de tus pedidos.",
            },
        ],
        "variables": ["primer_nombre", "orders", "delivery_address_city"],
    },
    "PAGOS": {
        "responsible_agent": "handle_general",
        "contexto": "Preguntas sobre pagos y cuotas.",
        "instrucciones": "Informar sobre pagos.",
        "escenarios": [
            {
                "id": 1,
                "condicion": "Siempre",
                "respuesta_sugerida": "Tenemos varios metodos de pago.",
            },
        ],
        "variables": ["primer_nombre", "orders"],
    },
    "PRODUCTOS": {
        "responsible_agent": "handle_general",
        "contexto": "Preguntas sobre productos o recomendaciones.",
        "instrucciones": "Ayudar con productos.",
        "escenarios": [
            {
                "id": 1,
                "condicion": "Siempre",
                "respuesta_sugerida": "Tenemos muchos productos disponibles.",
            },
        ],
        "variables": ["primer_nombre", "purchase_history", "user_category_preferences", "available_promotions"],
    },
    "CUENTA": {
        "responsible_agent": "handle_general",
        "contexto": "Preguntas sobre la cuenta del usuario.",
        "instrucciones": "Ayudar con la cuenta.",
        "escenarios": [
            {
                "id": 1,
                "condicion": "Siempre",
                "respuesta_sugerida": "Puedo ayudarte con tu cuenta.",
            },
        ],
        "variables": ["primer_nombre", "email", "phone", "email_verified", "phone_verified", "account_status"],
    },
    "DEVOLUCIONES": {
        "responsible_agent": "handle_general",
        "contexto": "El usuario quiere devolver un producto.",
        "instrucciones": "Informar sobre devoluciones.",
        "escenarios": [
            {
                "id": 1,
                "condicion": "Siempre",
                "respuesta_sugerida": "Puedes devolver dentro de 15 dias.",
            },
        ],
        "variables": ["primer_nombre", "orders"],
    },
    "FUERA_DE_ALCANCE": {
        "responsible_agent": "handle_general",
        "contexto": "Preguntas no relacionadas con Emporyum Tech.",
        "instrucciones": "Indicar que solo ayudas con Emporyum Tech.",
        "escenarios": [
            {
                "id": 1,
                "condicion": "Siempre",
                "respuesta_sugerida": "Solo puedo ayudar con temas de Emporyum Tech.",
            },
        ],
        "variables": ["primer_nombre"],
    },
}

# List of all valid topic names (used by the router)
VALID_TOPICS: list = list(SCENARIO_KNOWLEDGE_BASE.keys())
