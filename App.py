import streamlit as st
import pandas as pd
from datetime import date

# -------------------------
# Initialize session storage
# -------------------------
if "transactions" not in st.session_state:
    st.session_state["transactions"] = []

# -------------------------
# Helper Functions
# -------------------------
def add_transaction(tx_type, description, amount, category, subcategory, tx_date):
    st.session_state.transactions.append({
        "Type": tx_type,
        "Description": description,
        "Amount": amount,
        "Category": category,
        "Subcategory": subcategory,
        "Date": tx_date
    })

def filter_transactions(tx_type=None, category=None, date_range=None):
    df = pd.DataFrame(st.session_state.transactions)
    if df.empty:
        return df
    if tx_type:
        df = df[df["Type"] == tx_type]
    if category:
        df = df[df["Category"] == category]
    if date_range:
        start, end = date_range
        df = df[(df["Date"] >= start) & (df["Date"] <= end)]
    return df

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
    
    if not df.empty:
        total_income = df[df["Type"]=="Income"]["Amount"].sum()
        total_expense = df[df["Type"]=="Expense"]["Amount"].sum()
        net = total_income - total_expense

        col1, col2, col3 = st.columns(3)
        col1.metric("💰 Total Income", f"${total_income:,.2f}")
        col2.metric("📉 Total Expenses", f"${total_expense:,.2f}")
        col3.metric("📈 Net Cash Flow", f"${net:,.2f}")

        st.subheader("Expenses by Category")
        exp_df = df[df["Type"]=="Expense"]
        if not exp_df.empty:
            chart_data = exp_df.groupby("Category")["Amount"].sum()
            st.bar_chart(chart_data)

        st.subheader("All Transactions")
        st.dataframe(df.sort_values("Date", ascending=False))
    else:
        st.info("No transactions yet.")

# -------------------------
# Transactions Page
# -------------------------
elif page == "Transactions":
    st.title("💸 Add Transaction")
    
    with st.form("transaction_form"):
        tx_type = st.selectbox("Type", ["Income", "Expense"])
        description = st.text_input("Description")
        amount = st.number_input("Amount", min_value=0.0, step=0.01)
        tx_date = st.date_input("Date", value=date.today())
        
        # Categories
        if tx_type == "Expense":
            category = st.selectbox("Category", ["Office", "Travel", "Supplies", "Utilities", "Marketing", "Payroll", "Other"])
            subcategory = st.text_input("Subcategory (optional)")
        else:
            category = st.selectbox("Category", ["Sales", "Services", "Other"])
            subcategory = ""
        
        submitted = st.form_submit_button("Add Transaction")
        
        if submitted:
            if not description:
                st.error("Description is required.")
            elif amount <= 0:
                st.error("Amount must be greater than 0.")
            else:
                add_transaction(tx_type, description, amount, category, subcategory, tx_date)
                st.success(f"{tx_type} added: {description} (${amount:.2f})")

    st.subheader("Filter Transactions")
    filter_type = st.selectbox("Type Filter", ["All", "Income", "Expense"])
    filter_category = st.selectbox("Category Filter", ["All", "Office", "Travel", "Supplies", "Utilities", "Marketing", "Payroll", "Sales", "Services", "Other"])
    start_date = st.date_input("Start Date", value=date(2020, 1, 1))
    end_date = st.date_input("End Date", value=date.today())

    filt_type = None if filter_type=="All" else filter_type
    filt_cat = None if filter_category=="All" else filter_category
    filtered_df = filter_transactions(filt_type, filt_cat, (start_date, end_date))

    if not filtered_df.empty:
        st.dataframe(filtered_df.sort_values("Date", ascending=False))
        csv = filtered_df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download CSV", csv, "transactions.csv", "text/csv")
    else:
        st.info("No transactions match the filter.")
