# api/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema, OpenApiParameter
import logging

from api.youtube_client import YouTubeClient
from api.openai_client import OpenAIClient
from api.models import VideoInsight
from api.serializers import VideoInsightSerializer

openai_client = OpenAIClient()
logger = logging.getLogger(__name__)


class YouTubeVideoSearchView(APIView):
    serializer_class = VideoInsightSerializer

    @extend_schema(
        parameters=[
            OpenApiParameter(name="q", description="Search keywords", required=True, type=str),
            OpenApiParameter(name="max_results", description="Max number of results", required=False, type=int),
            OpenApiParameter(name="published_after", description="ISO date string, e.g. 2024-01-01T00:00:00Z", required=False, type=str),
        ],
        responses=VideoInsightSerializer(many=True),
        description="Searches YouTube videos and filters hidden gems (high views / low subs)."
    )
    def get(self, request):
        query = request.GET.get("q")
        max_results = int(request.GET.get("max_results", 20))

        if not query:
            return Response({"error": "Missing required parameter: q"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            yt = YouTubeClient()
            videos = yt.search_videos(query, max_results=max_results)
            video_ids = [v["video_id"] for v in videos]
            channel_ids = [v["channel_id"] for v in videos]

            video_stats = yt.get_video_stats(video_ids)
            channel_stats = yt.get_channel_stats(channel_ids)

            results = []
            for v in videos:
                vid = v["video_id"]
                cid = v["channel_id"]
                views = video_stats.get(vid, {}).get("views", 0)
                subs = channel_stats.get(cid, {}).get("subs", 0) or 1
                score = views / subs
                description = video_stats.get(vid, {}).get("description", "")

                results.append({
                    "video_id": vid,
                    "title": v["title"],
                    "channel_id": cid,
                    "channel_title": v["channel_title"],
                    "views": views,
                    "subs": subs,
                    "score": round(score, 2),
                    "description": description,
                })

            results = sorted(results, key=lambda x: x["score"], reverse=True)[:10]

            for item in results:
                try:
                    transcript = yt.get_transcript(item["video_id"])
                    full_description = f"{item['description']}\n\n{transcript}".strip()

                    insight = openai_client.generate_insight(item["title"], full_description)
                    item["insight"] = insight

                    VideoInsight.objects.update_or_create(
                        video_id=item["video_id"],
                        defaults={
                            "title": item["title"],
                            "description": item["description"],
                            "channel_title": item["channel_title"],
                            "views": item["views"],
                            "subs": item["subs"],
                            "score": item["score"],
                            "insight": insight,
                        }
                    )
                except Exception as e:
                    logger.warning(f"Error processing video {item['video_id']}: {e}")

            video_objs = VideoInsight.objects.filter(video_id__in=[v["video_id"] for v in results])
            serializer = VideoInsightSerializer(video_objs, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Search failed: {e}", exc_info=True)
            return Response({"error": "Internal server error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
