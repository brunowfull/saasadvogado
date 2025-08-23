from django.db import models
from django.utils import timezone
from decimal import Decimal
from users.models import Lawyer

class Cliente(models.Model):
    nome = models.CharField(max_length=200, verbose_name="Nome")
    nome_mae = models.CharField(max_length=200, blank=True, null=True, verbose_name="Nome da Mãe")
    cpf_cnpj = models.CharField(max_length=20, unique=True, verbose_name="CPF/CNPJ")
    email = models.EmailField(verbose_name="E-mail")
    telefone = models.CharField(max_length=20, verbose_name="Telefone")
    endereco = models.TextField(blank=True, null=True, verbose_name="Endereço")
    cidade = models.CharField(max_length=100, blank=True, null=True, verbose_name="Cidade")
    estado = models.CharField(max_length=2, blank=True, null=True, verbose_name="Estado")
    data_cadastro = models.DateTimeField(auto_now_add=True, verbose_name="Data de Cadastro")
    ativo = models.BooleanField(default=True, verbose_name="Ativo")
    area_cliente_ativa = models.BooleanField(default=False, verbose_name="Área do Cliente Ativa")
    senha_area_cliente = models.CharField(max_length=128, blank=True, null=True, verbose_name="Senha da Área do Cliente")
    
    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"
        ordering = ['-data_cadastro']
    
    def __str__(self):
        return self.nome


class TipoReceita(models.Model):
    nome = models.CharField(max_length=100, verbose_name="Nome")
    descricao = models.TextField(blank=True, null=True, verbose_name="Descrição")
    data_cadastro = models.DateTimeField(default=timezone.now, verbose_name="Data de Cadastro")
    
    class Meta:
        verbose_name = "Tipo de Receita"
        verbose_name_plural = "Tipos de Receita"
        ordering = ['-data_cadastro']
    
    def __str__(self):
        return self.nome

class TipoDespesa(models.Model):
    nome = models.CharField(max_length=100, verbose_name="Nome")
    descricao = models.TextField(blank=True, null=True, verbose_name="Descrição")
    data_cadastro = models.DateTimeField(default=timezone.now, verbose_name="Data de Cadastro")

    class Meta:
        verbose_name = "Tipo de Despesa"
        verbose_name_plural = "Tipos de Despesa"
    
    def __str__(self):
        return self.nome

class FormaPagamento(models.Model):
    nome = models.CharField(max_length=100, verbose_name="Nome")
    ativo = models.BooleanField(default=True, verbose_name="Ativo")
    data_cadastro = models.DateTimeField(default=timezone.now, verbose_name="Data de Cadastro")
    
    class Meta:
        verbose_name = "Forma de Pagamento"
        verbose_name_plural = "Formas de Pagamento"
    
    def __str__(self):
        return self.nome

class PrazoPagamento(models.Model):
    nome = models.CharField(max_length=100, verbose_name="Nome")
    dias = models.IntegerField(verbose_name="Dias")
    data_cadastro = models.DateTimeField(default=timezone.now, verbose_name="Data de Cadastro")
    
    class Meta:
        verbose_name = "Prazo de Pagamento"
        verbose_name_plural = "Prazos de Pagamento"
    
    def __str__(self):
        return f"{self.nome} - {self.dias} dias"

class Banco(models.Model):
    nome = models.CharField(max_length=100, verbose_name="Nome")
    ativo = models.BooleanField(default=True, verbose_name="Ativo")
    data_cadastro = models.DateTimeField(default=timezone.now, verbose_name="Data de Cadastro")
    
    class Meta:
        verbose_name = "Banco"
        verbose_name_plural = "Bancos"
    
    def __str__(self):
        return self.nome

