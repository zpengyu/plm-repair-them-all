from .strategy import PromptingStrategy
from .strategies.infilling import InfillingPrompting
from .strategies.instruct import InstructPrompting
from .strategies.instruct_python import InstructPromptingPython


class PromptStrategyRegistry:
    """
    Class for storing and retrieving prompting strategies based on their name.
    """

    __STRATEGIES: dict[str, type] = {
        "infilling": InfillingPrompting,
        "instruct": InstructPrompting,
        "instruct_python": InstructPromptingPython,
    }

    @classmethod
    def get_strategy(cls, name: str, **kwargs) -> PromptingStrategy:
        if name.lower().strip() not in cls.__STRATEGIES:
            raise ValueError(f"Unknown prompting strategy {name}")
        return cls.__STRATEGIES[name.lower().strip()](**kwargs)
