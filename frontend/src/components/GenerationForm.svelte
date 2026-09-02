<script lang="ts">

    import * as Field from "$lib/components/ui/field/index.ts";
    import {Card, CardHeader, CardContent, CardTitle, CardDescription} from "$lib/components/ui/card/index.ts";
    import Combobox from "./Combobox.svelte";
    import {Input} from "$lib/components/ui/input/index.ts";
    import {Checkbox} from "$lib/components/ui/checkbox/index.ts";
    import {Slider} from "$lib/components/ui/slider/index.ts";
    import {Button} from "$lib/components/ui/button/index.ts";
    import type { ApiClient } from "$lib/api/interface.ts"
    import {onMount} from "svelte";
    import type {OutputLanguage, SupportedPlatform} from "$lib/api/types.ts";
    import { ApiError } from "$lib/api/client.ts";

    let {
        api,
        onSuccess
    }: {
        api: ApiClient;
        onSuccess: (documentationId: string) => void;
    } = $props();

    let platforms = $state<Record<string, string>>({})
    let languages = $state<Record<string, string>>({})

    let repository_url = $state("");
    let selected_platform = $state<SupportedPlatform | "">("");
    let enable_access_token = $state(false);
    let access_token = $state("");
    let iteration = $state(1);

    let selected_language = $state<OutputLanguage | "">("");

    let is_access_token_hovered = $state(false);
    let loadingOptions = $state(true);
    let errorMessage = $state<string | null>(null);
    let existingDocumentationId = $state<string | null>(null);
    let submitting = $state(false);

    onMount(async () => {
        const [platformList, languageList] = await Promise.all([
            api.listPlatforms(),
            api.listLanguages(),
        ]);

        platforms = Object.fromEntries(platformList.map(platform => [platform.id, platform.label]))
        languages = Object.fromEntries(languageList.map(language => [language.code, language.label]))

        loadingOptions = false;
    })

    async function handleSubmit(event: SubmitEvent) {
        event.preventDefault()
        errorMessage = null;

        if (enable_access_token && access_token === "") {
            errorMessage = "Merci de fournir un accèss token";
            submitting = false;
            return;
        }

        if (selected_language === "" || selected_platform === "") {
            errorMessage = "Merci de remplir tous les champs";
            submitting = false;
            return;
        }


        submitting = true;

        try {
            const { documentation_id } = await api.generate({
                platform: selected_platform,
                url: repository_url,
                access_token: access_token,
                output_language: selected_language,
                iteration: iteration
            });
            onSuccess(documentation_id);
        } catch (e) {
            if (e instanceof ApiError && e.status === 409 && e.existingDocumentationId) {
                existingDocumentationId = e.existingDocumentationId
                errorMessage = "Ce dépôt a déà été documenté."
            } else {
                errorMessage = e instanceof Error ? e.message : "Une erreur est survenue.";
            }
        } finally {
            submitting = false;
        }
    }
</script>

{#if loadingOptions}
    <p class="text-sm text-muted-foreground">Chargement...</p>
{:else}
    <form onsubmit={handleSubmit}>
        <Field.Set>
            <Field.Legend>Source</Field.Legend>
            <Field.Group>
                <Field.Field>
                    <Field.Label for="platform">Plateforme</Field.Label>
                    <Combobox
                        bind:value={selected_platform}
                        mode="label"
                        placeholder_message="Sélectionnez une plateforme"
                        items={platforms}
                        search_message="Chercher..."
                        empty_message="Aucune plateforme correspondante."
                    />
                </Field.Field>

                <Field.Field>
                    <Field.Label for="repository-url">URL du dépôt</Field.Label>
                    <Input id="repository-url" bind:value={repository_url} required placeholder="https://platform/repository"/>

                    <Field.Field orientation="horizontal">
                        <Checkbox id="enable_access_token" bind:checked={enable_access_token}></Checkbox>
                        <Field.Label for="enable_access_token">Ajouter un access token</Field.Label>
                    </Field.Field>
                    {#if enable_access_token}
                        <Field.Field>
                            <Field.Label for="access_token">Token d'accès</Field.Label>
                            <Input id="access_token" bind:value={access_token} onfocus={() => is_access_token_hovered = true} onblur={() => is_access_token_hovered = false} required type={is_access_token_hovered ? "text" : "password"}/>
                        </Field.Field>
                    {/if}

                </Field.Field>
            </Field.Group>
        </Field.Set>
        <Field.Separator class="my-2"/>
        <Field.Set>
            <Field.Legend>Paramètres</Field.Legend>
            <Field.Group>
                <Field.Field>
                    <Field.Label for="iteration">Itération</Field.Label>
                    <div class="flex gap-5">
                        {iteration}
                        <Slider bind:value={iteration} min={0} max={10} step={1} type="single" />
                    </div>
                </Field.Field>

                <Field.Field>
                    <Field.Label for="language">Langue</Field.Label>
                    <Combobox
                        bind:value={selected_language}
                        mode="key"
                        placeholder_message="Sélectionnez une langue"
                        items={languages}
                        search_message="Chercher..."
                        empty_message="Aucune langue correspondante."
                    />
                </Field.Field>
            </Field.Group>
        </Field.Set>

        {#if errorMessage}
            <p class="text-sm text-destructive">
                {errorMessage}
                {#if existingDocumentationId}
                    <a href={`/docs/${existingDocumentationId}`} class="underline hover:text-destructive/80">
                        Voir la documentation existante
                    </a>
                {/if}
            </p>
        {/if}

        <div class="w-full flex justify-center pt-6">
            <Button type="submit" disabled={submitting}>
                {submitting ? "Lancement..." : "Lancer la génération"}
            </Button>
        </div>
    </form>
{/if}