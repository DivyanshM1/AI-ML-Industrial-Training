# Iris Flower Classification using Machine Learning

A beginner-level Machine Learning project that classifies Iris flowers into three species using Logistic Regression and Scikit-learn.

## About the Project

This project was developed to understand the basic Machine Learning workflow, from loading and exploring a dataset to training a model and making predictions.

The Iris dataset contains 150 samples belonging to three species:
- Setosa
- Versicolor
- Virginica

Each sample contains four measurements:
- Sepal length
- Sepal width
- Petal length
- Petal width

## Technologies Used

- Python 3.14
- Scikit-learn
- Pandas
- NumPy
- Matplotlib
- Seaborn
- Joblib
- Jupyter Notebook

## Machine Learning Workflow

1. Dataset loading
2. Data exploration and analysis
3. Exploratory Data Analysis (EDA)
4. Feature and target separation
5. Train-test split (80:20)
6. Logistic Regression model training
7. Model evaluation
8. Prediction on new data

## Project Structure

- `data/` - Dataset files
- `notebooks/` - Jupyter notebooks
- `src/` - Python scripts for loading, training, evaluation and prediction
- `models/` - Saved trained model
- `outputs/` - Evaluation-related files

## Installation and Usage

Clone the repository:

```bash
git clone YOUR_REPOSITORY_URL
cd iris_classification
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the project scripts from the project root:

```bash
python src/load_data.py
python src/train.py
python src/evaluate.py
python src/predict.py
```

## Learning Outcome

This project provided hands-on experience with supervised Machine Learning, data exploration, model training, evaluation metrics and predictions using Scikit-learn.