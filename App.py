import streamlit as st
import pandas as pd

# -------------------------
# Initialize session storage
# -------------------------
if "transactions" not in st.session_state:
    st.session_state["transactions"] = []

# -------------------------
# Helper functions
# -------------------------
def add_transaction(tx_type, description, amount):
    st.session_state.transactions.append({
        "Type": tx_type,
        "Description": description,
        "Amount": amount
    })

# -------------------------
# Sidebar Navigation
# -------------------------
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Dashboard", "Transactions"])

# -------------------------
# Dashboard Page
# -------------------------
if page == "Dashboard":
    st.title("📊 Dashboard")
    df = pd.DataFrame(st.session_state.transactions)
    
    total_income = df[df["Type"]=="Income"]["Amount"].sum() if not df.empty else 0
    total_expense = df[df["Type"]=="Expense"]["Amount"].sum() if not df.empty else 0
    net = total_income - total_expense
    
    st.metric("💰 Total Income", f"${total_income:,.2f}")
    st.metric("📉 Total Expenses", f"${total_expense:,.2f}")
    st.metric("📈 Net Cash Flow", f"${net:,.2f}")

# -------------------------
# Transactions Page
# -------------------------
elif page == "Transactions":
    st.title("💸 Add Transaction")
    
    with st.form("transaction_form"):
        tx_type = st.selectbox("Type", ["Income", "Expense"])
        description = st.text_input("Description")
        amount = st.number_input("Amount", min_value=0.0, step=0.01)
        submitted = st.form_submit_button("Add Transaction")
        
        if submitted and description and amount > 0:
            add_transaction(tx_type, description, amount)
            st.success(f"{tx_type} added: {description} (${amount:.2f})")
    
    st.subheader("All Transactions")
    if st.session_state.transactions:
        st.table(pd.DataFrame(st.session_state.transactions))
    else:
        st.info("No transactions yet.")
