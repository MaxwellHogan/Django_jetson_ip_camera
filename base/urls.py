from django.urls import path

from . import views

urlpatterns = [
    path("", views.stream_page, name="stream_page"),
    path("cam0_stream", views.cam0_stream, name="cam0_stream"),
    path("cam1_stream", views.cam1_stream, name="cam1_stream"),
]