import streamlit as st
import pandas as pd
from datetime import date

# -------------------------
# Initialize session state
# -------------------------
if "transactions" not in st.session_state:
    st.session_state["transactions"] = []

if "edit_index" not in st.session_state:
    st.session_state["edit_index"] = None

# -------------------------
# Helper functions
# -------------------------
def add_transaction(tx_type, description, amount, category, subcategory, tx_date, notes):
    st.session_state.transactions.append({
        "Type": tx_type,
        "Description": description,
        "Amount": amount,
        "Category": category,
        "Subcategory": subcategory,
        "Date": tx_date,
        "Notes": notes
    })

def edit_transaction(index, tx):
    st.session_state.transactions[index] = tx

def delete_transaction(index):
    st.session_state.transactions.pop(index)

def filter_transactions(tx_type=None, categories=None, keyword=None, date_range=None):
    df = calculate_running_balance()
    if df.empty:
        return df
    if tx_type:
        df = df[df["Type"] == tx_type]
    if categories:
        df = df[df["Category"].isin(categories)]
    if keyword:
        df = df[df["Description"].str.contains(keyword, case=False, na=False) |
                df["Notes"].str.contains(keyword, case=False, na=False)]
    if date_range:
        start, end = date_range
        df = df[(df["Date"] >= pd.to_datetime(start)) & (df["Date"] <= pd.to_datetime(end))]
    return df

def calculate_running_balance():
    # Ensure consistent columns
    columns = ["Type", "Description", "Amount", "Category", "Subcategory", "Date", "Notes"]
    tx_list = []
    for tx in st.session_state.transactions:
        clean_tx = {col: tx.get(col, "" if col != "Amount" else 0) for col in columns}
        if not clean_tx["Date"]:
            clean_tx["Date"] = date.today()  # default to today
        tx_list.append(clean_tx)

    df = pd.DataFrame(tx_list)
    if df.empty:
        return df

    # Ensure Date column is datetime
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
    df = calculate_running_balance()
    
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

        st.subheader("All Transactions with Running Balance")
        st.dataframe(df.sort_values("Date", ascending=False))
    else:
        st.info("No transactions yet.")

# -------------------------
# Transactions Page
# -------------------------
elif page == "Transactions":
    st.title("💸 Add Transaction")

    tx_type = st.selectbox("Type", ["Income", "Expense"], key="tx_type_select")

    # -------------------------
    # Expense Form
    # -------------------------
    if tx_type == "Expense":
        with st.form("expense_form"):
            description = st.text_input("Description", key="expense_desc")
            amount = st.number_input("Amount", min_value=0.0, step=0.01, key="expense_amount")
            tx_date = st.date_input("Date", value=date.today(), key="expense_date")
            default_categories = ["Rent", "Utilities", "Marketing", "Payroll", "Other"]
            category = st.selectbox("Category", default_categories, key="expense_category")
            custom_cat = st.text_input("Or type a custom category", key="expense_custom_cat")
            if custom_cat.strip():
                category = custom_cat.strip()
            subcategory = st.text_input("Subcategory (optional)", key="expense_subcategory")
            notes = st.text_area("Notes (optional)", key="expense_notes")
            submitted = st.form_submit_button("Add Expense")
            if submitted:
                if not description:
                    st.error("Description is required.")
                elif amount <= 0:
                    st.error("Amount must be greater than 0.")
                else:
                    add_transaction("Expense", description, amount, category, subcategory, tx_date, notes)
                    st.success(f"Expense added: {description} (${amount:.2f})")

    # -------------------------
    # Income Form
    # -------------------------
    else:
        with st.form("income_form"):
            description = st.text_input("Description", key="income_desc")
            amount = st.number_input("Amount", min_value=0.0, step=0.01, key="income_amount")
            tx_date = st.date_input("Date", value=date.today(), key="income_date")
            default_categories = ["Sales", "Services", "Other"]
            category = st.selectbox("Category", default_categories, key="income_category")
            custom_cat = st.text_input("Or type a custom category", key="income_custom_cat")
            if custom_cat.strip():
                category = custom_cat.strip()
            subcategory = st.text_input("Subcategory (optional)", key="income_subcategory")
            notes = st.text_area("Notes (optional)", key="income_notes")
            submitted = st.form_submit_button("Add Income")
            if submitted:
                if not description:
                    st.error("Description is required.")
                elif amount <= 0:
                    st.error("Amount must be greater than 0.")
                else:
                    add_transaction("Income", description, amount, category, subcategory, tx_date, notes)
                    st.success(f"Income added: {description} (${amount:.2f})")

    # -------------------------
    # Filter Transactions
    # -------------------------
    st.subheader("Filter Transactions")
    filter_type = st.selectbox("Type Filter", ["All", "Income", "Expense"], key="filter_type")
    keyword = st.text_input("Search Description / Notes", key="filter_keyword")

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
    filtered_df = filter_transactions(filt_type, filt_cat, keyword, (start_date, end_date))

    if not filtered_df.empty:
        st.dataframe(filtered_df.sort_values("Date", ascending=False))

        st.subheader("Edit/Delete Transactions")
        for idx, row in filtered_df.iterrows():
            cols = st.columns([3, 1, 1])
            cols[0].write(f"{row['Date'].date()} | {row['Type']} | {row['Category']} | {row['Description']} | ${row['Amount']:.2f}")
            if cols[1].button("Edit", key=f"edit_{idx}"):
                st.session_state.edit_index = idx
            if cols[2].button("Delete", key=f"delete_{idx}"):
                delete_transaction(idx)
                st.experimental_rerun()

