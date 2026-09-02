import type { ApiClient } from "$lib/api/interface.ts";
import type {DocumentationSummary, DocumentSummary, StreamEvent} from "$lib/api/types.ts";

const mockDocumentations: DocumentationSummary[] = [
    {
        documentation_id: "abc-123",
        documentation_name: "koine",
        additional_name: "main",
        fetched_date: "2026-08-01T10:00:00Z",
        input_token_used: 45000,
        output_token_used: 12000
    },
    {
        documentation_id: "def-456",
        documentation_name: "my-api",
        additional_name: "feature/auth",
        fetched_date: "2026-08-05T14:30:00Z",
        input_token_used: 22000,
        output_token_used: 8000
    }
]

const mockDocuments: DocumentSummary[] = [
    { document_name: "index", goal: "Vue d'ensemble", status: "approved", iteration: 1, review: "", source_node_ids: []},
    { document_name: "reference/auth-service", goal: "La référence", status: "draft", iteration: 2, review: "Pas fou", source_node_ids: []},
    { document_name: "how-to/add-a-provider", goal: "La référence", status: "draft", iteration: 2, review: "Pas fou", source_node_ids: []},
]

const mockDocumentContent = `# Vue d'ensemble
Ceci est un contenu de test pour valider le rendu de la page de documentation.

## Sous-Section

Un pe de texte supplémentaire, ave un [lien vers un autre document](/docs/abc-123/reference/auth-service).
`;

export const mockApi: ApiClient = {
    async generate(payload) {
        return { documentation_id: "mock-123"};
    },
    async listDocumentations() {
        return mockDocumentations;
    },
    async deleteDocumentation(documentationId: string) {},
    async getDocument(documentationId: string, documentName: string) {
        return {
            document_name: documentName,
            content: mockDocumentContent
        };
    },
    async listDocuments(documentation_id: string) {
        return mockDocuments;
    },
    async listPlatforms() {
        await new Promise(resolve => setTimeout(resolve, 150))
        return [
            { id: "GITHUB", label: "GitHub"},
            { id: "GITLAB", label: "GitLab"}
        ];
    },
    async listLanguages() {
        await new Promise(resolve => setTimeout(resolve, 150))
        return [
            { code: "fr", label: "Français"},
            { code: "en", label: "English"}
        ]
    },
    subscribeToProgress(documentationId: string, onEvent): () => void {
        const events: StreamEvent[] = [
            { type: "fetching" },
            { type: "repository_fetched", file_len: 128 },
            { type: "building_code_graph" },
            { type: "parsing_source_code" },
            { type: "source_code_parsed", structural_dependencies: 340 },
            { type: "linking_dependencies" },
            { type: "dependencies_linked", dependency_linked: 512},
            { type: "code_graph_built", nodes: 890, dependencies: 852 },
            { type: "enriching_code_graph" },
            { type: "code_graph_enriched" },
            { type: "planning_documentation" },
            { type: "plan_ready", documentation_length: 5 },
            { type: "writing_document", document_name: "index" },
            { type: "writing_document", document_name: "reference/auth-service" },
            { type: "document_written", document_name: "index", completed_count: 1, total_count: 5 },
            { type: "document_written", document_name: "reference/auth-service", completed_count: 2, total_count: 5 },
            { type: "reviewing_document", document_name: "index" },
            { type: "reviewing_document", document_name: "reference/auth-service" },
            { type: "document_reviewed", document_name: "index", completed_count: 1, total_count: 5 },
            { type: "document_reviewed", document_name: "reference/auth-service", completed_count: 2, total_count: 5 },
            { type: "complete"}
        ];

        let index = 0;
        const interval = setInterval(() => {
            if (index >= events.length) {
                clearInterval(interval);
                return;
            }
            onEvent(events[index]);
            index++;
        }, 1200);

        return () => clearInterval(interval);
    }
}
