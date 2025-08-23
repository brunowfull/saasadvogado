from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q, Count, Sum
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal
import json

from .models import (
    Task, Cliente, Processo, Audiencia, Publicacao,
    Receita, Despesa, AtividadeRecente, TipoReceita, TipoDespesa,
    FormaPagamento, Banco, PrazoPagamento, TipoDemanda
)
from users.models import Lawyer
from .forms import (
    TaskForm, ClienteForm, AdvogadoForm, ProcessoForm, 
    AudienciaForm, ReceitaForm, DespesaForm, DashboardFilterForm, TipoReceitaForm,
    TipoDespesaForm, FormaPagamentoForm, BancoForm, PrazoPagamentoForm, TipoDemandaForm
)

@login_required
def dashboard_view(request):
    """View principal do dashboard com métricas e dados avançados"""
    
    # Verificar se o usuário tem perfil de advogado
    try:
        advogado = request.user
    except:
        messages.warning(request, 'Perfil de advogado não encontrado. Entre em contato com o administrador.')
    
    # Filtros de período
    periodo = int(request.GET.get('periodo', 30))
    data_inicio = timezone.now() - timedelta(days=periodo)
    hoje = timezone.now().date()
    inicio_mes = hoje.replace(day=1)
    mes_anterior = (inicio_mes - timedelta(days=1)).replace(day=1)
    
    # === MÉTRICAS PRINCIPAIS ===
    
    # Clientes
    total_clientes = Cliente.objects.filter(ativo=True).count()
    clientes_novos = Cliente.objects.filter(
        data_cadastro__gte=data_inicio,
        ativo=True
    ).count()
    clientes_com_processos = Cliente.objects.filter(
        processo__isnull=False,
        ativo=True
    ).distinct().count()
    
    # Processos
    total_processos = Processo.objects.count()
    processos_ativos = Processo.objects.filter(status='ativo').count()
    processos_finalizados_mes = Processo.objects.filter(
        status='finalizado',
        data_fim__gte=inicio_mes
    ).count()
    
    # Tarefas
    tarefas_pendentes = Task.objects.filter(status='pendente').count()
    tarefas_atrasadas = Task.objects.filter(
        status='pendente',
        data_inicio__lt=timezone.now()
    ).count()
    tarefas_concluidas_mes = Task.objects.filter(
        status='concluida',
        data_atualizacao__gte=inicio_mes
    ).count()
    
    # Audiências
    audiencias_pendentes = Audiencia.objects.filter(
        data_hora__gte=timezone.now(),
        data_hora__lte=timezone.now() + timedelta(days=30)
    ).count()
    audiencias_hoje = Audiencia.objects.filter(
        data_hora__date=hoje
    ).count()
    audiencias_semana = Audiencia.objects.filter(
        data_hora__gte=timezone.now(),
        data_hora__lte=timezone.now() + timedelta(days=7)
    ).count()
    
    # Publicações
    publicacoes_nao_lidas = Publicacao.objects.filter(lida=False).count()
    publicacoes_mes = Publicacao.objects.filter(
        data_publicacao__gte=inicio_mes
    ).count()
    
    # === MÉTRICAS FINANCEIRAS AVANÇADAS ===
    
    # Receitas do mês atual
    receitas_mes = Receita.objects.filter(
        data_vencimento__gte=inicio_mes,
        data_vencimento__lte=hoje
    ).aggregate(total=Sum('valor_total'))['total'] or Decimal('0.00')
    
    receitas_pagas_mes = Receita.objects.filter(
        data_recebimento__gte=inicio_mes,
        data_recebimento__lte=hoje
    ).aggregate(total=Sum('valor_recebido'))['total'] or Decimal('0.00')
    
    receitas_pendentes = Receita.objects.filter(
        pago=False,
        data_vencimento__lte=hoje
    ).aggregate(total=Sum('valor_total'))['total'] or Decimal('0.00')
    
    receitas_vencidas = Receita.objects.filter(
        pago=False,
        data_vencimento__lt=hoje
    ).aggregate(total=Sum('valor_total'))['total'] or Decimal('0.00')
    
    # Receitas do mês anterior para comparação
    receitas_mes_anterior = Receita.objects.filter(
        data_vencimento__gte=mes_anterior,
        data_vencimento__lt=inicio_mes
    ).aggregate(total=Sum('valor_total'))['total'] or Decimal('0.00')
    
    # Despesas do mês
    despesas_mes = Despesa.objects.filter(
        data_vencimento__gte=inicio_mes,
        data_vencimento__lte=hoje
    ).aggregate(total=Sum('valor'))['total'] or Decimal('0.00')
    
    despesas_pagas_mes = Despesa.objects.filter(
        data_pagamento__gte=inicio_mes,
        data_pagamento__lte=hoje,
        pago=True
    ).aggregate(total=Sum('valor'))['total'] or Decimal('0.00')
    
    # Despesas do mês anterior para comparação
    despesas_mes_anterior = Despesa.objects.filter(
        data_vencimento__gte=mes_anterior,
        data_vencimento__lt=inicio_mes
    ).aggregate(total=Sum('valor'))['total'] or Decimal('0.00')
    
    # Cálculos de saldo e variação
    saldo_mes = receitas_pagas_mes - despesas_pagas_mes
    saldo_mes_anterior = receitas_mes_anterior - despesas_mes_anterior
    
    # Cálculo da variação percentual
    variacao_receitas = 0
    if receitas_mes_anterior > 0:
        variacao_receitas = ((receitas_mes - receitas_mes_anterior) / receitas_mes_anterior) * 100
    
    variacao_despesas = 0
    if despesas_mes_anterior > 0:
        variacao_despesas = ((despesas_mes - despesas_mes_anterior) / despesas_mes_anterior) * 100
    
    variacao_saldo = 0
    if saldo_mes_anterior != 0:
        variacao_saldo = ((saldo_mes - saldo_mes_anterior) / abs(saldo_mes_anterior)) * 100
    
    # === DADOS PARA GRÁFICOS ===
    
    # Distribuição de processos por status
    processos_por_status = list(Processo.objects.values('status').annotate(
        count=Count('id')
    ))
    
    # Receitas vs Despesas últimos 6 meses
    receitas_despesas_meses = []
    for i in range(6):
        mes_ref = hoje.replace(day=1) - timedelta(days=30*i)
        mes_fim = (mes_ref.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
        
        receitas = Receita.objects.filter(
            data_vencimento__gte=mes_ref,
            data_vencimento__lte=mes_fim
        ).aggregate(total=Sum('valor_total'))['total'] or 0
        
        despesas = Despesa.objects.filter(
            data_vencimento__gte=mes_ref,
            data_vencimento__lte=mes_fim
        ).aggregate(total=Sum('valor'))['total'] or 0
        
        receitas_despesas_meses.append({
            'mes': mes_ref.strftime('%b/%Y'),
            'receitas': float(receitas),
            'despesas': float(despesas)
        })
    
    receitas_despesas_meses.reverse()  # Ordem cronológica
    
    # Top 5 clientes por receita
    top_clientes = Cliente.objects.annotate(
        total_receitas=Sum('receita__valor_total')
    ).filter(
        total_receitas__isnull=False,
        ativo=True
    ).order_by('-total_receitas')[:5]
    
    # === ATIVIDADES E AGENDA ===
    
    # Atividades recentes
    atividades_recentes = AtividadeRecente.objects.select_related(
        'usuario', 'cliente', 'processo'
    ).order_by('-data_criacao')[:10]
    
    # Próximas audiências
    proximas_audiencias = Audiencia.objects.filter(
        data_hora__gte=timezone.now()
    ).select_related('processo', 'processo__cliente').order_by('data_hora')[:5]
    
    # Tarefas urgentes
    tarefas_urgentes = Task.objects.filter(
        status__in=['pendente', 'em_andamento'],
        prioridade__in=['alta', 'urgente'],
        data_inicio__lte=timezone.now() + timedelta(days=7)
    ).select_related('cliente', 'processo').order_by('data_inicio')[:5]
    
    # Próximos vencimentos de receitas
    proximos_vencimentos = Receita.objects.filter(
        pago=False,
        data_vencimento__gte=hoje,
        data_vencimento__lte=hoje + timedelta(days=30)
    ).select_related('cliente').order_by('data_vencimento')[:10]
    
    # Taxa de conversão de clientes
    taxa_conversao = 0
    if total_clientes > 0:
        taxa_conversao = (clientes_com_processos / total_clientes) * 100
    
    # Ticket médio
    ticket_medio = 0
    if total_clientes > 0 and receitas_mes > 0:
        ticket_medio = receitas_mes / total_clientes
    
    context = {
        # Métricas básicas
        'total_clientes': total_clientes,
        'total_processos': total_processos,
        'processos_ativos': processos_ativos,
        'tarefas_pendentes': tarefas_pendentes,
        'tarefas_atrasadas': tarefas_atrasadas,
        'audiencias_pendentes': audiencias_pendentes,
        'audiencias_hoje': audiencias_hoje,
        'audiencias_semana': audiencias_semana,
        'publicacoes_nao_lidas': publicacoes_nao_lidas,
        
        # Métricas financeiras
        'receitas_mes': receitas_mes,
        'receitas_pagas_mes': receitas_pagas_mes,
        'receitas_pendentes': receitas_pendentes,
        'receitas_vencidas': receitas_vencidas,
        'despesas_mes': despesas_mes,
        'despesas_pagas_mes': despesas_pagas_mes,
        'saldo_mes': saldo_mes,
        
        # Variações percentuais
        'variacao_receitas': round(variacao_receitas, 1),
        'variacao_despesas': round(variacao_despesas, 1),
        'variacao_saldo': round(variacao_saldo, 1),
        
        # Métricas calculadas
        'clientes_novos': clientes_novos,
        'clientes_com_processos': clientes_com_processos,
        'taxa_conversao': round(taxa_conversao, 1),
        'ticket_medio': ticket_medio,
        'processos_finalizados_mes': processos_finalizados_mes,
        'tarefas_concluidas_mes': tarefas_concluidas_mes,
        'publicacoes_mes': publicacoes_mes,
        
        # Dados para gráficos
        'processos_por_status': processos_por_status,
        'receitas_despesas_meses': receitas_despesas_meses,
        'top_clientes': top_clientes,
        
        # Listas
        'atividades_recentes': atividades_recentes,
        'proximas_audiencias': proximas_audiencias,
        'tarefas_urgentes': tarefas_urgentes,
        'proximos_vencimentos': proximos_vencimentos,
        
        # Formulário de filtro
        'filter_form': DashboardFilterForm(request.GET),
    }
    
    return render(request, 'dashboard/dashboard.html', context)

@login_required
def task_list(request):
    """Exibe o calendário de tarefas e audiências."""
    return render(request, 'dashboard/task_calendar.html')

@login_required
def task_create(request):
    """Criar nova tarefa"""
    if request.method == 'POST':
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            # Definir o advogado baseado no usuário logado
            task.advogado = request.user
            
            task.save()
            
            # Criar atividade recente
            AtividadeRecente.objects.create(
                tipo='tarefa_criada',
                descricao=f'Nova tarefa criada: {task.titulo}',
                usuario=request.user,
                task=task
            )
            
            messages.success(request, 'Tarefa criada com sucesso!')
            return redirect('dashboard:task_list')
    else:
        form = TaskForm()
    
    return render(request, 'dashboard/task_form.html', {'form': form, 'title': 'Nova Tarefa'})

@login_required
def task_update(request, pk):
    """Atualizar tarefa"""
    task = get_object_or_404(Task, pk=pk)
    
    if request.method == 'POST':
        form = TaskForm(request.POST, instance=task)
        if form.is_valid():
            form.save()
            messages.success(request, 'Tarefa atualizada com sucesso!')
            return redirect('dashboard:task_list')
    else:
        form = TaskForm(instance=task)
    
    return render(request, 'dashboard/task_form.html', {'form': form, 'title': 'Editar Tarefa'})

@login_required
def task_delete(request, pk):
    """Deletar tarefa"""
    task = get_object_or_404(Task, pk=pk)
    
    if request.method == 'POST':
        task.delete()
        messages.success(request, 'Tarefa excluída com sucesso!')
        return redirect('dashboard:task_list')
    
    return render(request, 'dashboard/task_confirm_delete.html', {'task': task})

@login_required
def task_detail(request, pk):
    """Detalhes da tarefa"""
    task = get_object_or_404(Task, pk=pk)
    
    return render(request, 'dashboard/task_detail.html', {
        'task': task
    })


# Views para Processos
@login_required
def processo_list(request):
    """Lista de processos"""
    processos = Processo.objects.select_related('cliente', 'advogado_responsavel').order_by('-data_inicio')
    return render(request, 'dashboard/processo_list.html', {'processos': processos})

@login_required
def processo_create(request):
    """Criar novo processo"""
    if request.method == 'POST':
        # Check if it's an AJAX request
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or 'application/json' in request.META.get('HTTP_ACCEPT', ''):
            form = ProcessoForm(request.POST)
            if form.is_valid():
                processo = form.save()
                
                # Criar atividade recente
                AtividadeRecente.objects.create(
                    tipo='processo_criado',
                    descricao=f'Novo processo criado: {processo.numero} - {processo.titulo}',
                    usuario=request.user,
                    processo=processo,
                    cliente=processo.cliente
                )
                
                return JsonResponse({
                    'success': True,
                    'process_id': processo.id,
                    'message': 'Processo criado com sucesso!'
                })
            else:
                return JsonResponse({
                    'success': False,
                    'errors': form.errors
                })
        else:
            # Regular form submission
            form = ProcessoForm(request.POST)
            if form.is_valid():
                processo = form.save()
                messages.success(request, 'Processo criado com sucesso!')
                return redirect('dashboard:processo_list')
    else:
        form = ProcessoForm()
    return render(request, 'dashboard/processo_form.html', {'form': form, 'title': 'Novo Processo'})

@login_required
def processo_update(request, pk):
    """Atualizar processo"""
    processo = get_object_or_404(Processo, pk=pk)
    if request.method == 'POST':
        # Check if it's an AJAX request
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or 'application/json' in request.META.get('HTTP_ACCEPT', ''):
            form = ProcessoForm(request.POST, instance=processo)
            if form.is_valid():
                form.save()
                
                # Criar atividade recente
                AtividadeRecente.objects.create(
                    tipo='processo_atualizado',
                    descricao=f'Processo atualizado: {processo.numero} - {processo.titulo}',
                    usuario=request.user,
                    processo=processo,
                    cliente=processo.cliente
                )
                
                return JsonResponse({
                    'success': True,
                    'message': 'Processo atualizado com sucesso!'
                })
            else:
                return JsonResponse({
                    'success': False,
                    'errors': form.errors
                })
        else:
            # Regular form submission
            form = ProcessoForm(request.POST, instance=processo)
            if form.is_valid():
                form.save()
                messages.success(request, 'Processo atualizado com sucesso!')
                return redirect('dashboard:processo_list')
    else:
        form = ProcessoForm(instance=processo)
    return render(request, 'dashboard/processo_form.html', {'form': form, 'title': 'Editar Processo'})

@login_required
def processo_detail(request, pk):
    """Detalhes do processo"""
    processo = get_object_or_404(Processo, pk=pk)
    
    # Check if it's an AJAX request
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or 'application/json' in request.META.get('HTTP_ACCEPT', ''):
        return JsonResponse({
            'success': True,
            'process': {
                'id': processo.id,
                'numero': processo.numero,
                'titulo': processo.titulo,
                'descricao': processo.descricao,
                'status': processo.status,
                'data_inicio': processo.data_inicio.strftime('%Y-%m-%d'),
                'data_fim': processo.data_fim.strftime('%Y-%m-%d') if processo.data_fim else None,
                'valor_causa': float(processo.valor_causa) if processo.valor_causa else None,
                'tribunal': processo.tribunal,
                'vara': processo.vara,
                'cliente_id': processo.cliente.id,
                'advogado_responsavel_id': processo.advogado_responsavel.id,
            }
        })
    
    return render(request, 'dashboard/processo_detail.html', {
        'processo': processo
    })

@login_required
def processo_delete(request, pk):
    """Deletar processo"""
    processo = get_object_or_404(Processo, pk=pk)
    if request.method == 'POST':
        processo.delete()
        messages.success(request, 'Processo excluído com sucesso!')
        return redirect('dashboard:processo_list')
    return render(request, 'dashboard/processo_confirm_delete.html', {'processo': processo})


# Views para Audiências
@login_required
def audiencia_list(request):
    """Lista de audiências"""
    audiencias = Audiencia.objects.select_related('processo').order_by('-data_hora')
    return render(request, 'dashboard/audiencia_list.html', {'audiencias': audiencias})

# Views para Clientes
from django.core.paginator import Paginator

@login_required
def cliente_list(request):
    """Lista de clientes"""
    clientes = Cliente.objects.all().order_by('nome')
    
    # Filtros
    search = request.GET.get('search')
    if search:
        clientes = clientes.filter(
            Q(nome__icontains=search) |
            Q(cpf_cnpj__icontains=search) |
            Q(email__icontains=search)
        )
    
    status = request.GET.get('status')
    if status == 'ativo':
        clientes = clientes.filter(ativo=True)
    elif status == 'inativo':
        clientes = clientes.filter(ativo=False)
    
    # Paginação
    page_size = request.GET.get('page_size', 15)
    try:
        page_size = int(page_size)
    except ValueError:
        page_size = 15
    
    paginator = Paginator(clientes, page_size)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Estatísticas para o dashboard
    active_clients_count = Cliente.objects.filter(ativo=True).count()
    clients_with_processes = Cliente.objects.filter(processo__isnull=False).distinct().count()
    
    # Novos clientes este mês
    today = timezone.now().date()
    inicio_mes = today.replace(day=1)
    new_clients_this_month = Cliente.objects.filter(
        data_cadastro__gte=inicio_mes,
        data_cadastro__lte=today
    ).count()
    
    # Obter todos os advogados para o modal de processo
    lawyers = Lawyer.objects.filter(is_active=True)
    
    return render(request, 'dashboard/clients.html', {
        'page_obj': page_obj,
        'page_size': page_size,
        'active_clients_count': active_clients_count,
        'clients_with_processes': clients_with_processes,
        'new_clients_this_month': new_clients_this_month,
        'lawyers': lawyers
    })

@login_required
def cliente_create(request):
    """Criar novo cliente"""
    if request.method == 'POST':
        # Check if it's an AJAX request
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or 'application/json' in request.META.get('HTTP_ACCEPT', ''):
            form = ClienteForm(request.POST)
            if form.is_valid():
                cliente = form.save()
                
                # Criar atividade recente
                AtividadeRecente.objects.create(
                    tipo='cliente_cadastrado',
                    descricao=f'Novo cliente cadastrado: {cliente.nome}',
                    usuario=request.user,
                    cliente=cliente
                )
                
                # Check if should create process automatically
                create_process = request.POST.get('create_process')
                if create_process == 'on':
                    # Get process data from request
                    process_numero = request.POST.get('process_numero')
                    process_titulo = request.POST.get('process_titulo')
                    process_descricao = request.POST.get('process_descricao')
                    
                    if process_numero and process_titulo and process_descricao:
                        try:
                            processo = Processo.objects.create(
                                numero=process_numero,
                                cliente=cliente,
                                advogado_responsavel=request.user,
                                titulo=process_titulo,
                                descricao=process_descricao,
                                status='ativo',
                                data_inicio=timezone.now().date()
                            )
                            
                            # Criar atividade recente para o processo
                            AtividadeRecente.objects.create(
                                tipo='processo_criado',
                                descricao=f'Processo criado automaticamente: {processo.numero} - {processo.titulo}',
                                usuario=request.user,
                                processo=processo,
                                cliente=cliente
                            )
                            
                            return JsonResponse({
                                'success': True,
                                'client_id': cliente.id,
                                'process_id': processo.id,
                                'message': 'Cliente e processo criados com sucesso!'
                            })
                        except Exception as e:
                            return JsonResponse({
                                'success': True,
                                'client_id': cliente.id,
                                'message': f'Cliente criado com sucesso, mas houve erro ao criar processo: {str(e)}'
                            })
                
                return JsonResponse({
                    'success': True,
                    'client_id': cliente.id,
                    'message': 'Cliente cadastrado com sucesso!'
                })
            else:
                return JsonResponse({
                    'success': False,
                    'errors': form.errors
                })
        else:
            # Regular form submission
            form = ClienteForm(request.POST)
            if form.is_valid():
                cliente = form.save()
                
                # Criar atividade recente
                AtividadeRecente.objects.create(
                    tipo='cliente_cadastrado',
                    descricao=f'Novo cliente cadastrado: {cliente.nome}',
                    usuario=request.user,
                    cliente=cliente
                )
                
                messages.success(request, 'Cliente cadastrado com sucesso!')
                return redirect('dashboard:clients')
    else:
        form = ClienteForm()
    
    return render(request, 'dashboard/client_form.html', {
        'form': form,
        'form_title': 'Novo Cliente',
        'button_text': 'Salvar'
    })

@login_required
def cliente_update(request, pk):
    """Atualizar cliente"""
    cliente = get_object_or_404(Cliente, pk=pk)
    
    if request.method == 'POST':
        # Check if it's an AJAX request
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or 'application/json' in request.META.get('HTTP_ACCEPT', ''):
            form = ClienteForm(request.POST, instance=cliente)
            if form.is_valid():
                form.save()
                return JsonResponse({
                    'success': True,
                    'message': 'Cliente atualizado com sucesso!'
                })
            else:
                return JsonResponse({
                    'success': False,
                    'errors': form.errors
                })
        else:
            # Regular form submission
            form = ClienteForm(request.POST, instance=cliente)
            if form.is_valid():
                form.save()
                messages.success(request, 'Cliente atualizado com sucesso!')
                return redirect('dashboard:clients')
    else:
        form = ClienteForm(instance=cliente)
    
    return render(request, 'dashboard/client_form.html', {
        'form': form,
        'form_title': 'Editar Cliente',
        'button_text': 'Salvar'
    })

@login_required
def cliente_detail(request, pk):
    """Detalhes do cliente"""
    cliente = get_object_or_404(Cliente, pk=pk)
    
    # Check if it's an AJAX request
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or 'application/json' in request.META.get('HTTP_ACCEPT', ''):
        # Get client processes
        processos = Processo.objects.filter(cliente=cliente).select_related('advogado_responsavel')
        processes_data = []
        for processo in processos:
            processes_data.append({
                'id': processo.id,
                'numero': processo.numero,
                'titulo': processo.titulo,
                'status': processo.status,
                'data_inicio': processo.data_inicio.strftime('%d/%m/%Y'),
                'advogado_responsavel': f"{processo.advogado_responsavel.first_name} {processo.advogado_responsavel.last_name}" if processo.advogado_responsavel else '-'
            })
        
        return JsonResponse({
            'success': True,
            'client': {
                'id': cliente.id,
                'nome': cliente.nome,
                'nome_mae': cliente.nome_mae,
                'cpf_cnpj': cliente.cpf_cnpj,
                'email': cliente.email,
                'telefone': cliente.telefone,
                'endereco': cliente.endereco,
                'cidade': cliente.cidade,
                'estado': cliente.estado,
                'ativo': cliente.ativo,
                'area_cliente_ativa': cliente.area_cliente_ativa,
                'data_cadastro': cliente.data_cadastro.strftime('%d/%m/%Y'),
            },
            'processes': processes_data
        })
    
    return render(request, 'dashboard/cliente_detail.html', {
        'cliente': cliente
    })

# Views para Advogados
@login_required
def advogado_list(request):
    """Lista de advogados"""
    advogados = Lawyer.objects.filter(is_active=True).order_by('username')
    
    # Paginação
    page_size = request.GET.get('page_size', 15)
    try:
        page_size = int(page_size)
    except ValueError:
        page_size = 15
    
    paginator = Paginator(advogados, page_size)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'dashboard/advogado_list.html', {
        'page_obj': page_obj,
        'page_size': page_size
    })

