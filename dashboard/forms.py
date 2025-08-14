from django import forms
from django.contrib.auth import get_user_model
from .models import Task, Cliente, Processo, Audiencia, Receita, Despesa, TipoDemanda, PrazoPagamento, Banco, TipoReceita, TipoDespesa, FormaPagamento
from users.models import Lawyer

User = get_user_model()

class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['titulo', 'descricao', 'data_inicio', 'data_fim', 'dia_todo', 'cliente', 'processo', 'prioridade', 'status']
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Título da tarefa'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Descrição da tarefa'}),
            'data_inicio': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'data_fim': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'dia_todo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'cliente': forms.Select(attrs={'class': 'form-control'}),
            'processo': forms.Select(attrs={'class': 'form-control'}),
            'prioridade': forms.Select(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
        }
        labels = {
            'titulo': 'Título',
            'descricao': 'Descrição',
            'data_inicio': 'Data/Hora de Início',
            'data_fim': 'Data/Hora de Fim',
            'dia_todo': 'Dia Todo',
            'cliente': 'Cliente',
            'processo': 'Processo',
            'prioridade': 'Prioridade',
            'status': 'Status',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Filtrar apenas clientes ativos
        self.fields['cliente'].queryset = Cliente.objects.filter(ativo=True)
        self.fields['processo'].queryset = Processo.objects.all()

class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ['nome', 'nome_mae', 'cpf_cnpj', 'email', 'telefone', 'endereco', 'cidade', 'estado', 'ativo']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome completo'}),
            'nome_mae': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome da mãe'}),
            'cpf_cnpj': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'CPF ou CNPJ'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'email@exemplo.com'}),
            'telefone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '(00) 00000-0000'}),
            'endereco': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Endereço completo'}),
            'cidade': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Cidade'}),
            'estado': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Estado'}),
            'ativo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class ProcessoForm(forms.ModelForm):
    class Meta:
        model = Processo
        fields = ['numero', 'cliente', 'advogado_responsavel', 'titulo', 'descricao', 'status', 
                 'data_inicio', 'data_fim', 'valor_causa', 'tribunal', 'vara']
        widgets = {
            'numero': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Número do processo'}),
            'cliente': forms.Select(attrs={'class': 'form-control'}),
            'advogado_responsavel': forms.Select(attrs={'class': 'form-control'}),
            'titulo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Título do processo'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Descrição detalhada'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'data_inicio': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'data_fim': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'valor_causa': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '0,00'}),
            'tribunal': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome do tribunal'}),
            'vara': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Vara'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['cliente'].queryset = Cliente.objects.filter(ativo=True)
        self.fields['advogado_responsavel'].queryset = User.objects.exclude(oab_number__isnull=True).exclude(oab_number='')

class AudienciaForm(forms.ModelForm):
    class Meta:
        model = Audiencia
        fields = ['processo', 'tipo', 'data_hora', 'local', 'observacoes']
        widgets = {
            'processo': forms.Select(attrs={'class': 'form-control'}),
            'tipo': forms.Select(attrs={'class': 'form-control'}),
            'data_hora': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'local': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Local da audiência'}),
            'observacoes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Observações'}),
        }

class ReceitaForm(forms.ModelForm):
    class Meta:
        model = Receita
        fields = ['descricao', 'valor_total', 'data_emissao', 'data_vencimento', 'data_recebimento', 'tipo', 'cliente',
                 'advogado', 'processo', 'tipo_demanda', 'condicao_pagamento', 'numero_parcelas', 'prazo',
                 'forma_pagamento', 'banco', 'observacoes', 'pago', 'parcial', 'desconto', 'valor_recebido',
                 'rateio_ativo', 'rateio_advogado_1', 'rateio_percentual_1', 'rateio_advogado_2', 'rateio_percentual_2',
                 'rateio_advogado_3', 'rateio_percentual_3']
        widgets = {
            'descricao': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Descrição da receita'}),
            'valor_total': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '0,00'}),
            'data_emissao': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'data_vencimento': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'data_recebimento': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'tipo': forms.Select(attrs={'class': 'form-control'}),
            'cliente': forms.Select(attrs={'class': 'form-control'}),
            'advogado': forms.Select(attrs={'class': 'form-control'}),
            'processo': forms.Select(attrs={'class': 'form-control'}),
            'tipo_demanda': forms.Select(attrs={'class': 'form-control'}),
            'condicao_pagamento': forms.Select(attrs={'class': 'form-control'}),
            'numero_parcelas': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Número de parcelas'}),
            'prazo': forms.Select(attrs={'class': 'form-control'}),
            'forma_pagamento': forms.Select(attrs={'class': 'form-control'}),
            'banco': forms.Select(attrs={'class': 'form-control'}),
            'observacoes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Observações'}),
            'pago': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'parcial': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'desconto': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '0,00'}),
            'valor_recebido': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '0,00'}),
            'rateio_ativo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'rateio_advogado_1': forms.Select(attrs={'class': 'form-control'}),
            'rateio_percentual_1': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Percentual'}),
            'rateio_advogado_2': forms.Select(attrs={'class': 'form-control'}),
            'rateio_percentual_2': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Percentual'}),
            'rateio_advogado_3': forms.Select(attrs={'class': 'form-control'}),
            'rateio_percentual_3': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Percentual'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['cliente'].queryset = Cliente.objects.filter(ativo=True)
        self.fields['advogado'].queryset = Lawyer.objects.all()
        self.fields['processo'].required = False
        self.fields['tipo_demanda'].queryset = TipoDemanda.objects.all()
        self.fields['prazo'].queryset = PrazoPagamento.objects.all()
        self.fields['banco'].queryset = Banco.objects.filter(ativo=True)
        self.fields['rateio_advogado_1'].queryset = Lawyer.objects.all()
        self.fields['rateio_advogado_2'].queryset = Lawyer.objects.all()
        self.fields['rateio_advogado_3'].queryset = Lawyer.objects.all()

