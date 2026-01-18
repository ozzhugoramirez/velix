from django.urls import path
from .views import *
from . import views

urlpatterns = [
     path("", HomeShopView.as_view(), name="shop"),
     path('product/<str:product_id>', DetalleShotView.as_view(), name='product_detail'),
     path('product/generate-share-link/<uuid:product_id>/', GenerateShareLinkView.as_view(), name='generate_share_link'),
     
     path('product/<uuid:product_id>/like/', LikeProductView.as_view(), name='like_product'),
     path('shops/products/<uuid:product_id>/comment/', CommentCreateView.as_view(), name='leave_comment'),

     
   path('Categoria/<str:category_name>/', HomeShoptCategoriaView.as_view(), name='shop_categoria_list'),
   
  
     path('cart', CarritoView.as_view(), name="cart") ,
     path('cart/add/<uuid:product_id>/', AddToCartView.as_view(), name='add_to_cart'),
     path('cart/remove/<uuid:product_id>/', RemoveFromCartView.as_view(), name='remove_from_cart'),
     path('cart/decrease/<uuid:product_id>/', DecreaseQuantityView.as_view(), name='decrease_quantity'),
    
     path('order/<int:order_id>/', OrderDetailView.as_view(), name='order_detail'),
    path('address/add/', views.AddAddressView.as_view(), name='add_address'),
    path('address/edit/<int:pk>/', views.EditAddressView.as_view(), name='edit_address'),
    path('address/delete/<int:pk>/', views.delete_address, name='delete_address'),
     path('checkout/', CheckoutView.as_view(), name='checkout'),
     path('payment/card/', PaymentCardView.as_view(), name='payment_card'),
     path('payment/transfer-cash/', PaymentTransferCashView.as_view(), name='payment_transfer_cash'),
     path('order/<int:order_id>/', OrderDetailView.as_view(), name='order_detail'),

     path("ofertas", ShopOfertasView.as_view(), name="shop_oferta"),

]
