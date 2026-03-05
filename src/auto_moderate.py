import pickle
import os
from youtube_service import get_authenticated_service
from database import save_comment, comment_exists

# Load toxic model + vectorizer
model_path = os.path.join(os.path.dirname(__file__), "../models/toxic_model.pkl")

with open(model_path, "rb") as f:
    model, vectorizer = pickle.load(f)

# Authenticate YouTube
youtube = get_authenticated_service()

# Your video ID
VIDEO_ID = "xSK3V0EH8yo"      # <-- change if needed


def moderate_video_comments():
    print("\nFetching comments...\n")

    request = youtube.commentThreads().list(
        part="snippet",
        videoId=VIDEO_ID,
        maxResults=50,
        textFormat="plainText"
    )
    response = request.execute()

    items = response.get("items", [])
    print("Total YouTube comments fetched:", len(items))

    for item in items:
        top_comment = item["snippet"]["topLevelComment"]
        comment_id = top_comment["id"]
        comment_text = top_comment["snippet"]["textDisplay"]
        author = top_comment["snippet"]["authorDisplayName"]

        print("\n----------------------------------------")
        print("Comment ID :", comment_id)
        print("Author     :", author)
        print("Text       :", comment_text)

        # STEP 1 — Avoid duplicates
        if comment_exists(comment_id):
            print("⚠ Already processed → skipping…")
            continue

        # STEP 2 — Predict toxicity
        X = vectorizer.transform([comment_text])
        probs = model.predict_proba(X)[0]

        labels = ["toxic", "severe", "obscene", "threat", "insult", "hate"]
        scores = dict(zip(labels, probs))

        toxic = scores["toxic"]
        severe = scores["severe"]

        # STEP 3 — Decision logic
        if severe > 0.45:
            decision = "Auto Delete"
        elif toxic > 0.55:
            decision = "auto delete"
        elif toxic > 0.35:
            decision = "flag for review"
        else:
            decision = "Allow"

        print("Decision   :", decision)

        # STEP 4 — Save into database
        save_comment({
            "youtube_comment_id": comment_id,
            "author": author,
            "text": comment_text,
            "toxic": scores["toxic"],
            "severe": scores["severe"],
            "obscene": scores["obscene"],
            "threat": scores["threat"],
            "insult": scores["insult"],
            "hate": scores["hate"],
            "final_decision": decision
        })
        print("✔ Saved to DB")

        # STEP 5 — Apply moderation action
        if decision == "Auto Delete":
            print("Trying to hide:", comment_id)

            try:
                res = youtube.comments().setModerationStatus(
                    id=comment_id,
                    moderationStatus="rejected",
                    banAuthor=False
                ).execute()

                print("API RESPONSE:", res)

            except Exception as e:
                print("ERROR:", e)

if __name__ == "__main__":
    moderate_video_comments()