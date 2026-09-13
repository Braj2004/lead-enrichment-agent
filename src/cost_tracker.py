"""
Token estimation and API cost calculation module.
Tracks token consumption and computes estimated cost per LLM invocation and per domain.
"""
from typing import Dict
try:
    import tiktoken
    TIKTOKEN_AVAILABLE = True
except ImportError:
    TIKTOKEN_AVAILABLE = False

from src.models import CostMetrics

# Model pricing structure (USD per 1,000,000 tokens)
MODEL_PRICING: Dict[str, Dict[str, float]] = {
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "gpt-4o": {"input": 2.50, "output": 10.00},
    "gemini-2.5-flash": {"input": 0.075, "output": 0.30},
    "gemini-1.5-flash": {"input": 0.075, "output": 0.30},
    "claude-3-5-sonnet": {"input": 3.00, "output": 15.00},
    "groq-llama-3.3-70b": {"input": 0.59, "output": 0.79},
    "default": {"input": 0.15, "output": 0.60},
}


def count_tokens(text: str, model_name: str = "gpt-4o-mini") -> int:
    """Accurately count or estimate tokens in a text string."""
    if not text:
        return 0
    if TIKTOKEN_AVAILABLE:
        try:
            encoding = tiktoken.get_encoding("cl100k_base")
            return len(encoding.encode(text))
        except Exception:
            pass
    # Fallback heuristic: ~4 characters per token for English text
    return max(1, len(text) // 4)


def calculate_cost(input_tokens: int, output_tokens: int, model_name: str = "gpt-4o-mini") -> float:
    """Calculate estimated cost in USD based on input and output token counts."""
    pricing = MODEL_PRICING.get(model_name.lower(), MODEL_PRICING["default"])
    input_cost = (input_tokens / 1_000_000.0) * pricing["input"]
    output_cost = (output_tokens / 1_000_000.0) * pricing["output"]
    return round(input_cost + output_cost, 6)


class CostTracker:
    """Tracks token consumption and API costs for the pipeline."""

    def __init__(self, default_model: str = "gpt-4o-mini"):
        self.default_model = default_model
        self.input_tokens = 0
        self.output_tokens = 0
        self.total_cost = 0.0

    def add_call(self, input_tokens: int, output_tokens: int, model_name: str = None) -> CostMetrics:
        """Record usage from an LLM call and update cumulative metrics."""
        model = model_name or self.default_model
        cost = calculate_cost(input_tokens, output_tokens, model)
        
        self.input_tokens += input_tokens
        self.output_tokens += output_tokens
        self.total_cost += cost

        return CostMetrics(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens,
            estimated_cost_usd=round(cost, 6)
        )

    def get_metrics(self) -> CostMetrics:
        """Return cumulative metrics."""
        return CostMetrics(
            input_tokens=self.input_tokens,
            output_tokens=self.output_tokens,
            total_tokens=self.input_tokens + self.output_tokens,
            estimated_cost_usd=round(self.total_cost, 6)
        )
