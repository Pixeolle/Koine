from pydantic import BaseModel


class SignatureNode(BaseModel):
    signature: str | None = None
    children: list['SignatureNode'] = []

    def render(self, depth = 0, root = True) -> str:
        indent = '  ' * depth
        next_depth = depth + 1 if self.signature is not None else depth
        children_str = ''.join([child.render(depth=next_depth, root=False) for child in self.children])

        signature_str = ''
        if self.signature is not None:
            signature_str += f'{indent}{self.signature}\n'

        signature_str += f'{children_str}'

        if root:
            signature_str = signature_str.strip()

        return signature_str
