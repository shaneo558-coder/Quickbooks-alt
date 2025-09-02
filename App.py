import streamlit as st
from datetime import date
import pandas as pd
from io import BytesIO

# Initialize session state for all data
if "clients" not in st.session_state:
    st.session_state["clients"] = []
if "projects" not in st.session_state:
    st.session_state["projects"] = []
if "invoices" not in st.session_state:
    st.session_state["invoices"] = []
if "transactions" not in st.session_state:
    st.session_state["transactions"] = []

# --- Data Management Functions ---
def add_client(name, email):
    st.session_state.clients.append({"Name": name, "Email": email})

def add_project(name, client_id):
    st.session_state.projects.append({"Name": name, "Client ID": client_id})

def add_invoice(project_id, amount, due_date):
    st.session_state.invoices.append({
        "Project ID": project_id,
        "Amount": amount,
        "Due Date": due_date,
        "Status": "Outstanding"
    })

def add_transaction(tx_type, description, amount, tx_date):
    st.session_state.transactions.append({
        "Type": tx_type,
        "Description": description,
        "Amount": amount,
        "Date": tx_date
    })

def calculate_running_balance():
    df = pd.DataFrame(st.session_state.transactions)
    if df.empty:
        return df
    df["Date"] = pd.to_datetime(df["Date"])
    balance = 0
    balances = []
    df = df.sort_values(by=["Date", "Type"], ascending=[True, False])
    for _, row in df.iterrows():
        if row["Type"] == "Income":
            balance += row["Amount"]
        else:
            balance -= row["Amount"]
        balances.append(balance)
    df["Running Balance"] = balances
    return df

@st.cache_data
def convert_df_to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Transactions')
    processed_data = output.getvalue()
    return processed_data

# --- Sidebar Navigation ---
page = st.sidebar.radio(
    "Go to", 
    ["Dashboard", "Clients & Projects", "Invoicing", "Record Transaction"]
)

# --- Page: Dashboard ---
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
        
        st.subheader("Outstanding Invoices 💰")
        invoices_df = pd.DataFrame(st.session_state.invoices)
        if not invoices_df.empty:
            outstanding_invoices = invoices_df[invoices_df["Status"] == "Outstanding"]
            st.dataframe(outstanding_invoices)
            st.metric("Total Due", f"${outstanding_invoices['Amount'].sum():.2f}")
        else:
            st.info("No outstanding invoices.")

        st.subheader("Recent Transactions")
        st.dataframe(df.sort_values("Date", ascending=False).head(5))

    else:
        st.info("Start by adding your first transaction.")

---
### 2. Page: Clients & Projects

elif page == "Clients & Projects":
    st.title("Client & Project Management 👤")
    st.markdown("Add and manage your clients and the projects you work on for them.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Add a New Client")
        with st.form("client_form"):
            name = st.text_input("Client Name")
            email = st.text_input("Client Email")
            if st.form_submit_button("Add Client"):
                if name:
                    add_client(name, email)
                    st.success(f"Client '{name}' added!")
                else:
                    st.error("Client name is required.")
    
    with col2:
        st.subheader("Add a New Project")
        with st.form("project_form"):
            client_options = [c["Name"] for c in st.session_state.clients]
            selected_client = st.selectbox("Select Client", [""] + client_options)
            project_name = st.text_input("Project Name")
            if st.form_submit_button("Add Project"):
                if project_name and selected_client:
                    client_id = client_options.index(selected_client)
                    add_project(project_name, client_id)
                    st.success(f"Project '{project_name}' for '{selected_client}' added!")
                else:
                    st.error("Project name and client are required.")
    
    st.subheader("Your Clients")
    if st.session_state.clients:
        st.dataframe(pd.DataFrame(st.session_state.clients))
    else:
        st.info("No clients added yet.")

    st.subheader("Your Projects")
    if st.session_state.projects:
        projects_df = pd.DataFrame(st.session_state.projects)
        clients_df = pd.DataFrame(st.session_state.clients)
        projects_df["Client"] = projects_df["Client ID"].apply(lambda x: clients_df.loc[x, "Name"])
        st.dataframe(projects_df.drop("Client ID", axis=1))
    else:
        st.info("No projects added yet.")

---
### 3. Page: Invoicing

elif page == "Invoicing":
    st.title("Create Invoice 📝")
    st.markdown("Create and manage invoices for your projects.")
    
    with st.form("invoice_form"):
        project_options = [p["Name"] for p in st.session_state.projects]
        selected_project = st.selectbox("Select Project", [""] + project_options)
        invoice_amount = st.number_input("Amount ($)", min_value=0.0, step=0.01)
        invoice_due_date = st.date_input("Due Date", value=date.today())
        
        submitted = st.form_submit_button("Create Invoice")
    
    if submitted:
        if not selected_project:
            st.error("You must select a project.")
        elif invoice_amount <= 0:
            st.error("Amount must be greater than zero.")
        else:
            project_id = project_options.index(selected_project)
            add_invoice(project_id, invoice_amount, invoice_due_date)
            st.success(f"Invoice for project '{selected_project}' created successfully!")
            
    st.subheader("Your Invoices")
    invoices_df = pd.DataFrame(st.session_state.invoices)
    if not invoices_df.empty:
        projects_df = pd.DataFrame(st.session_state.projects)
        invoices_df["Project"] = invoices_df["Project ID"].apply(lambda x: projects_df.loc[x, "Name"])
        st.dataframe(invoices_df.drop("Project ID", axis=1))
    else:
        st.info("No invoices created yet.")

---
### 4. Page: Record Transaction

elif page == "Record Transaction":
    st.title("Record Transaction ✍️")
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

This video provides a great tutorial on building a professional business analytics dashboard using Streamlit, which can help you understand how to structure your app for a business context.
https://www.youtube.com/watch?v=sIqBA0PhzGQ
http://googleusercontent.com/youtube_content/0 *YouTube video views will be stored in your YouTube History, and your data will be stored and used by YouTube according to its [Terms of Service](https://www.youtube.com/static?template=terms)*


