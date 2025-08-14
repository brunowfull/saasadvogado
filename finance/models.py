from django.db import models
from django.conf import settings
from django.utils import timezone

class Category(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Transaction(models.Model):
    TRANSACTION_TYPE_CHOICES = (
        ("INCOME", "Income"),
        ("EXPENSE", "Expense"),
    )

    lawyer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='transactions'
    )
    title = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    type = models.CharField(max_length=7, choices=TRANSACTION_TYPE_CHOICES)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    date = models.DateField()
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.type} - {self.title} - {self.amount}"

class Client(models.Model):
    name = models.CharField(max_length=255, verbose_name="Nome")
    email = models.EmailField(max_length=255, blank=True, null=True, verbose_name="Email")
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name="Telefone")
    address = models.TextField(blank=True, null=True, verbose_name="Endereço")
    cpf = models.CharField(max_length=14, unique=True, blank=True, null=True, verbose_name="CPF")
    mother_name = models.CharField(max_length=255, blank=True, null=True, verbose_name="Nome da Mãe")
    city = models.CharField(max_length=100, blank=True, null=True, verbose_name="Cidade")
    state = models.CharField(max_length=100, blank=True, null=True, verbose_name="Estado")
    client_area = models.BooleanField(default=False, verbose_name="Área do Cliente Ativa")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"

class FinancialCase(models.Model):
    STATUS_CHOICES = (
        ('OPEN', 'Aberto'),
        ('CLOSED', 'Fechado'),
        ('PENDING', 'Pendente'),
    )
    lawyer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='financial_cases', verbose_name="Advogado", null=True)
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='cases', verbose_name="Cliente")
    case_name = models.CharField(max_length=255, verbose_name="Nome do Caso")
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Valor Total")
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Valor Pago")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='OPEN', verbose_name="Status")
    creation_date = models.DateField(default=timezone.now, verbose_name="Data de Criação")

    def __str__(self):
        return f"{self.case_name} - {self.client.name}"

    @property
    def remaining_balance(self):
        return self.total_amount - self.amount_paid

    class Meta:
        verbose_name = "Caso Financeiro"
        verbose_name_plural = "Casos Financeiros"

class Payment(models.Model):
    PAYMENT_METHOD_CHOICES = (
        ('CASH', 'Dinheiro'),
        ('PIX', 'PIX'),
        ('CARD', 'Cartão'),
    )
    PAYMENT_STATUS_CHOICES = (
        ('PAID', 'Pago'),
        ('PENDING', 'Pendente'),
    )
    case = models.ForeignKey(FinancialCase, on_delete=models.CASCADE, related_name='payments', verbose_name="Caso")
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Valor")
    payment_date = models.DateField(default=timezone.now, verbose_name="Data do Pagamento", null=True, blank=True)
    due_date = models.DateField(verbose_name="Data de Vencimento", null=True, blank=True)
    payment_method = models.CharField(max_length=10, choices=PAYMENT_METHOD_CHOICES, verbose_name="Forma de Pagamento", null=True, blank=True)
    status = models.CharField(max_length=10, choices=PAYMENT_STATUS_CHOICES, default='PENDING', verbose_name="Status")
    description = models.TextField(blank=True, null=True, verbose_name="Descrição")

    def __str__(self):
        return f"Pagamento de {self.amount} para {self.case.case_name} em {self.payment_date}"

    class Meta:
        verbose_name = "Pagamento"
        verbose_name_plural = "Pagamentos"