from django.urls import path
from . import views

urlpatterns = [
    path('select-folder/', views.select_folder, name='select_folder'),
    path('', views.download_view, name='download'),
]