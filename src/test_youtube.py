from youtube_service import get_authenticated_service

youtube = get_authenticated_service()

# Fetch your channel info
request = youtube.channels().list(
    part="snippet",
    mine=True
)

response = request.execute()

print("Channel Name:", response["items"][0]["snippet"]["title"])

channels = youtube.channels().list(
    part="snippet",
    mine=True
).execute()

print("Logged in channel:", channels["items"][0]["snippet"]["title"])
