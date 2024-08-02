from threading import Thread
from openmind import AutoModelForCausalLM, AutoTokenizer
from transformers import TextIteratorStreamer
from typing import Optional, Dict, List, Any
from chatways.llm.utils import BaseChatModel, register_llm


@register_llm("openmind")
class OMChatModel(BaseChatModel):
    """
    openMind Chat Completions
    """

    engine: str = "openmind"
    model: str = ""
    default_model: str = "Qwen/Qwen1.5-4B-Chat"

    def __init__(
        self, model: Optional[str] = None, model_config: Optional[dict] = None
    ) -> None:
        if model is None:
            self.model = self.default_model
        else:
            self.model = model
        if model_config is None:
            model_config = {}
        model_config.update(trust_remote_code=True)
        self.client = AutoModelForCausalLM.from_pretrained(self.model, **model_config)
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.model, trust_remote_code=True
        )

    def _prepare_inputs(self, messages: List[Dict]):
        raw_inputs = self.tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )

        device = self.client.device
        model_inputs = self.tokenizer([raw_inputs], return_tensors="pt").to(device)
        return model_inputs

    def _add_basic_config(self, generation_config: Dict) -> Dict:
        generation_config.update(
            dict(do_sample=True, max_length=self.tokenizer.model_max_length)
        )
        return generation_config

    def invoke(
        self, messages: List[Dict], generation_config: Optional[dict] = None
    ) -> str:
        model_inputs = self._prepare_inputs(messages)

        if generation_config is None:
            generation_config = {}

        generation_config = self._add_basic_config(generation_config)
        generated_ids = self.client.generate(
            model_inputs.input_ids, **generation_config
        )
        generated_ids = [
            output_ids[len(input_ids) :]
            for input_ids, output_ids in zip(model_inputs.input_ids, generated_ids)
        ]

        response = self.tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[
            0
        ]
        return response

    def invoke_stream(
        self, messages: List[Dict], generation_config: Optional[dict] = None
    ) -> Any:
        model_inputs = self._prepare_inputs(messages)

        if generation_config is None:
            generation_config = {}

        streamer = TextIteratorStreamer(
            self.tokenizer, skip_prompt=True, skip_special_tokens=True
        )
        generation_kwargs = dict(model_inputs, streamer=streamer)
        generation_kwargs.update(generation_config)
        generation_kwargs = self._add_basic_config(generation_kwargs)
        thread = Thread(target=self.client.generate, kwargs=generation_kwargs)
        thread.start()
        return streamer
