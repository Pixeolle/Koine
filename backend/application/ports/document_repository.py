from abc import ABC, abstractmethod
from datetime import datetime

from backend.domain.entities.document import Document, DocumentCreate, DocumentUpdate
from backend.domain.entities.documentation import Documentation, DocumentationCreate, DocumentationUpdate


class DocumentRepository(ABC):

    @abstractmethod
    def create_document(self, document_create: DocumentCreate) -> None:
        pass

    @abstractmethod
    def get_document(self, documentation_id: str, document_name: str) -> Document:
        pass

    @abstractmethod
    def update_document(self, documentation_id: str, document_name: str, document_update: DocumentUpdate) -> None:
        pass

    @abstractmethod
    def delete_document(self, documentation_id, document_name) -> None:
        pass

    @abstractmethod
    def get_documents(self, documentation_id: str) -> list[Document]:
        pass

    @abstractmethod
    def create_documentation(self, documentation_create: DocumentationCreate)-> None:
        pass

    @abstractmethod
    def get_documentation(self, documentation_id: str) -> Documentation:
        pass

    @abstractmethod
    def update_documentation(self, documentation_id: str, documentation_update: DocumentationUpdate) -> None:
        pass

    @abstractmethod
    def delete_documentation(self, documentation_id) -> None:
        pass

    @abstractmethod
    def get_documentation_length(self, documentation_id: str) -> int:
        pass

    @abstractmethod
    def get_documentations(self) -> list[Documentation]:
        pass

    @abstractmethod
    def get_documentation_by_hash(self, documentation_filename: str) -> Documentation | None:
        pass
