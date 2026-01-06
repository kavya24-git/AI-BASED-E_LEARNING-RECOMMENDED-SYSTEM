import pandas as pd
from sklearn.preprocessing import LabelEncoder
import os

def safe_read_csv(path):
    if not os.path.exists(path):
        raise FileNotFoundError(f"File not found: {path}")
    return pd.read_csv(path)

def preprocess_data():
    # --- Load files (update paths if your structure is different) ---
    courses = safe_read_csv("datasets/courses.csv")
    ratings = safe_read_csv("datasets/ratings.csv")
    users = safe_read_csv("datasets/user_data.csv")

    print("Datasets Loaded Successfully!")
    print("Courses columns:", list(courses.columns))
    print("Ratings columns:", list(ratings.columns))
    print("Users columns:", list(users.columns))

    # --- Standardize column names (lowercase, strip) ---
    courses.columns = [c.strip().lower() for c in courses.columns]
    ratings.columns = [c.strip().lower() for c in ratings.columns]
    users.columns = [c.strip().lower() for c in users.columns]

    # Expected/possible column names mapping
    # courses: expect course_id, title, category or categories, tags, level
    # ratings: expect user_id, course_id, rating
    # users: expect user_id, age, gender, education_level or education, interests, skill_level

    # Rename common variants
    if "categories" in courses.columns and "category" not in courses.columns:
        courses = courses.rename(columns={"categories": "category"})
    if "courseid" in courses.columns and "course_id" not in courses.columns:
        courses = courses.rename(columns={"courseid": "course_id"})
    if "courseid" in ratings.columns and "course_id" not in ratings.columns:
        ratings = ratings.rename(columns={"courseid": "course_id"})
    if "userid" in ratings.columns and "user_id" not in ratings.columns:
        ratings = ratings.rename(columns={"userid": "user_id"})
    if "userid" in users.columns and "user_id" not in users.columns:
        users = users.rename(columns={"userid": "user_id"})
    if "education" in users.columns and "education_level" not in users.columns:
        users = users.rename(columns={"education": "education_level"})
    if "tags" in courses.columns and "tags" not in courses.columns:
        # nothing to do, keep tags
        pass

    # Fill missing columns with defaults if missing
    if "course_id" not in courses.columns:
        raise KeyError("courses.csv must contain a 'course_id' column.")
    if "user_id" not in ratings.columns or "course_id" not in ratings.columns:
        raise KeyError("ratings.csv must contain 'user_id' and 'course_id' columns.")
    if "user_id" not in users.columns:
        raise KeyError("user_data.csv must contain 'user_id' column.")

    # --- Handle missing values ---
    courses.fillna("", inplace=True)
    ratings.dropna(subset=["user_id", "course_id"], inplace=True)  # required
    users.fillna("", inplace=True)

    # --- Ensure correct dtypes ---
    # Convert ids to string for consistency
    courses["course_id"] = courses["course_id"].astype(str)
    ratings["course_id"] = ratings["course_id"].astype(str)
    ratings["user_id"] = ratings["user_id"].astype(str)
    users["user_id"] = users["user_id"].astype(str)

    # If ratings has numeric rating column with other name, try to detect it
    if "rating" not in ratings.columns:
        # try common variants
        for alt in ["score", "stars", "rate"]:
            if alt in ratings.columns:
                ratings = ratings.rename(columns={alt: "rating"})
                break
    # if still no rating, create implicit rating = 1
    if "rating" not in ratings.columns:
        ratings["rating"] = 1

    # --- Label encoding / feature creation for users (only if columns exist) ---
    encoders = {}
    for col in ["gender", "education_level", "skill_level"]:
        if col in users.columns:
            le = LabelEncoder()
            # fillna handled already; convert to string to avoid errors
            users[col] = users[col].astype(str)
            users[f"{col}_enc"] = le.fit_transform(users[col])
            encoders[col] = le

    # --- Prepare a combined text field for courses (useful for content-based) ---
    # create 'meta' column by concatenating title, category, tags, level (if present)
    meta_cols = []
    for c in ["title", "category", "tags", "level"]:
        if c in courses.columns:
            meta_cols.append(c)
    if not meta_cols:
        # fallback: use course_id as meta
        courses["meta"] = courses["course_id"]
    else:
        # join text fields with space
        courses["meta"] = courses[meta_cols].astype(str).apply(lambda row: " ".join([r for r in row if r and r != ""]), axis=1)

    # --- Merge datasets ---
    # Merge ratings + courses on course_id
    merged = pd.merge(ratings, courses, on="course_id", how="left", suffixes=("_rating", "_course"))
    # Merge merged + users on user_id
    full = pd.merge(merged, users, on="user_id", how="left", suffixes=("", "_user"))

    print("Merged data shape:", full.shape)

    # --- Save cleaned merged file ---
    cleaned_path = "datasets/cleaned_data.csv"
    full.to_csv(cleaned_path, index=False)
    print(f"Saved merged cleaned data to {cleaned_path}")

    # --- Create user-course matrix (pivot) ---
    # we will keep ratings (if many duplicates per user-course, take mean)
    pivot = ratings.copy()
    # ensure rating numeric
    try:
        pivot["rating"] = pd.to_numeric(pivot["rating"])
    except Exception:
        pivot["rating"] = pivot["rating"].astype(float, errors='ignore')

    user_course_matrix = pivot.groupby(["user_id", "course_id"])["rating"].mean().unstack(fill_value=0)
    matrix_path = "datasets/user_course_matrix.csv"
    user_course_matrix.to_csv(matrix_path)
    print(f"Saved user-course matrix to {matrix_path}")

    # --- Also save preprocessed users and courses for later use ---
    users.to_csv("datasets/preprocessed_users.csv", index=False)
    courses.to_csv("datasets/preprocessed_courses.csv", index=False)
    ratings.to_csv("datasets/preprocessed_ratings.csv", index=False)
    print("Saved preprocessed_users.csv, preprocessed_courses.csv, preprocessed_ratings.csv")

    print("Preprocessing finished successfully.")

if __name__ == "__main__":
    preprocess_data()