@login_required
def advogado_create(request):
    """Criar novo advogado"""
    if request.method == 'POST':
        form = AdvogadoForm(request.POST)
        if form.is_valid():
            lawyer = form.save()
            
            # Se login está ativado, criar usuário automaticamente
            if lawyer.enable_login:
                # O usuário já é criado pelo form.save(), mas podemos adicionar lógica adicional aqui se necessário
                pass
            
            # Se publicações estão ativadas, habilitar recebimento de publicações por e-mail
            if lawyer.enable_publications:
                # Esta lógica pode ser implementada em outras partes do sistema
                pass
                
            messages.success(request, 'Advogado cadastrado com sucesso!')
            return redirect('dashboard:advogado_list')
    else:
        form = AdvogadoForm()
    
    return render(request, 'dashboard/advogado_form.html', {
        'form': form,
        'title': 'Novo Advogado'
    })

@login_required
def advogado_update(request, pk):
    """Atualizar advogado"""
    lawyer = get_object_or_404(Lawyer, pk=pk)
    
    if request.method == 'POST':
        form = AdvogadoForm(request.POST, instance=lawyer)
        if form.is_valid():
            form.save()
            
            # Se login está ativado, garantir que o usuário esteja configurado corretamente
            if lawyer.enable_login:
                # O usuário já é atualizado pelo form.save(), mas podemos adicionar lógica adicional aqui se necessário
                pass
            
            # Se publicações estão ativadas, habilitar recebimento de publicações por e-mail
            if lawyer.enable_publications:
                # Esta lógica pode ser implementada em outras partes do sistema
                pass
                
            messages.success(request, 'Advogado atualizado com sucesso!')
            return redirect('dashboard:advogado_list')
    else:
        form = AdvogadoForm(instance=lawyer)
    
    return render(request, 'dashboard/advogado_form.html', {
        'form': form,
        'title': 'Editar Advogado'
    })

