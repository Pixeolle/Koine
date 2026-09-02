<script>
    import { onMount } from "svelte";
    import mermaid from "mermaid";

    mermaid.initialize({
        startOnLoad: false,
        theme: "base",
        themeVariables: {
            primaryColor: "#EDF1FB",
            primaryTextColor: "#000000",
            primaryBorderColor: "#2D3FA3",
            lineColor: "#707070",
            secondaryColor: "#F0F0F0",
            tertiaryColor: "#F7F7F7",
            fontFamily: "Geist, sans-serif"
        }
    })

    onMount(() => {
        mermaid.initialize({ startOnLoad: false, theme: "neutral" });

        document.querySelectorAll("pre code.language-mermaid").forEach(async (block, i) => {
            const graphDefinition = block.textContent ?? "";
            const { svg } = await mermaid.render(`mermaid-${i}`, graphDefinition);
            const wrapper = document.createElement("div");
            wrapper.innerHTML = svg;
            block.closest("pre")?.replaceWith(wrapper);
        })
    });
</script>