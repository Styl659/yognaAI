from flask import Flask, render_template, request
import pandas as pd
import os

app = Flask(__name__)  # Using Flask defaults (templates in templates/, static in static/)

def matches_scheme(row, user):
    """
    Returns True if the scheme (a row from the Excel file) matches the user's criteria.
    """

    # --- Farmer Check ---
    # If the scheme requires farmers ("Y"), user must have ticked farmer.
    if str(row.get('farmer', '')).strip().upper() == "Y" and not user.get("farmer"):
        return False

    # --- Rural Check ---
    if str(row.get('rural', '')).strip().upper() == "Y" and not user.get("rural"):
        return False

    # --- Pregnant Check ---
    if str(row.get('pregnant', '')).strip().upper() == "Y" and not user.get("pregnant"):
        return False

    # --- Income Check ---
    scheme_income = str(row.get('income', '')).strip().upper()
    user_income = user.get("income", "").strip().upper()
    if scheme_income == "ALL":
        pass  # Applies to everyone.
    elif scheme_income == "BPL":
        if user_income != "BPL":
            return False
    elif scheme_income == "LIG":
        if user_income not in ["LIG", "BPL"]:
            return False
    elif scheme_income == "EWS":
        if user_income not in ["EWS", "LIG", "BPL"]:
            return False
    elif scheme_income == "ABOVE":
        if user_income != "ABOVE":
            return False

    # --- Gender Check ---
    # "F" means scheme only for females.
    scheme_gender = str(row.get('gender', '')).strip().upper()
    if scheme_gender == "F" and user.get("gender", "").strip().lower() != "female":
        return False
    # If scheme_gender is "B" or any other value, no exclusion is applied.

    # --- Age Group Check ---
    scheme_age_group = str(row.get('age group', '')).strip().upper()
    user_group = user.get("group", "").strip().lower()  # Expected: "student", "adult", "seniors"
    try:
        user_age = float(user.get("age"))
    except:
        return False

    if scheme_age_group == "A":
        pass  # Applies to all.
    elif scheme_age_group == "STUDENT":
        if user_group != "student":
            return False
    elif scheme_age_group == "WA":
        if user_group != "adult":
            return False
    elif scheme_age_group == "SENIOR":
        if user_group != "seniors":
            return False
    elif scheme_age_group == "S":
        try:
            ageL = float(row.get('ageL', 0))
            ageH = float(row.get('ageH', 0))
        except:
            return False
        if not (ageL <= user_age <= ageH):
            return False

    # --- PWD Check ---
    # If the scheme requires PWD only ("Y"), then user must be disabled.
    scheme_pwd = str(row.get('pwd', '')).strip().upper()
    if scheme_pwd == "Y" and not user.get("disabled"):
        return False
    # If scheme_pwd is "B", it does not exclude non-disabled users.

    # --- Caste Check ---
    # If the scheme indicates caste with "B", it is a preference only, so no exclusion.
    # (If you need to check for SC specifically, you could add additional logic here.)

    return True

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/submit', methods=['POST'])
def submit():
    # Retrieve form data.
    name = request.form.get('name')
    age = request.form.get('age')
    gender = request.form.get('gender')
    group = request.form.get('group')
    income = request.form.get('income')
    selected_category = request.form.get('category', 'All')  # Default to "All"

    # Retrieve checkbox values.
    pregnant = 'pregnant' in request.form
    farmer   = 'farmer' in request.form
    rural    = 'rural' in request.form
    disabled = 'disabled' in request.form
    sc       = 'sc' in request.form

    # Build the user dictionary.
    user = {
        "name": name,
        "age": age,
        "gender": gender,
        "group": group,
        "income": income,
        "pregnant": pregnant,
        "farmer": farmer,
        "rural": rural,
        "disabled": disabled,
        "sc": sc
    }

    # Build absolute path to database.xlsm
    base_dir = os.path.abspath(os.path.dirname(__file__))
    db_path = os.path.join(base_dir, "database.xlsm")
    print("Looking for database at:", db_path)

    if not os.path.exists(db_path):
        return "Error: database.xlsm not found in the project directory."

    try:
        df = pd.read_excel(db_path, engine="openpyxl")
    except Exception as e:
        return f"Error loading database.xlsm: {e}"

    # Filter matching schemes with additional debug output.
    matched_schemes = []
    for idx, row in df.iterrows():
        scheme_name = row.get("Scheme name", "No Name")
        print(f"Evaluating scheme: {scheme_name}")
        if not matches_scheme(row, user):
            print(f"Scheme '{scheme_name}' did not match user criteria.")
            continue

        # Retrieve scheme's category; default to "Uncategorized" if missing.
        scheme_category = str(row.get("Category", "")).strip() or "Uncategorized"
        print(f"Scheme '{scheme_name}' category: '{scheme_category}'. Selected filter: '{selected_category}'.")

        # Use substring matching instead of strict equality.
        if selected_category != "All" and selected_category.lower() not in scheme_category.lower():
            print(f"Scheme '{scheme_name}' filtered out by category.")
            continue

        matched_schemes.append({
            "scheme_name": scheme_name,
            "info": row.get("Info", ""),
            "link": row.get("link", "#")
        })
        print(f"Scheme '{scheme_name}' added as a match.")

    print("User details:", user)
    print("Matched schemes count:", len(matched_schemes))

    return render_template('submission.html', name=name, schemes=matched_schemes)

if __name__ == '__main__':
    app.run(debug=True)