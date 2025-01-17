from typing import Optional
from .cost_strategy import CostStrategy

import tqdm


class MistralCostStrategy(CostStrategy):

    __COST_PER_MILLION_TOKENS = {
        "mistral-large-2411": {
            "prompt": 2,
            "completion": 6,
        },
        "codestral-2405": {
            "prompt": 0.2,
            "completion": 0.6,
        },
        "codestral-2501": {
            "prompt": 0.3,
            "completion": 0.9,
        },
    }

    @staticmethod
    def compute_costs(samples: list, model_name: str) -> Optional[dict]:
        if model_name not in MistralCostStrategy.__COST_PER_MILLION_TOKENS:
            return None

        costs = {
            "prompt_cost": 0.0,
            "completion_cost": 0.0,
            "total_cost": 0.0,
        }

        for sample in tqdm.tqdm(samples, f"Computing costs for {model_name}..."):
            if sample["generation"]:
                g = sample["generation"]
                prompt_token_count = g["usage"]["prompt_tokens"]
                candidates_token_count = g["usage"]["completion_tokens"]

                prompt_cost = MistralCostStrategy.__COST_PER_MILLION_TOKENS[model_name][
                    "prompt"
                ]
                completion_cost = MistralCostStrategy.__COST_PER_MILLION_TOKENS[
                    model_name
                ]["completion"]

                costs["prompt_cost"] += prompt_cost * prompt_token_count / 1000000
                costs["completion_cost"] += (
                    completion_cost * candidates_token_count / 1000000
                )

        costs["total_cost"] = costs["prompt_cost"] + costs["completion_cost"]
        return costs
