# api/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from drf_spectacular.utils import extend_schema, OpenApiParameter

from api.youtube_client import YouTubeClient
from api.openai_client import OpenAIClient
from api.models import VideoInsight
from api.serializers import VideoInsightSerializer

openai_client = OpenAIClient()


class YouTubeVideoSearchView(APIView):
    serializer_class = VideoInsightSerializer  # ← важливо для DRF/FastAPI автодокументації

    @extend_schema(
        parameters=[
            OpenApiParameter(name="q", description="Search keywords", required=True, type=str),
            OpenApiParameter(name="max_results", description="Max number of results", required=False, type=int),
            OpenApiParameter(name="published_after", description="ISO date string, e.g. 2024-01-01T00:00:00Z",
                             required=False, type=str),
        ],
        responses=VideoInsightSerializer(many=True),
        description="Searches YouTube videos and filters hidden gems (high views / low subs)."
    )
    def get(self, request):
        query = request.GET.get("q")
        max_results = int(request.GET.get("max_results", 20))
        published_after = request.GET.get("published_after")

        if not query:
            return Response({"error": "Missing required parameter: q"}, status=400)

        yt = YouTubeClient()
        videos = yt.search_videos(query, max_results=max_results, published_after=published_after)
        video_ids = [v["video_id"] for v in videos]
        channel_ids = [v["channel_id"] for v in videos]

        video_stats = yt.get_video_stats(video_ids)
        channel_stats = yt.get_channel_stats(channel_ids)

        results = []
        for v in videos:
            vid = v["video_id"]
            cid = v["channel_id"]
            title = v["title"]
            views = video_stats.get(vid, {}).get("views", 0)
            subs = channel_stats.get(cid, {}).get("subs", 0) or 1
            score = views / subs
            description = video_stats.get(vid, {}).get("description", "")

            # Отримуємо транскрипт і формуємо текст для GPT
            transcript = yt.get_transcript(vid)
            gpt_input = transcript if transcript else f"{title}\n\n{description}"
            insight = openai_client.generate_insight(gpt_input)

            results.append({
                "video_id": vid,
                "title": title,
                "channel_id": cid,
                "views": views,
                "subs": subs,
                "score": round(score, 2),
                "description": description,
                "insight": insight,
                "transcript": transcript
            })

        # Сортуємо за співвідношенням views / subs
        results = sorted(results, key=lambda x: x["score"], reverse=True)[:10]

        for item in results:
            VideoInsight.objects.update_or_create(
                video_id=item["video_id"],
                defaults={
                    "title": item["title"],
                    "description": item["description"],
                    "views": item["views"],
                    "subs": item["subs"],
                    "score": item["score"],
                    "insight": item["insight"],
                    "transcript": item["transcript"],
                }
            )

        # Сериалізація
        video_objs = VideoInsight.objects.filter(video_id__in=[v["video_id"] for v in results])
        serializer = VideoInsightSerializer(video_objs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
