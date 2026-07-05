# USD per 1M tokens — approximate list prices for cost estimates.
MODEL_PRICING: dict[str, dict[str, float]] = {
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "gpt-4o": {"input": 2.50, "output": 10.00},
    "claude-sonnet-4-20250514": {"input": 3.00, "output": 15.00},
    "claude-3-5-sonnet-latest": {"input": 3.00, "output": 15.00},
    "llama3.2": {"input": 0.0, "output": 0.0},
}


def estimate_cost_usd(model: str, *, prompt_tokens: int, completion_tokens: int) -> float:
    pricing = MODEL_PRICING.get(model)
    if pricing is None:
        for key, value in MODEL_PRICING.items():
            if model.startswith(key.split("-")[0]):
                pricing = value
                break
    if pricing is None:
        return 0.0

    input_cost = (prompt_tokens / 1_000_000) * pricing["input"]
    output_cost = (completion_tokens / 1_000_000) * pricing["output"]
    return round(input_cost + output_cost, 6)
