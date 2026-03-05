from flask import Blueprint, request, jsonify
from youtube_service import get_authenticated_service

moderation = Blueprint("moderation", __name__)

youtube = get_authenticated_service()


@moderation.route("/hide_comment", methods=["POST"])
def hide_comment():
    data = request.json
    comment_id = data.get("comment_id")

    try:
        youtube.comments().setModerationStatus(
            id=comment_id,
            moderationStatus="rejected",
            banAuthor=False
        ).execute()

        return jsonify({"status": "hidden"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500