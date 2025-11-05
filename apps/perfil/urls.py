from django.urls import path
from .views import *


urlpatterns = [
 
    path("", HomeProfileView.as_view(), name="profile"),

    path('Compartidos/', compartidosProfileView.as_view(), name='compartidos_perfil'),
    path('Miscompras/', miscomprasProfileView.as_view(), name='miscompras_perfil'),
    path('Coins/', coinsProfileView.as_view(), name='coins_perfil'),
    path('Favoritos/', favoritosProfileView.as_view(), name='favoritos_perfil'),

    path("editar/", PostProfileView.as_view(), name="data_profile"),
    path('order/<int:order_id>/', DetalleMiscompraView.as_view(), name='detalle_compra'),
] 



