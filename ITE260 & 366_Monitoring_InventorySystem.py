from datetime import datetime, date

# ============================================================
# 7-ELEVEN INVENTORY MONITORING SYSTEM - FINAL FOR P3
# Console-based Python project
# Default login: staff / staff123
# Note: Records are stored in memory and reset when the program closes.
# ============================================================

inventory = []
sales_history = []
users = {"staff": "staff123"}
CATEGORIES = [
    "drinks", "snacks", "instant food", "bread",
    "siopao", "ice cream", "cigarettes", "essentials"
]


def print_header(title):
    print("\n" + "=" * 72)
    print(title.center(72))
    print("=" * 72)


def print_table(headers, rows, aligns=None):
    """Print a neatly aligned text table. Column widths adapt to the content."""
    if not headers:
        return
    rows = [[str(value) for value in row] for row in rows]
    widths = [len(str(header)) for header in headers]
    for row in rows:
        for index, value in enumerate(row):
            widths[index] = max(widths[index], len(value))

    border = "+-" + "-+-".join("-" * width for width in widths) + "-+"

    def format_row(values):
        cells = []
        for index, value in enumerate(values):
            align = aligns[index] if aligns and index < len(aligns) else "left"
            cells.append(value.rjust(widths[index]) if align == "right" else value.ljust(widths[index]))
        return "| " + " | ".join(cells) + " |"

    print(border)
    print(format_row([str(header) for header in headers]))
    print(border)
    if rows:
        for row in rows:
            print(format_row(row))
    else:
        print(format_row(["No records found."] + [""] * (len(headers) - 1)))
    print(border)


def parse_date(text):
    try:
        parsed = datetime.strptime(text, "%Y-%m-%d").date()
        # Ensure the input exactly matches YYYY-MM-DD.
        if parsed.strftime("%Y-%m-%d") != text:
            return None
        return parsed
    except ValueError:
        return None


def is_letters_only(text):
    return bool(text) and all(char.isalpha() or char.isspace() for char in text) and any(char.isalpha() for char in text)


def is_numbers_only(text):
    return text.isdigit()


def is_decimal_number(text):
    if not text or text.count(".") > 1:
        return False
    if text.startswith(".") or text.endswith("."):
        return False
    return all(char.isdigit() or char == "." for char in text) and any(char.isdigit() for char in text)


def get_product_status(item, today=None):
    today = today or date.today()
    quantity = item["quantity"]
    expiry = item["exp_date"]

    # Stock status takes priority over expiry status, matching the original system.
    if quantity == 0:
        return "OUT OF STOCK"
    if quantity <= 5:
        return "LOW STOCK"
    if expiry:
        days_left = (expiry - today).days
        if days_left < 0:
            return "EXPIRED"
        if days_left == 0:
            return "EXPIRES TODAY"
        if days_left <= 7:
            return f"{days_left} DAYS LEFT"
    return "OK"


def dashboard():
    print_header("INVENTORY DASHBOARD")
    today = date.today()
    total_value = sum(item["price"] * item["quantity"] for item in inventory)
    out_of_stock = sum(1 for item in inventory if item["quantity"] == 0)
    low_stock = sum(1 for item in inventory if 0 < item["quantity"] <= 5)
    expired = sum(1 for item in inventory if item["exp_date"] and item["exp_date"] < today)
    expiring_soon = sum(
        1 for item in inventory
        if item["exp_date"] and 0 <= (item["exp_date"] - today).days <= 7
    )
    today_sales = sum(sale["total"] for sale in sales_history if sale["date"] == today)

    rows = [
        ["Total products", len(inventory)],
        ["Current inventory value", f"P{total_value:,.2f}"],
        ["Out of stock", out_of_stock],
        ["Low stock (1-5 units)", low_stock],
        ["Expired products", expired],
        ["Expiring within 7 days", expiring_soon],
        ["Today's sales", f"P{today_sales:,.2f}"],
    ]
    print_table(["METRIC", "VALUE"], rows)


def product_rows(products):
    rows = []
    today = date.today()
    for item in sorted(products, key=lambda product: product["id"]):
        expiry_text = item["exp_date"].strftime("%Y-%m-%d") if item["exp_date"] else "No expiry"
        rows.append([
            item["id"], item["name"].title(), item["category"].title(),
            f"P{item['price']:,.2f}", item["quantity"], expiry_text,
            item["supplier"].title(), get_product_status(item, today)
        ])
    return rows


