import streamlit as st
from datetime import date
import pandas as pd
from io import BytesIO

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
    # Sort by date and then by type to handle same-day transactions (income first)
    df = df.sort_values(by=["Date", "Type"], ascending=[True, False])
    for _, row in df.iterrows():
        if row["Type"] == "Income":
            balance += row["Amount"]
        else:
            balance -= row["Amount"]
        balances.append(balance)
    df["Running Balance"] = balances
    return df

# Helper function to convert dataframe to Excel
@st.cache_data
def convert_df_to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Transactions')
    processed_data = output.getvalue()
    return processed_data

# Sidebar navigation
page = st.sidebar.radio("Go to", ["Dashboard", "Quick Actions", "Reports"])

# Dashboard page
if page == "Dashboard":
    st.title("Your Cash Flow at a Glance 📊")
    df = calculate_running_balance()
    if not df.empty:
        total_income = df[df["Type"]=="Income"]["Amount"].sum()
        total_expense = df[df["Type"]=="Expense"]["Amount"].sum()
        net = total_income - total_expense
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Income", f"${total_income:.2f}")
        col2.metric("Total Expenses", f"${total_expense:.2f}")
        col3.metric("Net Cash Flow", f"${net:.2f}")
        
        st.subheader("Recent Transactions")
        st.dataframe(df.sort_values("Date", ascending=False).head(5))
        
        st.subheader("Full Transaction History")
        st.dataframe(df.sort_values("Date", ascending=False))
        
        excel_data = convert_df_to_excel(df)
        st.download_button(
            label="Download Data as Excel",
            data=excel_data,
            file_name="financial_data.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.info("Start by adding your first transaction in the 'Quick Actions' section.")

# Quick Actions page
elif page == "Quick Actions":
    st.title("Record a Transaction ✍️")
    st.markdown("Easily add income or expenses to track your cash flow.")
    
    with st.form("transaction_form"):
        tx_type = st.radio("Type", ["Income", "Expense"], horizontal=True)
        description = st.text_input("Description (e.g., 'Project Alpha Payment', 'Office Supplies')")
        amount = st.number_input("Amount", min_value=0.0, step=0.01)
        tx_date = st.date_input("Date", value=date.today())
        
        submitted = st.form_submit_button("Add Transaction")
        
    if submitted:
        if not description:
            st.error("Description is required.")
        elif amount <= 0:
            st.error("Amount must be greater than zero.")
        else:
            add_transaction(tx_type, description, amount, tx_date)
            st.success(f"🎉 {tx_type} added: '{description}' worth ${amount:.2f}")
            
# Reports page
elif page == "Reports":
    st.title("Financial Reports 📈")
    st.markdown("Get insights into your finances. More reports coming soon!")
    df = calculate_running_balance()
    
    if not df.empty:
        # Simple Income vs Expense chart
        st.subheader("Income vs. Expenses")
        chart_data = df.groupby("Type")["Amount"].sum().reset_index()
        st.bar_chart(chart_data, x="Type", y="Amount")

        # More complex, categorized report (requires more data)
        st.subheader("Expenses by Category (placeholder)")
        st.info("Future version will allow you to categorize expenses (e.g., Travel, Software, etc.) and view charts by category.")
        
    else:
        st.info("No data available to generate reports. Add some transactions first!")

