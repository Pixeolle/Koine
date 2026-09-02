

class IdAlreadyInserted(ValueError):
    def __init__(self, node_id: str):
        message = f'ID déjà présent dans le graph: {node_id}'
        super().__init__(message)
