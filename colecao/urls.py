from django.urls import path
from . import views

urlpatterns = [
    # Estoque
    path('estoque', views.estoque_view, name='estoque'),
    path('estoque/metrics', views.get_metrics_partial, name='get_metrics_partial'),
    path('estoque/metrics/pill', views.get_metrics_pill, name='get_metrics_pill'),
    path('estoque/<int:id>/increment', views.increment_estoque, name='increment_estoque'),
    path('estoque/<int:id>/decrement', views.decrement_estoque, name='decrement_estoque'),
    path('estoque/modal/ajustar/<int:id>', views.ajustar_estoque_modal_view, name='ajustar_estoque_modal'),
    path('estoque/exportar', views.exportar_estoque_csv, name='exportar_estoque_csv'),

    # Marcas
    path('marcas', views.marcas_view, name='marcas'),
    path('marcas/modal/novo', views.modal_nova_marca, name='modal_nova_marca'),
    path('marcas/modal/editar/<int:id>', views.modal_editar_marca, name='modal_editar_marca'),
    path('marcas/<int:id>', views.marca_detail_delete_view, name='marca_detail_delete'),
    path('marcas/<int:id>/editar', views.atualizar_marca, name='atualizar_marca'),
    path('marcas/options', views.options_marcas, name='options_marcas'),

    # Modelos
    path('modelos', views.modelos_view, name='modelos'),
    path('modelos/modal/novo', views.modal_novo_modelo, name='modal_novo_modelo'),
    path('modelos/modal/editar/<int:id>', views.modal_editar_modelo, name='modal_editar_modelo'),
    path('modelos/<int:id>', views.modelo_detail_delete_view, name='modelo_detail_delete'),
    path('modelos/<int:id>/editar', views.atualizar_modelo, name='atualizar_modelo'),
    path('modelos/options', views.options_modelos, name='options_modelos'),

    # Carrinhos
    path('carrinhos', views.carrinhos_view, name='carrinhos'),
    path('carrinhos/novo', views.form_novo_carrinho, name='form_novo_carrinho'),
    path('carrinhos/<int:id>', views.carrinho_detail_delete_view, name='carrinho_detail_delete'),
    path('carrinhos/<int:id>/editar', views.carrinho_editar_view, name='carrinho_editar'),
]
