"""
Agents sub-package for the graph reverse engineering pipeline.

Each agent is a focused, single-responsibility class that reads context from
the wiki / graph and produces structured output. All LLM calls must flow
through the ApiGatekeeper — never called directly from agent code.
"""
