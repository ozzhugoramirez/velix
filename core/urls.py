from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings
from .views import *
from django.conf.urls import  handler404
from apps.shops.views import *
from apps.user.views import AuthFlowView, LogoutView  # ajusta el import
from core import views
from apps.user.views import MagicStartView, MagicConsumeView, MagicCheckEmailView


handler404 = page_not_found

urlpatterns = [
    path('admin/', admin.site.urls),


    path("access/auth/", AuthFlowView.as_view(), name="login"),
    path("access/logout/", LogoutView.as_view(), name="logout"),
    path("auth/magic/", MagicStartView.as_view(), name="magic_start"),
    path("auth/magic/check-email/", MagicCheckEmailView.as_view(), name="magic_check_email"),
    path("auth/magic/<uuid:uid>/<str:token>/", MagicConsumeView.as_view(), name="magic_login_consume"),


    path('shops/',include('apps.shops.urls')),
    path('reclamo/', ReclamoCreateView.as_view(), name='reclamo_create'),
    path('reclamo/success/', ReclamoSuccesView.as_view(), name='reclamo_success'),
    path('whatsapp/', GrupoWhatsappView.as_view(), name='grupo_whatsapp'),
    path('welco/<str:user_id>', InvitationBienvenidoView.as_view(), name='invitation_bienvenido'),

    path('share/<uuid:product_id>/', ShareProductView.as_view(), name='share_product'),
    path('change-language/', views.change_language, name='change_language'),
    path('chatbot-message/', views.chatbot_message, name='chatbot_message'),
    path("", HomeView.as_view(), name="home"),
    path('search/', SearchView.as_view(), name="Search") ,
    path('search/suggestions/', SearchSuggestionsView.as_view(), name='search_suggestions'),

    path('informacion/<str:section>/', info_page, name='info_page'),
    path('Ayuda/<str:section>/', info_page_ayuda, name='info_page_ayuda'),
    path('SobreMi/<str:section>/', info_page_sobremi, name='info_sobre_mi'),
    path('Cuenta/<str:section>/', info_page_cuenta, name='info_sobre_cuenta'),
    path('Recurso/<str:section>/', info_page_recursos, name='info_sobre_recursos'),




    path("accounts/Profile/", include('apps.perfil.urls')),
   
     path('logout/', LogoutView.as_view(), name='logout'),

    path("notificaciones/", NotificationListView.as_view(), name="notification_list"),
    path("notificaciones/<uuid:notification_id>/", NotificationDetailView.as_view(), name="notification_detail"),


   


 
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)



