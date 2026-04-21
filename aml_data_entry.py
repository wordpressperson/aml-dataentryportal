import streamlit as st
import requests
import json
from datetime import datetime, date
import tempfile
import os

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
GATEWAY_URL = st.secrets.get("API_BASE_URL")
JWT_TOKEN = st.secrets.get("JWT_TOKEN")

# Ensure GATEWAY_URL has a scheme (http:// or https://)
if not GATEWAY_URL.startswith(("http://", "https://")):
    GATEWAY_URL = "http://" + GATEWAY_URL

HEADERS = {"Authorization": f"Bearer {JWT_TOKEN}"}

st.set_page_config(page_title="AML Data Entry Portal", layout="wide")
st.title("🏦 AML Data Entry Portal")
st.markdown("Add customers, accounts, or transactions. Data will be processed by the AML system and appear in the monitoring dashboard.")

# ----------------------------------------------------------------------
# Helper function to submit a single record via batch API
# ----------------------------------------------------------------------
def submit_record(record_type: str, record_data: dict) -> tuple:
    """
    Submits a single record (customer, account, or transaction) to the AML gateway.
    Returns (success, message).
    """
    temp_files = {}
    try:
        # Create temporary files for customers, accounts, transactions
        # For the record type being added, put the data; for others, put an empty list.
        if record_type == "customer":
            customers_data = [record_data]
            accounts_data = []
            transactions_data = []
        elif record_type == "account":
            customers_data = []
            accounts_data = [record_data]
            transactions_data = []
        else:  # transaction
            customers_data = []
            accounts_data = []
            transactions_data = [record_data]

        # Write customers.json
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(customers_data, f, indent=2)
            temp_files["customers"] = f.name

        # Write accounts.json
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(accounts_data, f, indent=2)
            temp_files["accounts"] = f.name

        # Write transactions.json
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(transactions_data, f, indent=2)
            temp_files["transactions"] = f.name

        # Prepare files for upload (open in binary read mode)
        files = {
            'accounts': ('accounts.json', open(temp_files["accounts"], 'rb'), 'application/json'),
            'customers': ('customers.json', open(temp_files["customers"], 'rb'), 'application/json'),
            'transactions': ('transactions.json', open(temp_files["transactions"], 'rb'), 'application/json')
        }

        response = requests.post(
            f"{GATEWAY_URL}/v1/batch",
            files=files,
            headers=HEADERS,
            timeout=60
        )

        # Close all file handles
        for f in files.values():
            f[1].close()

        if response.status_code in (200, 201):
            result = response.json()
            return True, f"Success! Batch ID: {result.get('batch_id')}, records processed: {result.get('records_processed')}"
        else:
            return False, f"Error {response.status_code}: {response.text}"
    except Exception as e:
        return False, f"Exception: {str(e)}"
    finally:
        # Clean up temporary files
        for path in temp_files.values():
            try:
                os.unlink(path)
            except:
                pass

# ----------------------------------------------------------------------
# Customer Form
# ----------------------------------------------------------------------
with st.expander("➕ Add New Customer", expanded=False):
    with st.form("customer_form"):
        col1, col2 = st.columns(2)
        with col1:
            customer_id = st.text_input("Customer ID *", value=f"CUST{datetime.now().strftime('%Y%m%d%H%M%S')}")
            full_name = st.text_input("Full Name *")
            dob = st.date_input("Date of Birth", value=date(1980, 1, 1))
            nationality = st.text_input("Nationality (ISO code)", "US")
        with col2:
            kyc_level = st.selectbox("KYC Level", ["basic", "standard", "enhanced"])
            pep_flag = st.checkbox("Politically Exposed Person (PEP)")
            occupation = st.text_input("Occupation")
            income_source = st.text_input("Income Source")
        risk_category = st.selectbox("Risk Category", ["low", "medium", "high", "critical"])
        submitted = st.form_submit_button("Submit Customer")
        if submitted:
            if not customer_id or not full_name:
                st.error("Customer ID and Full Name are required.")
            else:
                customer_data = {
                    "customer_id": customer_id,
                    "full_name": full_name,
                    "dob": dob.isoformat(),
                    "kyc_level": kyc_level,
                    "pep_flag": pep_flag,
                    "nationality": nationality,
                    "occupation": occupation,
                    "income_source": income_source,
                    "risk_category": risk_category
                }
                success, msg = submit_record("customer", customer_data)
                if success:
                    st.success(msg)
                else:
                    st.error(msg)