def show_table(show_dashboard=True):
    if not inventory:
        print("\n[EMPTY] No products have been added yet.")
        return False
    if show_dashboard:
        dashboard()
    print_header("INVENTORY / SHELF LIST")
    print_table(
        ["CODE", "PRODUCT", "CATEGORY", "SELLING PRICE", "STOCK", "EXPIRY DATE", "SUPPLIER", "STATUS"],
        product_rows(inventory),
        aligns=["right", "left", "left", "right", "right", "left", "left", "left"]
    )
    return True


def prompt_positive_number(label):
    while True:
        value = input(f"{label}: ").strip()
        if not value:
            print(f"{label} cannot be empty.")
            continue
        if not is_decimal_number(value):
            print("Invalid entry. Enter numbers only (example: 25 or 25.50).")
            continue
        number = float(value)
        if number <= 0:
            print("Value must be greater than zero.")
            continue
        return number


def prompt_product_code(prompt, allow_back=False):
    while True:
        value = input(prompt).strip().lower()
        if allow_back and value == "b":
            return None
        if not value:
            print("Product code cannot be empty.")
            continue
        if not is_numbers_only(value):
            print("Invalid product code. Enter numbers only.")
            continue
        code = int(value)
        if code <= 0:
            print("Product code must be greater than zero.")
            continue
        return code


def add_product():
    print_header("ADD NEW PRODUCT")
    while True:
        code = prompt_product_code("Product code")
        if any(item["id"] == code for item in inventory):
            print(f"Product code {code} already exists. Enter a different code.")
            continue
        break

    while True:
        name = input("Product name: ").strip().lower()
        if not name:
            print("Product name cannot be empty.")
        elif not is_letters_only(name):
            print("Use letters and spaces only for the product name.")
        else:
            break

    print("\nAVAILABLE CATEGORIES")
    print_table(["NO.", "CATEGORY"], [[index, category.title()] for index, category in enumerate(CATEGORIES, 1)])
    while True:
        category_input = input(f"Choose category (1-{len(CATEGORIES)}): ").strip()
        if not is_numbers_only(category_input):
            print("Enter a valid category number.")
            continue
        category_number = int(category_input)
        if 1 <= category_number <= len(CATEGORIES):
            category = CATEGORIES[category_number - 1]
            break
        print(f"Choose a number from 1 to {len(CATEGORIES)}.")

    while True:
        supplier = input("Supplier (press Enter for Unknown): ").strip().lower()
        if not supplier:
            supplier = "unknown"
            break
        if is_letters_only(supplier):
            break
        print("Use letters and spaces only for the supplier name.")

    cost = prompt_positive_number("Cost price")
    price = prompt_positive_number("Selling price")

    while True:
        stock_input = input("Initial stock quantity (0 or more): ").strip()
        if not is_numbers_only(stock_input):
            print("Enter a whole number. Stock cannot be negative.")
            continue
        stocks = int(stock_input)
        break

    while True:
        expiry_input = input("Expiry date (YYYY-MM-DD, or press Enter if none): ").strip()
        if not expiry_input:
            expiry_date = None
            break
        expiry_date = parse_date(expiry_input)
        if expiry_date:
            break
        print("Invalid date. Use the format YYYY-MM-DD, such as 2026-12-31.")

    inventory.append({
        "id": code, "name": name, "category": category, "price": price,
        "cost": cost, "quantity": stocks, "exp_date": expiry_date,
        "supplier": supplier
    })
    print(f"\nSUCCESS: {name.title()} has been added to the inventory.")


def find_product():
    if not inventory:
        print("\nNo products to search.")
        return
    print_header("FIND PRODUCT")
    while True:
        key = input("Enter product code or name (or B to go back): ").strip().lower()
        if key == "b":
            return
        if not key:
            print("Search input cannot be empty.")
            continue
        matches = [
            item for item in inventory
            if key == str(item["id"]) or key in item["name"]
        ]
        if matches:
            print_table(
                ["CODE", "PRODUCT", "CATEGORY", "SELLING PRICE", "STOCK", "EXPIRY DATE", "SUPPLIER", "STATUS"],
                product_rows(matches),
                aligns=["right", "left", "left", "right", "right", "left", "left", "left"]
            )
            return
        print("No matching product found. Please try again.")


