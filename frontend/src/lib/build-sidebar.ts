import type { DocumentSummary } from "./api/types";

interface SidebarLink {
    label: string;
    link: string;
}

interface SidebarGroup {
    label: string;
    items: (SidebarLink | SidebarGroup)[];
    collapsed?: boolean;
}

export function buildSidebar(
    documents: DocumentSummary[],
    documentationId: string
): (SidebarLink | SidebarGroup)[] {
    const root: (SidebarLink | SidebarGroup)[] = [
        { label: "Accueil", link: `/docs/${documentationId}`},
    ];

    for (const doc of documents) {
        if (doc.document_name === "index") continue;

        const parts = doc.document_name.split("/");
        const fileName = parts.pop()!;
        let currentLevel = root;

        for (const folderName of parts) {
            let group = currentLevel.find(
                (item): item is SidebarGroup => "items" in item && item.label === toLabel(folderName)
            );

            if (!group) {
                group = { label: toLabel(folderName), items: [], collapsed: true };
                currentLevel.push(group)
            }
            currentLevel = group.items
        }

        currentLevel.push({
            label: toLabel(fileName),
            link: `/docs/${documentationId}/${doc.document_name}`,
        })

    }
    
    return root;
}

export function toLabel(segment: string): string {
    return segment
        .replace(/-/g, " ")
        .split(" ")
        .map(word => word.charAt(0).toUpperCase() + word.slice(1))
        .join(" ");
}