from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("api/upload/", views.upload, name="api-upload"),
    path("api/explain/", views.explain, name="api-explain"),
    path("api/files/", views.files, name="api-files"),
    path("api/history/", views.history, name="api-history"),
    path("api/history/<int:entry_id>/", views.history_detail, name="api-history-detail"),
]
