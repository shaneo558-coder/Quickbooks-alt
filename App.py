# App.py
# A simple MVP for a service-based accounting app using Streamlit.
# Focuses on easy expense and income tracking with a clean, Apple-like UI.
# Uses SQLite for data persistence.
# Removed matplotlib dependency and Reports section to avoid ModuleNotFoundError.
# Automatically installs streamlit and pandas, optimized for Python 3.13.
# Run with: python3.13 -m streamlit run App.py

import subprocess
import sys
import importlib.util
import logging

# Set up logging to diagnose installation issues
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Function to check and install dependencies
def install_package(package):
    try:
        # Check if package is installed
        if importlib.util.find_spec(package) is None:
            logger.info(f"Installing {package}...")
            cmd = [sys.executable, "-m", "pip", "install", "--verbose", package]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            logger.info(f"{package} installed successfully:\n{result.stdout}")
        else:
            logger.info(f"{package} is already installed.")
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to install {package}. Error:\n{e.stderr}")
        logger.error(f"Try manually: 'python3.13 -m pip install {package}'")
    except Exception as e:
        logger.error(f"Error checking/installing {package}: {str(e)}")

# Install required packages (no matplotlib)
dependencies = ["streamlit", "pandas"]
for package in dependencies:
    install_package(package)

# Now import the required libraries
try:
    import streamlit as st
    import pandas as pd
    import sqlite3
    from datetime import datetime
except ModuleNotFoundError as e:
    logger.error(f"Import failed: {str(e)}. Ensure dependencies are installed.")
    raise

# Database setup
DB_NAME = "accounting.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS transactions
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  type TEXT NOT NULL,
                  amount REAL NOT NULL,
                  category TEXT,
                  description TEXT,
                  date TEXT NOT NULL)''')
    conn.commit()
    conn.close()

init_db()

# Helper functions
def add_transaction(t_type, amount, category, description):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("INSERT INTO transactions (type, amount, category, description, date) VALUES (?, ?, ?, ?, ?)",
              (t_type, amount, category, description, date))
    conn.commit()
    conn.close()

def get_transactions():
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM transactions ORDER BY date DESC", conn)
    conn.close()
    return df

def get_summary():
    df = get_transactions()
    if df.empty:
        return {"income": 0, "expenses": 0, "balance": 0}
    income = df[df['type'] == 'Income']['amount'].sum()
    expenses = df[df['type'] == 'Expense']['amount'].sum()
    balance = income - expenses
    return {"income": income, "expenses": expenses, "balance": balance}

# Streamlit app configuration
st.set_page_config(page_title="Simple Accounting", page_icon="📊", layout="wide")

# Custom CSS for Apple-like clean UI
st.markdown("""
    <style>
    /* General styling */
    body {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        color: #1c1e21;
    }
    .stApp {
        background-color: #f5f5f7;
    }
    /* Buttons */
    .stButton > button {
        background-color: #007aff;
        color: white;
        border: none;
        border-radius: 8px;
        padding: 10px 20px;
        font-size: 16px;
        font-weight: 600;
        transition: background-color 0.3s;
    }
    .stButton > button:hover {
        background-color: #0062cc;
    }
    /* Text inputs */
    .stTextInput > div > div > input {
        border: 1px solid #d2d2d7;
        border-radius: 8px;
        padding: 10px;
        font-size: 16px;
    }
    /* Select boxes */
    .stSelectbox > div > div > select {
        border: 1px solid #d2d2d7;
        border-radius: 8px;
        padding: 10px;
        font-size: 16px;
    }
    /* Headers */
    h1, h2, h3 {
        color: #1c1e21;
        font-weight: 600;
    }
    </style>
""", unsafe_allow_html=True)

# Sidebar for navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Dashboard", "Add Income", "Add Expense", "Transactions"])

if page == "Dashboard":
    st.title("Dashboard")
    summary = get_summary()
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Income", f"${summary['income']:.2f}", delta=None)
    with col2:
        st.metric("Total Expenses", f"${summary['expenses']:.2f}", delta=None)
    with col3:
        st.metric("Balance", f"${summary['balance']:.2f}", delta=None, delta_color="normal" if summary["balance"] >= 0 else "inverse")

    st.subheader("Recent Transactions")
    df = get_transactions().head(5)
    if not df.empty:
        st.dataframe(df[["type", "amount", "category", "date"]].style.format({"amount": "${:.2f}"}))
    else:
        st.info("No transactions yet. Add some income or expenses to get started.")

elif page == "Add Income":
    st.title("Add Income")
    with st.form("income_form"):
        amount = st.number_input("Amount", min_value=0.01, step=0.01)
        category = st.selectbox("Category", ["Service Revenue", "Freelance", "Salary", "Other"])
        description = st.text_input("Description (optional)")
        submitted = st.form_submit_button("Add Income")
        if submitted:
            add_transaction("Income", amount, category, description)
            st.success("Income added successfully!")

elif page == "Add Expense":
    st.title("Add Expense")
    with st.form("expense_form"):
        amount = st.number_input("Amount", min_value=0.01, step=0.01)
        category = st.selectbox("Category", ["Marketing", "Supplies", "Rent", "Utilities", "Other"])
        description = st.text_input("Description (optional)")
        submitted = st.form_submit_button("Add Expense")
        if submitted:
            add_transaction("Expense", amount, category, description)
            st.success("Expense added successfully!")

elif page == "Transactions":
    st.title("All Transactions")
    df = get_transactions()
    if not df.empty:
        st.dataframe(df[["type", "amount", "category", "description", "date"]].style.format({"amount": "${:.2f}"}))
    else:
        st.info("No transactions yet.")

# Note: For deployment (e.g., Streamlit Cloud), create a requirements.txt file with:
# streamlit
# pandas
# Also add runtime.txt with: python-3.13