# -------------------------
# Edit transaction modal
# -------------------------
if st.session_state.edit_index is not None:
    idx = st.session_state.edit_index
    tx = st.session_state.transactions[idx]
    st.subheader("✏️ Edit Transaction")
    with st.form("edit_form"):
        tx_type = st.selectbox("Type", ["Income", "Expense"], index=0 if tx["Type"]=="Income" else 1, key="edit_tx_type")
        description = st.text_input("Description", tx["Description"], key="edit_description")
        amount = st.number_input("Amount", min_value=0.0, step=0.01, value=tx["Amount"], key="edit_amount")
        tx_date = st.date_input("Date", value=tx["Date"], key="edit_date")

        if tx_type == "Expense":
            default_categories = ["Rent", "Utilities", "Marketing", "Payroll", "Other"]
            category = st.selectbox(
                "Category",
                default_categories,
                index=default_categories.index(tx["Category"]) if tx["Category"] in default_categories else 0,
                key="edit_expense_category"
            )
            custom_cat = st.text_input("Or type a custom category", tx["Category"] if tx["Category"] not in default_categories else "", key="edit_expense_custom")
            if custom_cat.strip():
                category = custom_cat.strip()
            subcategory = st.text_input("Subcategory (optional)", tx.get("Subcategory", ""), key="edit_expense_sub")
        else:
            default_categories = ["Sales", "Services", "Other"]
            category = st.selectbox(
                "Category",
                default_categories,
                index=default_categories.index(tx["Category"]) if tx["Category"] in default_categories else 0,
                key="edit_income_category"
            )
            custom_cat = st.text_input("Or type a custom category", tx["Category"] if tx["Category"] not in default_categories else "", key="edit_income_custom")
            if custom_cat.strip():
                category = custom_cat.strip()
            subcategory = st.text_input("Subcategory (optional)", tx.get("Subcategory", ""), key="edit_income_sub")

        notes = st.text_area("Notes (optional)", tx.get("Notes", ""), key="edit_notes")

        submitted = st.form_submit_button("Save Changes")
        if submitted:
            edit_transaction(idx, {
                "Type": tx_type,
                "Description": description,
                "Amount": amount,
                "Category": category,
                "Subcategory": subcategory,
                "Date": tx_date,
                "Notes": notes
            })
            st.success("Transaction updated!")
            st.session_state.edit_index = None
            st.experimental_rerun()
