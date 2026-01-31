from django.urls import path, include

from .views import *

urlpatterns = [
      path("", HomeAdminView.as_view(), name="dasboard"),
      path('login', LoginView.as_view(), name='rt'),
      path('clintes', ClientesAdminView.as_view(), name='clintes_admin'),
      path('Reclamos', ReclamosView.as_view(), name='Reclamos_admin'),
      path('ListProducto', ProductoAdminView.as_view(), name='ProductoAdminView'),
      path('productos/crear/', CrearProductoView.as_view(), name='crear_producto'),
      path('productos/editar/<uuid:pk>/', EditarProductoView.as_view(), name='editar_producto'),
      path('productos/eliminar/<uuid:pk>/', EliminarProductoView.as_view(), name='eliminar_producto'),
      path('productos/analizar/<uuid:product_id>/', AnalizarProductoView.as_view(), name='analizar_producto'),
      path('productos/vistas/<uuid:product_id>/', DetalleVistasProductoView.as_view(), name='detalle_vistas_producto'),
       path('productos/compartidos/<uuid:product_id>/', DetalleCompartidosProductoView.as_view(), name='detalle_compartidos_producto'),
      
      path('productos/compartidos/<uuid:share_id>/visitas/', ShareVisitDetailView.as_view(), name='detalle_visitas'),
      path('admin/productos/<uuid:product_id>/comentarios/', DetalleComentariosProductoView.as_view(), name='detalle_comentarios_producto'),
      path('reclamos/<int:reclamo_id>/atender/', AtenderReclamoView.as_view(), name='atender_reclamo'),
      path('admin/cupones/', CouponListView.as_view(), name='coupon_list'),
      path('admin/cupones/confirmar-borrado/<str:selected_ids>/', CouponDeleteConfirmView.as_view(), name='coupon_confirm_delete'),
      path('clientes/<int:usuario_id>/perfil/', VerPerfilView.as_view(), name='ver_perfil'),
      path('clientes/<int:usuario_id>/editar/', EditarUsuarioView.as_view(), name='editar_usuario'),
     
      path('search-queries-summary/', SearchQuerySummaryView.as_view(), name='search_queries'),
      path('confirm-delete-search-queries/', ConfirmDeleteSearchQueriesView.as_view(), name='confirm_delete_search_queries'),
       path('delete-selected-search-queries/', DeleteSelectedSearchQueriesView.as_view(), name='delete_selected_search_queries'),
      path('visitas_combinadas/', VisitasCombinadasView.as_view(), name='visitas_combinadas'),

      path('paginas-visitadas/<int:visita_id>/', PaginasVisitadasSesionView.as_view(), name='paginas_visitadas_sesion'),
      path('admin/crear-categoria/', CrearCategoriaView.as_view(), name='crear_categoria'),
       
      path('admin/ordenes/', OrderListView.as_view(), name='order_list'),
      path('admin/ordenes/<int:order_id>/', OrderDetailClienteView.as_view(), name='cliente_orden1'),

      path('perfiles/pendientes/', PerfilesPendientesView.as_view(), name='perfiles_pendientes'),
      path('perfil/revisar/<int:perfil_id>/', RevisarPerfilView.as_view(), name='revisar_perfil'),

      path("admin/notificaciones/", AdminNotificationDashboardView.as_view(), name="admin_notification_dashboard"),


      path('clientes/<int:usuario_id>/perfil/compra/', ItemProfileCompra.as_view(), name='item_profile_compra'),
      path('clientes/<int:usuario_id>/perfil/link/', ItemProfileLink.as_view(), name='item_profile_link'),
      path('clientes/<int:usuario_id>/perfil/visitas/', ItemProfileVisitas.as_view(), name='item_profile_visitas'),
      path('visita/<int:visita_id>/paginas/', PaginasVisitadas.as_view(), name='ver_paginas_visitadas'),
   

] 


