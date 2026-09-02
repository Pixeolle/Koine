import MarkdownIt from "markdown-it";
import Container from "markdown-it-container";
import Shiki from "@shikijs/markdown-it";
import githubLight from "@shikijs/themes/github-light"
import githubDark from "@shikijs/themes/github-dark"

let mdInstance: MarkdownIt | null = null;

async function getMarkdownRenderer(): Promise<MarkdownIt> {
    if (!mdInstance) {
        const md = new MarkdownIt({ html: false, linkify: true });

        md.use(await Shiki({
            themes: { light: githubLight, dark: githubDark},
            fallbackLanguage: 'wikitext'
        }));

        for (const type of ["note", "tip", "caution"]) {
            md.use(Container, type, {
                render(tokens: any[], idx: number) {
                    return tokens[idx].nesting === 1
                        ? `<div class="starlight-aside starlight-aside--${type}">\n`
                        : `</div>\n`
                },
            });
        }

        mdInstance = md;
    }

    return mdInstance;
}

export async function renderMarkdown(content: string, documentationId: string, validDocumentNames: Set<string>) {
    const md = await getMarkdownRenderer();

    md.renderer.rules.link_open = (tokens, idx, options, env, self) => {
        const hrefIndex = tokens[idx].attrIndex("href");
        const href_raw = tokens[idx].attrs?.[hrefIndex]?.[1] ?? "";
        const href = href_raw as string;
        const documentName = decodeURIComponent(href)

        if (validDocumentNames.has(documentName)) {
            tokens[idx].attrSet("href", `/docs/${documentationId}/${documentName}`)
        } else {
            tokens[idx].attrSet("href", "#");
            tokens[idx].attrSet("class", "text-muted-foreground no-underline cursor-default pointer-events-none");
            tokens[idx].attrSet("title", "Ce lien ne pointe vers aucun document valide.")
        }

        return self.renderToken(tokens, idx, options);
    };

    return md.render(content)
}