@login_required
def advogado_delete(request, pk):
    """Deletar advogado"""
    advogado = get_object_or_404(Lawyer, pk=pk)
    
    if request.method == 'POST':
        advogado.is_active = False
        advogado.save()
        messages.success(request, 'Advogado desativado com sucesso!')
        return redirect('dashboard:advogado_list')
    
    return render(request, 'dashboard/lawyer_confirm_delete.html', {'advogado': advogado})

@login_required
def advogado_detail(request, pk):
    """Detalhes do advogado"""
    lawyer = get_object_or_404(Lawyer, pk=pk)
    
    return render(request, 'dashboard/lawyer_detail.html', {
        'advogado': lawyer
    })

@login_required
def cliente_delete(request, pk):
    """Deletar cliente"""
    cliente = get_object_or_404(Cliente, pk=pk)
    
    if request.method == 'POST':
        # Always handle as AJAX since we're using modals now
        cliente.ativo = False
        cliente.save()
        
        # Criar atividade recente
        AtividadeRecente.objects.create(
            tipo='cliente_desativado',
            descricao=f'Cliente desativado: {cliente.nome}',
            usuario=request.user,
            cliente=cliente
        )
        
        return JsonResponse({'success': True, 'message': 'Cliente desativado com sucesso!'})
    
    return render(request, 'dashboard/client_confirm_delete.html', {'cliente': cliente})

