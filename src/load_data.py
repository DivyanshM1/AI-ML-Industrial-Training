
import pandas as pd
from sklearn.datasets import load_iris


def load_iris_data():
    # Load the built-in Iris dataset
    iris = load_iris()

    # Convert features into a DataFrame
    df = pd.DataFrame(
        iris.data,
        columns=iris.feature_names
    )

    # Add species column
    df["species"] = [
        iris.target_names[i]
        for i in iris.target
    ]

    return df


if __name__ == "__main__":
    df = load_iris_data()

    # Save dataset
    df.to_csv("data/iris.csv", index=False)

    print("Dataset loaded successfully!")
    print(df.head())
    print("\nDataset shape:", df.shape)
