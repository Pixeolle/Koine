from fastapi import Request
from starlette.requests import HTTPConnection

from backend.application.use_cases.run_documentation_pipeline_use_case import RunDocumentationPipelineUseCase
from backend.core.dependencies.pipeline import build_run_documentation_pipeline_use_case
from backend.core.dependencies.llm import build_agent_provider
from backend.domain.services.progress_broker import ProgressBroker
from backend.domain.agents.agent_provider import AgentProvider


def get_run_documentation_pipeline_use_case(request: Request) -> RunDocumentationPipelineUseCase:
    return build_run_documentation_pipeline_use_case(request.app.state.llm_client)

def get_progress_broker(request: Request) -> ProgressBroker:
    return request.app.state.progress_broker

def get_agent_provider(connection: HTTPConnection) -> AgentProvider:
    return build_agent_provider(connection.app.state.llm_client)