@login_required
def client_financial_view(request, pk):
    """Visualizar informações financeiras do cliente"""
    cliente = get_object_or_404(Cliente, pk=pk)
    receitas = Receita.objects.filter(cliente=cliente).order_by('-data_vencimento')
    formas_pagamento = FormaPagamento.objects.filter(ativo=True)
    
    if request.method == 'POST':
        # Check if it's an AJAX request
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or 'application/json' in request.META.get('HTTP_ACCEPT', ''):
            try:
                # Get form data
                valor_total = request.POST.get('valor_total')
                data_pagamento = request.POST.get('data_pagamento')
                data_vencimento = request.POST.get('data_vencimento')
                forma_pagamento_id = request.POST.get('forma_pagamento')
                tipo_id = request.POST.get('tipo')
                banco_id = request.POST.get('banco')
                descricao = request.POST.get('descricao')
                observacoes = request.POST.get('observacoes')
                pago = request.POST.get('pago') == 'on'
                
                # Validate required fields
                if not valor_total or not forma_pagamento_id or not tipo_id:
                    return JsonResponse({
                        'success': False,
                        'message': 'Campos obrigatórios não preenchidos.'
                    })
                
                # Get related objects
                forma_pagamento = FormaPagamento.objects.get(id=forma_pagamento_id)
                tipo_receita = TipoReceita.objects.get(id=tipo_id)
                banco = None
                if banco_id:
                    banco = Banco.objects.get(id=banco_id)
                
                # Create receita
                receita = Receita.objects.create(
                    cliente=cliente,
                    descricao=descricao or 'Pagamento',
                    valor_total=valor_total,
                    data_vencimento=data_vencimento or timezone.now().date(),
                    data_recebimento=data_pagamento if pago else None,
                    forma_pagamento=forma_pagamento,
                    tipo=tipo_receita,
                    banco=banco,
                    observacoes=observacoes,
                    pago=pago
                )
                
                # Create activity log
                AtividadeRecente.objects.create(
                    tipo='recebimento_confirmado',
                    descricao=f'Nova receita adicionada para {cliente.nome}: R$ {valor_total}',
                    usuario=request.user,
                    cliente=cliente
                )
                
                return JsonResponse({
                    'success': True,
                    'message': 'Pagamento adicionado com sucesso!'
                })
                
            except Exception as e:
                return JsonResponse({
                    'success': False,
                    'message': f'Erro ao adicionar pagamento: {str(e)}'
                })
        else:
            # Traditional form submission
            valor_total = request.POST.get('valor_total')
            data_pagamento = request.POST.get('data_pagamento')
            data_vencimento = request.POST.get('data_vencimento')
            forma_pagamento_id = request.POST.get('forma_pagamento')
            descricao = request.POST.get('descricao')
            
            if valor_total and forma_pagamento_id:
                try:
                    forma_pagamento = FormaPagamento.objects.get(id=forma_pagamento_id)
                    Receita.objects.create(
                        cliente=cliente,
                        descricao=descricao or 'Pagamento',
                        valor_total=valor_total,
                        data_vencimento=data_vencimento or timezone.now().date(),
                        data_recebimento=data_pagamento or timezone.now().date(),
                        forma_pagamento=forma_pagamento,
                        tipo=TipoReceita.objects.first(),  # Tipo padrão
                        pago=True
                    )
                    messages.success(request, 'Pagamento adicionado com sucesso!')
                except Exception as e:
                    messages.error(request, 'Erro ao adicionar pagamento: ' + str(e))
        
        return redirect('dashboard:client_financial', pk=cliente.pk)
    
    # Calcular totais e informações financeiras
    total_receitas = sum(r.valor_total for r in receitas if r.pago)
    receitas_pagas = sum(r.valor_total for r in receitas if r.pago)
    receitas_pendentes = sum(r.valor_total for r in receitas if not r.pago)
    
    # Adicionar informações financeiras a cada receita
    receitas_data = []
    for receita in receitas:
        # Calcular saldo devedor
        receita.saldo_devedor = receita.valor_total - (receita.valor_recebido or 0)
        
        # Calcular percentual pago
        if receita.valor_total and receita.valor_total > 0:
            receita.percentual_pago = int(((receita.valor_recebido or 0) / receita.valor_total) * 100)
        else:
            receita.percentual_pago = 0
            
        # Verificar se está vencida
        receita.vencida = receita.data_vencimento < timezone.now().date() and not receita.pago
        
        # Prepare data for JSON response
        receitas_data.append({
            'id': receita.id,
            'descricao': receita.descricao,
            'valor_total': f"{receita.valor_total:.2f}".replace('.', ','),
            'data_vencimento': receita.data_vencimento.strftime('%d/%m/%Y'),
            'pago': receita.pago,
            'vencida': receita.vencida
        })
    
    # Check if it's an AJAX request for GET
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or 'application/json' in request.META.get('HTTP_ACCEPT', ''):
        return JsonResponse({
            'success': True,
            'client': {
                'id': cliente.id,
                'nome': cliente.nome
            },
            'receitas': receitas_data,
            'total_receitas': f"{total_receitas:.2f}".replace('.', ','),
            'receitas_pagas': f"{receitas_pagas:.2f}".replace('.', ','),
            'receitas_pendentes': f"{receitas_pendentes:.2f}".replace('.', ',')
        })
    
    return render(request, 'dashboard/client_financial.html', {
        'cliente': cliente,
        'receitas': receitas,
        'formas_pagamento': formas_pagamento,
        'total_receitas': total_receitas
    })

@login_required
def payment_edit_view(request, client_pk, payment_pk):
    """Editar pagamento"""
    cliente = get_object_or_404(Cliente, pk=client_pk)
    receita = get_object_or_404(Receita, pk=payment_pk, cliente=cliente)
    
    if request.method == 'POST':
        form = ReceitaForm(request.POST, instance=receita)
        if form.is_valid():
            form.save()
            messages.success(request, 'Pagamento atualizado com sucesso!')
            return redirect('dashboard:client_financial', pk=client_pk)
    else:
        form = ReceitaForm(instance=receita)
    
    return render(request, 'dashboard/payment_edit_form.html', {
        'form': form,
        'cliente': cliente,
        'receita': receita,
        'title': 'Editar Pagamento'
    })

@login_required
def payment_delete_view(request, client_pk, payment_pk):
    """Deletar pagamento"""
    cliente = get_object_or_404(Cliente, pk=client_pk)
    receita = get_object_or_404(Receita, pk=payment_pk, cliente=cliente)
    
    if request.method == 'POST':
        receita.delete()
        messages.success(request, 'Pagamento excluído com sucesso!')
        return redirect('dashboard:client_financial', pk=client_pk)
    
    return render(request, 'dashboard/payment_confirm_delete.html', {
        'cliente': cliente,
        'receita': receita
    })

# Views AJAX para o dashboard
@login_required
def get_dashboard_data(request):
    """API endpoint para dados do dashboard"""
    periodo = int(request.GET.get('periodo', 30))
    data_inicio = timezone.now() - timedelta(days=periodo)
    
    # Dados para gráficos
    data = {
        'processos_mes': list(Processo.objects.filter(
            data_inicio__gte=data_inicio
        ).values('status').annotate(count=Count('id'))),
        'receitas_despesas': {
            'receitas': float(Receita.objects.filter(
                data_vencimento__gte=data_inicio
            ).aggregate(total=Sum('valor_total'))['total'] or 0),
            'despesas': float(Despesa.objects.filter(
                data_vencimento__gte=data_inicio
            ).aggregate(total=Sum('valor'))['total'] or 0)
        }
    }
    
    return JsonResponse(data)

@login_required 
def calendar_events(request):
    """API para eventos do calendário"""
    start = request.GET.get('start')
    end = request.GET.get('end')
    
    events = []
    
    # Tarefas
    tasks = Task.objects.filter(
        data_inicio__range=[start, end]
    )
    
    for task in tasks:
        events.append({
            'id': f'task-{task.id}',
            'title': task.titulo,
            'start': task.data_inicio.isoformat(),
            'end': task.data_fim.isoformat() if task.data_fim else None,
            'allDay': task.dia_todo,
            'color': '#007bff',
            'url': f'/dashboard/tasks/{task.id}/'
        })
    
    # Audiências
    audiencias = Audiencia.objects.filter(
        data_hora__range=[start, end]
    )
    
    for audiencia in audiencias:
        events.append({
            'id': f'audiencia-{audiencia.id}',
            'title': f'Audiência - {audiencia.processo.titulo}',
            'start': audiencia.data_hora.isoformat(),
            'color': '#dc3545',
            'url': f'/dashboard/audiencias/{audiencia.id}/'
        })
    
    return JsonResponse(events, safe=False)

