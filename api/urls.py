from django.urls import path
from .views import YouTubeVideoSearchView

urlpatterns = [
    path('videos/search/', YouTubeVideoSearchView.as_view(), name='video-search'),
]
