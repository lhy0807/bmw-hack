from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('train/<str:TrainID>/<str:Cabin>/<str:Seat>/', views.train, name='train'),
    path('train/', views.trains_dash, name='trains'),
    path('car/<str:vin>/', views.model, name='model'),
    path('car/', views.car, name='car'),
]