# Views para Audiências
@login_required
def audiencia_create(request):
    """Criar nova audiência"""
    if request.method == 'POST':
        # Check if it's an AJAX request
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or 'application/json' in request.META.get('HTTP_ACCEPT', ''):
            form = AudienciaForm(request.POST)
            if form.is_valid():
                audiencia = form.save()
                
                # Criar atividade recente
                AtividadeRecente.objects.create(
                    tipo='audiencia_agendada',
                    descricao=f'Audiência agendada: {audiencia.processo.titulo} - {audiencia.get_tipo_display()}',
                    usuario=request.user,
                    processo=audiencia.processo
                )
                
                return JsonResponse({
                    'success': True,
                    'audiencia_id': audiencia.id,
                    'message': 'Audiência agendada com sucesso!'
                })
            else:
                return JsonResponse({
                    'success': False,
                    'errors': form.errors
                })
        else:
            # Regular form submission
            form = AudienciaForm(request.POST)
            if form.is_valid():
                audiencia = form.save()
                
                # Criar atividade recente
                AtividadeRecente.objects.create(
                    tipo='audiencia_agendada',
                    descricao=f'Audiência agendada: {audiencia.processo.titulo} - {audiencia.get_tipo_display()}',
                    usuario=request.user,
                    processo=audiencia.processo
                )
                
                messages.success(request, 'Audiência agendada com sucesso!')
                return redirect('dashboard:home')
    else:
        form = AudienciaForm()
    
    return render(request, 'dashboard/audiencia_form.html', {'form': form, 'title': 'Agendar Audiência'})

@login_required
def audiencia_update(request, pk):
    """Atualizar audiência"""
    audiencia = get_object_or_404(Audiencia, pk=pk)
    
    if request.method == 'POST':
        form = AudienciaForm(request.POST, instance=audiencia)
        if form.is_valid():
            form.save()
            messages.success(request, 'Audiência atualizada com sucesso!')
            return redirect('dashboard:home')
    else:
        form = AudienciaForm(instance=audiencia)
    
    return render(request, 'dashboard/audiencia_form.html', {'form': form, 'title': 'Editar Audiência'})

@login_required
def audiencia_delete(request, pk):
    """Deletar audiência"""
    audiencia = get_object_or_404(Audiencia, pk=pk)
    
    if request.method == 'POST':
        audiencia.delete()
        messages.success(request, 'Audiência excluída com sucesso!')
        return redirect('dashboard:home')
    
    return render(request, 'dashboard/audiencia_confirm_delete.html', {'audiencia': audiencia})


@login_required
def activate_client_area(request, pk):
    """Ativar área do cliente"""
    cliente = get_object_or_404(Cliente, pk=pk)
    
    if request.method == 'POST':
        # Gerar senha aleatória
        import random
        import string
        senha = ''.join(random.choices(string.ascii_letters + string.digits, k=12))
        
        # Atualizar cliente
        cliente.area_cliente_ativa = True
        cliente.senha_area_cliente = senha  # Em produção, isso deve ser hasheado
        cliente.save()
        
        # Criar atividade recente
        AtividadeRecente.objects.create(
            tipo='cliente_area_ativada',
            descricao=f'Área do cliente ativada para: {cliente.nome}',
            usuario=request.user,
            cliente=cliente
        )
        
        messages.success(request, 'Área do cliente ativada com sucesso!')
        return redirect('dashboard:client_edit', pk=cliente.pk)
    
# Views para Receitas
from django.core.paginator import Paginator

@login_required
def receita_list(request):
    """Lista de receitas"""
    receitas = Receita.objects.all().order_by('-data_vencimento')
    
    # Filtros
    data_vencimento = request.GET.get('data_vencimento')
    cliente = request.GET.get('cliente')
    pago = request.GET.get('pago')
    pendente = request.GET.get('pendente')
    atrasado = request.GET.get('atrasado')
    tipo = request.GET.get('tipo')
    
    if data_vencimento:
        # Implementar filtro por data
        pass
    
    if cliente:
        receitas = receitas.filter(cliente_id=cliente)
    
    if pago:
        receitas = receitas.filter(pago=True if pago == '1' else False)
    
    if pendente:
        receitas = receitas.filter(pago=False)
    
    if atrasado:
        # Implementar filtro por atrasado
        pass
    
    if tipo:
        receitas = receitas.filter(tipo_id=tipo)
    
    # Paginação
    page_size = request.GET.get('page_size', 15)
    try:
        page_size = int(page_size)
    except ValueError:
        page_size = 15
    
    paginator = Paginator(receitas, page_size)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Dados para os filtros
    clientes = Cliente.objects.filter(ativo=True).order_by('nome')
    tipos_receita = TipoReceita.objects.all().order_by('nome')
    
    return render(request, 'dashboard/receitas.html', {
        'page_obj': page_obj,
        'page_size': page_size,
        'clientes': clientes,
        'tipos_receita': tipos_receita,
    })

@login_required
def receita_create(request):
    """Criar nova receita"""
    if request.method == 'POST':
        # Check if it's an AJAX request
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or 'application/json' in request.META.get('HTTP_ACCEPT', ''):
            form = ReceitaForm(request.POST)
            if form.is_valid():
                receita = form.save()
                
                # Criar atividade recente
                AtividadeRecente.objects.create(
                    tipo='receita_criada',
                    descricao=f'Nova receita lançada: {receita.descricao} - R$ {receita.valor_total}',
                    usuario=request.user,
                    cliente=receita.cliente
                )
                
                return JsonResponse({
                    'success': True,
                    'receita_id': receita.id,
                    'message': 'Receita cadastrada com sucesso!'
                })
            else:
                return JsonResponse({
                    'success': False,
                    'errors': form.errors
                })
        else:
            # Regular form submission
            form = ReceitaForm(request.POST)
            if form.is_valid():
                receita = form.save()
                messages.success(request, 'Receita cadastrada com sucesso!')
                return redirect('dashboard:receitas')
    else:
        form = ReceitaForm()
    
    return render(request, 'dashboard/receita_form.html', {
        'form': form,
    })

@login_required
def receita_update(request, pk):
    """Atualizar receita"""
    receita = get_object_or_404(Receita, pk=pk)
    
    if request.method == 'POST':
        form = ReceitaForm(request.POST, instance=receita)
        if form.is_valid():
            form.save()
            messages.success(request, 'Receita atualizada com sucesso!')
            return redirect('dashboard:receitas')
    else:
        form = ReceitaForm(instance=receita)
    
    return render(request, 'dashboard/receita_form.html', {
        'form': form,
    })

@login_required
def receita_delete(request, pk):
    """Deletar receita"""
    receita = get_object_or_404(Receita, pk=pk)
    
    if request.method == 'POST':
        receita.delete()
        messages.success(request, 'Receita excluída com sucesso!')
        return redirect('dashboard:receitas')
    
    return render(request, 'dashboard/receita_confirm_delete.html', {'receita': receita})

@login_required
def receita_pay(request, pk):
    """Baixar receita com suporte a pagamentos parciais"""
    receita = get_object_or_404(Receita, pk=pk)
    
    if request.method == 'POST':
        try:
            # Get form data
            valor_pagamento = Decimal(request.POST.get('valor_recebido', 0))
            data_recebimento = request.POST.get('data_recebimento')
            forma_pagamento_id = request.POST.get('forma_pagamento')
            banco_id = request.POST.get('banco')
            desconto = Decimal(request.POST.get('desconto', 0))
            
            # Calculate values
            valor_anterior = receita.valor_recebido or Decimal('0.00')
            novo_valor_recebido = valor_anterior + valor_pagamento
            valor_restante = receita.valor_total - novo_valor_recebido
            
            # Update receita
            receita.valor_recebido = novo_valor_recebido
            receita.data_recebimento = data_recebimento
            if forma_pagamento_id:
                receita.forma_pagamento_id = forma_pagamento_id
            if banco_id:
                receita.banco_id = banco_id
            receita.desconto = desconto
            
            # Determine payment status
            if valor_restante <= 0:
                receita.pago = True
                receita.parcial = False
                message = 'Receita quitada com sucesso!'
            else:
                receita.pago = False
                receita.parcial = True
                message = f'Pagamento parcial registrado. Restante: R$ {valor_restante:,.2f}'
            
            receita.save()
            
            # Create activity log
            AtividadeRecente.objects.create(
                tipo='recebimento_confirmado',
                descricao=f'Pagamento de R$ {valor_pagamento:,.2f} recebido de {receita.cliente.nome}',
                usuario=request.user,
                cliente=receita.cliente,
                processo=receita.processo
            )
            
            messages.success(request, message)
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': message,
                    'valor_restante': f'{valor_restante:,.2f}',
                    'quitado': receita.pago
                })
            
            return redirect('dashboard:receitas')
            
        except Exception as e:
            error_message = f'Erro ao processar pagamento: {str(e)}'
            messages.error(request, error_message)
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'message': error_message
                })
    else:
        # Formulário para baixar receita
        form = ReceitaForm(instance=receita)
    
    return render(request, 'dashboard/receita_pay.html', {
        'receita': receita,
        'form': form,
        'valor_restante': receita.valor_total - (receita.valor_recebido or Decimal('0.00'))
    })

