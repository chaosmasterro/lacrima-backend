"""
URL configuration for lacrima_backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.urls import path
from . import views   

urlpatterns = [
    path("ping/", views.ping, name="ping"),
    path("events/", views.events, name="events"),
    path("bets/", views.bets_list, name="bets_list"),
    path("place-bet/", views.place_bet, name="place_bet"),
]
