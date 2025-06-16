import streamlit as st
import json
import bcrypt
import os
from datetime import datetime
import uuid

USERS_FILE = "users.json"
EXPENSES_FILE = "expenses.json"

def load_users():
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, "w") as f:
            json.dump({}, f)
    with open(USERS_FILE, "r") as f:
        return json.load(f)

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=4)

def load_expenses():
    if not os.path.exists(EXPENSES_FILE):
        with open(EXPENSES_FILE, "w") as f:
            json.dump({}, f)
    with open(EXPENSES_FILE, "r") as f:
        expenses = json.load(f)
    
    # Ensure all expenses have a unique ID
    modified = False
    for user, user_expenses in expenses.items():
        for i, expense in enumerate(user_expenses):
            if "id" not in expense or not expense["id"]:
                expenses[user][i]["id"] = str(uuid.uuid4())
                modified = True
    
    if modified:
        save_expenses(expenses) # Save changes back to file
    return expenses

def save_expenses(expenses):
    with open(EXPENSES_FILE, "w") as f:
        json.dump(expenses, f, indent=4)

def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def check_password(password, hashed_password):
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

def signup_page():
    st.subheader("Create New Account")
    with st.form("signup_form"):
        new_username = st.text_input("Username")
        new_password = st.text_input("Password", type="password")
        confirm_password = st.text_input("Confirm Password", type="password")
        signup_submitted = st.form_submit_button("Signup")

        if signup_submitted:
            if new_password == confirm_password:
                users = load_users()
                if new_username in users:
                    st.warning("Username already exists. Please choose a different one.")
                else:
                    users[new_username] = hash_password(new_password)
                    save_users(users)
                    st.success("Account created successfully! Please login.")
            else:
                st.error("Passwords do not match.")

def login_page():
    st.subheader("Login to Your Account")
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        login_submitted = st.form_submit_button("Login")

        if login_submitted:
            users = load_users()
            if username in users and check_password(password, users[username]):
                st.session_state['logged_in'] = True
                st.session_state['username'] = username
                st.success(f"Welcome, {username}!")
                st.rerun()
            else:
                st.error("Invalid username or password.")

def main_app():
    st.title("Expense Tracker / Budget App")
    st.write(f"Welcome, {st.session_state['username']}!")

    st.sidebar.title("Navigation")
    if st.sidebar.button("Logout"):
        st.session_state['logged_in'] = False
        st.session_state['username'] = None
        st.rerun()

    username = st.session_state['username']
    user_expenses = load_expenses().get(username, [])

    st.header("Add New Expense")
    with st.form("add_expense_form"):
        amount = st.number_input("Amount", min_value=0.01, format="%.2f")
        category = st.selectbox("Category", ["Food", "Transport", "Entertainment", "Utilities", "Rent", "Salary", "Other"])
        date = st.date_input("Date", datetime.now())
        
        currencies = ["USD", "EUR", "GBP", "JPY", "INR", "AUD", "CAD", "CHF", "CNY", "SEK", "NZD", "MXN", "SGD", "HKD", "NOK", "KRW", "TRY", "RUB", "ZAR", "BRL"]
        selected_currency = st.selectbox("Currency", currencies, index=currencies.index("INR") if "INR" in currencies else 0)

        add_expense_submitted = st.form_submit_button("Add Expense")

        if add_expense_submitted:
            expense = {
                "id": str(uuid.uuid4()), # Add a unique ID
                "amount": amount,
                "category": category,
                "date": str(date),
                "currency": selected_currency
            }
            expenses = load_expenses()
            if username not in expenses:
                expenses[username] = []
            expenses[username].append(expense)
            save_expenses(expenses)
            st.success("Expense added successfully!")
            st.rerun()

    st.header("Your Expenses")
    if user_expenses:
        import pandas as pd
        import plotly.express as px

        df = pd.DataFrame(user_expenses)
        
        # Add a delete button for each row
        df['Delete'] = [f"Delete_{i}" for i in range(len(df))]
        
        # Convert date to datetime objects for plotting
        df['date'] = pd.to_datetime(df['date'])
        
        st.dataframe(df)

        # Handle delete button clicks
        for i, row in df.iterrows():
            if st.button(f"Delete {row['category']} ({row['amount']} {row['currency']})", key=f"delete_btn_{row['id']}"):
                expenses = load_expenses()
                expenses[username] = [exp for exp in expenses[username] if exp['id'] != row['id']]
                save_expenses(expenses)
                st.success("Expense deleted successfully!")
                st.rerun()

        st.subheader("Expense Summary by Category")
        category_summary = df.groupby("category")["amount"].sum().reset_index()
        st.table(category_summary)

        st.subheader("Expense Summary by Currency")
        currency_summary = df.groupby("currency")["amount"].sum().reset_index()
        st.table(currency_summary)

        st.subheader("Monthly Expenses Trend")
        df['month_year'] = df['date'].dt.to_period('M').astype(str)
        monthly_expenses = df.groupby('month_year')['amount'].sum().reset_index()
        
        fig = px.bar(monthly_expenses, x='month_year', y='amount', 
                     title='Monthly Expenses',
                     labels={'month_year': 'Month', 'amount': 'Total Amount'})
        st.plotly_chart(fig, use_container_width=True)

    else:
        st.info("No expenses recorded yet.")

def main():
    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False

    if st.session_state['logged_in']:
        main_app()
    else:
        st.sidebar.title("Authentication")
        choice = st.sidebar.radio("Go to", ["Login", "Signup"], index=1) # Default to Signup for testing
        if choice == "Login":
            login_page()
        elif choice == "Signup":
            signup_page()

if __name__ == "__main__":
    main()