def category_view():
    if not inventory:
        print("\nNo products have been added yet.")
        return
    print_header("VIEW PRODUCTS BY CATEGORY")
    print_table(["NO.", "CATEGORY"], [[i, category.title()] for i, category in enumerate(CATEGORIES, 1)])
    while True:
        value = input(f"Choose category (1-{len(CATEGORIES)}) or B to go back: ").strip().lower()
        if value == "b":
            return
        if not is_numbers_only(value) or not 1 <= int(value) <= len(CATEGORIES):
            print(f"Invalid choice. Enter a number from 1 to {len(CATEGORIES)}.")
            continue
        category = CATEGORIES[int(value) - 1]
        break

    matches = [item for item in inventory if item["category"] == category]
    print(f"\nCATEGORY: {category.upper()}")
    print_table(
        ["CODE", "PRODUCT", "SELLING PRICE", "STOCK", "EXPIRY DATE", "STATUS"],
        [[item["id"], item["name"].title(), f"P{item['price']:,.2f}", item["quantity"],
          item["exp_date"].strftime("%Y-%m-%d") if item["exp_date"] else "No expiry",
          get_product_status(item)] for item in sorted(matches, key=lambda product: product["id"])],
        aligns=["right", "left", "right", "right", "left", "left"]
    )


def update_product():
    if not show_table():
        return
    print_header("UPDATE PRODUCT")
    while True:
        code = prompt_product_code("Enter product code to update (or B to go back)", allow_back=True)
        if code is None:
            return
        item = next((product for product in inventory if product["id"] == code), None)
        if item:
            break
        print("Product code not found. Try again.")

    print(f"\nSelected: {item['name'].title()} (Code: {item['id']})")
    print(f"Current cost: P{item['cost']:,.2f} | Current selling price: P{item['price']:,.2f}")
    item["price"] = prompt_positive_number("New selling price")
    item["cost"] = prompt_positive_number("New cost price")

    print("\nEXPIRY DATE OPTIONS")
    print_table(["OPTION", "ACTION"], [[1, "Change expiry date"], [2, "Remove expiry date"], [3, "Keep current expiry date"]])
    while True:
        choice = input("Choose option (1-3): ").strip()
        if choice not in {"1", "2", "3"}:
            print("Invalid choice. Enter 1, 2, or 3.")
            continue
        if choice == "1":
            while True:
                expiry_input = input("New expiry date (YYYY-MM-DD): ").strip()
                expiry_date = parse_date(expiry_input)
                if expiry_date:
                    item["exp_date"] = expiry_date
                    break
                print("Invalid date. Use YYYY-MM-DD.")
        elif choice == "2":
            item["exp_date"] = None
        break

    print("\nProduct updated successfully.")
    print_table(
        ["CODE", "PRODUCT", "CATEGORY", "COST", "SELLING PRICE", "STOCK", "EXPIRY DATE", "SUPPLIER", "STATUS"],
        [[item["id"], item["name"].title(), item["category"].title(), f"P{item['cost']:,.2f}",
          f"P{item['price']:,.2f}", item["quantity"],
          item["exp_date"].strftime("%Y-%m-%d") if item["exp_date"] else "No expiry",
          item["supplier"].title(), get_product_status(item)]]
    )


def remove_product():
    if not show_table(show_dashboard=False):
        return
    print_header("REMOVE PRODUCT")
    while True:
        code = prompt_product_code("Enter product code to remove (or B to go back)", allow_back=True)
        if code is None:
            return
        item = next((product for product in inventory if product["id"] == code), None)
        if not item:
            print("Product code not found. Try again.")
            continue
        confirm = input(f"Remove {item['name'].title()} (code {code})? Type Y to confirm: ").strip().lower()
        if confirm == "y":
            inventory.remove(item)
            print("Product removed successfully.")
        else:
            print("Removal cancelled.")
        return


def stock_in():
    if not show_table(show_dashboard=False):
        return
    print_header("STOCK IN")
    while True:
        code = prompt_product_code("Enter product code (or B to go back)", allow_back=True)
        if code is None:
            return
        item = next((product for product in inventory if product["id"] == code), None)
        if item:
            break
        print("Product code not found. Try again.")
    while True:
        amount = input(f"Quantity to add to {item['name'].title()}: ").strip()
        if not is_numbers_only(amount) or int(amount) <= 0:
            print("Enter a whole number greater than zero.")
            continue
        item["quantity"] += int(amount)
        print(f"Stock updated. New quantity: {item['quantity']}")
        return


