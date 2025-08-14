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
    FormaPagamento, Banco
)
from users.models import Lawyer
from .forms import (
    TaskForm, ClienteForm, AdvogadoForm, ProcessoForm, 
    AudienciaForm, ReceitaForm, DespesaForm, DashboardFilterForm
)

@login_required
def dashboard_view(request):
    """View principal do dashboard com métricas e dados"""
    
    # Verificar se o usuário tem perfil de advogado
    try:
        advogado = request.user
    except:
        # Se não tem perfil de advogado, criar um básico ou redirecionar
        messages.warning(request, 'Perfil de advogado não encontrado. Entre em contato com o administrador.')
        # Você pode criar um advogado básico ou redirecionar para uma página de configuração
    
    # Filtros
    periodo = int(request.GET.get('periodo', 30))
    data_inicio = timezone.now() - timedelta(days=periodo)
    
    # Métricas principais
    total_clientes = Cliente.objects.filter(ativo=True).count()
    total_processos = Processo.objects.count()
    
    # Tarefas
    tarefas_pendentes = Task.objects.filter(
        status='pendente',
        data_inicio__gte=data_inicio
    ).count()
    
    # Audiências pendentes
    audiencias_pendentes = Audiencia.objects.filter(
        data_hora__gte=timezone.now(),
        data_hora__lte=timezone.now() + timedelta(days=30)
    ).count()
    
    # Publicações não lidas
    publicacoes_nao_lidas = Publicacao.objects.filter(
        lida=False,
        data_publicacao__gte=data_inicio
    ).count()
    
    # Financeiro do mês
    hoje = timezone.now().date()
    inicio_mes = hoje.replace(day=1)
    
    receitas_mes = Receita.objects.filter(
        data_vencimento__gte=inicio_mes,
        data_vencimento__lte=hoje
    ).aggregate(total=Sum('valor_total'))['total'] or Decimal('0.00')
    
    despesas_mes = Despesa.objects.filter(
        data_vencimento__gte=inicio_mes,
        data_vencimento__lte=hoje
    ).aggregate(total=Sum('valor'))['total'] or Decimal('0.00')
    
    saldo_mes = receitas_mes - despesas_mes
    
    # Clientes ativos (novos no período)
    clientes_novos = Cliente.objects.filter(
        data_cadastro__gte=data_inicio,
        ativo=True
    ).count()
    
    # Atividades recentes
    atividades_recentes = AtividadeRecente.objects.select_related(
        'usuario', 'cliente', 'processo'
    )[:10]
    
    # Próximas audiências
    proximas_audiencias = Audiencia.objects.filter(
        data_hora__gte=timezone.now()
    ).select_related('processo', 'processo__cliente').order_by('data_hora')[:5]
    
    # Tarefas urgentes
    tarefas_urgentes = Task.objects.filter(
        status__in=['pendente', 'em_andamento'],
        prioridade__in=['alta', 'urgente'],
        data_inicio__lte=timezone.now() + timedelta(days=7)
    ).select_related('cliente', 'processo')[:5]
    
    # Estatísticas para gráficos
    processos_por_status = Processo.objects.values('status').annotate(
        count=Count('id')
    )
    
    context = {
        'total_clientes': total_clientes,
        'total_processos': total_processos,
        'tarefas_pendentes': tarefas_pendentes,
        'audiencias_pendentes': audiencias_pendentes,
        'publicacoes_nao_lidas': publicacoes_nao_lidas,
        'receitas_mes': receitas_mes,
        'despesas_mes': despesas_mes,
        'saldo_mes': saldo_mes,
        'clientes_novos': clientes_novos,
        'atividades_recentes': atividades_recentes,
        'proximas_audiencias': proximas_audiencias,
        'tarefas_urgentes': tarefas_urgentes,
        'processos_por_status': list(processos_por_status),
        'filter_form': DashboardFilterForm(request.GET),
    }
    
    return render(request, 'dashboard/dashboard.html', context)

@login_required
def task_list(request):
    """Lista de tarefas"""
    tasks = Task.objects.select_related('cliente', 'processo', 'advogado').order_by('-data_inicio')
    
    # Filtros
    status = request.GET.get('status')
    if status:
        tasks = tasks.filter(status=status)
    
    prioridade = request.GET.get('prioridade')
    if prioridade:
        tasks = tasks.filter(prioridade=prioridade)
    
    return render(request, 'dashboard/task_list.html', {'tasks': tasks})

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

# Views para Clientes
from django.core.paginator import Paginator

@login_required
def cliente_list(request):
    """Lista de clientes"""
    clientes = Cliente.objects.filter(ativo=True).order_by('nome')
    
    # Busca
    search = request.GET.get('search')
    if search:
        clientes = clientes.filter(
            Q(nome__icontains=search) |
            Q(cpf_cnpj__icontains=search) |
            Q(email__icontains=search)
        )
    
    # Paginação
    page_size = request.GET.get('page_size', 15)
    try:
        page_size = int(page_size)
    except ValueError:
        page_size = 15
    
    paginator = Paginator(clientes, page_size)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'dashboard/clients.html', {
        'page_obj': page_obj,
        'page_size': page_size
    })

@login_required
def cliente_create(request):
    """Criar novo cliente"""
    if request.method == 'POST':
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
        # Marcar como inativo em vez de deletar
        cliente.ativo = False
        cliente.save()
        messages.success(request, 'Cliente desativado com sucesso!')
        return redirect('dashboard:clients')
    
    return render(request, 'dashboard/client_confirm_delete.html', {'cliente': cliente})

@login_required
def client_financial_view(request, pk):
    """Visualizar informações financeiras do cliente"""
    cliente = get_object_or_404(Cliente, pk=pk)
    receitas = Receita.objects.filter(cliente=cliente).order_by('-data_vencimento')
    formas_pagamento = FormaPagamento.objects.filter(ativo=True)
    
    if request.method == 'POST':
        # Adicionar novo pagamento
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
    
    # Adicionar informações financeiras a cada receita
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
    """Baixar receita"""
    receita = get_object_or_404(Receita, pk=pk)
    
    if request.method == 'POST':
        # Processar o pagamento
        receita.pago = True
        receita.data_recebimento = request.POST.get('data_recebimento')
        receita.forma_pagamento_id = request.POST.get('forma_pagamento')
        receita.banco_id = request.POST.get('banco')
        receita.parcial = request.POST.get('parcial') == 'on'
        receita.desconto = request.POST.get('desconto', 0)
        receita.valor_recebido = request.POST.get('valor_recebido')
        receita.save()
        
        messages.success(request, 'Receita baixada com sucesso!')
        return redirect('dashboard:receitas')
    else:
        # Formulário para baixar receita
        form = ReceitaForm(instance=receita)
    
    return render(request, 'dashboard/receita_pay.html', {
        'receita': receita,
        'form': form,
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