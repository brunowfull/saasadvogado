from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.dashboard_view, name='home'),
    path('clients/', views.cliente_list, name='clients'),
    path('clients/create/', views.cliente_create, name='client_create'),
    path('clients/<int:pk>/edit/', views.cliente_update, name='client_edit'),
    path('clients/<int:pk>/delete/', views.cliente_delete, name='client_delete'),
    path('clients/<int:pk>/', views.cliente_detail, name='client_detail'),
    path('clients/<int:pk>/financial/', views.client_financial_view, name='client_financial'),
    path('clients/<int:client_pk>/financial/edit_payment/<int:payment_pk>/', views.payment_edit_view, name='payment_edit'),
    path('clients/<int:client_pk>/financial/delete_payment/<int:payment_pk>/', views.payment_delete_view, name='payment_delete'),
    path('clients/<int:pk>/activate_area/', views.activate_client_area, name='client_activate_area'),
    path('clients/<int:pk>/processes/', views.client_processes, name='client_processes'),
    path('get_payment_options/', views.get_payment_options, name='get_payment_options'),

    # Lawyer URLs
    path('lawyers/', views.advogado_list, name='lawyers'),
    path('lawyers/create/', views.advogado_create, name='lawyer_create'),
    path('lawyers/<int:pk>/edit/', views.advogado_update, name='lawyer_edit'),
    path('lawyers/<int:pk>/delete/', views.advogado_delete, name='lawyer_delete'),
    path('lawyers/<int:pk>/', views.advogado_detail, name='lawyer_detail'),

    # Task URLs
    path('tasks/', views.task_list, name='task_list'),
    path('tasks/create/', views.task_create, name='task_create'),
    path('tasks/<int:pk>/edit/', views.task_update, name='task_update'),
    path('tasks/<int:pk>/delete/', views.task_delete, name='task_delete'),
    path('tasks/<int:pk>/', views.task_detail, name='task_detail'),
    
    # Receitas URLs
    path('receitas/', views.receita_list, name='receitas'),
    path('receitas/create/', views.receita_create, name='receita_create'),
    path('receitas/<int:pk>/edit/', views.receita_update, name='receita_update'),
    path('receitas/<int:pk>/delete/', views.receita_delete, name='receita_delete'),
    path('receitas/<int:pk>/pay/', views.receita_pay, name='receita_pay'),
    path('receitas/<int:pk>/', views.receita_detail, name='receita_detail'),
    
    # Audiencia URLs
    path('audiencias/', views.audiencia_list, name='audiencia_list'),
    path('audiencias/create/', views.audiencia_create, name='audiencia_create'),
    path('audiencias/<int:pk>/edit/', views.audiencia_update, name='audiencia_update'),
    path('audiencias/<int:pk>/delete/', views.audiencia_delete, name='audiencia_delete'),
    
    # Processo URLs
    path('processos/', views.processo_list, name='processo_list'),
    path('processos/create/', views.processo_create, name='processo_create'),
    path('processos/<int:pk>/edit/', views.processo_update, name='processo_update'),
    path('processos/<int:pk>/delete/', views.processo_delete, name='processo_delete'),
    path('processos/<int:pk>/', views.processo_detail, name='processo_detail'),

    path('calendar_events/', views.calendar_events, name='calendar_events'),
    
    # AJAX Modal endpoints
    path('ajax/cliente/create/', views.cliente_create, name='ajax_cliente_create'),
    path('ajax/processo/create/', views.processo_create, name='ajax_processo_create'),
    path('ajax/audiencia/create/', views.audiencia_create, name='ajax_audiencia_create'),
    path('ajax/receita/create/', views.receita_create, name='ajax_receita_create'),
    path('ajax/get_clientes/', views.get_clientes_ajax, name='get_clientes_ajax'),
    path('ajax/get_processos/', views.get_processos_ajax, name='get_processos_ajax'),
    path('ajax/get_formas_pagamento/', views.get_formas_pagamento_ajax, name='get_formas_pagamento_ajax'),
    
    # Client management AJAX endpoints
    path('client/<int:pk>/edit/', views.client_edit, name='client_edit'),
    path('client/<int:pk>/financial/', views.client_financial, name='client_financial'),
    path('client/<int:pk>/activate-area/', views.activate_client_area, name='activate_client_area'),
    path('receita/<int:receita_pk>/add-payment/', views.add_partial_payment, name='add_partial_payment'),
    
    
    # TipoReceita URLs
    path('tipo-receita/', views.tipo_receita_list, name='tipo_receita_list'),
    path('tipo-receita/create/', views.tipo_receita_create, name='tipo_receita_create'),
    path('tipo-receita/<int:pk>/edit/', views.tipo_receita_update, name='tipo_receita_update'),
    path('tipo-receita/<int:pk>/delete/', views.tipo_receita_delete, name='tipo_receita_delete'),

    # TipoDespesa URLs
    path('tipo-despesa/', views.tipo_despesa_list, name='tipo_despesa_list'),
    path('tipo-despesa/create/', views.tipo_despesa_create, name='tipo_despesa_create'),
    path('tipo-despesa/<int:pk>/edit/', views.tipo_despesa_update, name='tipo_despesa_update'),
    path('tipo-despesa/<int:pk>/delete/', views.tipo_despesa_delete, name='tipo_despesa_delete'),

    # FormaPagamento URLs
    path('forma-pagamento/', views.forma_pagamento_list, name='forma_pagamento_list'),
    path('forma-pagamento/create/', views.forma_pagamento_create, name='forma_pagamento_create'),
    path('forma-pagamento/<int:pk>/edit/', views.forma_pagamento_update, name='forma_pagamento_update'),
    path('forma-pagamento/<int:pk>/delete/', views.forma_pagamento_delete, name='forma_pagamento_delete'),

    # Banco URLs
    path('banco/', views.banco_list, name='banco_list'),
    path('banco/create/', views.banco_create, name='banco_create'),
    path('banco/<int:pk>/edit/', views.banco_update, name='banco_update'),
    path('banco/<int:pk>/delete/', views.banco_delete, name='banco_delete'),

    # PrazoPagamento URLs
    path('prazo-pagamento/', views.prazo_pagamento_list, name='prazo_pagamento_list'),
    path('prazo-pagamento/create/', views.prazo_pagamento_create, name='prazo_pagamento_create'),
    path('prazo-pagamento/<int:pk>/edit/', views.prazo_pagamento_update, name='prazo_pagamento_update'),
    path('prazo-pagamento/<int:pk>/delete/', views.prazo_pagamento_delete, name='prazo_pagamento_delete'),

    # TipoDemanda URLs
    path('tipo-demanda/', views.tipo_demanda_list, name='tipo_demanda_list'),
    path('tipo-demanda/create/', views.tipo_demanda_create, name='tipo_demanda_create'),
    path('tipo-demanda/<int:pk>/edit/', views.tipo_demanda_update, name='tipo_demanda_update'),
    path('tipo-demanda/<int:pk>/delete/', views.tipo_demanda_delete, name='tipo_demanda_delete'),
]