from django.urls import path

from . views import game_detail, make_move, AllGamesList


urlpatterns = [
    path('detail/<int:pk>/',
         game_detail,
         name="gameplay_detail"),
    path('make_move/<int:pk>/',
         make_move,
         name="gameplay_make_move"),
    path('all/', AllGamesList.as_view()),
]