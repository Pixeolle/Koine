

class IdNotFound(ValueError):
    def __init__(self, node_id: str):
        message = f'Id non présent dans le graph {node_id}'
        super().__init__(message)
