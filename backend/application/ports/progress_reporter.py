from abc import ABC, abstractmethod
from enum import Enum


class ProgressEventType(Enum):
    FETCHING = 'fetching'
    REPOSITORY_FETCHED = 'repository_fetched'
    BUILDING_CODE_GRAPH = 'building_code_graph'
    PARSING_SOURCE_CODE = 'parsing_source_code'
    SOURCE_CODE_PARSED = 'source_code_parsed'
    LINKING_DEPENDENCIES = 'linking_dependencies'
    DEPENDENCIES_LINKED = 'dependencies_linked'
    CODE_GRAPH_BUILT = 'code_graph_built'
    ENRICHING_CODE_GRAPH = 'enriching_code_graph'
    CODE_GRAPH_ENRICHED = 'code_graph_enriched'
    PLANNING_DOCUMENTATION = 'planning_documentation'
    PLAN_READY = 'plan_ready'
    WRITING_DOCUMENT = 'writing_document'
    DOCUMENT_WRITTEN = 'document_written'
    REVIEWING_DOCUMENT = 'reviewing_document'
    DOCUMENT_REVIEWED = 'document_reviewed'
    COMPLETE = 'complete'
    ERROR = 'error'


class ProgressReporter(ABC):

    @abstractmethod
    async def report(self, event_type: ProgressEventType, **data) -> None:
        pass