@login_required
def receita_detail(request, pk):
    """Detalhes da receita"""
    receita = get_object_or_404(Receita, pk=pk)
    
    return render(request, 'dashboard/receita_detail.html', {
        'receita': receita,
    })
    return redirect('dashboard:client_edit', pk=cliente.pk)

# Views para TipoReceita
@login_required
def tipo_receita_list(request):
    """Lista de tipos de receita"""
    tipos_receita = TipoReceita.objects.all().order_by('nome')
    
    return render(request, 'dashboard/tipo_receita_list.html', {
        'tipos_receita': tipos_receita
    })

@login_required
def tipo_receita_create(request):
    """Criar novo tipo de receita"""
    if request.method == 'POST':
        form = TipoReceitaForm(request.POST)
        if form.is_valid():
            tipo_receita = form.save()
            messages.success(request, 'Tipo de receita cadastrado com sucesso!')
            return redirect('dashboard:tipo_receita_list')
    else:
        form = TipoReceitaForm()
    
    return render(request, 'dashboard/tipo_receita_form.html', {
        'form': form,
        'form_title': 'Novo Tipo de Receita',
        'button_text': 'Salvar'
    })

@login_required
def tipo_receita_update(request, pk):
    """Atualizar tipo de receita"""
    tipo_receita = get_object_or_404(TipoReceita, pk=pk)
    
    if request.method == 'POST':
        form = TipoReceitaForm(request.POST, instance=tipo_receita)
        if form.is_valid():
            form.save()
            messages.success(request, 'Tipo de receita atualizado com sucesso!')
            return redirect('dashboard:tipo_receita_list')
    else:
        form = TipoReceitaForm(instance=tipo_receita)
    
    return render(request, 'dashboard/tipo_receita_form.html', {
        'form': form,
        'form_title': 'Editar Tipo de Receita',
        'button_text': 'Salvar'
    })

@login_required
def tipo_receita_delete(request, pk):
    """Deletar tipo de receita"""
    tipo_receita = get_object_or_404(TipoReceita, pk=pk)
    
    if request.method == 'POST':
        tipo_receita.delete()
        messages.success(request, 'Tipo de receita excluído com sucesso!')
        return redirect('dashboard:tipo_receita_list')
    
    return render(request, 'dashboard/tipo_receita_confirm_delete.html', {'tipo_receita': tipo_receita})

# Views para TipoDespesa
@login_required
def tipo_despesa_list(request):
    """Lista de tipos de despesa"""
    tipos_despesa = TipoDespesa.objects.all().order_by('nome')
    
    return render(request, 'dashboard/tipo_despesa_list.html', {
        'tipos_despesa': tipos_despesa
    })

@login_required
def tipo_despesa_create(request):
    """Criar novo tipo de despesa"""
    if request.method == 'POST':
        form = TipoDespesaForm(request.POST)
        if form.is_valid():
            tipo_despesa = form.save()
            messages.success(request, 'Tipo de despesa cadastrado com sucesso!')
            return redirect('dashboard:tipo_despesa_list')
    else:
        form = TipoDespesaForm()
    
    return render(request, 'dashboard/tipo_despesa_form.html', {
        'form': form,
        'form_title': 'Novo Tipo de Despesa',
        'button_text': 'Salvar'
    })

@login_required
def tipo_despesa_update(request, pk):
    """Atualizar tipo de despesa"""
    tipo_despesa = get_object_or_404(TipoDespesa, pk=pk)
    
    if request.method == 'POST':
        form = TipoDespesaForm(request.POST, instance=tipo_despesa)
        if form.is_valid():
            form.save()
            messages.success(request, 'Tipo de despesa atualizado com sucesso!')
            return redirect('dashboard:tipo_despesa_list')
    else:
        form = TipoDespesaForm(instance=tipo_despesa)
    
    return render(request, 'dashboard/tipo_despesa_form.html', {
        'form': form,
        'form_title': 'Editar Tipo de Despesa',
        'button_text': 'Salvar'
    })

@login_required
def tipo_despesa_delete(request, pk):
    """Deletar tipo de despesa"""
    tipo_despesa = get_object_or_404(TipoDespesa, pk=pk)
    
    if request.method == 'POST':
        tipo_despesa.delete()
        messages.success(request, 'Tipo de despesa excluído com sucesso!')
        return redirect('dashboard:tipo_despesa_list')
    
    return render(request, 'dashboard/tipo_despesa_confirm_delete.html', {'tipo_despesa': tipo_despesa})

# Views para FormaPagamento
@login_required
def forma_pagamento_list(request):
    """Lista de formas de pagamento"""
    formas_pagamento = FormaPagamento.objects.all().order_by('nome')
    
    return render(request, 'dashboard/forma_pagamento_list.html', {
        'formas_pagamento': formas_pagamento
    })

@login_required
def forma_pagamento_create(request):
    """Criar nova forma de pagamento"""
    if request.method == 'POST':
        form = FormaPagamentoForm(request.POST)
        if form.is_valid():
            forma_pagamento = form.save()
            messages.success(request, 'Forma de pagamento cadastrada com sucesso!')
            return redirect('dashboard:forma_pagamento_list')
    else:
        form = FormaPagamentoForm()
    
    return render(request, 'dashboard/forma_pagamento_form.html', {
        'form': form,
        'form_title': 'Nova Forma de Pagamento',
        'button_text': 'Salvar'
    })

@login_required
def forma_pagamento_update(request, pk):
    """Atualizar forma de pagamento"""
    forma_pagamento = get_object_or_404(FormaPagamento, pk=pk)
    
    if request.method == 'POST':
        form = FormaPagamentoForm(request.POST, instance=forma_pagamento)
        if form.is_valid():
            form.save()
            messages.success(request, 'Forma de pagamento atualizada com sucesso!')
            return redirect('dashboard:forma_pagamento_list')
    else:
        form = FormaPagamentoForm(instance=forma_pagamento)
    
    return render(request, 'dashboard/forma_pagamento_form.html', {
        'form': form,
        'form_title': 'Editar Forma de Pagamento',
        'button_text': 'Salvar'
    })

@login_required
def forma_pagamento_delete(request, pk):
    """Deletar forma de pagamento"""
    forma_pagamento = get_object_or_404(FormaPagamento, pk=pk)
    
    if request.method == 'POST':
        forma_pagamento.delete()
        messages.success(request, 'Forma de pagamento excluída com sucesso!')
        return redirect('dashboard:forma_pagamento_list')
    
    return render(request, 'dashboard/forma_pagamento_confirm_delete.html', {'forma_pagamento': forma_pagamento})

# Views para Banco
@login_required
def banco_list(request):
    """Lista de bancos"""
    bancos = Banco.objects.all().order_by('nome')
    
    return render(request, 'dashboard/banco_list.html', {
        'bancos': bancos
    })

@login_required
def banco_create(request):
    """Criar novo banco"""
    if request.method == 'POST':
        form = BancoForm(request.POST)
        if form.is_valid():
            banco = form.save()
            messages.success(request, 'Banco cadastrado com sucesso!')
            return redirect('dashboard:banco_list')
    else:
        form = BancoForm()
    
    return render(request, 'dashboard/banco_form.html', {
        'form': form,
        'form_title': 'Novo Banco',
        'button_text': 'Salvar'
    })

@login_required
def banco_update(request, pk):
    """Atualizar banco"""
    banco = get_object_or_404(Banco, pk=pk)
    
    if request.method == 'POST':
        form = BancoForm(request.POST, instance=banco)
        if form.is_valid():
            form.save()
            messages.success(request, 'Banco atualizado com sucesso!')
            return redirect('dashboard:banco_list')
    else:
        form = BancoForm(instance=banco)
    
    return render(request, 'dashboard/banco_form.html', {
        'form': form,
        'form_title': 'Editar Banco',
        'button_text': 'Salvar'
    })

@login_required
def banco_delete(request, pk):
    """Deletar banco"""
    banco = get_object_or_404(Banco, pk=pk)
    
    if request.method == 'POST':
        banco.delete()
        messages.success(request, 'Banco excluído com sucesso!')
        return redirect('dashboard:banco_list')
    
    return render(request, 'dashboard/banco_confirm_delete.html', {'banco': banco})

# Views para PrazoPagamento
@login_required
def prazo_pagamento_list(request):
    """Lista de prazos de pagamento"""
    prazos_pagamento = PrazoPagamento.objects.all().order_by('nome')
    
    return render(request, 'dashboard/prazo_pagamento_list.html', {
        'prazos_pagamento': prazos_pagamento
    })

@login_required
def prazo_pagamento_create(request):
    """Criar novo prazo de pagamento"""
    if request.method == 'POST':
        form = PrazoPagamentoForm(request.POST)
        if form.is_valid():
            prazo_pagamento = form.save()
            messages.success(request, 'Prazo de pagamento cadastrado com sucesso!')
            return redirect('dashboard:prazo_pagamento_list')
    else:
        form = PrazoPagamentoForm()
    
    return render(request, 'dashboard/prazo_pagamento_form.html', {
        'form': form,
        'form_title': 'Novo Prazo de Pagamento',
        'button_text': 'Salvar'
    })

