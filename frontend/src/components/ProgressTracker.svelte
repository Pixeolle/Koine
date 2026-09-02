<script lang="ts">
    import { onMount, onDestroy } from "svelte";
    import { api } from "$lib/api/client.ts";
    import type { StreamEvent, StreamEventType } from "$lib/api/types.ts"

    let { documentationId }: { documentationId: string } = $props();

    const PHASES = [
        { label: "Récupération du dépôt", events: ["fetching", "repository_fetched"] },
        { label: "Construction du graphe", events: ["building_code_graph", "parsing_source_code", "source_code_parsed", "linking_dependencies", "dependencies_linked", "code_graph_built"] },
        { label: "Enrichissement", events: ["enriching_code_graph", "code_graph_enriched"] },
        { label: "Planification", events: ["planning_documentation", "plan_ready"] },
        { label: "Rédaction & révision", events: ["writing_document", "document_written", "reviewing_document", "document_reviewed"]}
    ];

    const MAIN_TEXT: Record<string, string> = {
        fetching: "Récupération du dépôt en cours...",
        repository_fetched: "Dépôt récupéré",
        building_code_graph: "Construction du graph de code...",
        parsing_source_code: "Analyse du code source...",
        source_code_parsed: "Code source analysé",
        linking_dependencies: "Résolution des dépendances...",
        dependencies_linked: "Dépendances résolues",
        code_graph_built: "Graph de code construit",
        enriching_code_graph: "Compréhension approfondie du code...",
        code_graph_enriched: "Analyse enrichie",
        planning_documentation: "Élaboration du plan de documentation...",
        plan_ready: "Plan de documentation prêt",
        writing_document: "Rédaction en cours",
        document_written: "Rédaction en cours",
        reviewing_document: "Vérification en cours",
        document_reviewed: "Vérification en cours",
        complete: "Documentation générée avec succès",
        error: "Une erreur est survenue"
    };

    let currentPhaseIndex = $state(0);
    let mainText = $state("Initialisation...");
    let subText = $state("");
    let errorMessage = $state<string | null>(null);
    let unsubscribe: (() => void) | undefined;

    function phaseIndexFor(eventType: string): number {
        return PHASES.findIndex(phase => phase.events.includes(eventType as never))
    }

    function buildSubText(event: StreamEvent): string {
        switch (event.type) {
            case "repository_fetched":
                return event.file_len != null ? `${event.file_len} fichiers récupéres` : "";
            case "source_code_parsed":
                return event.structural_dependencies != null ? `${event.structural_dependencies} dépendances structurelles identifées` : "";
            case "dependencies_linked":
                return event.dependency_linked != null ? `${event.dependency_linked} dépendances liées` : "";
            case "code_graph_built":
                return event.nodes != null && event.dependencies != null ? `${event.nodes} nœuds, ${event.dependencies} dépendances` : "";
            case "plan_ready":
                return event.documentation_length != null ? `${event.documentation_length} documents à générer` : "";
            case "document_written":
            case "document_reviewed":
                return event.completed_count != null && event.total_count != null ?
                    `${event.completed_count} / ${event.total_count} documents ${event.type === "document_written" ? "rédigés" : "vérifiés"}` : "";
            default:
                return "";
        }
    }

    function handleEvent(event: StreamEvent) {
        console.log(event)
        if (event.type === "error") {
            errorMessage = event.detail ?? "Une erreur est survenue.";
            return;
        }

        const idx = phaseIndexFor(event.type);
        if (idx >= 0) currentPhaseIndex = idx;

        mainText = MAIN_TEXT[event.type] ?? event.type;
        if (event.type === "writing_document" || event.type === "reviewing_document") {
            mainText = `${MAIN_TEXT[event.type]} - ${event.total_count} Documents`;
        }
        subText = buildSubText(event);

        if (event.type === "complete") {
            setTimeout(() => window.location.href = `/docs/${documentationId}`, 1000);
        }
    }

    onMount(() => {
        unsubscribe = api.subscribeToProgress(documentationId, handleEvent);
    });

    onDestroy(() => unsubscribe?.())
</script>

<main class="min-h-screen flex">
    <aside class="w-64 border-r border-border p-8 flex flex-col gap-6">
        {#each PHASES as phase, i}
            <div class="flex items-start gap-3">
                <div class="flex flex-col items-center">
                    <div
                        class="h-3 w-3 rounded-full transition-colors duration-500 {
                        i < currentPhaseIndex ? 'bg-primary' : i === currentPhaseIndex ? 'bg-primary ring-4 ring-primary/20' : 'bg-muted'
                        }"
                    ></div>
                    {#if i < PHASES.length - 1}
                        <div class="w-px flex-1 mt-1 transition-colors duration-500 {i < currentPhaseIndex ? "bg-primary" : "bg-muted"}"></div>
                    {/if}
                </div>
                <span class="text-sm pt-[-2px] {i <= currentPhaseIndex ? 'text-foreground font-medium' : 'text-muted-foreground'}">
                    {phase.label}
                </span>
            </div>
        {/each}
    </aside>

    <div class="flex-1 flex items-center justify-center">
        {#if errorMessage}
            <p class="text-destructive text-lg">{errorMessage}</p>
        {:else}
            <div class="text-center space-y-2">
                {#key mainText}
                    <p class="text-2xl font-semibold animate-in fade-in slide-in-from-bottom-2 duration-300">
                        {mainText}
                    </p>
                {/key}
                {#if subText}
                    {#key subText}
                        <p class="text-sm text-muted-foreground animate-in fade-in duration-300">
                            {subText}
                        </p>
                    {/key}
                {/if}
            </div>
        {/if}
    </div>
</main>