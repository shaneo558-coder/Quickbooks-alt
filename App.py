# App.py
# A simple MVP for a service-based accounting app using Streamlit.
# Focuses on easy expense and income tracking with a clean, Apple-like UI.
# Uses SQLite for data persistence.
# Run with: streamlit run App.py

import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import matplotlib.pyplot as plt

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
page = st.sidebar.radio("Go to", ["Dashboard", "Add Income", "Add Expense", "Transactions", "Reports"])

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

elif page == "Reports":
    st.title("Reports")
    df = get_transactions()
    if df.empty:
        st.info("No data available for reports.")
    else:
        df['date'] = pd.to_datetime(df['date'])
        df['month'] = df['date'].dt.to_period('M')
        
        monthly_summary = df.groupby(['month', 'type'])['amount'].sum().unstack().fillna(0)
        monthly_summary['balance'] = monthly_summary.get('Income', 0) - monthly_summary.get('Expense', 0)
        
        st.subheader("Monthly Summary")
        st.dataframe(monthly_summary.style.format("${:.2f}"))
        
        st.subheader("Income vs Expenses")
        fig, ax = plt.subplots()
        monthly_summary[['Income', 'Expense']].plot(kind='bar', ax=ax)
        ax.set_ylabel("Amount ($)")
        ax.set_title("Monthly Income and Expenses")
        st.pyplot(fig)
        
        st.subheader("Category Breakdown")
        expense_by_cat = df[df['type'] == 'Expense'].groupby('category')['amount'].sum()
        if not expense_by_cat.empty:
            fig2, ax2 = plt.subplots()
            expense_by_cat.plot(kind='pie', ax=ax2, autopct='%1.1f%%')
            ax2.set_title("Expenses by Category")
            st.pyplot(fig2)
        
        income_by_cat = df[df['type'] == 'Income'].groupby('category')['amount'].sum()
        if not income_by_cat.empty:
            fig3, ax3 = plt.subplots()
            income_by_cat.plot(kind='pie', ax=ax3, autopct='%1.1f%%')
            ax3.set_title("Income by Category")
            st.pyplot(fig3)
