from backend.domain.entities.llm_message import LLMMessage
from backend.domain.exceptions.domain_error import DomainError


class EmptyResponseError(DomainError):
    def __init__(self, model: str, messages: list[LLMMessage]):
        discussion = ''
        for message in messages:
            discussion += f'{message.role}: {message.content} \r\n'

        message = f"{model} n'a pas répondu au prompt suivant: \n{discussion}"
        super().__init__(message)
