from flask import Blueprint, request, jsonify
from analytics_engine import (
    get_full_analytics,
    get_overall_stats,
    get_toxicity_trend,
    get_top_toxic_words,
    toxicity_distribution
)
from database import save_comment, fetch_recent_comments, get_settings, update_settings
import pickle
import os
import numpy as np
from datetime import datetime

api = Blueprint("api", __name__)

# Load ML model + vectorizer once
from pathlib import Path

model_path = Path(__file__).resolve().parent.parent.parent / "models" / "toxic_model.pkl"

with open(model_path, "rb") as f:
    model, vectorizer = pickle.load(f)


# ---------------------------------------------------------
# ANALYZE COMMENT (LLM model)
# ---------------------------------------------------------
@api.route("/analyze", methods=["POST"])
def analyze_comment():
    data = request.json

    if "text" not in data:
        return jsonify({"error": "Missing 'text' field"}), 400

    text = data["text"]

    # Predict
    X = vectorizer.transform([text])
    probs = model.predict_proba(X)[0].tolist()

    labels = ["toxic", "severe", "obscene", "threat", "insult", "hate"]
    scores = dict(zip(labels, probs))

    # Apply thresholds
    settings = get_settings()

    toxic = scores["toxic"]
    severe = scores["severe"]

    if severe > settings["severe_threshold"]:
        decision = "Auto Delete"
    elif toxic > settings["flag_threshold"]:
        decision = "Flag for Review"
    else:
        decision = "Allow"

    return jsonify({
        "scores": scores,
        "decision": decision
    })


# ---------------------------------------------------------
# SAVE PROCESSED COMMENT
# ---------------------------------------------------------
@api.route("/save_comment", methods=["POST"])
def save_comment_api():
    data = request.json

    required_fields = ["youtube_comment_id", "author", "text", "scores", "decision"]

    for f in required_fields:
        if f not in data:
            return jsonify({"error": f"Missing field '{f}'"}), 400

    scores = data["scores"]

    save_comment({
        "youtube_comment_id": data["youtube_comment_id"],
        "author": data["author"],
        "text": data["text"],
        "toxic": scores["toxic"],
        "severe": scores["severe"],
        "obscene": scores["obscene"],
        "threat": scores["threat"],
        "insult": scores["insult"],
        "hate": scores["hate"],
        "final_decision": data["decision"]
    })

    return jsonify({"status": "saved"})


# ---------------------------------------------------------
# DASHBOARD APIs
# ---------------------------------------------------------
@api.route("/stats", methods=["GET"])
def api_stats():
    return jsonify(get_overall_stats())


@api.route("/trend", methods=["GET"])
def api_trend():
    return jsonify(get_toxicity_trend())


@api.route("/words", methods=["GET"])
def api_words():
    return jsonify(get_top_toxic_words())


@api.route("/distribution", methods=["GET"])
def api_distribution():
    return jsonify(toxicity_distribution())


@api.route("/comments", methods=["GET"])
def api_comments():
    return jsonify(fetch_recent_comments(50))


@api.route("/analytics", methods=["GET"])
def api_full_analytics():
    return jsonify(get_full_analytics())


# ---------------------------------------------------------
# SETTINGS API
# ---------------------------------------------------------
@api.route("/settings", methods=["GET"])
def api_get_settings():
    return jsonify(get_settings())


@api.route("/update_settings", methods=["POST"])
def api_update_settings():
    data = request.json

    toxic = float(data.get("toxic_threshold"))
    severe = float(data.get("severe_threshold"))
    flag = float(data.get("flag_threshold"))

    update_settings(toxic, severe, flag)

    return jsonify({"status": "updated"})


# ---------------------------------------------------------
# LIVE FEED (Dashboard Auto-Refresh)
# ---------------------------------------------------------
@api.route("/live_feed", methods=["GET"])
def live_feed():
    """
    Returns last 10 comments (for live dashboard updates)
    """
    return jsonify(fetch_recent_comments(10))