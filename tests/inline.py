"""
Interactive testing script for the Emporyum Tech assistant.

Usage:
    python tests/inline.py

This runs an interactive chat loop where you can test your bot.
It uses MemorySaver (in-memory) for checkpointing - no database needed.
State persists within the session for multi-turn conversations.

Change the USER_ID below to test with different user profiles:
    user_001: Carlos (Bogota) - 2 orders, active installments
    user_002: Maria (Medellin) - 1 paid order, fashion
    user_003: Andres (Cali) - New user, no orders
    user_004: Valentina (Barranquilla) - Heavy buyer, late payments
    user_005: Santiago (Bogota) - Cancelled order, frustrated
    user_006: Camila (Cartagena) - Recent delivery, return-eligible
    user_007: Diego (Bucaramanga) - Loyal customer, all paid
    user_008: Laura (Pereira) - Unverified email, pending order
"""

import asyncio
import os
import sys
import traceback

# Setup path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from dotenv import load_dotenv

load_dotenv(os.path.join(project_root, ".env"))

from langgraph.checkpoint.memory import MemorySaver

from source.application.graph import workflow

# ============================================================
# CONFIGURATION - Change these to test different scenarios
# ============================================================
USER_ID = "user_001"  # Change to test different user profiles
CONVERSATION_ID = "test-002"  # Change to start a fresh conversation
# ============================================================


async def run_chat():
    """Interactive chat loop."""
    checkpointer = MemorySaver()
    graph = workflow.compile(checkpointer=checkpointer)
    config = {"configurable": {"thread_id": CONVERSATION_ID}}
    chat_history = []

    print(f"\n{'=' * 60}")
    print("  Emporyum Tech Assistant - Interactive Testing")
    print(f"  User: {USER_ID} | Conversation: {CONVERSATION_ID}")
    print("  Type 'exit' to quit, 'reset' to clear history")
    print(f"{'=' * 60}\n")

    while True:
        try:
            query = input("YOU: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if not query:
            continue
        if query.lower() == "exit":
            print("Goodbye!")
            break
        if query.lower() == "reset":
            chat_history = []
            print("[Chat history cleared]\n")
            continue

        try:
            result = await graph.ainvoke(
                input={
                    "question": query,
                    "messages": chat_history,
                    "user_id": USER_ID,
                    "conversation_id": CONVERSATION_ID,
                    "generation": "",
                    "flow": [],
                    "user_data": None,
                    "user_data_summary": None,
                    "selected_topic": None,
                    "selected_agent": None,
                    "router_reasoning": None,
                    "current_step": None,
                    "is_return_in_progress": False,
                    "last_topic_selected": None,
                    "set_previous_selected_topics": [],
                },
                config=config,
            )

            generation = result.get("generation", "(no response generated)")
            flow = result.get("flow", [])
            topic = result.get("selected_topic", "-")
            agent = result.get("selected_agent", "-")
            step = result.get("current_step")
            reasoning = result.get("router_reasoning", "")

            print(f"\nASSISTANT: {generation}")
            print(f"  [flow]   : {' -> '.join(flow)}")
            print(f"  [topic]  : {topic}")
            print(f"  [agent]  : {agent}")
            if step:
                print(f"  [step]   : {step}")
            if reasoning:
                print(f"  [reason] : {reasoning}")
            print()

            # Update chat history for next turn
            chat_history.append({"role": "user", "content": query})
            chat_history.append({"role": "assistant", "content": generation})

        except Exception as e:
            print(f"\n[ERROR] {type(e).__name__}: {e}")
            print(traceback.format_exc())
            print()


if __name__ == "__main__":
    asyncio.run(run_chat())
