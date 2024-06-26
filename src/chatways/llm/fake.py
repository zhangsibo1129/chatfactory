import time
import random
from typing import Optional, Any

from chatways.llm.utils import BaseChatModel, register_llm


@register_llm("fake")
class FakeChatModel(BaseChatModel):
    """
    Fake Chat Model
    """

    engine = "fake"
    model: str = ""
    default_model: str = "fake_chat_model"

    def __init__(
        self, model: Optional[str] = None, model_config: Optional[dict] = None
    ) -> None:
        if model is None:
            self.model = self.default_model
        else:
            self.model = model
        self.candidates = [
            "That's a great question. Let me think about it for a moment.",
            "I appreciate your perspective, and I'll take that into consideration.",
            "It's an interesting topic, I'd love to discuss it further.",
            "I'm not entirely sure, but I can look into it and get back to you.",
            "I'm open to exploring different ideas and finding a solution together.",
            "I see where you're coming from, and I respect your point of view.",
            "Let's brainstorm some potential options and see what might work best.",
            "I'm willing to collaborate and find a way to move forward.",
            "I value your input, and I'm interested in hearing more about your thoughts.",
            "It's important to approach this with an open mind and consider all possibilities.",
        ]

    def invoke(self, messages: Any, generation_config: Optional[dict] = None) -> str:
        response = random.choice(self.candidates)
        response += " (generated by fake llm)"
        return response

    def invoke_stream(
        self, messages: Any, generation_config: Optional[dict] = None
    ) -> Any:
        response = random.choice(self.candidates)
        response += " (generated by fake llm)"
        for part in response.split():
            yield part + " "
            time.sleep(0.1)