class Processo(models.Model):
    STATUS_CHOICES = [
        ('ativo', 'Ativo'),
        ('suspenso', 'Suspenso'),
        ('arquivado', 'Arquivado'),
        ('finalizado', 'Finalizado'),
    ]
    
    numero = models.CharField(max_length=50, unique=True, verbose_name="Número do Processo")
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, verbose_name="Cliente")
    advogado_responsavel = models.ForeignKey('users.Lawyer', on_delete=models.CASCADE, verbose_name="Advogado Responsável")
    titulo = models.CharField(max_length=200, verbose_name="Título")
    descricao = models.TextField(verbose_name="Descrição")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ativo', verbose_name="Status")
    data_inicio = models.DateField(verbose_name="Data de Início")
    data_fim = models.DateField(blank=True, null=True, verbose_name="Data de Fim")
    valor_causa = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="Valor da Causa")
    tribunal = models.CharField(max_length=100, blank=True, null=True, verbose_name="Tribunal")
    vara = models.CharField(max_length=100, blank=True, null=True, verbose_name="Vara")
    
    class Meta:
        verbose_name = "Processo"
        verbose_name_plural = "Processos"
        ordering = ['-data_inicio']
    
    def __str__(self):
        return f"{self.numero} - {self.titulo}"

class Task(models.Model):
    PRIORIDADE_CHOICES = [
        ('baixa', 'Baixa'),
        ('media', 'Média'),
        ('alta', 'Alta'),
        ('urgente', 'Urgente'),
    ]
    
    STATUS_CHOICES = [
        ('pendente', 'Pendente'),
        ('em_andamento', 'Em Andamento'),
        ('concluida', 'Concluída'),
        ('cancelada', 'Cancelada'),
    ]
    
    titulo = models.CharField(max_length=200, verbose_name="Título")
    descricao = models.TextField(blank=True, null=True, verbose_name="Descrição")
    data_inicio = models.DateTimeField(verbose_name="Data/Hora de Início")
    data_fim = models.DateTimeField(blank=True, null=True, verbose_name="Data/Hora de Fim")
    dia_todo = models.BooleanField(default=False, verbose_name="Dia Todo")
    advogado = models.ForeignKey('users.Lawyer', on_delete=models.CASCADE, verbose_name="Advogado")
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, blank=True, null=True, verbose_name="Cliente")
    processo = models.ForeignKey(Processo, on_delete=models.CASCADE, blank=True, null=True, verbose_name="Processo")
    prioridade = models.CharField(max_length=20, choices=PRIORIDADE_CHOICES, default='media', verbose_name="Prioridade")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pendente', verbose_name="Status")
    data_criacao = models.DateTimeField(auto_now_add=True, verbose_name="Data de Criação")
    data_atualizacao = models.DateTimeField(auto_now=True, verbose_name="Data de Atualização")
    
    class Meta:
        verbose_name = "Tarefa"
        verbose_name_plural = "Tarefas"
        ordering = ['-data_inicio']
    
    def __str__(self):
        return self.titulo

class Audiencia(models.Model):
    TIPO_CHOICES = [
        ('inicial', 'Inicial'),
        ('instrucao', 'Instrução'),
        ('conciliacao', 'Conciliação'),
        ('julgamento', 'Julgamento'),
        ('outros', 'Outros'),
    ]
    
    processo = models.ForeignKey(Processo, on_delete=models.CASCADE, verbose_name="Processo")
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, verbose_name="Tipo")
    data_hora = models.DateTimeField(verbose_name="Data e Hora")
    local = models.CharField(max_length=200, verbose_name="Local")
    observacoes = models.TextField(blank=True, null=True, verbose_name="Observações")
    compareceu = models.BooleanField(default=False, verbose_name="Compareceu")
    resultado = models.TextField(blank=True, null=True, verbose_name="Resultado")
    data_criacao = models.DateTimeField(auto_now_add=True, verbose_name="Data de Criação")
    
    class Meta:
        verbose_name = "Audiência"
        verbose_name_plural = "Audiências"
        ordering = ['-data_hora']
    
    def __str__(self):
        return f"{self.processo.numero} - {self.get_tipo_display()} - {self.data_hora.strftime('%d/%m/%Y %H:%M')}"

