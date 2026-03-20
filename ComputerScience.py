import streamlit as st
import anthropic

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(page_title="AI Chatbot", page_icon="🤖")
st.title("🤖 AI Chatbot")
st.caption("Powered by Claude")

# ── API client (reads key from Streamlit Secrets) ─────────────────────────────
try:
    API_KEY = st.secrets["ANTHROPIC_API_KEY"]
except Exception:
    st.error("⚠️ API key not found. Go to Manage App → Settings → Secrets and add your ANTHROPIC_API_KEY.")
    st.stop()

client = anthropic.Anthropic(api_key=API_KEY)

# ── Sidebar settings ─────────────────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ Settings")

    persona = st.selectbox(
        "Chatbot Persona",
        ["General Assistant", "CS Tutor", "Creative Writer", "Joke Bot", "✏️ Custom"]
    )

    # ── Custom persona creator ────────────────────────────────────────────────
    PERSONAS = {
        "General Assistant": "You are a helpful and friendly assistant.",
        "CS Tutor":          "You are a computer science tutor. Explain concepts clearly and simply, using analogies and short code examples where helpful.",
        "Creative Writer":   "You are a creative writing assistant. Help the user craft vivid, imaginative stories and ideas.",
        "Joke Bot":          "You are a comedian. Respond to everything with wit and humour, and include a relevant joke when appropriate.",
    }

    if persona == "✏️ Custom":
        custom_prompt = st.text_area(
            "Write your own system prompt:",
            placeholder='e.g. "You are a pirate who only speaks in rhymes."',
            height=120,
        )
        system_prompt = custom_prompt if custom_prompt.strip() else "You are a helpful assistant."
        if not custom_prompt.strip():
            st.caption("ℹ️ Using default prompt until you write one above.")
    else:
        system_prompt = PERSONAS[persona]

    st.divider()

    if st.button("🗑️ Clear Chat"):
        st.session_state.messages = []
        st.rerun()

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

    # ── Streaming response ────────────────────────────────────────────────────
    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        full_reply = ""

        try:
            with client.messages.stream(
                model="claude-sonnet-4-20250514",
                max_tokens=1000,
                system=system_prompt,
                messages=st.session_state.messages,
            ) as stream:
                for text_chunk in stream.text_stream:
                    full_reply += text_chunk
                    response_placeholder.markdown(full_reply + "▌")  # blinking cursor effect

            response_placeholder.markdown(full_reply)  # final response without cursor

        except anthropic.AuthenticationError:
            full_reply = "⚠️ Invalid API key. Please check your Streamlit Secrets."
            response_placeholder.markdown(full_reply)
        except anthropic.RateLimitError:
            full_reply = "⚠️ Rate limit hit. Please wait a moment and try again."
            response_placeholder.markdown(full_reply)
        except Exception as e:
            full_reply = f"⚠️ Unexpected error: {e}"
            response_placeholder.markdown(full_reply)

    # Add assistant reply to history
    st.session_state.messages.append({"role": "assistant", "content": full_reply})
