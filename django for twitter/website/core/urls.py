from django.urls import path
from . import views


urlpatterns = [
    path("" , views.index, name ='index'),
    path('followers/', views.followers_view, name='followers_view'),
]
