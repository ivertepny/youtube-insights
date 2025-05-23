from django.db import models


class VideoInsight(models.Model):
    video_id = models.CharField(max_length=32, unique=True)
    title = models.TextField()
    description = models.TextField(blank=True)
    views = models.PositiveIntegerField()
    subs = models.PositiveIntegerField()
    score = models.FloatField()
    insight = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title[:50]} ({self.score})"