class DespesaForm(forms.ModelForm):
    class Meta:
        model = Despesa
        fields = ['descricao', 'valor', 'data_vencimento', 'data_pagamento', 'tipo', 'fornecedor', 
                 'processo', 'forma_pagamento', 'observacoes', 'pago']
        widgets = {
            'descricao': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Descrição da despesa'}),
            'valor': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '0,00'}),
            'data_vencimento': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'data_pagamento': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'tipo': forms.Select(attrs={'class': 'form-control'}),
            'fornecedor': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome do fornecedor'}),
            'processo': forms.Select(attrs={'class': 'form-control'}),
            'forma_pagamento': forms.Select(attrs={'class': 'form-control'}),
            'observacoes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Observações'}),
            'pago': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['processo'].required = False

# Form para filtros no dashboard
class DashboardFilterForm(forms.Form):
    PERIODO_CHOICES = [
        ('7', 'Últimos 7 dias'),
        ('30', 'Últimos 30 dias'),
        ('90', 'Últimos 90 dias'),
        ('365', 'Último ano'),
    ]
    
    periodo = forms.ChoiceField(
        choices=PERIODO_CHOICES,
        initial='30',
        widget=forms.Select(attrs={'class': 'form-control form-control-sm'})
    )
    

# Form para advogados
from users.models import Lawyer
from django.contrib.auth.forms import UserCreationForm

class AdvogadoForm(UserCreationForm):
    class Meta:
        model = Lawyer
        fields = ['username', 'first_name', 'last_name', 'email', 'cpf', 'oab_number', 'oab_section',
                  'phone', 'pix_key', 'professional_address', 'registration_date', 'enable_publications', 'enable_login']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome de usuário'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Sobrenome'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'email@exemplo.com'}),
            'cpf': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'CPF'}),
            'oab_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Número OAB'}),
            'oab_section': forms.Select(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '(00) 00000-0000'}),
            'pix_key': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Chave PIX'}),
            'professional_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Endereço profissional'}),
            'registration_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'enable_publications': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'enable_login': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'username': 'Nome de Usuário',
            'first_name': 'Nome',
            'last_name': 'Sobrenome',
            'email': 'Email',
            'cpf': 'CPF',
            'oab_number': 'Número OAB',
            'oab_section': 'Seccional OAB',
            'phone': 'Telefone',
            'pix_key': 'Chave PIX',
            'professional_address': 'Endereço Profissional',
            'registration_date': 'Data de Cadastro',
            'enable_publications': 'Publicações Ativadas',
            'enable_login': 'Login Ativado',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Personalizar campos de senha
        self.fields['password2'].widget.attrs.update({'class': 'form-control'})
        self.fields['password2'].label = 'Confirmação de Senha'
        self.fields['password2'].help_text = 'Digite a mesma senha novamente, para verificação.'

    advogado = forms.ModelChoiceField(
        queryset=User.objects.exclude(oab_number__isnull=True).exclude(oab_number=''),
        required=False,
        empty_label="Todos os advogados",
        widget=forms.Select(attrs={'class': 'form-control form-control-sm'})
    )
    
    status_processo = forms.ChoiceField(
        choices=[('', 'Todos')] + Processo.STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control form-control-sm'})
    )

# Form para TipoReceita
class TipoReceitaForm(forms.ModelForm):
   class Meta:
       model = TipoReceita
       fields = ['nome', 'descricao']
       widgets = {
           'nome': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome do tipo de receita'}),
           'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Descrição do tipo de receita'}),
       }

class TipoDespesaForm(forms.ModelForm):
    class Meta:
        model = TipoDespesa
        fields = ['nome', 'descricao', 'data_cadastro']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome do tipo de despesa'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Descrição do tipo de despesa'}),
            'data_cadastro': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
        }

class FormaPagamentoForm(forms.ModelForm):
    class Meta:
        model = FormaPagamento
        fields = ['nome', 'data_cadastro']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome da forma de pagamento'}),
            'data_cadastro': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
        }

class BancoForm(forms.ModelForm):
    class Meta:
        model = Banco
        fields = ['nome', 'data_cadastro']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome do banco'}),
            'data_cadastro': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
        }

class PrazoPagamentoForm(forms.ModelForm):
    class Meta:
        model = PrazoPagamento
        fields = ['nome', 'dias', 'data_cadastro']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome do prazo de pagamento'}),
            'dias': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Número de dias'}),
            'data_cadastro': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
        }

class TipoDemandaForm(forms.ModelForm):
    class Meta:
        model = TipoDemanda
        fields = ['nome']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome do tipo de demanda'}),
        }