class Publicacao(models.Model):
    processo = models.ForeignKey(Processo, on_delete=models.CASCADE, verbose_name="Processo")
    titulo = models.CharField(max_length=200, verbose_name="Título")
    conteudo = models.TextField(verbose_name="Conteúdo")
    data_publicacao = models.DateField(verbose_name="Data de Publicação")
    orgao = models.CharField(max_length=100, verbose_name="Órgão")
    tipo = models.CharField(max_length=100, blank=True, null=True, verbose_name="Tipo")
    lida = models.BooleanField(default=False, verbose_name="Lida")
    data_criacao = models.DateTimeField(auto_now_add=True, verbose_name="Data de Criação")
    
    class Meta:
        verbose_name = "Publicação"
        verbose_name_plural = "Publicações"
        ordering = ['-data_publicacao']
    
    def __str__(self):
        return f"{self.processo.numero} - {self.titulo}"

class Receita(models.Model):
    CONDICAO_PAGAMENTO_CHOICES = [
        ('a_vista', 'À vista'),
        ('parcelado', 'Parcelado'),
        ('entrada_parcelado', 'Entrada + Parcelado'),
    ]
    
    descricao = models.CharField(max_length=200, verbose_name="Descrição")
    valor_total = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Valor Total")
    data_emissao = models.DateField(default=timezone.now, verbose_name="Data de Emissão")
    data_vencimento = models.DateField(verbose_name="Data de Vencimento")
    data_recebimento = models.DateField(blank=True, null=True, verbose_name="Data de Recebimento")
    tipo = models.ForeignKey(TipoReceita, on_delete=models.CASCADE, verbose_name="Tipo de Receita")
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, verbose_name="Cliente")
    advogado = models.ForeignKey('users.Lawyer', on_delete=models.CASCADE, blank=True, null=True, verbose_name="Advogado")
    processo = models.ForeignKey(Processo, on_delete=models.CASCADE, blank=True, null=True, verbose_name="Processo")
    tipo_demanda = models.ForeignKey('TipoDemanda', on_delete=models.CASCADE, blank=True, null=True, verbose_name="Tipo de Demanda")
    condicao_pagamento = models.CharField(max_length=20, choices=CONDICAO_PAGAMENTO_CHOICES, verbose_name="Condição de Pagamento")
    numero_parcelas = models.IntegerField(blank=True, null=True, verbose_name="Número de Parcelas")
    prazo = models.ForeignKey('PrazoPagamento', on_delete=models.CASCADE, blank=True, null=True, verbose_name="Prazo")
    forma_pagamento = models.ForeignKey(FormaPagamento, on_delete=models.CASCADE, verbose_name="Forma de Pagamento")
    banco = models.ForeignKey(Banco, on_delete=models.CASCADE, blank=True, null=True, verbose_name="Banco")
    observacoes = models.TextField(blank=True, null=True, verbose_name="Observações")
    pago = models.BooleanField(default=False, verbose_name="Pago")
    parcial = models.BooleanField(default=False, verbose_name="Parcial")
    desconto = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Desconto")
    valor_recebido = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="Valor Recebido")
    rateio_ativo = models.BooleanField(default=False, verbose_name="Rateio Ativo")
    rateio_advogado_1 = models.ForeignKey('users.Lawyer', on_delete=models.CASCADE, blank=True, null=True, related_name='rateio_advogado_1', verbose_name="Advogado 1 (Rateio)")
    rateio_percentual_1 = models.DecimalField(max_digits=5, decimal_places=2, default=0, blank=True, null=True, verbose_name="Percentual Advogado 1")
    rateio_advogado_2 = models.ForeignKey('users.Lawyer', on_delete=models.CASCADE, blank=True, null=True, related_name='rateio_advogado_2', verbose_name="Advogado 2 (Rateio)")
    rateio_percentual_2 = models.DecimalField(max_digits=5, decimal_places=2, default=0, blank=True, null=True, verbose_name="Percentual Advogado 2")
    rateio_advogado_3 = models.ForeignKey('users.Lawyer', on_delete=models.CASCADE, blank=True, null=True, related_name='rateio_advogado_3', verbose_name="Advogado 3 (Rateio)")
    rateio_percentual_3 = models.DecimalField(max_digits=5, decimal_places=2, default=0, blank=True, null=True, verbose_name="Percentual Advogado 3")
    data_criacao = models.DateTimeField(auto_now_add=True, verbose_name="Data de Criação")
    data_atualizacao = models.DateTimeField(auto_now=True, verbose_name="Data de Atualização")
    
    class Meta:
        verbose_name = "Receita"
        verbose_name_plural = "Receitas"
        ordering = ['-data_vencimento']
    
    def __str__(self):
        return f"{self.descricao} - R$ {self.valor_total}"

