from django.urls import path
from .views import ProfileView
from django.contrib.auth.views import LoginView, LogoutView



urlpatterns =[
    path('profile/', ProfileView.as_view(), name = 'profile'),
    path('login/', LoginView.as_view() ),
    path('logout/', LogoutView.as_view()),
]