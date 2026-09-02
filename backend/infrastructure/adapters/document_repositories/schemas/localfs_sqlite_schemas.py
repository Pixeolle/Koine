from datetime import datetime
from pathlib import Path

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel

from backend.domain.entities.document import Document, DocumentCreate, DocumentStatus
from backend.domain.entities.documentation import Documentation, DocumentationStatus, DocumentationCreate


class DocumentModel(SQLModel, table=True):
    document_id: str = Field(default=None, primary_key=True)
    documentation_id: str = Field(default=None, foreign_key="documentationmodel.documentation_id")
    document_name: str
    goal: str
    filepath: str
    status: DocumentStatus = DocumentStatus.DRAFT
    review: str = ''
    iteration: int = 0
    source_node_ids: list[str] = Field(default=[], sa_column=Column(JSON))


    def to_domain(self) -> Document:
        with Path.open(Path(self.filepath), 'r', encoding='utf8') as reader:
            content = reader.read()

        return Document(
            document_name=self.document_name,
            documentation_id=self.documentation_id,
            goal=self.goal,
            content=content,
            status=self.status,
            review=self.review,
            iteration=self.iteration,
            source_node_ids=self.source_node_ids
        )

    @classmethod
    def from_document_create(cls, document_create: DocumentCreate, documentation_repository_path: Path) -> "DocumentModel":
        document_path = Path(f"{document_create.document_name}.md")
        destination_directory = (
                documentation_repository_path.absolute() /
                document_create.documentation_id /
                document_path.parent
        )
        destination_directory.mkdir(parents=True, exist_ok=True)

        destination_path = destination_directory / document_path.name
        destination_path.touch()

        return cls(
            document_id=document_create.document_id,
            documentation_id=document_create.documentation_id,
            document_name=document_create.document_name,
            goal=document_create.goal,
            filepath=destination_path.as_posix(),
        )

    def write_content(self, content: str) -> None:
        with Path.open(Path(self.filepath), 'w', encoding='utf8') as writer:
            writer.write(content)


class DocumentationModel(SQLModel, table=True):
    documentation_id: str = Field(default=None, primary_key=True)
    documentation_name: str
    additional_name: str | None = None
    fetched_date: datetime
    status: DocumentationStatus = DocumentationStatus.DRAFT
    call_used: int = 0
    input_token_used: int = 0
    output_token_used: int = 0
    hash: int

    def to_domain(self) -> Documentation:
        return Documentation(
            documentation_id=self.documentation_id,
            documentation_name=self.documentation_name,
            additional_name=self.additional_name,
            fetched_date=self.fetched_date,
            status=self.status,
            call_used=self.call_used,
            input_token_used=self.input_token_used,
            output_token_used=self.output_token_used,
            hash=self.hash
        )

    @classmethod
    def from_domain(cls, documentation_create: DocumentationCreate) -> "DocumentationModel":
        return cls(
            documentation_id=documentation_create.documentation_id,
            documentation_name=documentation_create.documentation_name,
            additional_name=documentation_create.additional_name,
            fetched_date=documentation_create.fetched_date,
            hash=documentation_create.hash
        )
