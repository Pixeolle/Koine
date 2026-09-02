<script lang="ts">
    import DocumentationList from './DocumentationList.svelte';
    import GenerationForm from './GenerationForm.svelte'
    import { Button } from "$lib/components/ui/button"
    import * as Dialog from '$lib/components/ui/dialog'
    import { api } from "$lib/api/client.ts";

    let formOpen = $state(false);
</script>

<main class="container mx-auto py-16 space-y-12">
    <h1 class="text-4xl font-bold texte-center">Koine</h1>

    <DocumentationList api={api}/>

    <div class="flex justify-center">
        <Button size="lg" onclick={() => formOpen = true}>
            Nouvelle documentation
        </Button>
    </div>
</main>

<Dialog.Root bind:open={formOpen}>
    <Dialog.Content class="sm:max-w-lg max-h-[90vh] overflow-y-auto scrollbar-hide">
        <Dialog.Header>
            <Dialog.Title class="text-2xl font-bold tracking-tight">Générer une documentation</Dialog.Title>
        </Dialog.Header>
        <GenerationForm api={api} onSuccess={(documentation_id) => window.location.href = `/generations/${documentation_id}/progress`} />
    </Dialog.Content>

</Dialog.Root>
