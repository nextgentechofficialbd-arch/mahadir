from .base import Agent, RunContext, ContractViolation, TransientError, FatalError
from .planner import PlannerAgent
from .researcher import ResearcherAgent
from .writer import WriterAgent
from .critic import CriticAgent
from .verifier import VerifierAgent
from .postmortem import PostmortemAgent

PIPELINE = [
    ("planner", PlannerAgent),
    ("researcher", ResearcherAgent),
    ("writer", WriterAgent),
    ("critic", CriticAgent),
    ("verifier", VerifierAgent),
    ("postmortem", PostmortemAgent),
]


def build_agents() -> dict:
    return {name: cls() for name, cls in PIPELINE}
