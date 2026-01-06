import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import StandardScaler
import pickle

# Load preprocessed data
courses = pd.read_csv("datasets/courses.csv")
ratings = pd.read_csv("datasets/ratings.csv")
users = pd.read_csv("datasets/user_data.csv")

# Pivot table for ratings
rating_matrix = ratings.pivot_table(index='user_id', columns='course_id', values='rating').fillna(0)

# Normalize
scaler = StandardScaler()
rating_matrix_scaled = scaler.fit_transform(rating_matrix)

# Compute Cosine Similarity
similarity = cosine_similarity(rating_matrix_scaled)

# Convert back to DataFrame
similarity_df = pd.DataFrame(similarity, index=rating_matrix.index, columns=rating_matrix.index)

def recommend_courses(user_id, top_n=5):
    if user_id not in similarity_df.index:
        return ["User ID not found"]

    # Get similar users
    similar_users = similarity_df[user_id].sort_values(ascending=False)[1:6]

    # Get courses liked by similar users
    recommended_courses = ratings[
        ratings['user_id'].isin(similar_users.index)
    ].sort_values(by='rating', ascending=False)['course_id'].unique()

    return recommended_courses[:top_n]

# Test recommendation
print("Recommended courses for user 1:")
print(recommend_courses(1))

# Save the model as model.pkl
with open("model.pkl", "wb") as f:
    pickle.dump(similarity_df, f)
