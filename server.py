from flask import Flask, render_template, request, redirect, url_for, session, flash
import pandas as pd
import os

app = Flask(__name__)
app.secret_key = "your_secret_key"  # Needed for session management

def matches_scheme(row, user):
    """
    Returns True if the scheme (a row from the Excel file) matches the user's criteria.
    """
    # --- Farmer Check ---
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
        pass
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
    scheme_gender = str(row.get('gender', '')).strip().upper()
    if scheme_gender == "F" and user.get("gender", "").strip().lower() != "female":
        return False

    # --- Age Group Check ---
    scheme_age_group = str(row.get('age group', '')).strip().upper()
    user_group = user.get("group", "").strip().lower()  # Expected: "student", "adult", "seniors"
    try:
        user_age = float(user.get("age"))
    except:
        return False

    if scheme_age_group == "A":
        pass
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
    scheme_pwd = str(row.get('pwd', '')).strip().upper()
    if scheme_pwd == "Y" and not user.get("disabled"):
        return False

    # --- Caste Check ---
    # (If needed, add caste-specific logic here.)

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
    selected_category = request.form.get('category', 'All')
    keyword = request.form.get('keyword', '').strip()  # Keyword search field

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

    # Save the user info in session (for later use in pagination).
    session['user'] = user

    # Build absolute path to database.xlsm
    base_dir = os.path.abspath(os.path.dirname(__file__))
    db_path = os.path.join(base_dir, "database.xlsm")
    if not os.path.exists(db_path):
        return "Error: database.xlsm not found in the project directory."

    try:
        df = pd.read_excel(db_path, engine="openpyxl")
    except Exception as e:
        return f"Error loading database.xlsm: {e}"

    # Filter matching schemes.
    matched_schemes = []
    for idx, row in df.iterrows():
        scheme_name = row.get("Scheme name", "No Name")
        if not matches_scheme(row, user):
            continue

        # Retrieve scheme's category (default if missing).
        scheme_category = str(row.get("Category", "")).strip() or "Uncategorized"
        # Category filter (substring check).
        if selected_category != "All" and selected_category.lower() not in scheme_category.lower():
            continue

        # Keyword search: check if keyword is in the scheme name or info.
        if keyword:
            if keyword.lower() not in str(row.get("Scheme name", "")).lower() and \
               keyword.lower() not in str(row.get("Info", "")).lower():
                continue

        matched_schemes.append({
            "scheme_name": scheme_name,
            "info": row.get("Info", ""),
            "link": row.get("link", "#")
        })

    # Save the matched schemes in session for pagination.
    session['matched_schemes'] = matched_schemes
    return redirect(url_for('results', page=1))


@app.route('/favorite')
def favorite():
    # Get the scheme name from query parameters.
    scheme_name = request.args.get('scheme_name')
    if not scheme_name:
        flash("Invalid scheme.")
        return redirect(url_for('results', page=1))
    
    favorites = session.get('favorites', [])
    if scheme_name not in favorites:
        favorites.append(scheme_name)
        flash(f"Added {scheme_name} to favorites.")
    session['favorites'] = favorites
    return redirect(url_for('results', page=request.args.get('page', 1)))


@app.route('/remove_favorite')
def remove_favorite():
    # Get the scheme name from query parameters.
    scheme_name = request.args.get('scheme_name')
    if not scheme_name:
        flash("Invalid scheme.")
        return redirect(url_for('results', page=1))
    
    favorites = session.get('favorites', [])
    if scheme_name in favorites:
        favorites.remove(scheme_name)
        flash(f"Removed {scheme_name} from favorites.")
    session['favorites'] = favorites
    # Redirect back to the referring page if available.
    return redirect(request.referrer or url_for('results', page=1))


@app.route('/results')
def results():
    # Pagination setup.
    matched_schemes = session.get('matched_schemes', [])
    page = int(request.args.get('page', 1))
    per_page = 10  # Number of schemes per page
    total = len(matched_schemes)
    start = (page - 1) * per_page
    end = start + per_page
    page_schemes = matched_schemes[start:end]
    total_pages = (total + per_page - 1) // per_page
    
    # Retrieve favorites from session.
    favorites = session.get('favorites', [])

    return render_template('submission.html', 
                           name=session.get('user', {}).get('name', 'User'),
                           schemes=page_schemes,
                           page=page,
                           total_pages=total_pages,
                           favorites=favorites)

@app.route('/favorites')
def show_favorites():
    favorites = session.get('favorites', [])
    return render_template('favorites.html', favorites=favorites)

if __name__ == '__main__':
    app.run(debug=True)
