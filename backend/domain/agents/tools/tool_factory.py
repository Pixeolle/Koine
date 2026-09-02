from backend.application.ports.document_repository import DocumentRepository
from backend.application.ports.graph_engine import GraphEngine
from backend.domain.agents.tools.document_repository_tool_provider import DocumentRepositoryToolProvider
from backend.domain.agents.tools.graph_engine_tool_provider import GraphEngineToolProvider
from backend.domain.entities.document import Document
from backend.domain.entities.llm_tool import LLMTool


class ToolFactory:

    def __init__(
            self,
            graph_engine: GraphEngine,
            document_repository: DocumentRepository
    ):
        self.graph_engine_tool_provider = GraphEngineToolProvider(graph_engine)
        self.document_repository_tool_provider = DocumentRepositoryToolProvider(document_repository)

    def build_structurer_tools(self, documentation_id: str) -> list[LLMTool]:
        return [
            self.document_repository_tool_provider.get_create_document(documentation_id),
            self.document_repository_tool_provider.get_delete_document(documentation_id),
            self.document_repository_tool_provider.get_get_documents(documentation_id),
            self.document_repository_tool_provider.get_get_document(documentation_id),
        ] + self.get_navigation_tools(documentation_id)

    def build_writer_tools(self, documentation_id: str, document: Document) -> list[LLMTool]:
        return [
            self.document_repository_tool_provider.get_get_document(documentation_id),
            self.document_repository_tool_provider.get_get_documents(documentation_id),
            self.document_repository_tool_provider.get_update_one_document(documentation_id, document.document_name)
        ] + self.get_navigation_tools(documentation_id)

    def build_judge_tools(self, documentation_id: str, document: Document) -> list[LLMTool]:
        return [
            self.document_repository_tool_provider.get_get_document(documentation_id),
            self.document_repository_tool_provider.get_get_documents(documentation_id),
            self.document_repository_tool_provider.get_review_one_document(documentation_id, document.document_name),
            self.document_repository_tool_provider.get_validate_one_document(documentation_id, document.document_name)
        ] + self.get_navigation_tools(documentation_id)

    def build_assistant_tools(self, documentation_id: str) -> list[LLMTool]:
        return [
            self.document_repository_tool_provider.get_get_documents(documentation_id),
            self.document_repository_tool_provider.get_get_document(documentation_id),
        ] + self.get_navigation_tools(documentation_id)

    def get_navigation_tools(self, documentation_id: str) -> list[LLMTool]:
        return [
            self.graph_engine_tool_provider.get_get_root_nodes(documentation_id),
            self.graph_engine_tool_provider.get_get_children(),
            self.graph_engine_tool_provider.get_get_parents(),
            self.graph_engine_tool_provider.get_get_node_content(documentation_id),
            self.graph_engine_tool_provider.get_get_node_synthesis(documentation_id),
        ]

