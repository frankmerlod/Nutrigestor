from django.urls import path
from . import views


urlpatterns = [
    # Vista usuarios
    path('', views.lista_usuarios, name='lista_usuarios'),
    path('agregar/', views.agregar_usuario, name='agregar_usuario'),
    path('editar/<int:pk>/', views.editar_usuario, name='editar_usuario'),
    path('eliminar/<int:pk>/', views.eliminar_usuario, name='eliminar_usuario'),
    path('detalle/<int:pk>/', views.detalle_usuario, name='detalle_usuario'),
    
    # Vista nutricion
    path('nutricion/<int:pk>/', views.vista_nutricion, name='vista_nutricion'),
    path('generar_pdf/<int:usuario_id>/', views.generar_pdf, name='generar_pdf'),
    # Vista nutricion Comidas
    path('copiar_opcion_menu/<int:opcion_id>/<int:comida_id>/', views.copiar_opcion_menu, name='copiar_opcion_menu'),
    path('agregar_comida/<int:usuario_id>/', views.agregar_comida, name='agregar_comida'),
    path('editar_comida/<int:pk>/', views.editar_comida, name='editar_comida'),
    path('eliminar_comida/<int:pk>/', views.eliminar_comida, name='eliminar_comida'),
    path('agregar_opcion_menu/<int:comida_id>/', views.agregar_opcion_menu, name='agregar_opcion_menu'),
    path('editar_opcion_menu/<int:pk>/', views.editar_opcion_menu, name='editar_opcion_menu'),
    path('eliminar_opcion_menu/<int:pk>/', views.eliminar_opcion_menu, name='eliminar_opcion_menu'),
    path('agregar_alimento_en_opcion/<int:opcion_id>/<int:usuario_id>/', views.agregar_alimento_en_opcion, name='agregar_alimento_en_opcion'),
    path('editar_alimento_en_opcion/<int:opcion_id>/', views.editar_alimento_en_opcion, name='editar_alimento_en_opcion'),
    path('eliminar_alimento_en_opcion/<int:pk>/', views.eliminar_alimento_en_opcion, name='eliminar_alimento_en_opcion'),
    path('agregar_alimento/<int:opcion_id>/', views.agregar_alimento, name='agregar_alimento'),
    
    # Vista detalles de comida
    path('comida/<int:pk>/', views.detalle_comida, name='detalle_comida'),
    path('agregar_opcion_menu_detalle/<int:comida_id>/', views.agregar_opcion_menu_detalle, name='agregar_opcion_menu_detalle'),
    path('editar_opcion_menu_detalle/<int:pk>/', views.editar_opcion_menu_detalle, name='editar_opcion_menu_detalle'),
    path('eliminar_opcion_menu_detalle/<int:pk>/', views.eliminar_opcion_menu_detalle, name='eliminar_opcion_menu_detalle'),
    path('agregar_alimento_en_opcion_detalle/<int:usuario_id>/<int:opcion_id>', views.agregar_alimento_en_opcion_detalle, name='agregar_alimento_en_opcion_detalle'),
    path('editar_alimento_en_opcion_detalle/<int:opcion_id>/', views.editar_alimento_en_opcion_detalle, name='editar_alimento_en_opcion_detalle'),
    path('eliminar_alimento_en_opcion_detalle/<int:pk>/', views.eliminar_alimento_en_opcion_detalle, name='eliminar_alimento_en_opcion_detalle'),
    path('agregar_alimento_detalle/<int:opcion_id>/', views.agregar_alimento_detalle, name='agregar_alimento_detalle'),
    
    # Vista detalles de opcion de comida
    path('opcion/<int:opcion_id>/', views.detalle_opcion, name='detalle_opcion'),
    path('agregar_alimento_en_opcion_detalle_opcion/<int:usuario_id>/<int:opcion_id>/', views.agregar_alimento_en_opcion_detalle_opcion, name='agregar_alimento_en_opcion_detalle_opcion'),
    path('editar_alimento_en_opcion_detalle_opcion/<int:pk>/', views.editar_alimento_en_opcion_detalle_opcion, name='editar_alimento_en_opcion_detalle_opcion'),
    path('eliminar_alimento_en_opcion_detalle_opcion/<int:pk>/', views.eliminar_alimento_en_opcion_detalle_opcion, name='eliminar_alimento_en_opcion_detalle_opcion'),
    path('agregar_alimento_detalle_opcion/<int:opcion_id>', views.agregar_alimento_detalle_opcion, name='agregar_alimento_detalle_opcion'),
    
    # Vista Lista de alimentos en base de datos
    path('alimentos', views.lista_alimentos, name='lista_alimentos'),
    path('editar_alimento/<int:pk>/', views.editar_alimento, name='editar_alimento'),
    path('eliminar_alimento/<int:pk>/', views.eliminar_alimento, name='eliminar_alimento'),
    path('buscar_alimentos/', views.buscar_alimentos_base_datos, name='buscar_alimentos_base_datos'),
    path('buscaralimentonutritionix/', views.buscar_alimento_nutritionix, name='buscar_alimento_nutritionix'),
    path('obtener_detalle_alimento/', views.obtener_detalle_alimento, name='obtener_detalle_alimento'),
    
]


