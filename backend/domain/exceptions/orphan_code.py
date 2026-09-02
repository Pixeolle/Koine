from tree_sitter import Node

from backend.domain.exceptions.domain_error import DomainError


class OrphanCode(DomainError):
    def __init__(self, node: Node):
        message = f'Code orphelin: \n{node.text}'
        super().__init__(message)
