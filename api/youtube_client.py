# api/youtube_client.py
import os
from googleapiclient.discovery import build
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")


class YouTubeClient:
    def __init__(self):
        self.youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)

    def search_videos(self, query, published_after=None, max_results=20):
        search_response = self.youtube.search().list(
            q=query,
            part="id,snippet",
            maxResults=max_results,
            type="video",
            publishedAfter=published_after,
        ).execute()

        videos = []
        for item in search_response.get("items", []):
            video_id = item["id"]["videoId"]
            title = item["snippet"]["title"]
            channel_id = item["snippet"]["channelId"]
            videos.append({
                "video_id": video_id,
                "title": title,
                "channel_id": channel_id,
            })
        return videos

    def get_video_stats(self, video_ids):
        response = self.youtube.videos().list(
            part="statistics,snippet",
            id=",".join(video_ids)
        ).execute()

        stats = {}
        for item in response.get("items", []):
            video_id = item["id"]
            stats[video_id] = {
                "views": int(item["statistics"].get("viewCount", 0)),
                "likes": int(item["statistics"].get("likeCount", 0)),
                "description": item["snippet"].get("description", ""),
            }
        return stats

    def get_channel_stats(self, channel_ids):
        response = self.youtube.channels().list(
            part="statistics",
            id=",".join(channel_ids)
        ).execute()

        stats = {}
        for item in response.get("items", []):
            channel_id = item["id"]
            stats[channel_id] = {
                "subs": int(item["statistics"].get("subscriberCount", 0))
            }
        return stats

    def get_transcript(self, video_id):
        try:
            transcript = YouTubeTranscriptApi.get_transcript(video_id)
            return " ".join([t["text"] for t in transcript])
        except (TranscriptsDisabled, NoTranscriptFound):
            return ""
        except Exception:
            return ""
