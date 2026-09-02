<script lang="ts">
    import { onMount } from "svelte";
    import {Skeleton} from "$lib/components/ui/skeleton";
    import DocumentationCard from "./DocumentationCard.svelte"
    import type { ApiClient } from "$lib/api/interface";
    import type { DocumentationSummary } from "$lib/api/types.ts";

    let { api }: { api: ApiClient } = $props();

    let documentations = $state<DocumentationSummary[]>([]);
    let loading = $state(true);

    async function load() {
        loading = true;
        documentations = await api.listDocumentations();
        loading = false;
    }

    async function handleDelete(documentationId: string) {
        await api.deleteDocumentation(documentationId);
        documentations = documentations.filter(documentation => documentation.documentation_id !== documentationId);
    }

    onMount(load);
</script>

{#if loading}
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {#each { length: 3 } as _}
            <Skeleton class="h-40 w-full rounded-lg" />
        {/each}
    </div>
    <p class="text-center text-muted-foreground">Chargement...</p>
{:else if documentations.length === 0}
    <p class="text-center text-muted-forgeground">Aucune documentation générée pour le moment.</p>
{:else}
    <div class="grid grid-cols-1 md:grid-cols2 lg:grid-cols-3 gap-4">
        {#each documentations as documentation (documentation.documentation_id)}
            <DocumentationCard {documentation} onDelete={handleDelete} />
        {/each}
    </div>
{/if}