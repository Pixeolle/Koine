<script lang="ts">
    import {Card, CardHeader, CardTitle, CardContent, CardFooter} from "$lib/components/ui/card/index.ts";
    import type { DocumentationSummary } from "$lib/api/types.ts";
    import {Button} from "$lib/components/ui/button";
    import { X } from "@lucide/svelte";
    import * as AlertDialog from "$lib/components/ui/alert-dialog";

    let {
        documentation,
        onDelete
    }: {
        documentation: DocumentationSummary;
        onDelete: (documentationId: string) => void;
    } = $props();

    let confirmOpen = $state(false);

    function handleConfirmDelete() {
        onDelete(documentation.documentation_id)
        confirmOpen = false;
    }
</script>

<Card class="relative" onclick={() => window.location.href = `/docs/${documentation.documentation_id}`}>
    <Button
        variant="ghost"
        size="icon"
        class="absolute top-2 right-2 h-7 w-7 text-muted-foreground hover:text-destructive"
        onclick={(e) => {e.stopPropagation(); confirmOpen=true}}
    >
        <X class="h-4 w-4"/>
        <span class="sr-only">Supprimer</span>
    </Button>

    <CardContent>
        <div class="flex items-baseline gap-1 pr-8">
            <CardTitle class="text-xl font-semibold">{documentation.documentation_name}</CardTitle>
            {#if documentation.additional_name != null}
                <span class="text-sm text-muted-foreground">/ {documentation.additional_name}</span>
            {/if}
        </div>
        <p class="text-xs text-muted-foreground">{new Date(documentation.fetched_date).toLocaleDateString()}</p>
    </CardContent>

    <CardFooter class="flex justify-between text-[11px] text-muted-foreground/70">
        <span>{documentation.input_token_used.toLocaleString()} token in</span>
        <span>{documentation.output_token_used.toLocaleString()} token out</span>
    </CardFooter>
</Card>

<AlertDialog.Root bind:open={confirmOpen}>
    <AlertDialog.Content>
        <AlertDialog.Header>
            <AlertDialog.Title>Supprimer cette documentation ?</AlertDialog.Title>
            <AlertDialog.Description>
                Cette action est irréversible. Tous les documents associés seront définitivement supprimés.
            </AlertDialog.Description>
        </AlertDialog.Header>
        <AlertDialog.Footer>
            <AlertDialog.Cancel>Annuler</AlertDialog.Cancel>
            <AlertDialog.Action
                onclick={handleConfirmDelete}
                class="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
                Supprimer
            </AlertDialog.Action>
        </AlertDialog.Footer>
    </AlertDialog.Content>
</AlertDialog.Root>
