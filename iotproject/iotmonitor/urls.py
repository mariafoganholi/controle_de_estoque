from django.urls import path
from . import views

urlpatterns = [
    path('batata', views.batata, name='hello'),
    path('lista', views.lista_produtos),
    path('entrada_estoque/<int:pk>/', views.entrada_estoque),
    path('saida_estoque/<int:pk>/', views.saida_estoque)

    # path('', views.thing_list, name='thing_list'),
    # path('things/<int:pk>/', views.thing_detail, name='thing_detail'),
    # path('sensors/<int:pk>/readings/csv/', views.export_readings_csv, name='export_readings_csv'),
    # path('readings', views.new_reading, name='new_reading'),
]
