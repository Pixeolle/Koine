from dataclasses import dataclass


@dataclass
class LLMUsageTracker:
    total_calls: int = 0
    total_input_tokens: int = 0
    total_output_tokens: int = 0

    def record(self, input_tokens: int, output_tokens) -> None:
        self.total_calls += 1
        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens

        return