class Despesa(models.Model):
    descricao = models.CharField(max_length=200, verbose_name="Descrição")
    valor = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Valor")
    data_vencimento = models.DateField(verbose_name="Data de Vencimento")
    data_pagamento = models.DateField(blank=True, null=True, verbose_name="Data de Pagamento")
    tipo = models.ForeignKey(TipoDespesa, on_delete=models.CASCADE, verbose_name="Tipo")
    fornecedor = models.CharField(max_length=200, blank=True, null=True, verbose_name="Fornecedor")
    processo = models.ForeignKey(Processo, on_delete=models.CASCADE, blank=True, null=True, verbose_name="Processo")
    forma_pagamento = models.ForeignKey(FormaPagamento, on_delete=models.CASCADE, verbose_name="Forma de Pagamento")
    observacoes = models.TextField(blank=True, null=True, verbose_name="Observações")
    pago = models.BooleanField(default=False, verbose_name="Pago")
    data_criacao = models.DateTimeField(auto_now_add=True, verbose_name="Data de Criação")
    
    class Meta:
        verbose_name = "Despesa"
        verbose_name_plural = "Despesas"
        ordering = ['-data_vencimento']
    
    def __str__(self):
        return f"{self.descricao} - R$ {self.valor}"

class AtividadeRecente(models.Model):
    TIPO_CHOICES = [
        ('cliente_cadastrado', 'Cliente Cadastrado'),
        ('cliente_desativado', 'Cliente Desativado'),
        ('audiencia_agendada', 'Audiência Agendada'),
        ('documento_gerado', 'Documento Gerado'),
        ('recebimento_confirmado', 'Recebimento Confirmado'),
        ('tarefa_criada', 'Tarefa Criada'),
        ('processo_criado', 'Processo Criado'),
        ('processo_atualizado', 'Processo Atualizado'),
        ('publicacao_recebida', 'Publicação Recebida'),
    ]
    
    tipo = models.CharField(max_length=30, choices=TIPO_CHOICES, verbose_name="Tipo")
    descricao = models.CharField(max_length=300, verbose_name="Descrição")
    usuario = models.ForeignKey('users.Lawyer', on_delete=models.CASCADE, verbose_name="Advogado")
    data_criacao = models.DateTimeField(auto_now_add=True, verbose_name="Data de Criação")
    
    # Campos opcionais para relacionamento
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, blank=True, null=True)
    processo = models.ForeignKey(Processo, on_delete=models.CASCADE, blank=True, null=True)
    task = models.ForeignKey(Task, on_delete=models.CASCADE, blank=True, null=True)
    
    class Meta:
        verbose_name = "Atividade Recente"
        verbose_name_plural = "Atividades Recentes"
        ordering = ['-data_criacao']
    
    def __str__(self):
        return f"{self.get_tipo_display()} - {self.descricao[:50]}..."

# Fornecedor para despesas
class Fornecedor(models.Model):
    nome = models.CharField(max_length=200, verbose_name="Nome")
    cnpj_cpf = models.CharField(max_length=20, blank=True, null=True, verbose_name="CNPJ/CPF")
    telefone = models.CharField(max_length=20, blank=True, null=True, verbose_name="Telefone")
    email = models.EmailField(blank=True, null=True, verbose_name="E-mail")
    endereco = models.TextField(blank=True, null=True, verbose_name="Endereço")
    ativo = models.BooleanField(default=True, verbose_name="Ativo")
    
    class Meta:
        verbose_name = "Fornecedor"
        verbose_name_plural = "Fornecedores"
    
    def __str__(self):
        return self.nome

class TipoDemanda(models.Model):
    nome = models.CharField(max_length=100, verbose_name="Nome")
    descricao = models.TextField(blank=True, null=True, verbose_name="Descrição")
    area_direito = models.CharField(max_length=100, blank=True, null=True, verbose_name="Área do Direito")
    
    class Meta:
        verbose_name = "Tipo de Demanda"
        verbose_name_plural = "Tipos de Demanda"
    
    def __str__(self):
        return self.nome