from neomodel import (
    JSONProperty,
    RelationshipFrom,
    RelationshipTo,
    StringProperty,
    StructuredNode,
    ZeroOrMore,
    ZeroOrOne,
)


class CodeNodeEntity(StructuredNode):
    graph_id = StringProperty(unique_index=False, required=True)
    code_node_id = StringProperty(unique_index=True, required=True)
    code_block = JSONProperty(required=True)
    llm_synthesis = JSONProperty()

    contain = RelationshipTo(
        'CodeNodeEntity',
        relation_type='CONTAIN',
        cardinality=ZeroOrMore,
    )

    is_contained_by = RelationshipFrom(
        'CodeNodeEntity',
        relation_type='CONTAIN',
        cardinality=ZeroOrOne
    )

    call = RelationshipTo(
        'CodeNodeEntity',
        relation_type='CALL',
        cardinality=ZeroOrMore
    )

    is_called_by = RelationshipFrom(
        'CodeNodeEntity',
        relation_type='CALL',
        cardinality=ZeroOrMore
    )

    def __hash__(self):
        return hash(self.code_node_id)
