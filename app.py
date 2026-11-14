import os
import streamlit as st
import torch
from transformers import pipeline
from scraper import fetch_website_contents

# --- Streamlit Page Configuration ---
st.set_page_config(
    page_title="AI Website Summarizer — Llama 3.2 1B",
    page_icon="🌐",
    layout="centered",
)

# --- Model Configuration ---
# We use Llama 3.2 1B (Instruction-Tuned).
# By default, we point to unsloth/Llama-3.2-1B-Instruct (an un-gated mirror of Meta's official weights),
# allowing anyone to run it immediately without needing a Hugging Face approval token.
DEFAULT_MODEL = "unsloth/Llama-3.2-1B-Instruct"

@st.cache_resource(show_spinner=False)
def load_llm_pipeline(model_id: str = DEFAULT_MODEL):
    """
    Load the Llama 3.2 1B text-generation pipeline.
    Cached so it loads into memory only once across Streamlit reruns.
    """
    device = "cuda" if torch.cuda.is_available() else "cpu"
    torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32

    # Support optional HF_TOKEN from environment if using official meta-llama repos
    hf_token = os.getenv("HF_TOKEN", None)

    pipe = pipeline(
        "text-generation",
        model=model_id,
        torch_dtype=torch_dtype,
        device=device,
        token=hf_token,
    )
    return pipe, device


# --- Prompt Engineering ---
system_prompt = (
    "You are an experienced English professor who excels in summarization of any English language content. "
    "You will be given the text contents of a website and your job is to summarize it using clear, everyday English "
    "that is easily understood by anyone. If the website includes news, updates, or announcements, include a concise "
    "section highlighting them. Format your output in clean Markdown."
)

user_prompt_template = (
    "Here are the contents of a website. Please provide a clear, structured summary:\n\n"
)


def messages_for(website_content: str):
    """
    Format conversational chat messages for Llama 3.2 Instruct.
    """
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"{user_prompt_template}{website_content}"},
    ]


def summarize(url: str, pipe, max_new_tokens: int = 300) -> str:
    """
    Fetch website text and generate summary using Llama 3.2 1B.
    """
    website = fetch_website_contents(url)
    if not website or not website.strip():
        return "⚠️ Could not extract meaningful text from this webpage."

    messages = messages_for(website)
    outputs = pipe(
        messages,
        max_new_tokens=max_new_tokens,
        do_sample=False,  # Deterministic decoding for consistent summaries
    )
    summary = outputs[0]["generated_text"][-1]["content"]
    return summary, website


# --- UI Layout ---

st.title("🌐 AI Website Summarizer")
st.caption("Powered by open-source **Meta Llama 3.2 (1B Parameters)** via Hugging Face Transformers.")

# Sidebar for hardware info & settings
with st.sidebar:
    st.header("⚙️ Model & Hardware")
    device_name = "NVIDIA CUDA GPU" if torch.cuda.is_available() else "CPU (Standard)"
    st.info(f"**Execution Device:** {device_name}")
    st.markdown(
        """
        - **Model:** Llama 3.2 1B Instruct  
        - **Parameters:** ~1.2 Billion  
        - **Inference:** 100% Local / Open Source  
        - **API Keys Needed:** Zero (No OpenAI API costs)
        """
    )
    st.divider()
    max_tokens = st.slider("Max Summary Length (tokens):", min_value=100, max_value=500, value=300, step=50)

# Main input form
url = st.text_input(
    "Enter a website URL to summarize:",
    placeholder="https://en.wikipedia.org/wiki/Python_(programming_language)",
)

if st.button("Summarize Website", type="primary"):
    if not url or not url.strip():
        st.warning("Please enter a valid URL first.")
    else:
        # Load model with friendly spinner
        with st.spinner("Loading Llama 3.2 1B into memory (first run downloads weights)..."):
            try:
                pipe, device = load_llm_pipeline()
            except Exception as e:
                st.error(f"Failed to load model: {e}")
                pipe = None

        if pipe is not None:
            with st.spinner("Scraping webpage and generating summary with Llama 3.2..."):
                try:
                    summary, raw_text = summarize(url, pipe, max_new_tokens=max_tokens)
                    st.success("✅ Summary Generated!")
                    st.markdown("### 📝 Summary")
                    st.markdown(summary)

                    with st.expander("🔍 View Raw Scraped Website Content"):
                        st.text(raw_text)

                except Exception as e:
                    st.error(f"Something went wrong during summarization: {e}")
