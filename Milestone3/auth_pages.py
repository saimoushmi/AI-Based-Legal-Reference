import streamlit as st
from auth_utils import sign_in, sign_up, update_user
import base64
import os


def get_img_as_base64(file=None):
    base_dir = os.path.dirname(__file__)
    candidates = []
    if file:
        candidates.extend([file, os.path.join(base_dir, file)])
    candidates.extend([
        os.path.join(base_dir, "bg.png"),
        os.path.join(base_dir, "bg.jpg"),
        "bg.png",
        "bg.jpg"
    ])

    for path in candidates:
        if path and os.path.exists(path):
            mime_type = "image/png" if path.lower().endswith(".png") else "image/jpeg"
            with open(path, "rb") as f:
                data = f.read()
            return base64.b64encode(data).decode(), mime_type

    return None, None



def apply_custom_styling():
    img, mime_type = get_img_as_base64("bg.jpg")  # The function now returns the correct mime type
    if img:
        st.markdown(f"""
        <style>
            [data-testid="stHeader"], footer {{ display: none; }}

            .stApp {{
                background: linear-gradient(rgba(0,0,0,0.7), rgba(0,0,0,0.7)),
                            url("data:{mime_type};base64,{img}");
                background-size: cover !important;
                background-position: center !important;
                background-attachment: fixed !important;
                color: #ffffff;
            }}

            /* Make content container centered and slightly wider */
            .block-container {{
                max-width: 700px;
                margin: 0 auto;
                padding-top: 3rem;
                padding-bottom: 3rem;
            }}

            .stApp > div:first-child > div:first-child > div:first-child {{
                display: flex;
                flex-direction: column;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
                width: 100%;
            }}

            h1, h2, p, h4 {{
                text-align: center;
                color: #ffffff;
            }}

            /* Input boxes without shadow */
            div[data-testid="stTextInput"] input {{
                background-color: rgba(255, 255, 255, 0.1);
                color: white;
                border-radius: 5px;
                border: 1px solid rgba(255, 255, 255, 0.4);
                padding: 0.75rem 1rem;
                width: 100%;
                box-shadow: none !important;
                outline: none !important;
            }}

            div[data-testid="stTextInput"] input::placeholder {{
                color: #b0b0b0;
                opacity: 1;
            }}

            /* Main action buttons inside a form */
            div[data-testid="stForm"] .stButton>button, .stButton>button {{
                background-color: #6d28d9 !important;
                color: white !important;
                border-radius: 4px !important;
                width: 100% !important;
                padding: 0.6rem !important;
                font-weight: 600;
                text-decoration: none;
                text-align: center !important;
            }}

            div[data-testid="stForm"] .stButton>button:hover, .stButton>button:hover {{
                background-color: #5b21b6 !important;
                color: white !important;
            }}

            /* Left-aligned account text and button stacked */
            .account-left {{
                display: flex;
                flex-direction: column;
                align-items: flex-start;
                color: #ddd;
                font-size: 0.9rem;
                margin-top: 0.5rem;
            }}

            /* --- FINAL CSS RULE FOR DELETE BUTTON --- */
            [data-testid="stSidebar"] [data-testid="stHorizontalBlock"] > div:nth-child(2) {{
                display: flex;
                justify-content: center;
                align-items: center;
            }}
            [data-testid="stSidebar"] [data-testid="stHorizontalBlock"] > div:nth-child(2) .stButton>button {{
                background-color: transparent !important;
                border: none !important;
                box-shadow: none !important;
                padding: 0 !important;
                display: flex;
                justify-content: center;
                align-items: center;
                width: 38px !important;
                height: 38px !important;
                min-width: 38px !important;
                min-height: 38px !important;
            }}
            [data-testid="stSidebar"] [data-testid="stHorizontalBlock"] > div:nth-child(2) .stButton>button:hover {{
                background-color: rgba(255, 255, 255, 0.15) !important;
                color: #ff4b4b !important;
            }}
            /* --- END OF FINAL RULE --- */
        </style>
        """, unsafe_allow_html=True)


