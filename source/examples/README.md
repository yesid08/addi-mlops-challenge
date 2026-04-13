# Examples — Pattern Reference

This folder shows the **framework patterns** used in this project: how LangGraph nodes work, how LangChain chains are built, and how the Knowledge Base is structured.

These patterns show **how the framework works**. The **what** — which agents to build, which topics to define, how to route, how to structure your architecture — is your design decision.

## Files

| File | What it shows |
|------|--------------|
| `example_kb_entry.py` | The schema/structure of a Knowledge Base topic entry |
| `example_chain.py` | How to build an LLM chain with Pydantic structured output |
| `example_domain_function.py` | The skeleton of an async graph node (domain function) |
| `example_graph.py` | A minimal runnable LangGraph graph — use it to verify your setup |

## Setup Verification

```bash
poetry run python -m source.examples.example_graph
```

You should see a greeting and "Setup is working!" message.

## Key Concepts

**LangGraph** organizes your application as a graph of nodes connected by edges. Each node is an async function that receives the full state and returns a partial dict to update it. See `example_graph.py` for the `StateGraph` API.

**LangChain chains** combine a prompt template with an LLM. Using `.with_structured_output(PydanticModel)` ensures the LLM returns data matching your schema. See `example_chain.py`.

**Domain functions** are the graph nodes that contain your business logic. They read from the Knowledge Base, prepare data for the chain, invoke it, and return state updates. See `example_domain_function.py`.

**The Knowledge Base** encodes business rules as structured data. Each topic has instructions, conditional scenarios, and a list of required user data fields. See `example_kb_entry.py` for the schema.
