
import pandas as pd
import joblib

from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression


# Load dataset
df = pd.read_csv("data/iris.csv")

# Separate features and target
X = df.drop("species", axis=1)
y = df["species"]

# Split dataset
X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42,
    stratify=y
)

# Create ML pipeline
model = make_pipeline(
    StandardScaler(),
    LogisticRegression(max_iter=200)
)

# Train model
model.fit(X_train, y_train)

# Save trained model
joblib.dump(model, "models/iris_model.pkl")

# Save test data for evaluation
joblib.dump(
    (X_test, y_test),
    "outputs/test_data.pkl"
)

print("Model trained successfully!")
print("Training samples:", len(X_train))
print("Testing samples:", len(X_test))
