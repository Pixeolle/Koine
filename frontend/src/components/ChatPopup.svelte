<script lang="ts">
    import { onMount, onDestroy } from "svelte";
    import * as Dialog from "$lib/components/ui/dialog";
    import * as Select from "$lib/components/ui/select"
    import { Button } from "$lib/components/ui/button";
    import { MessageCircle, ArrowUp } from "@lucide/svelte";
    import { chatStore } from "$lib/chat/chat-store.svelte"
    import { api } from "$lib/api/client.ts"
    import type {OutputLanguageResponse} from "$lib/api/types.ts";

    let { documentationId, documents }: { documentationId: string, documents: Set<string> } = $props();

    let open = $state(false);
    let connected = $state(false);
    let inputValue = $state("");
    let selectedLanguage = $state("fr");
    let languages = $state<OutputLanguageResponse[]>([]);
    let messagesContainer: HTMLDivElement;

    onMount(async () => {
        languages = await api.listLanguages();
    });

    function handleOpen() {
        open = true;
        if (!connected) {
            chatStore.connect(documentationId, documents);
            connected = true;
        }
    }

    function handleSend() {
        if (inputValue.trim() && !chatStore.streaming) {
            chatStore.send(inputValue, selectedLanguage);
        }
        messagesContainer.scrollTo({ top: messagesContainer.scrollHeight, behavior: "smooth"})

        inputValue = "";
        return;
    }

    function handleKeydown(e: KeyboardEvent) {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    }

    onDestroy(() => chatStore.disconnect());
</script>

<Button
    size="icon"
    class="fixed bottom-6 right-6 h-12 w-12 rounded-full shadow-lg z-50"
    onclick={handleOpen}
>
    <MessageCircle class="h-5 w-5" />
</Button>

<Dialog.Root bind:open>
    <Dialog.Content class="!max-w-none w-[80vw] h-[80vh] flex flex-col p-0 gap-0">
        <div bind:this={messagesContainer} class="flex-1 overflow-y-auto px-6 py-4 space-y-4">
            {#if chatStore.messages.length === 0}
                <p class="text-center text-muted-foreground text-sm mt-8">
                    Poser une question sur ce Repository
                </p>
            {/if}

            {#each chatStore.messages as message, i}
                <div class={message.role === "user" ? "flex justify-end" : "flex justify-start"}>
                    {#if message.role === "user"}
                        <span class="inline-block max-w-[75%] rounded-lg px-3 py-2 text-sm bg-primary text-primary-foreground">
                            {message.content}
                        </span>
                    {:else if chatStore.renderedMessages[i]}
                        <div class="max-w-[85%] rounded-lg border bg-muted/50 px-4 py-3">
                            <div class="prose prose-sm dark:prose-invert max-w-none">
                                {@html chatStore.renderedMessages[i]}
                            </div>
                        </div>
                    {:else if chatStore.streaming && i === chatStore.messages.length - 1}
                        {#if chatStore.messages[i].content.length === 0}
                            <div class="flex gap-1 items-center h-4">
                                <span class="h-1.5 w-1.5 rounded-full bg-muted-foreground animate-bounce [animation-delay:-0.3s]"></span>
                                <span class="h-1.5 w-1.5 rounded-full bg-muted-foreground animate-bounce [animation-delay:-0.15s]"></span>
                                <span class="h-1.5 w-1.5 rounded-full bg-muted-foreground animate-bounce"></span>
                            </div>
                        {:else}
                            <div class="max-w-[85%] rounded-lg border bg-muted/50 px-4 py-3">
                                <div class="prose prose-sm dark:prose-invert max-w-none">
                                    {message.content}
                                </div>
                            </div>
                        {/if}
                    {:else}
                        <div class="max-w-[85%] rounded-lg border bg-muted/50 px-4 py-3">
                            <div class="prose prose-sm dark:prose-invert max-w-none">
                                {message.content}
                            </div>
                        </div>
                    {/if}
                </div>
            {/each}
        </div>

        <div class="border-t p-3">
            <div class="rounded-xl forder bg-background focus-within:ring-1 focus-within:ring-ring">
                <textarea
                    bind:value={inputValue}
                    onkeydown={handleKeydown}
                    placeholder="Pose ta question"
                    disabled={chatStore.streaming}
                    rows="2"
                    class="w-full resize-none bg-transparent px-4 py-3 text-sm outline-none placeholder:text-muted-foreground"
                ></textarea>
                <div class="flex items-center justify-between px-2 pb-2">
                    <Select.Root type="single" bind:value={selectedLanguage}>
                        <Select.Trigger class="w-auto border-0 shadow-none h-7 px-2 text-xs text-muted-foreground">
                            {languages.find(l => l.code === selectedLanguage)?.label ?? selectedLanguage}
                        </Select.Trigger>
                        <Select.Content>
                            {#each languages as lang}
                                <Select.Item value={lang.code}>{lang.label}</Select.Item>
                            {/each}
                        </Select.Content>
                    </Select.Root>

                    <Button
                        size="icon"
                        class="h-8 w-8 rounded-full"
                        disabled={chatStore.streaming || !inputValue.trim()}
                        onclick={handleSend}
                    >
                        <ArrowUp class="h-4 w-4" />
                    </Button>
                </div>
            </div>
        </div>
    </Dialog.Content>
</Dialog.Root>

