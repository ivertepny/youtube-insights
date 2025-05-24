# api/serializers.py
from rest_framework import serializers

class VideoInsightSerializer(serializers.Serializer):
    video_id = serializers.CharField()
    title = serializers.CharField()
    views = serializers.IntegerField()
    subs = serializers.IntegerField()
    score = serializers.FloatField()
    description = serializers.CharField()
    insight = serializers.CharField()
