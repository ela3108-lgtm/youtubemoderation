import pandas as pd
import pickle
import os

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.multiclass import OneVsRestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report

# Load dataset
data_path = os.path.join(os.path.dirname(__file__), "../data/train.csv")
df = pd.read_csv(data_path)

# Use smaller sample for development (important for your laptop)
df = df.sample(30000, random_state=42)

X_text = df["comment_text"]
y = df[['toxic','severe_toxic','obscene',
        'threat','insult','identity_hate']]

# TF-IDF
vectorizer = TfidfVectorizer(max_features=5000)
X = vectorizer.fit_transform(X_text)

# Split
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# Multi-label model
model = OneVsRestClassifier(LogisticRegression(max_iter=2000,class_weight="balanced"))
model.fit(X_train, y_train)

# Evaluate
y_pred = model.predict(X_test)
print(classification_report(y_test, y_pred,zero_division=0))

# Save model
model_path = os.path.join(os.path.dirname(__file__), "../models/toxic_model.pkl")

with open(model_path, "wb") as f:
    pickle.dump((model, vectorizer), f)

print("Model saved successfully.")
