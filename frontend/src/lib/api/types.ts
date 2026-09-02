import type { components } from "$lib/api/types.generated.ts";

export type DocumentationSummary = components["schemas"]["DocumentationSummary"]
export type DocumentResponse = components["schemas"]["DocumentResponse"]
export type GenerateRequest = components["schemas"]["GenerationRequest"]
export type GenerateResponse = components["schemas"]["GenerationResponse"]
export type OutputLanguageResponse = components["schemas"]["OutputLanguageResponse"]
export type OutputLanguage = components["schemas"]["OutputLanguage"]
export type SupportedPlatformResponse = components["schemas"]["SupportedPlatformResponse"]
export type SupportedPlatform = components["schemas"]["SupportedPlatform"]
export type DocumentSummary = components["schemas"]["DocumentSummary"]

export type StreamEventType =
    | 'fetching'
    | 'repository_fetched'
    | 'building_code_graph'
    | 'parsing_source_code'
    | 'source_code_parsed'
    | 'linking_dependencies'
    | 'dependencies_linked'
    | 'code_graph_built'
    | 'enriching_code_graph'
    | 'code_graph_enriched'
    | 'planning_documentation'
    | 'plan_ready'
    | 'writing_document'
    | 'document_written'
    | 'reviewing_document'
    | 'document_reviewed'
    | 'complete'
    | 'error';

export interface StreamEvent {
    type: StreamEventType;
    file_len?: number | null;
    detail?: string | null;
    total_count?: number | null;
    completed_count?: number | null;
    structural_dependencies?: number | null;
    dependency_linked?: number | null;
    nodes?: number | null;
    dependencies?: number | null;
    documentation_length?: number | null;
    document_name?: string | null;
}
