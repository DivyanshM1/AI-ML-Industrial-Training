"""
PERSONAL EXPENSE TRACKER
A command-line Python project with CSV persistence, summaries and reports.

Run: python expense_tracker.py
No third-party packages are required.
"""

import csv
from datetime import date, datetime
from pathlib import Path

DATA_FILE = Path(__file__).with_name("expenses.csv")
CATEGORIES = [
    "Food", "Transport", "Shopping", "Education",
    "Bills", "Entertainment", "Health", "Other"
]


def load_expenses():
    """Load saved transactions from the CSV file."""
    if not DATA_FILE.exists():
        return []
    with DATA_FILE.open("r", newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def save_expenses(expenses):
    """Save transactions so they remain available after closing the app."""
    fields = ["date", "category", "description", "amount"]
    with DATA_FILE.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        writer.writerows(expenses)


def get_amount():
    """Validate the amount entered by the user."""
    while True:
        try:
            amount = float(input("Amount (INR): ").strip())
            if amount <= 0:
                print("Amount must be greater than zero.")
                continue
            return round(amount, 2)
        except ValueError:
            print("Enter a valid number, for example 125.50.")


def add_expense(expenses):
    print("\n--- ADD NEW EXPENSE ---")
    print("Categories:", ", ".join(CATEGORIES))

    category = input("Category: ").strip().title()
    if category not in CATEGORIES:
        print("Choose a category from the displayed list.")
        return

    description = input("Description: ").strip()
    if not description:
        print("Description cannot be empty.")
        return

    amount = get_amount()
    entered_date = input(
        f"Date [YYYY-MM-DD, Enter for {date.today()}]: "
    ).strip()

    if not entered_date:
        entered_date = date.today().isoformat()
    else:
        try:
            datetime.strptime(entered_date, "%Y-%m-%d")
        except ValueError:
            print("Invalid date. Use YYYY-MM-DD.")
            return

    expenses.append({
        "date": entered_date,
        "category": category,
        "description": description,
        "amount": f"{amount:.2f}"
    })
    save_expenses(expenses)
    print("Expense saved successfully.")


def view_expenses(expenses):
    print("\n--- EXPENSE HISTORY ---")
    if not expenses:
        print("No expenses recorded yet.")
        return

    print(f"{'No.':<5}{'Date':<13}{'Category':<16}{'Description':<24}{'Amount (INR)':>15}")
    print("-" * 73)

    for number, item in enumerate(expenses, start=1):
        print(
            f"{number:<5}{item['date']:<13}{item['category']:<16}"
            f"{item['description'][:22]:<24}{float(item['amount']):>15.2f}"
        )


def spending_summary(expenses):
    print("\n--- SPENDING SUMMARY ---")
    if not expenses:
        print("No data available. Add an expense first.")
        return

    total = sum(float(item["amount"]) for item in expenses)
    month = date.today().strftime("%Y-%m")
    monthly_total = sum(
        float(item["amount"])
        for item in expenses
        if item["date"].startswith(month)
    )

    print(f"Total recorded spending : INR {total:,.2f}")
    print(f"Spending this month     : INR {monthly_total:,.2f}")
    print(f"Number of transactions  : {len(expenses)}")
    print(f"Average expense         : INR {total / len(expenses):,.2f}")


def category_report(expenses):
    print("\n--- CATEGORY-WISE BREAKDOWN ---")
    if not expenses:
        print("No data available. Add an expense first.")
        return

    totals = {}
    for item in expenses:
        category = item["category"]
        totals[category] = totals.get(category, 0) + float(item["amount"])

    grand_total = sum(totals.values())
    print(f"{'Category':<20}{'Amount (INR)':>16}{'Share':>12}")
    print("-" * 48)

    for category, amount in sorted(
        totals.items(), key=lambda pair: pair[1], reverse=True
    ):
        share = amount / grand_total * 100
        print(f"{category:<20}{amount:>16.2f}{share:>11.1f}%")

    print("-" * 48)
    print(f"{'TOTAL':<20}{grand_total:>16.2f}{100:>10.1f}%")


def delete_expense(expenses):
    print("\n--- DELETE EXPENSE ---")
    if not expenses:
        print("There are no expenses to delete.")
        return

    view_expenses(expenses)
    try:
        number = int(input("Enter the expense number to delete: "))
        if not 1 <= number <= len(expenses):
            print("That expense number does not exist.")
            return
    except ValueError:
        print("Enter a valid whole number.")
        return

    removed = expenses.pop(number - 1)
    save_expenses(expenses)
    print(f"Deleted '{removed['description']}'.")


def main():
    expenses = load_expenses()

    while True:
        print("\n" + "=" * 42)
        print("          PERSONAL EXPENSE TRACKER")
        print("=" * 42)
        print("1. Add an expense")
        print("2. View expense history")
        print("3. View spending summary")
        print("4. View category breakdown")
        print("5. Delete an expense")
        print("6. Exit")
        print("-" * 42)

        choice = input("Select an option (1-6): ").strip()

        if choice == "1":
            add_expense(expenses)
        elif choice == "2":
            view_expenses(expenses)
        elif choice == "3":
            spending_summary(expenses)
        elif choice == "4":
            category_report(expenses)
        elif choice == "5":
            delete_expense(expenses)
        elif choice == "6":
            print("Your expenses are saved. Goodbye.")
            break
        else:
            print("Invalid selection. Choose a number from 1 to 6.")


if __name__ == "__main__":
    main()
