import os
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI
from scraper import fetch_website_contents

# Loading my API key from the .env file, same as I do in the notebook
load_dotenv(override=True)
api_key = os.getenv('OPENAI_API_KEY')

# Setting up the OpenAI client once, so I don't recreate it every time someone clicks the button
openai = OpenAI()

# Same system prompt I used in my notebook - tells the AI how to behave
system_prompt = """
    You are an experienced English professor who excels in summarization of any english language content. 
    You will be given contents of websites and you will summerize the content using simple regular english in such a way that 
    it is easily understood by anyone. Do not wrap the markdown in a code block - respond just with the markdown.
"""

# Same user prompt template as my notebook
user_prompt = """
    Here are the contents of a website. Provide a short summay of this website.
    If it includes news or annoucements, then summarize those too.
"""

# Building the messages list to send to the model - identical logic to messages_for() in my notebook
def messages_for(website):
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt + website}
    ]

# Same summarize function from my notebook, just moved here so the app can use it
def summarize(url):
    website = fetch_website_contents(url)
    response = openai.chat.completions.create(
        model="gpt-4.1-mini",
        messages=messages_for(website)
    )
    return response.choices[0].message.content


# ---- This is where the actual web page/UI starts ----

st.set_page_config(page_title="AI Website Summarizer", page_icon="🌐")

st.title("🌐 AI Website Summarizer")
st.write("Paste in any website link and get a simple, plain-English summary powered by AI.")

# A quick warning if the API key isn't set up, so I don't get a confusing error later
if not api_key:
    st.error("No OpenAI API key found. Please add OPENAI_API_KEY to your .env file.")

# Text box where the user types a URL
url = st.text_input("Enter a website URL:", placeholder="https://example.com")

# Button that triggers the summarization when clicked
if st.button("Summarize"):
    if not url:
        st.warning("Please enter a URL first.")
    else:
        # Showing a spinner while the request is in progress, since this can take a few seconds
        with st.spinner("Reading the website and generating a summary..."):
            try:
                summary = summarize(url)
                st.markdown("### Summary")
                st.markdown(summary)
            except Exception as e:
                st.error(f"Something went wrong: {e}")
