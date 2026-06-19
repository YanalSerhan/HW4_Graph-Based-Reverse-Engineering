"""
crew_orchestrator.py — extracts the CrewAI orchestration logic to adhere to file length limits.
"""

import logging
from typing import Any

from .crew_steps_agents import step_analyse, step_detect_bugs, step_inspect
from .crew_types import PipelineConfig

logger = logging.getLogger(__name__)


def run_crew_orchestration(
    config: PipelineConfig,
    graph: Any,
    communities: list[Any],
    repo_path: str,
    counter: Any,
    budgets: dict[str, int],
    errors: list[str],
) -> tuple[list[Any], list[Any], list[Any]]:
    """Runs the CrewAI orchestration or falls back to direct execution."""
    try:
        from crewai import Agent, Crew, Process, Task
        from langchain_core.language_models.llms import BaseLLM

        if not isinstance(config.llm_call, BaseLLM):
            raise ValueError("CrewAI requires a Langchain BaseLLM instance")

        analyst = Agent(
            role='Graph Analyst',
            goal='Analyze architectural graphs and produce insights',
            backstory='You analyze Python codebases using AST graphs.',
            llm=config.llm_call,
            allow_delegation=False
        )
        inspector = Agent(
            role='Code Inspector',
            goal='Validate graph-inferred insights against source code',
            backstory='You read source files to confirm architectural hypotheses.',
            llm=config.llm_call,
            allow_delegation=False
        )
        detector = Agent(
            role='Architectural Bug Detector',
            goal='Detect structural anti-patterns like SPOFs',
            backstory='You find single points of failure in the codebase.',
            llm=config.llm_call,
            allow_delegation=False
        )

        insights = step_analyse(
            config, graph, communities, repo_path, counter, budgets["GraphAnalystAgent"], errors
        )
        inspection_results = step_inspect(
            config, graph, insights, repo_path, counter, budgets["CodeInspectorAgent"], errors
        )
        bugs = step_detect_bugs(
            config, graph, communities, counter, budgets["ArchitecturalBugDetector"], errors
        )

        crew = Crew(
            agents=[analyst, inspector, detector],
            tasks=[
                Task(
                    description="Extract insights from graph.",
                    expected_output="Insights summary",
                    agent=analyst
                ),
                Task(
                    description="Validate insights via code.",
                    expected_output="Validation summary",
                    agent=inspector
                ),
                Task(
                    description="Detect architectural bugs.",
                    expected_output="Bug report",
                    agent=detector
                )
            ],
            process=Process.sequential
        )
        logger.info("CrewAI orchestration initialized. Running tasks...")
        crew.kickoff()

    except (ImportError, ValueError):
        insights = step_analyse(
            config, graph, communities, repo_path, counter, budgets["GraphAnalystAgent"], errors
        )
        inspection_results = step_inspect(
            config, graph, insights, repo_path, counter, budgets["CodeInspectorAgent"], errors
        )
        bugs = step_detect_bugs(
            config, graph, communities, counter, budgets["ArchitecturalBugDetector"], errors
        )

    return insights, inspection_results, bugs
