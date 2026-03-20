import streamlit as st
import anthropic

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(page_title="AI Chatbot", page_icon="🤖")
st.title("🤖 AI Chatbot")
st.caption("Powered by Claude")

# ── API client ───────────────────────────────────────────────────────────────
# Replace the string below with your actual Anthropic API key
# Get one free at: https://console.anthropic.com
API_KEY = st.secrets["ANTHROPIC_API_KEY"]
client = anthropic.Anthropic(api_key=API_KEY)

# ── Sidebar settings ─────────────────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ Settings")
    persona = st.selectbox(
        "Chatbot Persona",
        ["General Assistant", "CS Tutor", "Creative Writer", "Joke Bot"]
    )
    if st.button("🗑️ Clear Chat"):
        st.session_state.messages = []
        st.rerun()

# ── System prompts for each persona ──────────────────────────────────────────
PERSONAS = {
    "General Assistant": "You are a helpful and friendly assistant.",
    "CS Tutor":          "You are a computer science tutor. Explain concepts clearly and simply, using analogies and short code examples where helpful.",
    "Creative Writer":   "You are a creative writing assistant. Help the user craft vivid, imaginative stories and ideas.",
    "Joke Bot":          "You are a comedian. Respond to everything with wit and humour, and include a relevant joke when appropriate.",
}

system_prompt = PERSONAS[persona]

# ── Session state for chat history ───────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []

# ── Display existing messages ─────────────────────────────────────────────────
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ── Handle new user input ────────────────────────────────────────────────────
if prompt := st.chat_input("Type a message..."):

    # Add user message to history and display it
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Call the Claude API
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                response = client.messages.create(
                    model="claude-sonnet-4-20250514",
                    max_tokens=1000,
                    system=system_prompt,
                    messages=st.session_state.messages,
                )
                reply = response.content[0].text
            except Exception as e:
                reply = f"⚠️ Error: {e}"

        st.markdown(reply)

    # Add assistant reply to history
    st.session_state.messages.append({"role": "assistant", "content": reply})
