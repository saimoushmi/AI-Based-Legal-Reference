import streamlit as st
from legal_chat_bot import create_rag_chain, ask_query
from auth_utils import (
    init_db, sign_out, add_message_to_history, get_session_history,
    create_new_session, get_user_sessions, delete_session
)
from auth_pages import show_sign_in, show_sign_up, show_edit_profile, get_img_as_base64

# Initialize DB
init_db()

# Page configuration
st.set_page_config(page_title="Legal Chatbot", page_icon="⚖️", layout="wide")

# Page navigation
if "page" not in st.session_state:
    st.session_state["page"] = "signin"


def apply_chatbot_styling():
    """Applies custom CSS for the main chatbot interface."""
    img, mime_type = get_img_as_base64("bg.png")
    if img:
        st.markdown(f"""
        <style>
            .stApp {{
                background: linear-gradient(rgba(0,0,0,0.7), rgba(0,0,0,0.7)),
                            url("data:{mime_type};base64,{img}");
                background-size: cover !important;
                background-position: center !important;
                background-attachment: fixed !important;
            }}
            [data-testid="stHeader"] {{ background-color: transparent; }}
            [data-testid="stSidebar"] > div:first-child {{
                background: linear-gradient(rgba(10, 25, 41, 0.85), rgba(25, 55, 109, 0.85));
                border-right: 2px solid rgba(255, 255, 255, 0.1);
            }}
            [data-testid="stSidebar"] .stMarkdown,
            [data-testid="stSidebar"] .stButton > button,
            [data-testid="stSidebar"] h3 {{ color: #ffffff; }}
            [data-testid="stSidebar"] .stButton > button {{
                background-color: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 5px;
            }}
            [data-testid="stSidebar"] .stButton > button:hover {{
                background-color: rgba(255, 255, 255, 0.2);
                color: #f0f2f6 !important;
                border: 1px solid rgba(255, 255, 255, 0.3);
            }}
            h1, [data-testid="stCaptionContainer"] p {{ color: #ffffff; }}
            .stChatMessage {{
                background-color: rgba(45, 52, 54, 0.8);
                border-radius: 0.5rem;
                padding: 1rem;
                border: 1px solid rgba(255, 255, 255, 0.1);
            }}
            footer {{ display: none; }}
        </style>
        """, unsafe_allow_html=True)


def show_about():
    """Display the About page."""
    st.title("ℹ️ About Legal Chatbot")
    st.write("""
        This AI-based legal chatbot helps retrieve legal references, case laws,
        and other relevant legal information using AI-powered RAG (Retrieval-Augmented Generation) methods.

        Features:
        - Chat with an AI assistant for legal queries
        - Store past chat sessions
        - User profile management
        - Easy navigation between chat sessions
    """)
    if st.button("⬅️ Back to Chatbot", use_container_width=True):
        st.session_state["page"] = "chatbot"
        st.rerun()


# -------------------- Chatbot Page --------------------
def show_chatbot():
    apply_chatbot_styling()

    user = st.session_state.get("user", {})
    if not user or "id" not in user:
        st.error("Authentication error. Please sign in again.")
        st.session_state["page"] = "signin"
        st.rerun()
        return
    user_id = user["id"]

    st.session_state.setdefault("session_id", None)
    st.session_state.setdefault("messages", [])

    with st.sidebar:
        st.markdown("### 👤 Profile")
        if user.get("profile_pic"):
            st.image(user["profile_pic"], width=150)
        else:
            st.markdown("<div style='font-size:70px; text-align:center;'>👤</div>", unsafe_allow_html=True)
        full_name = f"{user.get('first_name', '')} {user.get('last_name', '')}".strip()
        st.markdown(f"**{full_name}**")
        st.write(user["email"])

        if st.button("✏️ Edit Details", use_container_width=True):
            st.session_state["page"] = "edit_profile"
            st.rerun()

        if st.button("ℹ️ About", use_container_width=True):
            st.session_state["page"] = "about"
            st.rerun()

        if st.button("🚪 Log Out", use_container_width=True):
            sign_out()
            st.rerun()

        st.markdown("---")
        if st.button("➕ New Chat", use_container_width=True):
            st.session_state.session_id = None
            st.session_state.messages = []
            st.rerun()

        st.markdown("### Past Conversations")
        sessions = get_user_sessions(user_id)
        for session_id, session_name in sessions:
            col1, col2 = st.columns([4, 1])
            with col1:
                if st.button(session_name, key=f"session_{session_id}", use_container_width=True):
                    st.session_state.session_id = session_id
                    st.session_state.messages = get_session_history(session_id)
                    st.rerun()
            with col2:
                if st.button("🗑️", key=f"delete_{session_id}", use_container_width=True):
                    delete_session(session_id)
                    if st.session_state.session_id == session_id:
                        st.session_state.session_id = None
                        st.session_state.messages = []
                    st.rerun()

    st.title("⚖️ AI-Based Legal Reference and Case Retrieval System")
    st.caption("Your Legal Chatbot")

    if "rag_chain" not in st.session_state:
        with st.spinner("Loading Legal RAG model..."):
            st.session_state["rag_chain"] = create_rag_chain()
    rag_chain = st.session_state["rag_chain"]

    for msg in st.session_state["messages"]:
        st.chat_message(msg["role"]).write(msg["content"])

    if prompt := st.chat_input("Type your legal query..."):
        active_session_id = st.session_state.session_id
        is_new_chat = not active_session_id

        if is_new_chat:
            session_name = prompt[:50] + "..." if len(prompt) > 50 else prompt
            active_session_id = create_new_session(user_id, session_name)
            st.session_state.session_id = active_session_id

        st.session_state["messages"].append({"role": "user", "content": prompt})
        add_message_to_history(active_session_id, "user", prompt)
        st.chat_message("user").write(prompt)

        with st.spinner("Thinking..."):
            previous_history = st.session_state["messages"][:-1]
            bot_reply = ask_query(rag_chain, prompt, previous_history)

        st.session_state["messages"].append({"role": "assistant", "content": bot_reply})
        add_message_to_history(active_session_id, "assistant", bot_reply)
        st.chat_message("assistant").write(bot_reply)

        if is_new_chat:
            st.rerun()


# -------------------- Page Routing --------------------
page = st.session_state.get("page", "signin")

if page == "signin":
    show_sign_in()
elif page == "signup":
    show_sign_up()
elif page == "edit_profile":
    show_edit_profile()
elif page == "about":
    show_about()
else:
    show_chatbot()
