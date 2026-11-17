
import streamlit as st
import sqlite3
import hashlib
import hmac
import secrets
import os


def hash_password(password, salt=None):
    salt = salt or secrets.token_hex(16)
    hashed = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        200000
    ).hex()
    return salt, hashed


def setup_users(db_name):
    conn = sqlite3.connect(db_name)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            username TEXT UNIQUE NOT NULL COLLATE NOCASE,
            salt TEXT NOT NULL,
            password_hash TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def login_screen(db_name):
    setup_users(db_name)

    st.markdown("""
    <style>
    .login-title {
        text-align: center;
        color: #5DE0D0;
        font-size: 34px;
        font-weight: bold;
    }
    .login-subtitle {
        text-align: center;
        color: white;
        font-size: 17px;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown(
        '<div class="login-title">💊 Medicine AI System</div>',
        unsafe_allow_html=True
    )
    st.markdown(
        '<div class="login-subtitle">Secure Login and Registration</div>',
        unsafe_allow_html=True
    )

    st.write("")
    left, center, right = st.columns([1, 1.5, 1])

    with center:
        login_tab, register_tab = st.tabs(
            ["🔐 Login", "📝 Create User Account"]
        )

        with login_tab:
            with st.form("login_form"):
                username = st.text_input("Username")
                password = st.text_input(
                    "Password", type="password"
                )
                login = st.form_submit_button(
                    "Login", use_container_width=True
                )

            if login:
                admin_username = os.getenv(
                    "MED_ADMIN_USER", "admin"
                )
                admin_password = os.getenv(
                    "MED_ADMIN_PASSWORD", "Admin@12345"
                )

                if (
                    hmac.compare_digest(username, admin_username)
                    and hmac.compare_digest(password, admin_password)
                ):
                    st.session_state.logged_in = True
                    st.session_state.role = "admin"
                    st.session_state.username = admin_username
                    st.rerun()

                conn = sqlite3.connect(db_name)
                user = conn.execute("""
                    SELECT full_name, salt, password_hash
                    FROM users
                    WHERE username = ?
                """, (username.strip(),)).fetchone()
                conn.close()

                if user:
                    _, entered_hash = hash_password(
                        password, user[1]
                    )

                    if hmac.compare_digest(entered_hash, user[2]):
                        st.session_state.logged_in = True
                        st.session_state.role = "user"
                        st.session_state.username = username.strip()
                        st.session_state.full_name = user[0]
                        st.rerun()

                st.error("Invalid username or password.")

        with register_tab:
            with st.form("register_form"):
                full_name = st.text_input("Full Name")
                new_username = st.text_input("Create Username")
                new_password = st.text_input(
                    "Create Password", type="password"
                )
                confirm_password = st.text_input(
                    "Confirm Password", type="password"
                )

                register = st.form_submit_button(
                    "Create Account", use_container_width=True
                )

            if register:
                if not full_name.strip() or not new_username.strip():
                    st.error("Please enter your name and username.")
                elif len(new_password) < 8:
                    st.error("Password must contain at least 8 characters.")
                elif new_password != confirm_password:
                    st.error("Passwords do not match.")
                else:
                    salt, password_hash = hash_password(new_password)

                    try:
                        conn = sqlite3.connect(db_name)
                        conn.execute("""
                            INSERT INTO users
                            (full_name, username, salt, password_hash)
                            VALUES (?, ?, ?, ?)
                        """, (
                            full_name.strip(),
                            new_username.strip(),
                            salt,
                            password_hash
                        ))
                        conn.commit()
                        conn.close()

                        st.success(
                            "Account created successfully! Please log in."
                        )

                    except sqlite3.IntegrityError:
                        st.error("This username already exists.")

    return True
