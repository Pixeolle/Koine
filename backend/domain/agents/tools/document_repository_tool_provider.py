from backend.application.ports.document_repository import DocumentRepository
from backend.domain.entities.document import Document, DocumentCreate, DocumentStatus, DocumentUpdate
from backend.domain.entities.llm_tool import ArgumentType, LLMTool, ToolArgument


class DocumentRepositoryToolProvider:

    def __init__(self, document_repository: DocumentRepository):
        self.document_repository = document_repository

        self.argument_library: dict[str, ToolArgument] = {
            'document_name': ToolArgument(
                name='document_name',
                type=ArgumentType.STRING,
                description="The document's identifier, without file extension - it will automatically be saved as .md.",
            ),
            'goal': ToolArgument(
                name='goal',
                type=ArgumentType.STRING,
                description=(
                    "What a reader should understand after reading this document, stated precisely. "
                    "Also state what this document should NOT cover, to avoid overlapping with other planned document."
                ),
            ),
            'source_node_ids': ToolArgument(
                name='source_node_ids',
                type=ArgumentType.ARRAY,
                description="List of node's id that contribute to create this document",
                items=ToolArgument(
                    name='node_id',
                    type=ArgumentType.STRING,
                    description='Id of the node'
                ),
                is_discriminating=False
            )
        }

    def get_create_document(self, documentation_id: str) -> LLMTool:

        def create_document(document_name: str, goal: str) -> str:
            self.document_repository.create_document(
                DocumentCreate(
                    documentation_id=documentation_id,
                    document_name=document_name,
                    goal=goal
                )
            )
            return f"Document '{document_name}' created."

        return LLMTool(
            function=create_document,
            description=(
                "Create a new MD documentation file, given its name and the goal it must "
                "fulfill within the overall documentation plan. This registers the file's "
                "intent only - do not include any content here; the file's content will be "
                "written separately, later, by another step."
            ),
            arguments=[
                self.argument_library['document_name'],
                self.argument_library['goal']
            ]
        )

    def get_delete_document(self, documentation_id: str) -> LLMTool:

        def delete_document(document_name: str) -> str:
            self.document_repository.delete_document(documentation_id, document_name)
            return f"Document '{document_name}' deleted."

        return LLMTool(
            function=delete_document,
            description=(
                "Permanently remove a document from the documentation plan by its name. "
                "This cannot be undone - only use it if the document was created by mistake "
                "or is confirmed to no longer be needed."
            ),
            arguments=[
                self.argument_library['document_name']
            ]
        )

    def get_get_document(self, documentation_id: str) -> LLMTool:

        def get_document(document_name: str) -> Document | None:
            return self.document_repository.get_document(documentation_id, document_name)

        return LLMTool(
            function=get_document,
            description=(
                "Retrieve the current full state of a document - its goal, status, iteration count, and content if "
                "any has been written yet. Use this to check a document's goal before writing it, or to re-read "
                "its current content before revising it."
            ),
            arguments=[
                self.argument_library['document_name']
            ],
            can_be_deleted=False
        )

    def get_update_document(self, documentation_id: str) -> LLMTool:

        def update_document(
                document_name: str,
                goal: str | None = None,
                content: str | None = None,
                source_node_ids: list[str] | None = None) -> str:
            document_update = DocumentUpdate(
                goal=goal,
                content=content,
                source_node_ids=source_node_ids
            )

            self.document_repository.update_document(documentation_id, document_name, document_update)
            changed = [field for field in ("goal", "content", "source_node_ids") if locals()[field] is not None]
            return f"Document '{document_name}' updated ({', '.join(changed)})."


        return LLMTool(
            function=update_document,
            description=(
                "Update one or more fields of an existing document. Only the fields you provide are changed - omitted "
                "fields (left as null) stay untouched. Providing content replaces the document's entire content, it "
                "does not append to it."
            ),
            arguments=[
                self.argument_library['document_name'],
                self.argument_library['goal'],
                ToolArgument(
                    name='content',
                    type=ArgumentType.STRING,
                    description=(
                        "The full MD content of the document, replacing any previous content entirely. Valid MD "
                        "syntax, no manual frontmatter, no file extension in this value."
                    ),
                    is_discriminating=False
                ),
                self.argument_library['source_node_ids']
            ]
        )

    def get_get_documents(self, documentation_id: str) -> LLMTool:

        def get_documents() -> dict[str, dict]:
            documents: dict[str, dict] = {}

            for document in self.document_repository.get_documents(documentation_id):
                documents[document.document_name] = {
                    'goal': document.goal,
                    'status': document.status.value
                }

                if len(document.review) > 0:
                    documents[document.document_name]['review'] = document.review
            return documents

        return LLMTool(
            function=get_documents,
            description=(
                "Get an overview of every document in the plan - their name, goal, current status and review is this "
                "field is not empty - without their full content. Use get_document to read a specific document's "
                "content if needed."
            ),
            arguments=[]
        )

    def get_validate_one_document(self, documentation_id: str, document_name: str) -> LLMTool:

        def validate_document() -> str:
            self.document_repository.update_document(
                documentation_id,
                document_name,
                DocumentUpdate(status=DocumentStatus.APPROVED)
            )
            return f"Document '{document_name}' approved."

        return LLMTool(
            function=validate_document,
            description=(
                "Approve a document as final - use this only when its content fully and precisely satisfies its "
                "stated goal, with nothing lef to improve. This ends the review cycle for this document. If "
                "anything needs to change, use review_document instead."
            ),
            arguments=[]
        )

    def get_review_one_document(self, documentation_id: str, document_name: str) -> LLMTool:

        def review_document(review: str) -> str:
            self.document_repository.update_document(
                documentation_id,
                document_name,
                DocumentUpdate(status=DocumentStatus.DRAFT, review=review)
            )
            return f"Document '{document_name}' has been reviewed and sent back for revision."

        return LLMTool(
            function=review_document,
            description=(
                "Reject a document and send it back to the writer for revision, with your feedback attached. Use this "
                "whenever the content foes not yet fully satisfy the document's stated goal. If it does, "
                "use validate_document instead"
            ),
            arguments=[
                ToolArgument(
                    name='review',
                    type=ArgumentType.STRING,
                    description=(
                        "Concrete, actionable feedback for the writer. State precisely what is missing, incorrect, or "
                        "unclear, and what should change - not a general impression. The writer will revise based "
                        "only on this text, without seeing your reasoning."
                    )
                )
            ]
        )

    def get_update_one_document(self, documentation_id: str, document_name: str) -> LLMTool:

        def update_document(
                content: str | None = None,
                source_node_ids: list[str] | None = None) -> str:
            document_update = DocumentUpdate(
                content=content,
                source_node_ids=source_node_ids
            )

            self.document_repository.update_document(documentation_id, document_name, document_update)
            changed = [field for field in ("goal", "content", "source_node_ids") if locals()[field] is not None]
            return f"Document '{document_name}' updated ({', '.join(changed)})."

        return LLMTool(
            function=update_document,
            description=(
                "Update one or more fields of an existing document. Only the fields you provide are changed - omitted "
                "fields (left as null) stay untouched. Providing content replaces the document's entire content, it "
                "does not append to it."
            ),
            arguments=[
                ToolArgument(
                    name='content',
                    type=ArgumentType.STRING,
                    description=(
                        "The full MD content of the document, replacing any previous content entirely. Valid MD "
                        "syntax, no manual frontmatter, no file extension in this value."
                    ),
                    is_discriminating=False
                ),
                self.argument_library['source_node_ids']
            ]
        )
