import streamlit as st
import anthropic
import base64
import io
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(page_title="AI Chatbot", page_icon="🤖")
st.title("🤖 AI Chatbot")
st.caption("Powered by Claude")

# ── API client ────────────────────────────────────────────────────────────────
try:
    API_KEY = st.secrets["ANTHROPIC_API_KEY"]
except Exception:
    st.error("⚠️ API key not found. Go to Manage App → Settings → Secrets and add your ANTHROPIC_API_KEY.")
    st.stop()

client = anthropic.Anthropic(api_key=API_KEY)

# ── PDF export helper ─────────────────────────────────────────────────────────
def generate_pdf(messages):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter,
                            rightMargin=50, leftMargin=50,
                            topMargin=60, bottomMargin=40)
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle("Title", parent=styles["Title"],
                                 textColor=colors.HexColor("#1a1a2e"), fontSize=20)
    user_style  = ParagraphStyle("User", parent=styles["Normal"],
                                 textColor=colors.HexColor("#0f3460"),
                                 fontSize=11, spaceAfter=4,
                                 fontName="Helvetica-Bold")
    bot_style   = ParagraphStyle("Bot", parent=styles["Normal"],
                                 textColor=colors.HexColor("#16213e"),
                                 fontSize=11, spaceAfter=4)
    meta_style  = ParagraphStyle("Meta", parent=styles["Normal"],
                                 textColor=colors.grey, fontSize=8)

    story = []
    story.append(Paragraph("🤖 AI Chatbot — Conversation Export", title_style))
    story.append(Paragraph(f"Exported on {datetime.now().strftime('%Y-%m-%d %H:%M')}", meta_style))
    story.append(Spacer(1, 20))

    for msg in messages:
        if isinstance(msg["content"], list):
            text = next((b["text"] for b in msg["content"] if b.get("type") == "text"), "[image]")
        else:
            text = msg["content"]

        # Escape special XML chars for ReportLab
        text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

        if msg["role"] == "user":
            story.append(Paragraph("You:", user_style))
            story.append(Paragraph(text, bot_style))
        else:
            story.append(Paragraph("Claude:", user_style))
            story.append(Paragraph(text, bot_style))

        story.append(Spacer(1, 10))

    doc.build(story)
    buffer.seek(0)
    return buffer.read()

# ── Sidebar settings ──────────────────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ Settings")

    # Persona selector
    persona = st.selectbox(
        "Chatbot Persona",
        ["General Assistant", "CS Tutor", "Creative Writer", "Joke Bot", "✏️ Custom"]
    )

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
        base_system_prompt = custom_prompt if custom_prompt.strip() else "You are a helpful assistant."
        if not custom_prompt.strip():
            st.caption("ℹ️ Using default prompt until you write one above.")
    else:
        base_system_prompt = PERSONAS[persona]

    st.divider()

    # Language selector
    st.subheader("🌍 Response Language")
    language = st.selectbox(
        "Reply in:",
        ["English", "Spanish", "French", "German", "Italian",
         "Portuguese", "Japanese", "Chinese", "Arabic", "Hindi"]
    )
    system_prompt = base_system_prompt if language == "English" else \
        base_system_prompt + f" Always respond in {language}, regardless of what language the user writes in."

    st.divider()

    # Image upload
    st.subheader("🖼️ Image Upload")
    uploaded_image = st.file_uploader(
        "Attach an image to your next message:",
        type=["png", "jpg", "jpeg", "gif", "webp"],
    )
    if uploaded_image:
        st.image(uploaded_image, caption="Image ready to send", use_container_width=True)

    st.divider()

    # ── PDF Export button ─────────────────────────────────────────────────────
    st.subheader("📄 Export Chat")
    if st.session_state.get("messages"):
        pdf_bytes = generate_pdf(st.session_state.messages)
        st.download_button(
            label="⬇️ Download as PDF",
            data=pdf_bytes,
            file_name=f"chat_export_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
            mime="application/pdf",
        )
    else:
        st.caption("Start chatting to enable PDF export.")

    st.divider()

    if st.button("🗑️ Clear Chat"):
        st.session_state.messages = []
        st.rerun()

# ── Session state ─────────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []

# ── Text-to-speech helper ─────────────────────────────────────────────────────
def tts_button(text, key):
    """Renders a speak button using browser Web Speech API via an HTML component."""
    safe_text = text.replace("`", "").replace('"', "&quot;").replace("\n", " ")
    st.components.v1.html(f"""
        <button onclick="
            var u = new SpeechSynthesisUtterance('{safe_text}');
            window.speechSynthesis.speak(u);
        " style="
            background:#f0f2f6; border:1px solid #ccc; border-radius:6px;
            padding:4px 10px; cursor:pointer; font-size:13px;
        ">🔊 Read aloud</button>
    """, height=40)

# ── Display existing messages ─────────────────────────────────────────────────
for i, msg in enumerate(st.session_state.messages):
    with st.chat_message(msg["role"]):
        if isinstance(msg["content"], list):
            for block in msg["content"]:
                if block.get("type") == "text":
                    st.markdown(block["text"])
            st.caption("📎 Image was attached to this message")
        else:
            st.markdown(msg["content"])
        # TTS button on assistant messages
        if msg["role"] == "assistant":
            tts_button(msg["content"], key=f"tts_{i}")

# ── Handle new user input ─────────────────────────────────────────────────────
if prompt := st.chat_input("Type a message..."):

    if uploaded_image:
        image_bytes = uploaded_image.read()
        image_b64 = base64.standard_b64encode(image_bytes).decode("utf-8")
        message_content = [
            {"type": "image", "source": {"type": "base64",
             "media_type": uploaded_image.type, "data": image_b64}},
            {"type": "text", "text": prompt},
        ]
    else:
        message_content = prompt

    st.session_state.messages.append({"role": "user", "content": message_content})
    with st.chat_message("user"):
        st.markdown(prompt)
        if uploaded_image:
            st.caption("📎 Image attached")

    # Streaming response
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
                    response_placeholder.markdown(full_reply + "▌")

            response_placeholder.markdown(full_reply)

        except anthropic.AuthenticationError:
            full_reply = "⚠️ Invalid API key. Please check your Streamlit Secrets."
            response_placeholder.markdown(full_reply)
        except anthropic.RateLimitError:
            full_reply = "⚠️ Rate limit hit. Please wait a moment and try again."
            response_placeholder.markdown(full_reply)
        except Exception as e:
            full_reply = f"⚠️ Unexpected error: {e}"
            response_placeholder.markdown(full_reply)

        # TTS button for the new response
        tts_button(full_reply, key=f"tts_new")

    st.session_state.messages.append({"role": "assistant", "content": full_reply})
