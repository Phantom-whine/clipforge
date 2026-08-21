# clips/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'projects', views.ProjectViewSet, basename='project')
router.register(r'projects/(?P<project_id>[^/.]+)/clips', views.ClipViewSet, basename='clip')

urlpatterns = [
    path('', include(router.urls)),
]