@login_required
def prazo_pagamento_update(request, pk):
    """Atualizar prazo de pagamento"""
    prazo_pagamento = get_object_or_404(PrazoPagamento, pk=pk)
    
    if request.method == 'POST':
        form = PrazoPagamentoForm(request.POST, instance=prazo_pagamento)
        if form.is_valid():
            form.save()
            messages.success(request, 'Prazo de pagamento atualizado com sucesso!')
            return redirect('dashboard:prazo_pagamento_list')
    else:
        form = PrazoPagamentoForm(instance=prazo_pagamento)
    
    return render(request, 'dashboard/prazo_pagamento_form.html', {
        'form': form,
        'form_title': 'Editar Prazo de Pagamento',
        'button_text': 'Salvar'
    })

@login_required
def prazo_pagamento_delete(request, pk):
    """Deletar prazo de pagamento"""
    prazo_pagamento = get_object_or_404(PrazoPagamento, pk=pk)
    
    if request.method == 'POST':
        prazo_pagamento.delete()
        messages.success(request, 'Prazo de pagamento excluído com sucesso!')
        return redirect('dashboard:prazo_pagamento_list')
    
    return render(request, 'dashboard/prazo_pagamento_confirm_delete.html', {'prazo_pagamento': prazo_pagamento})

# Views para TipoDemanda
@login_required
def tipo_demanda_list(request):
    """Lista de tipos de demanda"""
    tipos_demanda = TipoDemanda.objects.all().order_by('nome')
    
    return render(request, 'dashboard/tipo_demanda_list.html', {
        'tipos_demanda': tipos_demanda
    })

@login_required
def tipo_demanda_create(request):
    """Criar novo tipo de demanda"""
    if request.method == 'POST':
        form = TipoDemandaForm(request.POST)
        if form.is_valid():
            tipo_demanda = form.save()
            messages.success(request, 'Tipo de demanda cadastrado com sucesso!')
            return redirect('dashboard:tipo_demanda_list')
    else:
        form = TipoDemandaForm()
    
    return render(request, 'dashboard/tipo_demanda_form.html', {
        'form': form,
        'form_title': 'Novo Tipo de Demanda',
        'button_text': 'Salvar'
    })

@login_required
def tipo_demanda_update(request, pk):
    """Atualizar tipo de demanda"""
    tipo_demanda = get_object_or_404(TipoDemanda, pk=pk)
    
    if request.method == 'POST':
        form = TipoDemandaForm(request.POST, instance=tipo_demanda)
        if form.is_valid():
            form.save()
            messages.success(request, 'Tipo de demanda atualizado com sucesso!')
            return redirect('dashboard:tipo_demanda_list')
    else:
        form = TipoDemandaForm(instance=tipo_demanda)
    
    return render(request, 'dashboard/tipo_demanda_form.html', {
        'form': form,
        'form_title': 'Editar Tipo de Demanda',
        'button_text': 'Salvar'
    })

@login_required
def tipo_demanda_delete(request, pk):
    """Deletar tipo de demanda"""
    tipo_demanda = get_object_or_404(TipoDemanda, pk=pk)
    
    if request.method == 'POST':
        tipo_demanda.delete()
        messages.success(request, 'Tipo de demanda excluído com sucesso!')
        return redirect('dashboard:tipo_demanda_list')
    
    return render(request, 'dashboard/tipo_demanda_confirm_delete.html', {'tipo_demanda': tipo_demanda})

@login_required
def client_processes(request, pk):
    """API endpoint para buscar processos de um cliente"""
    cliente = get_object_or_404(Cliente, pk=pk)
    processos = Processo.objects.filter(cliente=cliente).select_related('advogado_responsavel')
    
    processes_data = []
    for processo in processos:
        processes_data.append({
            'id': processo.id,
            'numero': processo.numero,
            'titulo': processo.titulo,
            'status': processo.status,
            'data_inicio': processo.data_inicio.strftime('%d/%m/%Y'),
            'advogado_responsavel': f"{processo.advogado_responsavel.first_name} {processo.advogado_responsavel.last_name}" if processo.advogado_responsavel else '-'
        })
    
    return JsonResponse({
        'processes': processes_data,
        'client_name': cliente.nome
    })

@login_required
def get_payment_options(request):
    """Get payment form options for AJAX requests"""
    try:
        tipos_receita = TipoReceita.objects.all()
        formas_pagamento = FormaPagamento.objects.filter(ativo=True)
        bancos = Banco.objects.filter(ativo=True)
        
        return JsonResponse({
            'success': True,
            'tipos_receita': [{'id': t.id, 'nome': t.nome} for t in tipos_receita],
            'formas_pagamento': [{'id': f.id, 'nome': f.nome} for f in formas_pagamento],
            'bancos': [{'id': b.id, 'nome': b.nome} for b in bancos]
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erro ao carregar opções: {str(e)}'
        })

# AJAX helper views for modals
@login_required
def get_clientes_ajax(request):
    """Retorna lista de clientes ativos em JSON para os selects dos modais"""
    clientes = Cliente.objects.filter(ativo=True).values('id', 'nome')
    return JsonResponse(list(clientes), safe=False)

@login_required
def get_processos_ajax(request):
    """Retorna lista de processos ativos em JSON para os selects dos modais"""
    processos = Processo.objects.filter(status='ativo').values('id', 'numero', 'titulo', 'cliente__nome')
    return JsonResponse(list(processos), safe=False)

@login_required
def get_formas_pagamento_ajax(request):
    """Retorna lista de formas de pagamento ativas em JSON para os selects dos modais"""
    try:
        formas_pagamento = FormaPagamento.objects.filter(ativo=True).values('id', 'nome').order_by('nome')
        return JsonResponse({
            'success': True,
            'formas_pagamento': list(formas_pagamento)
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erro ao carregar formas de pagamento: {str(e)}'
        })

# Views específicas para o novo sistema de clientes
@login_required
def client_edit(request, pk):
    """Editar cliente via AJAX"""
    cliente = get_object_or_404(Cliente, pk=pk)
    
    if request.method == 'POST':
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            form = ClienteForm(request.POST, instance=cliente)
            if form.is_valid():
                form.save()
                
                # Criar atividade recente
                AtividadeRecente.objects.create(
                    tipo='cliente_atualizado',
                    descricao=f'Cliente atualizado: {cliente.nome}',
                    usuario=request.user,
                    cliente=cliente
                )
                
                return JsonResponse({
                    'success': True,
                    'message': 'Cliente atualizado com sucesso!'
                })
            else:
                return JsonResponse({
                    'success': False,
                    'errors': form.errors
                })
    
    return JsonResponse({'success': False, 'message': 'Método não permitido'})

@login_required
def client_financial(request, pk):
    """Retornar informações financeiras do cliente via AJAX"""
    cliente = get_object_or_404(Cliente, pk=pk)
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            # Buscar receitas do cliente
            receitas = Receita.objects.filter(cliente=cliente).order_by('-data_vencimento')
            
            # Calcular totais considerando pagamentos parciais
            total_receitas = receitas.aggregate(total=Sum('valor_total'))['total'] or Decimal('0.00')
            total_recebido = Decimal('0.00')
            total_restante = Decimal('0.00')
            
            for receita in receitas:
                valor_recebido = receita.valor_recebido or Decimal('0.00')
                total_recebido += valor_recebido
                if not receita.pago:
                    total_restante += (receita.valor_total - valor_recebido)
            
            # Preparar dados das receitas
            receitas_data = []
            for receita in receitas:
                valor_recebido = receita.valor_recebido or Decimal('0.00')
                valor_restante = receita.valor_total - valor_recebido
                
                # Determinar status
                if receita.pago:
                    status = 'Pago'
                    status_class = 'success'
                elif receita.parcial or valor_recebido > 0:
                    status = 'Parcial'
                    status_class = 'warning'
                else:
                    status = 'Pendente'
                    status_class = 'danger'
                
                receitas_data.append({
                    'id': receita.id,
                    'descricao': receita.descricao,
                    'valor_total': f"{receita.valor_total:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'),
                    'valor_recebido': f"{valor_recebido:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'),
                    'valor_restante': f"{valor_restante:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'),
                    'data_vencimento': receita.data_vencimento.strftime('%d/%m/%Y') if receita.data_vencimento else '-',
                    'data_recebimento': receita.data_recebimento.strftime('%d/%m/%Y') if receita.data_recebimento else '-',
                    'pago': receita.pago,
                    'parcial': receita.parcial,
                    'status': status,
                    'status_class': status_class,
                    'processo': receita.processo.numero if receita.processo else '-',
                    'forma_pagamento': receita.forma_pagamento.nome if receita.forma_pagamento else '-'
                })
            
            return JsonResponse({
                'success': True,
                'cliente': cliente.nome,
                'total_receitas': f"{total_receitas:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'),
                'total_recebido': f"{total_recebido:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'),
                'total_restante': f"{total_restante:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'),
                'receitas': receitas_data
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Erro ao carregar informações financeiras: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'message': 'Requisição inválida'})

