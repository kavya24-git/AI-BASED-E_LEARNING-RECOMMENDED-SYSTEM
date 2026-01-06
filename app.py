from flask import Flask, render_template, request, redirect, session
import pandas as pd
import sqlite3

app = Flask(__name__)
app.secret_key = "your_secret_key"

# -------------------------------------------------------
# DATABASE CONNECTION
# -------------------------------------------------------
def get_db():
    conn = sqlite3.connect("users.db")
    conn.row_factory = sqlite3.Row
    return conn

def create_user_table():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            age INTEGER,
            gender TEXT,
            profession TEXT
        )
    """)
    conn.commit()
    conn.close()

create_user_table()

# -------------------------------------------------------
# LOAD DATA
# -------------------------------------------------------
courses = pd.read_csv("datasets/courses.csv")

# -------------------------------------------------------
# HOME LOGIN PAGE
# -------------------------------------------------------
@app.route("/")
def home():
    return render_template("login.html")

# -------------------------------------------------------
# USER LOGIN
# -------------------------------------------------------
@app.route("/user_login")
def user_login():
    return render_template("user_login.html")

@app.route("/login", methods=["POST"])
def login():
    username = request.form.get("username")
    password = request.form.get("password")

    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
    user = cur.fetchone()

    if user:
        session["user_id"] = user["id"]
        session["username"] = user["username"]
        session["profession"] = user["profession"]
        return redirect("/dashboard")
    else:
        return render_template("user_login.html", error="Invalid username or password")

# -------------------------------------------------------
# USER REGISTRATION
# -------------------------------------------------------
@app.route("/register")
def register_page():
    return render_template("register.html")

@app.route("/register_user", methods=["POST"])
def register_user():
    username = request.form["username"]
    password = request.form["password"]
    age = request.form["age"]
    gender = request.form["gender"]
    profession = request.form["profession"]

    try:
        conn = get_db()
        conn.execute(
            "INSERT INTO users (username, password, age, gender, profession) VALUES (?,?,?,?,?)",
            (username, password, age, gender, profession)
        )
        conn.commit()
        conn.close()
        return render_template("user_login.html", message="Registration successful! Please login.")
    except:
        return render_template("register.html", error="Username already exists!")

# -------------------------------------------------------
# USER DASHBOARD
# -------------------------------------------------------
@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect("/")
    return render_template("dashboard.html", username=session["username"])

# -------------------------------------------------------
# SEARCH FEATURE
# -------------------------------------------------------
@app.route("/search", methods=["GET", "POST"])
def search():
    query = request.values.get("query", "").strip().lower()

    if not query:
        return render_template("result.html", courses=[])

    df = pd.read_csv("datasets/courses.csv")

    results = df[
        df["title"].str.lower().str.contains(query, na=False) |
        df["category"].str.lower().str.contains(query, na=False) |
        df["tags"].astype(str).str.lower().str.contains(query, na=False)
    ]

    return render_template("result.html",
                           courses=results.to_dict(orient="records"),
                           query=query)

# -------------------------------------------------------
# COURSE RECOMMENDATIONS BASED ON PROFESSION
# -------------------------------------------------------
@app.route("/recommend")
def recommend():
    if "user_id" not in session:
        return redirect("/")

    profession = session.get("profession", "").lower()

    if profession == "":
        recommended = courses.sample(10).to_dict(orient="records")
    else:
        recommended = courses[
            courses["category"].str.lower().str.contains(profession, na=False) |
            courses["tags"].astype(str).str.lower().str.contains(profession, na=False)
        ].to_dict(orient="records")

    return render_template("recommendations.html", courses=recommended)

# -------------------------------------------------------
# COURSE DETAILS PAGE
# -------------------------------------------------------
@app.route("/course/<int:course_id>")
def course_details(course_id):
    df = pd.read_csv("datasets/courses.csv")
    course = df[df["course_id"] == course_id]

    if course.empty:
        return "Course not found"

    course = course.iloc[0].to_dict()
    return render_template("course_details.html", course=course)

# -------------------------------------------------------
# ADMIN LOGIN
# -------------------------------------------------------
@app.route("/admin")
def admin_page():
    return render_template("admin_login.html")

@app.route("/admin_login", methods=["POST"])
def admin_login():
    username = request.form["username"]
    password = request.form["password"]

    if username == "admin" and password == "admin123":
        session["admin"] = True
        return redirect("/admin_dashboard")
    else:
        return render_template("admin_login.html", error="Invalid Admin Credentials")

# -------------------------------------------------------
# ADMIN DASHBOARD (VIEW + ADD + DELETE + ANALYTICS + GRAPHS)
# -------------------------------------------------------
@app.route("/admin_dashboard")
def admin_dashboard():
    if "admin" not in session:
        return redirect("/admin")

    df = pd.read_csv("datasets/courses.csv")

    # Category Graph Data
    category_counts = df["category"].value_counts().tolist()
    category_labels = df["category"].value_counts().index.tolist()

    # Level Graph Data
    level_counts = df["level"].value_counts().tolist()
    level_labels = df["level"].value_counts().index.tolist()

    return render_template(
        "admin_dashboard.html",
        courses=df.to_dict(orient="records"),
        total_courses=len(df),
        total_users=50,
        searches=200,
        msg=None,
        category_counts=category_counts,
        category_labels=category_labels,
        level_counts=level_counts,
        level_labels=level_labels
    )

# -------------------------------------------------------
# ADMIN ADD COURSE
# -------------------------------------------------------
@app.route("/admin_add_course", methods=["POST"])
def admin_add_course():
    if "admin" not in session:
        return redirect("/admin")

    df = pd.read_csv("datasets/courses.csv")

    new_course = {
        "course_id": int(request.form["course_id"]),
        "title": request.form["title"],
        "category": request.form["category"],
        "tags": request.form["tags"],
        "meta": request.form["meta"],
        "level": request.form["level"]
    }

    df = df.append(new_course, ignore_index=True)
    df.to_csv("datasets/courses.csv", index=False)

    return redirect("/admin_dashboard")

# -------------------------------------------------------
# ADMIN DELETE COURSE
# -------------------------------------------------------
@app.route("/admin_delete_course", methods=["POST"])
def admin_delete_course():
    if "admin" not in session:
        return redirect("/admin")

    df = pd.read_csv("datasets/courses.csv")
    delete_id = int(request.form["course_id"])

    df = df[df["course_id"] != delete_id]
    df.to_csv("datasets/courses.csv", index=False)

    return redirect("/admin_dashboard")

# -------------------------------------------------------
# LOGOUTS
# -------------------------------------------------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

@app.route("/admin_logout")
def admin_logout():
    session.pop("admin", None)
    return redirect("/admin")

# -------------------------------------------------------
# RUN APP
# -------------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True)
