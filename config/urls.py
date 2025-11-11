from django.contrib import admin
from django.urls import path
from django.contrib.auth import views as auth_views
from tucanasta.views import index, comparador_view, signup  # si tienes esta vista
from tucanasta import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', index, name='index'),
    path('comparador/', comparador_view, name='comparador'),  # opcional (protegida)
    path('login/',  auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('buscar/', comparador_view, name='buscar_productos'),
     path('logout/', auth_views.LogoutView.as_view(next_page='index'), name='logout'),
    path('signup/', signup, name='signup'),
    path('categoria/<str:tipo>/', views.productos_por_categoria, name='productos_por_categoria'),
    # ver cotización y ajustes
    path('agregar_cotizacion/', views.agregar_cotizacion, name='agregar_cotizacion'),
    path('agregar_cotizacion/<int:producto_id>/', views.agregar_cotizacion, name='agregar_cotizacion_id'),# POST AJAX(())
    path('cotizacion/', views.ver_cotizacion, name='ver_cotizacion'),
    path('cotizacion/actualizar/', views.actualizar_item, name='actualizar_item'),
    path('cotizacion/eliminar/', views.eliminar_item, name='eliminar_item'),
    path('cotizacion/guardar/', views.guardar_cotizacion, name='guardar_cotizacion'),
    path('pyme/ingresar/', views.pyme_ingresar, name='pyme_ingresar'),
    path('mis-cotizaciones/', views.mis_cotizaciones, name='mis_cotizaciones'),
    path('cotizacion/reabrir/', views.reabrir_cotizacion, name='reabrir_cotizacion'),
    path('cotizacion/eliminar/', views.eliminar_cotizacion, name='eliminar_cotizacion'),
    path('pyme/registro/', views.pyme_registro, name='pyme_registro'),
    path('pyme/dashboard/', views.pyme_dashboard, name='pyme_dashboard'),
    path('panel-admin/revisiones/', views.revisar_productos, name='revisar_productos'),
    path('panel-admin/revisiones/<int:pk>/aprobar/', views.aprobar_producto, name='aprobar_producto'),
    path('panel-admin/revisiones/<int:pk>/rechazar/', views.rechazar_producto, name='rechazar_producto'),
    path('panel-admin/revisiones/<int:pk>/editar/', views.editar_producto_admin, name='editar_producto_admin'),
    path('ajustes/', views.ajustes, name='ajustes'),
    path('producto/<int:producto_id>/', views.producto_detalle, name='producto_detalle'),
    path('panel-admin/revisar-productos/', views.revisar_productos, name='revisar_productos'),
    path('panel-admin/aprobar-pyme/<int:pk>/', views.aprobar_pyme, name='aprobar_pyme'),
    path('panel-admin/rechazar-pyme/<int:pk>/', views.rechazar_pyme, name='rechazar_pyme'),

]
 