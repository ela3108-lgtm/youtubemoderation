import sqlite3
import os
from collections import Counter
from datetime import datetime, timedelta
import re

DB_PATH = os.path.join(os.path.dirname(__file__), "moderation.db")


def get_connection():
    return sqlite3.connect(DB_PATH, check_same_thread=False)


# ---------------------------------------------------------
# 1. BASIC ANALYTICS: Total count / toxic ratio
# ---------------------------------------------------------
def get_overall_stats():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM comments")
    total = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*) FROM comments
        WHERE final_decision = 'Auto Delete'
           OR final_decision = 'Flag for Review'
    """)
    toxic_count = cursor.fetchone()[0]

    conn.close()

    return {
        "total_comments": total,
        "toxic_comments": toxic_count,
        "safe_comments": total - toxic_count,
        "toxicity_ratio": round((toxic_count / total * 100), 2) if total else 0
    }


# ---------------------------------------------------------
# 2. TIME-SERIES TOXICITY TREND (hourly)
# ---------------------------------------------------------
def get_toxicity_trend(hours=24):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT timestamp, toxic
        FROM comments
        ORDER BY timestamp ASC
    """)

    rows = cursor.fetchall()
    conn.close()

    now = datetime.utcnow()
    cutoff = now - timedelta(hours=hours)

    filtered = [
        (datetime.strptime(ts, "%Y-%m-%d %H:%M:%S"), score)
        for ts, score in rows
        if datetime.strptime(ts, "%Y-%m-%d %H:%M:%S") >= cutoff
    ]

    # Create hourly buckets
    buckets = {}
    for i in range(hours):
        bucket_time = now - timedelta(hours=i)
        bucket_key = bucket_time.strftime("%H:%M")

        buckets[bucket_key] = {
            "avg_toxicity": 0,
            "count": 0
        }

    for ts, score in filtered:
        bucket_key = ts.strftime("%H:%M")
        if bucket_key in buckets:
            buckets[bucket_key]["avg_toxicity"] += score
            buckets[bucket_key]["count"] += 1

    # Final average per hour
    for key, data in buckets.items():
        if data["count"] > 0:
            data["avg_toxicity"] /= data["count"]

    return buckets


# ---------------------------------------------------------
# 3. SPIKE DETECTION
# ---------------------------------------------------------
def detect_spike(trend_data):
    """
    Detects if the last hour has >40% increase in toxicity.
    """
    values = [v["avg_toxicity"] for v in trend_data.values() if v["avg_toxicity"] > 0]

    if len(values) < 3:
        return {"spike": False, "percent_increase": 0}

    last = values[-1]
    previous = values[-2]

    if previous == 0:
        return {"spike": False, "percent_increase": 0}

    increase = ((last - previous) / previous) * 100

    return {
        "spike": increase > 40,
        "percent_increase": round(increase, 2)
    }


# ---------------------------------------------------------
# 4. TOP TOXIC WORDS (TF-like)
# ---------------------------------------------------------
def get_top_toxic_words(limit=15):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT text
        FROM comments
        WHERE final_decision = 'Auto Delete'
           OR final_decision = 'Flag for Review'
    """)

    toxic_comments = [row[0] for row in cursor.fetchall()]
    conn.close()

    if not toxic_comments:
        return []

    tokenizer = re.compile(r"\b\w+\b")

    words = []
    for text in toxic_comments:
        tokens = tokenizer.findall(text.lower())
        words.extend(tokens)

    # Remove common stopwords
    stopwords = {"the", "is", "and", "to", "you", "me", "that", "it", "of", "in", "for", "on", "a", "an"}
    filtered = [w for w in words if len(w) > 3 and w not in stopwords]

    freq = Counter(filtered)
    return freq.most_common(limit)


# ---------------------------------------------------------
# 5. TOXICITY DISTRIBUTION BY LABEL
# ---------------------------------------------------------
def toxicity_distribution():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT toxic, severe, obscene, threat, insult, hate
        FROM comments
    """)

    rows = cursor.fetchall()
    conn.close()

    dist = {
        "toxic": 0,
        "severe": 0,
        "obscene": 0,
        "threat": 0,
        "insult": 0,
        "hate": 0
    }

    for row in rows:
        for i, key in enumerate(dist.keys()):
            if row[i] > 0.5:
                dist[key] += 1

    return dist


# ---------------------------------------------------------
# 6. Combined analytics for dashboard
# ---------------------------------------------------------
def get_full_analytics():
    stats = get_overall_stats()
    trend = get_toxicity_trend()
    spike_info = detect_spike(trend)
    top_words = get_top_toxic_words()
    dist = toxicity_distribution()

    return {
        "overall_stats": stats,
        "trend": trend,
        "spike": spike_info,
        "top_toxic_words": top_words,
        "toxicity_distribution": dist
    }