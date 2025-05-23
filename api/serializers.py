# api/serializers.py
from rest_framework import serializers
from api.models import VideoInsight


class VideoInsightSerializer(serializers.ModelSerializer):
    class Meta:
        model = VideoInsight
        fields = [
            "video_id",
            "channel_id",
            "title",
            "description",
            "views",
            "subs",
            "score",
            "insight",
            "created_at"
        ]
