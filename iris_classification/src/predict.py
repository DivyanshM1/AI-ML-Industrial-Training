
import joblib
import pandas as pd

# Load trained model
model = joblib.load("models/iris_model.pkl")

# New flower measurements
new_flower = pd.DataFrame(
    [[5.1, 3.5, 1.4, 0.2]],
    columns=[
        "sepal length (cm)",
        "sepal width (cm)",
        "petal length (cm)",
        "petal width (cm)"
    ]
)

# Predict species
prediction = model.predict(new_flower)

print("Predicted Species:", prediction[0])
