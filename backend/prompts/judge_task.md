# Task 

Review the MD content of one document against its goal and against the code it describes. 

# Document

- Name: ${document_name}
- Goal: ${goal}

<content_to_review>
${content}
</content_to_review>

# Source nodes

These are the node ids the writer already used and found while producing this content - a convenient, known-valid 
starting point for your verification, not the boundary of what you can check. Use get_node_synthesis or get_node 
content directly on them to save step, then use get_root_nodes, get_children, or get_parents freely if you nood to 
check anything beyond them - for instance, a claim that isn't grounded in any of these nodes, or a related node the 
writer should have checked but didn't.

${source_node_ids}

If this list is empty, that is itself worth noting: it means the writer didn't track what it grounded the content in

# Language

The content should be written in ${output_language}. Code identifiers, function and parameter names, and code sample should remain exactly as found in the source - flag it if anything has been translated.

# When you're done

Follow the process from your instructions. Call validate_document if the content is accurate and complete, or 
review_document with precise feedback if it isn't. The stop calling tools and reply with a short summary of your 
verdict.