@login_required
def add_partial_payment(request, receita_pk):
    """Adicionar pagamento parcial a uma receita"""
    receita = get_object_or_404(Receita, pk=receita_pk)
    
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            # Get form data
            valor_pagamento = Decimal(request.POST.get('valor_pagamento', 0))
            data_pagamento = request.POST.get('data_pagamento')
            forma_pagamento_id = request.POST.get('forma_pagamento')
            banco_id = request.POST.get('banco')
            observacoes = request.POST.get('observacoes', '')
            
            # Validate amount
            valor_anterior = receita.valor_recebido or Decimal('0.00')
            valor_restante = receita.valor_total - valor_anterior
            
            if valor_pagamento <= 0:
                return JsonResponse({
                    'success': False,
                    'message': 'O valor do pagamento deve ser maior que zero.'
                })
            
            if valor_pagamento > valor_restante:
                return JsonResponse({
                    'success': False,
                    'message': f'O valor do pagamento (R$ {valor_pagamento:,.2f}) não pode ser maior que o valor restante (R$ {valor_restante:,.2f}).'
                })
            
            # Calculate new values
            novo_valor_recebido = valor_anterior + valor_pagamento
            novo_valor_restante = receita.valor_total - novo_valor_recebido
            
            # Update receita
            receita.valor_recebido = novo_valor_recebido
            receita.data_recebimento = data_pagamento if data_pagamento else timezone.now().date()
            
            if forma_pagamento_id:
                receita.forma_pagamento_id = forma_pagamento_id
            if banco_id:
                receita.banco_id = banco_id
                
            # Add to observations
            if observacoes:
                if receita.observacoes:
                    receita.observacoes += f'\n\n[{timezone.now().strftime("%d/%m/%Y")}] {observacoes}'
                else:
                    receita.observacoes = f'[{timezone.now().strftime("%d/%m/%Y")}] {observacoes}'
            
            # Determine payment status
            if novo_valor_restante <= 0:
                receita.pago = True
                receita.parcial = False
                message = f'Receita quitada com pagamento de R$ {valor_pagamento:,.2f}!'
            else:
                receita.pago = False
                receita.parcial = True
                message = f'Pagamento parcial de R$ {valor_pagamento:,.2f} registrado. Restante: R$ {novo_valor_restante:,.2f}'
            
            receita.save()
            
            # Create activity log
            AtividadeRecente.objects.create(
                tipo='recebimento_confirmado',
                descricao=f'Pagamento parcial de R$ {valor_pagamento:,.2f} recebido de {receita.cliente.nome}',
                usuario=request.user,
                cliente=receita.cliente,
                processo=receita.processo
            )
            
            return JsonResponse({
                'success': True,
                'message': message,
                'novo_valor_recebido': f'{novo_valor_recebido:,.2f}',
                'novo_valor_restante': f'{novo_valor_restante:,.2f}',
                'quitado': receita.pago
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Erro ao processar pagamento: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'message': 'Método não permitido'})

@login_required 
def activate_client_area(request, pk):
    """Ativar área do cliente e gerar senha"""
    cliente = get_object_or_404(Cliente, pk=pk)
    
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            import secrets
            import string
            
            # Gerar senha aleatória
            alphabet = string.ascii_letters + string.digits
            password = ''.join(secrets.choice(alphabet) for i in range(8))
            
            # Ativar área do cliente
            cliente.area_cliente_ativa = True
            cliente.senha_area_cliente = password  # Assumindo que este campo existe
            cliente.save()
            
            # Criar atividade recente
            AtividadeRecente.objects.create(
                tipo='area_cliente_ativada',
                descricao=f'Área do cliente ativada: {cliente.nome}',
                usuario=request.user,
                cliente=cliente
            )
            
            return JsonResponse({
                'success': True,
                'cpf': cliente.cpf_cnpj,
                'password': password,
                'message': 'Área do cliente ativada com sucesso!'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Erro ao ativar área do cliente: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'message': 'Método não permitido'})

# Views para Processos
@login_required
def processo_list(request):
    """Lista de processos"""
    processos = Processo.objects.all().select_related('cliente', 'advogado_responsavel').order_by('-data_inicio')
    return render(request, 'dashboard/processo_list.html', {'processos': processos})

@login_required
def processo_create(request):
    """Criar novo processo"""
    if request.method == 'POST':
        # Check if it's an AJAX request
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            form = ProcessoForm(request.POST)
            if form.is_valid():
                processo = form.save(commit=False)
                processo.advogado_responsavel = request.user
                processo.save()
                
                # Criar atividade recente
                AtividadeRecente.objects.create(
                    tipo='processo_criado',
                    descricao=f'Novo processo criado: {processo.numero} - {processo.titulo}',
                    usuario=request.user,
                    processo=processo,
                    cliente=processo.cliente
                )
                
                return JsonResponse({
                    'success': True,
                    'process_id': processo.id,
                    'message': 'Processo criado com sucesso!'
                })
            else:
                return JsonResponse({
                    'success': False,
                    'errors': form.errors
                })
        else:
            # Regular form submission
            form = ProcessoForm(request.POST)
            if form.is_valid():
                processo = form.save(commit=False)
                processo.advogado_responsavel = request.user
                processo.save()
                
                # Criar atividade recente
                AtividadeRecente.objects.create(
                    tipo='processo_criado',
                    descricao=f'Novo processo criado: {processo.numero} - {processo.titulo}',
                    usuario=request.user,
                    processo=processo,
                    cliente=processo.cliente
                )
                
                messages.success(request, 'Processo criado com sucesso!')
                return redirect('dashboard:processo_list')
    else:
        form = ProcessoForm()
    
    return render(request, 'dashboard/processo_form.html', {'form': form})

@login_required
def processo_update(request, pk):
    """Atualizar processo"""
    processo = get_object_or_404(Processo, pk=pk)
    
    if request.method == 'POST':
        form = ProcessoForm(request.POST, instance=processo)
        if form.is_valid():
            form.save()
            
            # Criar atividade recente
            AtividadeRecente.objects.create(
                tipo='processo_atualizado',
                descricao=f'Processo atualizado: {processo.numero}',
                usuario=request.user,
                processo=processo,
                cliente=processo.cliente
            )
            
            messages.success(request, 'Processo atualizado com sucesso!')
            return redirect('dashboard:processo_list')
    else:
        form = ProcessoForm(instance=processo)
    
    return render(request, 'dashboard/processo_form.html', {'form': form, 'processo': processo})

@login_required
def processo_detail(request, pk):
    """Detalhes do processo"""
    processo = get_object_or_404(Processo, pk=pk)
    return render(request, 'dashboard/processo_detail.html', {'processo': processo})

@login_required
def processo_delete(request, pk):
    """Deletar processo"""
    processo = get_object_or_404(Processo, pk=pk)
    
    if request.method == 'POST':
        processo.status = 'arquivado'
        processo.save()
        
        # Criar atividade recente
        AtividadeRecente.objects.create(
            tipo='processo_arquivado',
            descricao=f'Processo arquivado: {processo.numero}',
            usuario=request.user,
            processo=processo,
            cliente=processo.cliente
        )
        
        messages.success(request, 'Processo arquivado com sucesso!')
        return redirect('dashboard:processo_list')
    
    return render(request, 'dashboard/confirm_delete.html', {
        'object': processo,
        'object_name': 'processo'
    })

# View para audiências que estava faltando 
@login_required
def audiencia_create(request):
    """Criar nova audiência"""
    if request.method == 'POST':
        # Check if it's an AJAX request
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            form = AudienciaForm(request.POST)
            if form.is_valid():
                audiencia = form.save()
                
                # Criar atividade recente
                AtividadeRecente.objects.create(
                    tipo='audiencia_agendada',
                    descricao=f'Audiência agendada: {audiencia.processo.numero} - {audiencia.get_tipo_display()}',
                    usuario=request.user,
                    processo=audiencia.processo,
                    cliente=audiencia.processo.cliente
                )
                
                return JsonResponse({
                    'success': True,
                    'audiencia_id': audiencia.id,
                    'message': 'Audiência agendada com sucesso!'
                })
            else:
                return JsonResponse({
                    'success': False,
                    'errors': form.errors
                })
        else:
            # Regular form submission
            form = AudienciaForm(request.POST)
            if form.is_valid():
                audiencia = form.save()
                
                # Criar atividade recente
                AtividadeRecente.objects.create(
                    tipo='audiencia_agendada',
                    descricao=f'Audiência agendada: {audiencia.processo.numero} - {audiencia.get_tipo_display()}',
                    usuario=request.user,
                    processo=audiencia.processo,
                    cliente=audiencia.processo.cliente
                )
                
                messages.success(request, 'Audiência agendada com sucesso!')
                return redirect('dashboard:audiencia_list')
    else:
        form = AudienciaForm()
    
    return render(request, 'dashboard/audiencia_form.html', {'form': form})
