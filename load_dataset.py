import pandas as pd

def load_datasets():
    courses = pd.read_csv("datasets/courses.csv")
    ratings = pd.read_csv("datasets/ratings.csv")
    users = pd.read_csv("datasets/user_data.csv")

    print("Courses Loaded:", courses.shape)
    print("Ratings Loaded:", ratings.shape)
    print("Users Loaded:", users.shape)

    return courses, ratings, users

if __name__ == "__main__":
    load_datasets()
