import streamlit as st
from datetime import date
import pandas as pd

# Initialize session state
if "transactions" not in st.session_state:
    st.session_state["transactions"] = []

# Function to add a transaction
def add_transaction(tx_type, description, amount, tx_date):
    st.session_state.transactions.append({
        "Type": tx_type,
        "Description": description,
        "Amount": amount,
        "Date": tx_date
    })

# Function to calculate running balance
def calculate_running_balance():
    df = pd.DataFrame(st.session_state.transactions)
    if df.empty:
        return df
    df["Date"] = pd.to_datetime(df["Date"])
    balance = 0
    balances = []
    for _, row in df.sort_values("Date").iterrows():
        if row["Type"] == "Income":
            balance += row["Amount"]
        else:
            balance -= row["Amount"]
        balances.append(balance)
    df["Running Balance"] = balances
    return df

# Sidebar navigation
page = st.sidebar.radio("Go to", ["Dashboard", "Transactions"])

# Dashboard page
if page == "Dashboard":
    st.title("Dashboard")
    df = calculate_running_balance()
    if not df.empty:
        total_income = df[df["Type"]=="Income"]["Amount"].sum()
        total_expense = df[df["Type"]=="Expense"]["Amount"].sum()
        net = total_income - total_expense
        st.metric("Total Income", f"${total_income:.2f}")
        st.metric("Total Expenses", f"${total_expense:.2f}")
        st.metric("Net Cash Flow", f"${net:.2f}")
        st.dataframe(df.sort_values("Date", ascending=False))
    else:
        st.info("No transactions yet.")

# Transactions page
elif page == "Transactions":
    st.title("Add Transaction")
    tx_type = st.selectbox("Type", ["Income", "Expense"])
    description = st.text_input("Description")
    amount = st.number_input("Amount", min_value=0.0, step=0.01)
    tx_date = st.date_input("Date", value=date.today())
    if st.button("Add Transaction"):
        if not description:
            st.error("Description required.")
        elif amount <= 0:
            st.error("Amount must be > 0.")
        else:
            add_transaction(tx_type, description, amount, tx_date)
            st.success(f"{tx_type} added: {description} (${amount:.2f})")
