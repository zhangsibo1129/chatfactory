import json
import argparse
import gradio as gr

from chatways import ArxivChatBot, ARXIV_SYSTEM_PROMPT

# Step 1. Configuration
CSS = """#chatbot {
    height: 60vh !important;
    display: flex;
    flex-direction: column-reverse;
}
#max_papers {
    height: 5vh !important;
}
.scrollable-markdown {
    max-height: 55vh  !important; /* 设置最大高度 */
    overflow-y: scroll; /* 启用垂直滚动条 */
}
"""

HEADER = (
    "# Chat with arXiv\n\n"
    "Chat with arXiv uses LLM to make finding academic papers on arXiv more natural and insightful. "
    "Easily discover the most relevant studies with user-friendly search functionality."
)

OPENAI_PARAMEATERS = [
    ("temperature", 1.0, 0.0, 2.0, 0.01),
    ("top_p", 1.0, 0.0, 1.0, 0.01),
    ("frequency_penalty", 0.0, -2.0, 2.0, 0.01),
    ("presence_penalty", 0.0, -2.0, 2.0, 0.01),
]

HF_PARAMETERS = [
    ("temperature", 1.0, 0.0, 2.0, 0.01),
    ("top_k", 50, 0, 100, 1),
    ("top_p", 1.0, 0.0, 2.0, 0.01),
    ("max_new_tokens", 512, 0, 1024, 1),
]

FAKE_PARAMETERS = [
    ("temperature", 1.0, 0.0, 2.0, 0.01),
    ("top_k", 50, 0, 100, 1),
    ("top_p", 1.0, 0.0, 2.0, 0.01),
    ("max_new_tokens", 512, 0, 1024, 1),
]


# Step 2. Argument Parsing
def parse_args():
    parser = argparse.ArgumentParser(description="Simple Chat Application")
    parser.add_argument(
        "-a",
        "--address",
        type=str,
        default="127.0.0.1",
        help="Default address is 127.0.0.1",
    )
    parser.add_argument(
        "-p", "--port", type=int, default=7860, help="Default port is 7860"
    )
    parser.add_argument(
        "-le", "--llm-engine", type=str, default=None, help="The LLM engine to use"
    )
    parser.add_argument(
        "-lm", "--llm-model", type=str, default=None, help="The LLM model path"
    )
    parser.add_argument(
        "-lc",
        "--llm-model-config",
        type=str,
        default=None,
        help="The LLM model configuration in JSON format",
    )
    return parser.parse_args()


args = parse_args()

# Step 3. Bot initialization
bot = ArxivChatBot(
    llm_config={
        "engine": args.llm_engine,
        "model": args.llm_model,
        "model_config": (
            json.loads(args.llm_model_config) if args.llm_model_config else None
        ),
    }
)


# Step 4. Callbacks definition
def get_generation_config(components):
    if args.llm_engine == "openai" or args.llm_engine is None:
        parameters = OPENAI_PARAMEATERS
    elif args.llm_engine == "huggingface":
        parameters = HF_PARAMETERS
    elif args.llm_engine == "fake":
        parameters = FAKE_PARAMETERS

    parameter_components = components[: int(len(components) / 2)]
    availabel_components = components[int(len(components) / 2) :]
    generation_config = {}
    for parameter, parameter_component, availabel_component in zip(
        parameters, parameter_components, availabel_components
    ):
        if availabel_component:
            parameter_component = None
        generation_config.update({parameter[0]: parameter_component})
    return generation_config


def respond(message, history_chat, history_search, max_papers, stream, *components):
    generation_config = get_generation_config(components)
    response, paper_cards, paper_search_query = bot.chat(
        message=message,
        history_chat=history_chat,
        history_search=history_search,
        generation_config=generation_config,
        max_results=max_papers,
        stream=stream,
    )
    history_search.append([message, paper_search_query])
    history_chat.append([message, ""])
    if stream:
        for chunk in response:
            if chunk is not None:
                history_chat[-1][1] += chunk
                yield "", history_chat, history_search, paper_cards
    else:
        history_chat[-1][1] = response
        yield "", history_chat, history_search, paper_cards


def clean_conversation():
    return "", [], []


def create_component(label, value, minimum, maximum, step):
    return gr.Slider(
        label=label,
        value=value,
        minimum=minimum,
        maximum=maximum,
        step=step,
        interactive=True,
    )


def enable_parameter_slider():
    return False


# Step 5. Gradio Interface
with gr.Blocks(css=CSS) as demo:
    gr.Markdown(HEADER)
    history_search = gr.State([])

    with gr.Row():
        system_prompt = gr.Textbox(
            placeholder=ARXIV_SYSTEM_PROMPT,
            show_label=False,
            interactive=False,
            scale=9,
        )
        stream_component = gr.Checkbox(
            value=True, label="Stream", interactive=True, scale=1
        )

    with gr.Row():
        with gr.Column(scale=2):
            chatbot = gr.Chatbot(
                elem_id="chatbot", show_label=False, show_copy_button=True
            )
        with gr.Column(scale=1):
            max_papers = gr.Slider(
                elem_id="max_papers",
                label="Paper Candidates",
                value=5,
                minimum=1,
                maximum=50,
                step=1,
            )
            paper_cards = gr.Markdown(
                visible=True, elem_classes=["scrollable-markdown"]
            )

    with gr.Row():
        inputs = gr.Textbox(placeholder="Input", show_label=False, scale=8)
        clean_btn = gr.Button(scale=1, value="Clean", variant="stop")
        send_btn = gr.Button(scale=1, value="Send", variant="primary")

    with gr.Accordion("Parameters", open=False):
        if args.llm_engine == "openai" or args.llm_engine is None:
            parameters = OPENAI_PARAMEATERS
        elif args.llm_engine == "huggingface":
            parameters = HF_PARAMETERS
        elif args.llm_engine == "fake":
            parameters = FAKE_PARAMETERS

        availabel_components = []
        parameter_components = []
        index = 0
        while index < len(parameters):
            with gr.Row():
                with gr.Column():
                    parameter_components.append(create_component(*parameters[index]))
                    availabel_components.append(
                        gr.Checkbox(label="Disable", value=True, interactive=True)
                    )
                    index += 1
                if index < len(parameters):
                    with gr.Column():
                        parameter_components.append(
                            create_component(*parameters[index])
                        )
                        availabel_components.append(
                            gr.Checkbox(label="Disable", value=True, interactive=True)
                        )
                        index += 1

    inputs.submit(
        respond,
        [
            inputs,
            chatbot,
            history_search,
            max_papers,
            stream_component,
            *(parameter_components + availabel_components),
        ],
        [inputs, chatbot, history_search, paper_cards],
    )
    send_btn.click(
        respond,
        [
            inputs,
            chatbot,
            history_search,
            max_papers,
            stream_component,
            *(parameter_components + availabel_components),
        ],
        [inputs, chatbot, history_search, paper_cards],
    )
    clean_btn.click(clean_conversation, outputs=[inputs, chatbot, history_search])

    for parameter_component, availabel_component in zip(
        parameter_components, availabel_components
    ):
        parameter_component.change(
            fn=enable_parameter_slider, outputs=availabel_component
        )

if __name__ == "__main__":
    demo.launch(server_name=args.address, server_port=args.port)
