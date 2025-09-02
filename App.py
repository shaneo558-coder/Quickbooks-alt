import streamlit as st
import pandas as pd
from datetime import date

# -------------------------
# Initialize session storage
# -------------------------
if "transactions" not in st.session_state:
    st.session_state["transactions"] = []

if "prev_tx_type" not in st.session_state:
    st.session_state.prev_tx_type = "Income"  # default

# -------------------------
# Helper functions
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

def edit_transaction(index, tx):
    st.session_state.transactions[index] = tx

def delete_transaction(index):
    st.session_state.transactions.pop(index)

def filter_transactions(tx_type=None, categories=None, date_range=None):
    df = pd.DataFrame(st.session_state.transactions)
    if df.empty:
        return df
    if tx_type:
        df = df[df["Type"] == tx_type]
    if categories:
        df = df[df["Category"].isin(categories)]
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

        st.subheader("Income vs Expense Over Time")
        df_sorted = df.sort_values("Date")
        pivot = df_sorted.pivot_table(index="Date", columns="Type", values="Amount", aggfunc="sum").fillna(0)
        st.line_chart(pivot)

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

        # Reset category if type changed
        if tx_type != st.session_state.prev_tx_type:
            if tx_type == "Expense":
                st.session_state["expense_category"] = "Rent"
            else:
                st.session_state["income_category"] = "Sales"
            st.session_state.prev_tx_type = tx_type

        description = st.text_input("Description")
        amount = st.number_input("Amount", min_value=0.0, step=0.01)
        tx_date = st.date_input("Date", value=date.today())
        
        # Category based on type with separate keys
        if tx_type == "Expense":
            category = st.selectbox(
                "Category",
                ["Rent", "Utilities", "Marketing", "Payroll", "Other"],
                key="expense_category"
            )
            subcategory = st.text_input("Subcategory (optional)", key="expense_subcategory")
        else:  # Income
            category = st.selectbox(
                "Category",
                ["Sales", "Services", "Other"],
                key="income_category"
            )
            subcategory = st.text_input("Subcategory (optional)", key="income_subcategory")
        
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
    
    # Filter categories depend on type
    if filter_type == "Income":
        filter_categories = st.multiselect(
            "Category Filter",
            ["Sales", "Services", "Other"]
        )
    elif filter_type == "Expense":
        filter_categories = st.multiselect(
            "Category Filter",
            ["Rent", "Utilities", "Marketing", "Payroll", "Other"]
        )
    else:
        filter_categories = st.multiselect(
            "Category Filter",
            ["Rent", "Utilities", "Marketing", "Payroll", "Sales", "Services", "Other"]
        )
    
    start_date = st.date_input("Start Date", value=date(2020, 1, 1))
    end_date = st.date_input("End Date", value=date.today())

    filt_type = None if filter_type=="All" else filter_type
    filt_cat = filter_categories if filter_categories else None
    filtered_df = filter_transactions(filt_type, filt_cat, (start_date, end_date))

    if not filtered_df.empty:
        st.dataframe(filtered_df.sort_values("Date", ascending=False))
        
        st.subheader("Edit/Delete Transactions")
        for idx, row in filtered_df.iterrows():
            cols = st.columns([3, 1, 1])
            cols[0].write(f"{row['Date']} | {row['Type']} | {row['Category']} | {row['Description']} | ${row['Amount']:.2f}")
            if cols[1].button("Edit", key=f"edit_{idx}"):
                st.session_state.edit_index = idx
            if cols[2].button("Delete", key=f"delete_{idx}"):
                delete_transaction(idx)
                st.experimental_rerun()

# -------------------------
# Edit transaction modal
# -------------------------
if "edit_index" in st.session_state:
    idx = st.session_state.edit_index
    tx = st.session_state.transactions[idx]
    st.subheader("✏️ Edit Transaction")
    with st.form("edit_form"):
        tx_type = st.selectbox("Type", ["Income", "Expense"], index=0 if tx["Type"]=="Income" else 1)
        description = st.text_input("Description", tx["Description"])
        amount = st.number_input("Amount", min_value=0.0, step=0.01, value=tx["Amount"])
        tx_date = st.date_input("Date", value=tx["Date"])
        
        if tx_type == "Expense":
            category = st.selectbox(
                "Category",
                ["Rent", "Utilities", "Marketing", "Payroll", "Other"],
                index=["Rent", "Utilities", "Marketing", "Payroll", "Other"].index(tx["Category"])
            )
            subcategory = st.text_input("Subcategory (optional)", tx.get("Subcategory", ""), key="edit_expense_sub")
        else:
            category = st.selectbox(
                "Category",
                ["Sales", "Services", "Other"],
                index=["Sales", "Services", "Other"].index(tx["Category"])
            )
            subcategory = st.text_input("Subcategory (optional)", "", key="edit_income_sub")
        
        submitted = st.form_submit_button("Save Changes")
        if submitted:
            edit_transaction(idx, {
                "Type": tx_type,
                "Description": description,
                "Amount": amount,
                "Category": category,
                "Subcategory": subcategory,
                "Date": tx_date
            })
            st.success("Transaction updated!")
            del st.session_state.edit_index
            st.experimental_rerun()
