from enum import Enum
from functools import lru_cache

from pydantic import BaseModel


class ArchitecturalLayer(Enum):
    API = 'api'
    BUSINESS_LOGIC = 'business_logic'
    DATABASE = 'database'
    UTILITY = 'utility'
    CONFIGURATION = 'configuration'
    OTHER = 'other'

    @classmethod
    @lru_cache(maxsize=1)
    def values(cls) -> list[str]:
        return [item.value for item in cls]

class IdentityCard(BaseModel):
    one_liner: str
    architectural_layer: ArchitecturalLayer

class ExecutionPurity(Enum):
    PURE = 'pure'
    READ_IO = 'read_io'
    WRITE_IO = 'write_io'
    STATE_MUTATION = 'state_mutation'
    OTHER = 'other'

    @classmethod
    @lru_cache(maxsize=1)
    def values(cls) -> list[str]:
        return [item.value for item in cls]

class TechnicalAnalysis(BaseModel):
    functional_summary: str
    execution_purity: ExecutionPurity
    side_effects_description: str | None

class DependencyNature(Enum):
    STDLIB_MODULE = 'stdlib_module'
    THIRD_PARTY_LIB = 'third_party_lib'
    GLOBAL_VARIABLE = 'global_variable'
    ENVIRONMENT_VARIABLE = 'environment_variable'
    MODULE = 'module'
    METHOD = 'method'
    CLASS = 'class'
    FUNCTION = 'function'
    ATTRIBUTE = 'attribute'
    DECORATOR = 'decorator'
    ENUM = 'enum'
    OTHER = 'other'

    @classmethod
    @lru_cache(maxsize=1)
    def values(cls) -> list[str]:
        return [item.value for item in cls]

class ImplicitDependency(BaseModel):
    symbol: str
    nature: DependencyNature
    context: str

class DependencyMapping(BaseModel):
    implicit_dependencies: list[ImplicitDependency]

class AgentHints(BaseModel):
    edge_cases: list[str]
    documentation_tags: list[str]

class LLMSynthesis(BaseModel):
    thought: str
    identity_card: IdentityCard
    technical_analysis: TechnicalAnalysis
    dependency_mapping: DependencyMapping
    agent_hints: AgentHints

    def __str__(self) -> str:
        return str(self.model_dump_json())

    def serialize(self, fqn: str) -> str:

        lines = [
            f"# === SEMANTIC SUMMARY: {fqn} ===",
            f"# Core Role: {self.identity_card.one_liner}",
            f"# Execution Purity: {self.technical_analysis.execution_purity}",
            f"# Side Effects: {self.technical_analysis.side_effects_description}",
            "# ",
            "# Detailed Functional Summary:"
        ]

        for line in self.technical_analysis.functional_summary.splitlines():
            lines.append(f"# {line}")

        return "\n".join(lines)
