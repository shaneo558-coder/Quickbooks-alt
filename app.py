import streamlit as st
import pandas as pd
import io
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

# -------------------------
# Initialize session storage
# -------------------------
if "transactions" not in st.session_state:
    st.session_state["transactions"] = []

# -------------------------
# Helper Functions
# -------------------------
def add_transaction(tx_type, description, amount, category, subcategory):
    st.session_state.transactions.append({
        "Type": tx_type,
        "Description": description,
        "Amount": amount,
        "Category": category,
        "Subcategory": subcategory
    })

def filter_transactions(tx_type=None, category=None):
    df = pd.DataFrame(st.session_state.transactions)
    if df.empty:
        return df
    if tx_type:
        df = df[df["Type"] == tx_type]
    if category:
        df = df[df["Category"] == category]
    return df

def generate_invoice_pdf(client, amount, description):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    c.setFont("Helvetica-Bold", 20)
    c.drawString(200, 750, "Invoice")
    c.setFont("Helvetica", 12)
    c.drawString(50, 700, f"Client: {client}")
    c.drawString(50, 680, f"Description: {description}")
    c.drawString(50, 660, f"Amount: ${amount:.2f}")
    c.drawString(50, 640, "Thank you for your business!")
    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer

# -------------------------
# Sidebar Navigation
# -------------------------
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Dashboard", "Transactions", "Generate Invoice"])

# -------------------------
# Dashboard
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
        st.dataframe(df)
    else:
        st.info("No transactions yet.")

# -------------------------
# Transactions
# -------------------------
elif page == "Transactions":
    st.title("💸 Add Transaction")

    with st.form("transaction_form"):
        tx_type = st.selectbox("Type", ["Income", "Expense"])
        description = st.text_input("Description")
        amount = st.number_input("Amount", min_value=0.0, step=0.01)
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
                add_transaction(tx_type, description, amount, category, subcategory)
                st.success(f"{tx_type} added: {description} (${amount:.2f})")

    st.subheader("Filter Transactions")
    filter_type = st.selectbox("Type Filter", ["All", "Income", "Expense"])
    filter_category = st.selectbox("Category Filter", ["All"] + ["Office","Travel","Supplies","Utilities","Marketing","Payroll","Other","Sales","Services"])

    filt_type = None if filter_type=="All" else filter_type
    filt_cat = None if filter_category=="All" else filter_category
    filtered_df = filter_transactions(filt_type, filt_cat)

    if not filtered_df.empty:
        st.dataframe(filtered_df)
    else:
        st.info("No transactions match the filter.")

# -------------------------
# Generate Invoice
# -------------------------
elif page == "Generate Invoice":
    st.title("🧾 Generate Invoice")
    client = st.text_input("Client Name")
    description = st.text_input("Description")
    amount = st.number_input("Amount", min_value=0.0, step=0.01)
    if st.button("Generate PDF"):
        if not client or not description or amount <= 0:
            st.error("All fields must be filled correctly.")
        else:
            pdf = generate_invoice_pdf(client, amount, description)
            st.download_button(label="Download Invoice PDF", data=pdf, file_name=f"{client}_invoice.pdf", mime="application/pdf")
            st.success("Invoice generated!")
