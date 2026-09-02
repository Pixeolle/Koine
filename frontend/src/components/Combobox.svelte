<script lang="ts">
 import CheckIcon from "@lucide/svelte/icons/check";
 import ChevronsUpDownIcon from "@lucide/svelte/icons/chevrons-up-down";
 import { tick } from "svelte";
 import * as Command from "$lib/components/ui/command/index.js";
 import * as Popover from "$lib/components/ui/popover/index.js";
 import { Button } from "$lib/components/ui/button/index.js";
 import { cn } from "$lib/utils.js";

 interface Props {
  value: string
  mode: "label" | "key"
  placeholder_message: string;
  items: Record<string, string>;
  search_message: string;
  empty_message: string
 }
 let { value = $bindable(""), mode = "key", placeholder_message, items, search_message, empty_message }: Props = $props()

 let key: string = $state("");

 $effect(() =>{
  if (mode === "label") {
   value = items[key]
  } else {
   value = key
  }
 })

 let open = $state(false);
 let triggerRef = $state<HTMLButtonElement>(null!);

 // We want to refocus the trigger button when the user selects
 // an item from the list so users can continue navigating the
 // rest of the form with the keyboard.
 function closeAndFocusTrigger() {
  open = false;
  tick().then(() => {
   triggerRef.focus();
  });
 }
</script>

<Popover.Root bind:open>
 <Popover.Trigger bind:ref={triggerRef}>
  {#snippet child({ props })}
   <Button
    {...props}
    variant="outline"
    class="w-56 justify-between"
    role="combobox"
    aria-expanded={open}
   >
    {items[key] || placeholder_message}
    <ChevronsUpDownIcon class="opacity-50" />
   </Button>
  {/snippet}
 </Popover.Trigger>
 <Popover.Content class="w-56 p-0">
  <Command.Root>
   <Command.Input placeholder={search_message} />
   <Command.List>
    <Command.Empty>{empty_message}</Command.Empty>
    <Command.Group value="frameworks">
     {#each Object.keys(items) as item_key }
      <Command.Item
       value={items[item_key]}
       onSelect={() => {
        key = item_key;
        closeAndFocusTrigger();
       }}
      >
       <CheckIcon
        class={cn(key !== item_key && "text-transparent")}
       />
       {items[item_key]}
      </Command.Item>
     {/each}
    </Command.Group>
   </Command.List>
  </Command.Root>
 </Popover.Content>
</Popover.Root>