from datetime import datetime
from pathlib import Path

from pydantic import BaseModel
from sqlmodel import Session, SQLModel, create_engine, func, select

from backend.application.ports.document_repository import DocumentRepository
from backend.domain.entities.document import Document, DocumentCreate, DocumentUpdate
from backend.domain.entities.documentation import Documentation, DocumentationCreate, DocumentationUpdate
from backend.infrastructure.adapters.document_repositories.schemas.localfs_sqlite_schemas import (
    DocumentationModel,
    DocumentModel,
)
from backend.domain.entities.documentation import DocumentationStatus


class LocalFSSqLiteAdapter(DocumentRepository):

    def __init__(self, database_path: Path, documentation_repository_path: Path):
        self.engine = create_engine(f'sqlite:///{database_path}')
        SQLModel.metadata.create_all(self.engine)
        self.documentation_repository_path = documentation_repository_path

    def create_document(self, document_create: DocumentCreate) -> None:
        if self._get_document(document_create.documentation_id, document_create.document_name) is not None:
            raise ValueError(f'{document_create.document_name} in {document_create.documentation_id} already exists')

        entity = DocumentModel.from_document_create(document_create, self.documentation_repository_path)
        with Session(self.engine) as session:
            session.add(entity)
            session.commit()

        return

    def get_document(self, documentation_id: str, document_name: str) -> Document:
        document = self._get_document(documentation_id, document_name)
        if document is None:
            raise ValueError(f"There is no document named {document_name}.")

        return document.to_domain()

    def update_document(self, documentation_id: str, document_name: str, document_update: DocumentUpdate) -> None:
        entity = self._get_document(documentation_id, document_name)
        if entity is None:
            raise ValueError(f"There is no document named {document_name}")

        if document_update.content is not None:
            entity.write_content(document_update.content)

        self._update_entity(entity, document_update, excluded_fields= {"content"})

        return

    def delete_document(self, documentation_id, document_name) -> None:
        entity = self._get_document(documentation_id, document_name)
        if entity is None:
            raise ValueError(f"{document_name} in {documentation_id} doesn't exist")

        Path(entity.filepath).unlink()

        with Session(self.engine) as session:
            session.delete(entity)
            session.commit()

        return

    def get_documents(self, documentation_id: str) -> list[Document]:
        return [document_model.to_domain() for document_model in self._get_documents(documentation_id)]

    def create_documentation(self, documentation_create: DocumentationCreate) -> None:
        if self._get_documentation(documentation_create.documentation_id) is not None:
            raise ValueError(f"{documentation_create.documentation_id} already exists")

        entity = DocumentationModel.from_domain(documentation_create)

        with Session(self.engine) as session:
            session.add(entity)
            session.commit()

        return

    def get_documentation(self, documentation_id: str) -> Documentation:
        entity = self._get_documentation(documentation_id)
        if entity is None:
            raise ValueError(f"There is no entity with id: {documentation_id}.")

        return entity.to_domain()

    def update_documentation(self, documentation_id: str, documentation_update: DocumentationUpdate) -> None:
        entity = self._get_documentation(documentation_id)
        if entity is None:
            raise ValueError(f"There is no documentation with id: {documentation_id}.")

        self._update_entity(entity, documentation_update)

        return

    def delete_documentation(self, documentation_id) -> None:
        entity = self._get_documentation(documentation_id)
        if entity is None:
            raise ValueError(f"{documentation_id} doesn't exist")

        documents = self._get_documents(documentation_id)

        with Session(self.engine) as session:
            session.delete(entity)
            for document in documents:
                session.delete(document)
            session.commit()

    def get_documentation_length(self, documentation_id: str) -> int:
        with Session(self.engine) as session:
            statement = select(func.count()).select_from(DocumentModel).where(DocumentModel.documentation_id == documentation_id)
            documentation_length = session.exec(statement).one()

        assert isinstance(documentation_length, int)
        return documentation_length

    def get_documentations(self) -> list[Documentation]:
        with Session(self.engine) as session:
            statement = select(DocumentationModel).where(DocumentationModel.status == DocumentationStatus.FINISHED)
            documentations = session.exec(statement).all()

        assert isinstance(documentations, list)
        assert all(isinstance(documentation, DocumentationModel) for documentation in documentations)

        return [documentation.to_domain() for documentation in documentations]

    def get_documentation_by_hash(self, documentation_filename: str) -> Documentation | None:
        hashed_documentation = hash(documentation_filename)

        with Session(self.engine) as session:
            statement = select(DocumentationModel).where(DocumentationModel.hash == hashed_documentation)
            documentation = session.exec(statement).first()

        return documentation

    def _get_document(self, documentation_id: str, document_name: str) -> DocumentModel | None:
        with Session(self.engine) as session:
            statement = select(
                DocumentModel
            ).where(DocumentModel.document_id == Document.build_document_id(documentation_id, document_name))
            document: DocumentModel | None = session.exec(statement).first()

        return document

    def _update_entity(
            self,
            entity: SQLModel,
            update_model: BaseModel,
            excluded_fields: set[str] | None = None
    ) -> None:
        if excluded_fields is None:
            excluded_fields = set()

        changes = update_model.model_dump(exclude_none=True)

        for field, value in changes.items():
            if field not in excluded_fields:
                setattr(entity, field, value)

        with Session(self.engine) as session:
            session.add(entity)
            session.commit()
            session.refresh(entity)

        return

    def _get_documents(self, documentation_id: str) -> list[DocumentModel]:
        with Session(self.engine) as session:
            statement = select(DocumentModel).where(DocumentModel.documentation_id == documentation_id)
            document_models = session.exec(statement).all()

        assert isinstance(document_models, list)
        assert all(isinstance(document_model, DocumentModel) for document_model in document_models)
        return document_models

    def _get_documentation(self, documentation_id) -> DocumentationModel | None:
        with Session(self.engine) as session:
            statement = select(
                DocumentationModel
            ).where(DocumentationModel.documentation_id == documentation_id)
            documentation: DocumentationModel | None = session.exec(statement).first()

        return documentation