# ----------------------------------------------------------------------
# Account Form
# ----------------------------------------------------------------------
with st.expander("➕ Add New Account", expanded=False):
    with st.form("account_form"):
        col1, col2 = st.columns(2)
        with col1:
            account_id = st.text_input("Account ID *", value=f"ACC{datetime.now().strftime('%Y%m%d%H%M%S')}")
            customer_id = st.text_input("Customer ID *")
            country = st.text_input("Country (ISO code)", "US")
            opened_at = st.date_input("Account Opening Date", value=date.today())
        with col2:
            account_type = st.selectbox("Account Type", ["current", "savings", "private_banking", "corporate", "business"])
            balance = st.number_input("Initial Balance (USD)", value=0.0, step=1000.0)
            currency = st.text_input("Currency", "USD")
            status = st.selectbox("Status", ["active", "restricted", "closed"])
        risk_rating = st.selectbox("Risk Rating", ["low", "medium", "high", "critical"])
        submitted = st.form_submit_button("Submit Account")
        if submitted:
            if not account_id or not customer_id:
                st.error("Account ID and Customer ID are required.")
            else:
                account_data = {
                    "account_id": account_id,
                    "customer_id": customer_id,
                    "country": country,
                    "opened_at": opened_at.isoformat() + "T00:00:00Z",
                    "account_type": account_type,
                    "balance": balance,
                    "currency": currency,
                    "status": status,
                    "risk_rating": risk_rating
                }
                success, msg = submit_record("account", account_data)
                if success:
                    st.success(msg)
                else:
                    st.error(msg)

# ----------------------------------------------------------------------
# Transaction Form
# ----------------------------------------------------------------------
with st.expander("➕ Add New Transaction", expanded=False):
    with st.form("transaction_form"):
        col1, col2 = st.columns(2)
        with col1:
            txn_id = st.text_input("Transaction ID *", value=f"T{datetime.now().strftime('%Y%m%d%H%M%S')}")
            account_id = st.text_input("Account ID *")
            amount = st.number_input("Amount", value=1000.0, step=1000.0)
            currency = st.text_input("Currency", "USD")
        with col2:
            counterparty_country = st.text_input("Counterparty Country (ISO code)", "AE")
            transaction_type = st.selectbox("Transaction Type", ["wire_transfer", "cash_deposit", "cash_withdrawal", "card_payment", "internal_transfer"])
            purpose = st.text_input("Purpose of Transaction")
            counterparty_name = st.text_input("Counterparty Name")
        timestamp = st.datetime_input("Timestamp", value=datetime.now())
        risk_flags = st.text_area("Risk Flags (comma‑separated)", value="")
        submitted = st.form_submit_button("Submit Transaction")
        if submitted:
            if not txn_id or not account_id:
                st.error("Transaction ID and Account ID are required.")
            else:
                transaction_data = {
                    "txn_id": txn_id,
                    "account_id": account_id,
                    "timestamp": timestamp.isoformat() + "Z",
                    "amount": amount,
                    "currency": currency,
                    "counterparty_country": counterparty_country,
                    "transaction_type": transaction_type,
                    "purpose": purpose,
                    "counterparty_name": counterparty_name
                }
                if risk_flags:
                    transaction_data["risk_flags"] = [flag.strip() for flag in risk_flags.split(",") if flag.strip()]
                success, msg = submit_record("transaction", transaction_data)
                if success:
                    st.success(msg)
                else:
                    st.error(msg)

# ----------------------------------------------------------------------
# Sidebar: Quick view of recent alerts (URL scheme already fixed)
# ----------------------------------------------------------------------
st.sidebar.header("🔍 Live Alerts Preview")
if st.sidebar.button("Refresh Alerts"):
    try:
        resp = requests.get(f"{GATEWAY_URL}/v1/alerts?limit=5", headers=HEADERS, timeout=10)
        if resp.status_code == 200:
            alerts = resp.json().get("alerts", [])
            if alerts:
                for a in alerts:
                    st.sidebar.markdown(f"**{a['txn_id']}** – risk {a['risk_score']:.2f} – {a['alert_type']}")
            else:
                st.sidebar.info("No alerts yet.")
        else:
            st.sidebar.error(f"Could not fetch alerts (HTTP {resp.status_code}).")
    except Exception as e:
        st.sidebar.error(f"Error: {e}")

st.sidebar.markdown("---")
st.sidebar.info("All data is sent to the AML backend. The monitoring dashboard will reflect updates within seconds.")
