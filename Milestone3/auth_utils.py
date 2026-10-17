import sqlite3
import streamlit as st
import os
import hashlib
import re

# Path to SQLite database
DB_PATH = os.path.join(os.path.dirname(__file__), "users.db")


def hash_password(password: str) -> str:
    """Hashes a password using SHA-256."""
    return hashlib.sha256(password.encode()).hexdigest()


def init_db():
    """Initialize the database and create tables if they don't exist."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            profile_pic BLOB
        )
    """)

    # Chat sessions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            session_name TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)

    # Chat history table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES chat_sessions (id) ON DELETE CASCADE
        )
    """)

    conn.commit()
    conn.close()


def add_user(first_name, last_name, email, password, profile_pic=None) -> bool:
    """Add a new user to the database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    hashed_password = hash_password(password)
    try:
        cursor.execute(
            "INSERT INTO users (first_name, last_name, email, password, profile_pic) VALUES (?, ?, ?, ?, ?)",
            (first_name, last_name, email, hashed_password, profile_pic)
        )
        conn.commit()
        st.success("Account created successfully!")
        return True
    except sqlite3.IntegrityError:
        st.error("Email already registered. Please sign in.")
        return False
    finally:
        conn.close()


def get_user(email: str, password: str):
    """Get a user by email and password."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    hashed_password = hash_password(password)
    cursor.execute(
        "SELECT id, first_name, last_name, email, profile_pic FROM users WHERE email=? AND password=?",
        (email, hashed_password)
    )
    result = cursor.fetchone()
    conn.close()
    return result


def is_password_valid(password: str) -> bool:
    """Check if the password meets complexity rules."""
    errors = []
    if len(password) < 8:
        errors.append("Password must be at least 8 characters long.")
    if not re.search(r"[A-Z]", password):
        errors.append("Password must contain at least one uppercase letter.")
    if not re.search(r"[a-z]", password):
        errors.append("Password must contain at least one lowercase letter.")
    if not re.search(r"\d", password):
        errors.append("Password must contain at least one number.")
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        errors.append("Password must contain at least one special character.")

    if errors:
        for e in errors:
            st.error(e)
        return False
    return True


def sign_in(email: str, password: str) -> bool:
    """Sign in a user and store session data."""
    user = get_user(email, password)
    if not user:
        st.error("Invalid email or password.")
        return False
    st.session_state["user"] = {
        "id": user[0],
        "first_name": user[1],
        "last_name": user[2],
        "email": user[3],
        "profile_pic": user[4]
    }
    st.success(f"Welcome back, {user[1]}!")
    return True


def sign_up(first_name, last_name, email, password, confirm_password, profile_pic=None) -> bool:
    """Sign up a new user."""
    if password != confirm_password:
        st.error("Passwords do not match.")
        return False
    if "@" not in email:
        st.error("Invalid email address.")
        return False
    if not is_password_valid(password):
        return False

    pic_bytes = profile_pic.read() if profile_pic else None
    if add_user(first_name, last_name, email, password, pic_bytes):
        return sign_in(email, password)
    return False


def sign_out():
    """Sign out the user and clear session state."""
    for key in ["user", "messages", "session_id", "current_session_id"]:
        if key in st.session_state:
            del st.session_state[key]
    st.success("Logged out successfully.")


# --- Chat session and history functions ---

def create_new_session(user_id: int, session_name: str) -> int:
    """Create a new chat session."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO chat_sessions (user_id, session_name) VALUES (?, ?)",
            (user_id, session_name)
        )
        conn.commit()
        return cursor.lastrowid
    except sqlite3.Error as e:
        st.error(f"Error creating session: {e}")
        return None
    finally:
        conn.close()


def get_user_sessions(user_id: int):
    """Get all chat sessions for a user."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT id, session_name FROM chat_sessions WHERE user_id=? ORDER BY created_at DESC",
            (user_id,)
        )
        return cursor.fetchall()
    except sqlite3.Error as e:
        st.error(f"Error fetching sessions: {e}")
        return []
    finally:
        conn.close()


def delete_session(session_id: int):
    """Delete a chat session and its messages."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM chat_sessions WHERE id=?", (session_id,))
        conn.commit()
    except sqlite3.Error as e:
        st.error(f"Error deleting session: {e}")
    finally:
        conn.close()


def add_message_to_history(session_id: int, role: str, content: str):
    """Add a message to a chat session."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO chat_history (session_id, role, content) VALUES (?, ?, ?)",
            (session_id, role, content)
        )
        conn.commit()
    except sqlite3.Error as e:
        st.error(f"Error saving message: {e}")
    finally:
        conn.close()


def get_session_history(session_id: int):
    """Get chat history for a session."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT role, content FROM chat_history WHERE session_id=? ORDER BY timestamp ASC",
            (session_id,)
        )
        return [{"role": role, "content": content} for role, content in cursor.fetchall()]
    except sqlite3.Error as e:
        st.error(f"Error retrieving chat history: {e}")
        return []
    finally:
        conn.close()


# ✅ Added missing function
def update_user(user_id, first_name, last_name, password=None, profile_pic=None):
    """Update user profile details."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    query = "UPDATE users SET first_name=?, last_name=?"
    params = [first_name, last_name]

    if password:
        hashed_password = hash_password(password)
        query += ", password=?"
        params.append(hashed_password)

    if profile_pic is not None:
        query += ", profile_pic=?"
        params.append(profile_pic)

    query += " WHERE id=?"
    params.append(user_id)

    cursor.execute(query, tuple(params))
    conn.commit()

    cursor.execute("SELECT id, first_name, last_name, email, profile_pic FROM users WHERE id=?", (user_id,))
    updated_user = cursor.fetchone()
    conn.close()

    return updated_user
