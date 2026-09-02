# Task

Plan the documentation for this codebase from scratch

# Language

Write every document name and every goal in ${output_language}. Code identifiers, function names, and parameter 
names stay as they are in the source - never translate those. If ${output_language} cannot be written with plain 
lowercase hyphenated ASCII, transliterate document name to their closest ASCII equivalent to satisfy the URL 
constraint from your instructions, while keeping goals fully in ${output_language}.

# Scale 

This codebase has ${root_node_count} top-level modules ant ${total_node_count} nodes in total. Use this only to 
calibrate the plan's granularity - a small, focused codebase may need only a handful of files, while a large one may 
need reference files split per module rather than one file for everything. This is not a target for how many nodes 
to visit individually; your exploration should stay proportionate to what's needed to scope each file's goal 
precisely, as described in your instructions.

# Before you start

Call get_documents once, before anything else. If it returns existing entries, a plan is already partially in progress -
treat those as already decided, do not recreate or duplicate them, and focus on completing what's missing rather than
starting over.

# Process

Follow the exploration and planning method described in your instructions: strat from the graph's root nodes, walk down
until you understand the codebase's real shape, then design the file plan and register it with create_document - one
call per file.

You don't need to catalog every leaf node individually. Explore deep enough to understand the structure and group nodes
correctly; once a part of the graph is clear enough to scope a file's goal precisely, move on rather than continuing to
enumerate it node by node.

# When you're done

Once you're confident the plan is mutually exclusive and collectively exhaustive relative to everything you explored,
stop calling tools. reply with a short plain-text summary of the plan: the files you created and, in one line each, what
each one covers. Nothing further will be read from you tool calls after that message.
