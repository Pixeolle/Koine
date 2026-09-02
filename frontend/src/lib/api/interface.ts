import type {
    DocumentationSummary,
    DocumentResponse,
    GenerateRequest,
    GenerateResponse,
    OutputLanguageResponse,
    StreamEvent,
    SupportedPlatformResponse,
    DocumentSummary
} from "./types";

export interface ApiClient {
    listPlatforms(): Promise<SupportedPlatformResponse[]>;
    listLanguages(): Promise<OutputLanguageResponse[]>;
    listDocuments(documentationId: string): Promise<DocumentSummary[]>;
    listDocumentations(): Promise<DocumentationSummary[]>;
    generate(payload: GenerateRequest): Promise<GenerateResponse>;
    deleteDocumentation(documentationId: string): Promise<void>;
    getDocument(documentationId: string, documentName: string): Promise<DocumentResponse>;
    subscribeToProgress(documentationId: string, onEvent: (event: StreamEvent) => void): () => void;
}