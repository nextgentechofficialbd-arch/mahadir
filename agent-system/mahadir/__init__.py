"""Mahadir MAS — a self-improving multi-agent system.

Agents: Planner -> Researcher -> Writer -> Critic -> Verifier -> Postmortem,
driven by an Orchestrator with retries, budgets, circuit breakers and
persistent memory. The LLM "brain" is pluggable: OpenAI, Anthropic, any
OpenAI-compatible endpoint, or a deterministic offline MockBrain.
"""

__version__ = "1.0.0"