def stock_out():
    if not show_table(show_dashboard=False):
        return
    print_header("STOCK OUT / RECORD SALE")
    while True:
        code = prompt_product_code("Enter product code (or B to go back)", allow_back=True)
        if code is None:
            return
        item = next((product for product in inventory if product["id"] == code), None)
        if item:
            break
        print("Product code not found. Try again.")

    if item["exp_date"] and item["exp_date"] < date.today():
        print("SALE BLOCKED: This product is expired.")
        return
    if item["quantity"] == 0:
        print("This product is out of stock.")
        return

    while True:
        amount = input(f"Quantity to sell ({item['quantity']} available): ").strip()
        if not is_numbers_only(amount) or int(amount) <= 0:
            print("Enter a whole number greater than zero.")
            continue
        quantity_sold = int(amount)
        if quantity_sold > item["quantity"]:
            print(f"Insufficient stock. Only {item['quantity']} unit(s) available.")
            continue
        break

    item["quantity"] -= quantity_sold
    total = quantity_sold * item["price"]
    profit = quantity_sold * (item["price"] - item["cost"])
    sales_history.append({
        "date": date.today(), "code": code, "name": item["name"],
        "qty": quantity_sold, "total": total, "profit": profit
    })
    print(f"Sale recorded: {quantity_sold} x {item['name'].title()} = P{total:,.2f}")


def sales_report():
    print_header("TODAY'S SALES REPORT")
    today = date.today()
    today_sales = [sale for sale in sales_history if sale["date"] == today]
    rows = [[sale["code"], sale["name"].title(), sale["qty"], f"P{sale['total']:,.2f}", f"P{sale['profit']:,.2f}"]
            for sale in today_sales]
    print(f"Date: {today.strftime('%Y-%m-%d')}")
    print_table(["CODE", "PRODUCT", "QTY SOLD", "TOTAL SALES", "PROFIT"], rows,
                aligns=["right", "left", "right", "right", "right"])
    total_sales = sum(sale["total"] for sale in today_sales)
    total_profit = sum(sale["profit"] for sale in today_sales)
    print(f"Total sales: P{total_sales:,.2f}")
    print(f"Total profit: P{total_profit:,.2f}")


def expiry_report():
    print_header("EXPIRY REPORT")
    today = date.today()
    matches = [item for item in inventory if item["exp_date"] and (item["exp_date"] - today).days <= 7]
    matches.sort(key=lambda item: item["exp_date"])
    rows = []
    for item in matches:
        days_left = (item["exp_date"] - today).days
        if days_left < 0:
            expiry_status = f"EXPIRED ({abs(days_left)} day(s) ago)"
        elif days_left == 0:
            expiry_status = "EXPIRES TODAY"
        else:
            expiry_status = f"{days_left} day(s) left"
        rows.append([item["id"], item["name"].title(), item["category"].title(),
                     item["exp_date"].strftime("%Y-%m-%d"), item["quantity"], expiry_status])
    print_table(["CODE", "PRODUCT", "CATEGORY", "EXPIRY DATE", "STOCK", "STATUS"], rows,
                aligns=["right", "left", "left", "left", "right", "left"])
    if not matches:
        print("No products are expired or expiring within the next 7 days.")


def login():
    print_header("7-ELEVEN INVENTORY SYSTEM LOGIN")
    attempts = 0
    while attempts < 3:
        username = input("Username: ").strip()
        password = input("Password: ").strip()
        if not username or not password:
            print("Username and password cannot be empty. Please try again.\n")
            continue
        if username in users and users[username] == password:
            print(f"\nLogin successful. Welcome, {username}!\n")
            return username
        attempts += 1
        print(f"Invalid username or password. Attempt {attempts}/3.\n")
    print("Maximum login attempts reached. Exiting system.")
    return None


def main_menu(username):
    while True:
        print_header("7-ELEVEN INVENTORY MONITORING SYSTEM")
        menu_rows = [
            [1, "Add Product"], [2, "View Inventory / Shelf"],
            [3, "Find Product"], [4, "View by Category"],
            [5, "Update Product"], [6, "Remove Product"],
            [7, "Stock In"], [8, "Stock Out / Record Sale"],
            [9, "Sales Report"], [10, "Expiry Report"], [11, "Logout / Exit"]
        ]
        print_table(["OPTION", "ACTION"], menu_rows, aligns=["right", "left"])
        choice = input("Choose an option (1-11): ").strip()
        if not is_numbers_only(choice) or not 1 <= int(choice) <= 11:
            print("Invalid choice. Enter a number from 1 to 11.")
            continue

        actions = {
            "1": add_product,
            "2": show_table,
            "3": find_product,
            "4": category_view,
            "5": update_product,
            "6": remove_product,
            "7": stock_in,
            "8": stock_out,
            "9": sales_report,
            "10": expiry_report,
        }
        if choice == "11":
            print(f"\nGoodbye, {username}!")
            break
        actions[choice]()
        input("\nPress Enter to return to the main menu...")


if __name__ == "__main__":
    logged_user = login()
    if logged_user:
        main_menu(logged_user)