def show_sign_in():
    apply_custom_styling()

    st.markdown("<h1>Legal ChatBot ⚖️</h1>", unsafe_allow_html=True)
    st.markdown("<p>AI-Based Legal Reference and Case Retrieval System</p>", unsafe_allow_html=True)

    with st.container():
        st.markdown("<h2>Sign In</h2>", unsafe_allow_html=True)

        with st.form("signin_form", clear_on_submit=False):
            email = st.text_input("Email", placeholder="Enter your email", label_visibility="hidden")
            password = st.text_input("Password", type="password", placeholder="Enter your password",
                                     label_visibility="hidden")
            submitted = st.form_submit_button("Sign In")

            if submitted:
                if sign_in(email, password):
                    st.session_state["page"] = "chat"
                    st.rerun()

    st.markdown('<div class="account-left">Don\'t have an account?</div>', unsafe_allow_html=True)
    if st.button("Sign Up", key="nav_to_signup"):
        st.session_state["page"] = "signup"
        st.rerun()


def show_sign_up():
    apply_custom_styling()

    st.markdown("<h1>Legal ChatBot ⚖️</h1>", unsafe_allow_html=True)
    st.markdown("<p>AI-Based Legal Reference and Case Retrieval System</p>", unsafe_allow_html=True)

    with st.container():
        st.markdown("<h2>Sign Up</h2>", unsafe_allow_html=True)

        # FIX: Changed clear_on_submit from True to False
        with st.form("signup_form", clear_on_submit=False):
            first_name = st.text_input("First Name", placeholder="First Name", label_visibility="hidden")
            last_name = st.text_input("Last Name", placeholder="Last Name", label_visibility="hidden")
            email = st.text_input("Email", placeholder="Email", label_visibility="hidden")
            password = st.text_input("Password", type="password", placeholder="Password", label_visibility="hidden")
            confirm_password = st.text_input("Confirm Password", type="password", placeholder="Confirm Password",
                                             label_visibility="hidden")
            profile_pic = st.file_uploader("Upload Profile Picture (Optional)", type=['png', 'jpg', 'jpeg'])
            submitted = st.form_submit_button("Create Account")

            if submitted:
                if sign_up(first_name, last_name, email, password, confirm_password, profile_pic):
                    st.session_state["page"] = "chat"
                    st.rerun()

    st.markdown('<div class="account-left">Already have an account?</div>', unsafe_allow_html=True)
    if st.button("Sign In", key="nav_to_signin"):
        st.session_state["page"] = "signin"
        st.rerun()


def show_edit_profile():
    apply_custom_styling()

    st.markdown("<h1>Edit Profile ✏️</h1>", unsafe_allow_html=True)

    user = st.session_state.get("user")
    if not user:
        st.error("You must be logged in to edit your profile.")
        if st.button("Go to Sign In"):
            st.session_state['page'] = 'signin'
            st.rerun()
        return

    with st.container():
        with st.form("edit_profile_form", clear_on_submit=False):
            st.markdown("<h4>Update your details</h4>", unsafe_allow_html=True)

            first_name = st.text_input("First Name", value=user.get("first_name", ""))
            last_name = st.text_input("Last Name", value=user.get("last_name", ""))

            st.markdown("<br>", unsafe_allow_html=True)

            password = st.text_input("New Password (leave blank to keep current)", type="password")
            confirm_password = st.text_input("Confirm New Password", type="password")

            profile_pic_file = st.file_uploader("Update Profile Picture (Optional)", type=['png', 'jpg', 'jpeg'])

            submitted = st.form_submit_button("Save Changes")

            if submitted:
                if not first_name or not last_name:
                    st.error("First name and last name cannot be empty.")
                elif password and password != confirm_password:
                    st.error("Passwords do not match.")
                else:
                    new_pic_bytes = profile_pic_file.read() if profile_pic_file else None
                    new_password = password if password else None

                    updated_user_data = update_user(
                        user_id=user["id"],
                        first_name=first_name,
                        last_name=last_name,
                        password=new_password,
                        profile_pic=new_pic_bytes
                    )

                    if updated_user_data:
                        st.session_state["user"] = {
                            "id": updated_user_data[0],
                            "first_name": updated_user_data[1],
                            "last_name": updated_user_data[2],
                            "email": updated_user_data[3],
                            "profile_pic": updated_user_data[4],
                        }
                        st.success("Profile updated successfully!")

    if st.button("⬅️ Back to Chat"):
        st.session_state["page"] = "chat"
        st.rerun()