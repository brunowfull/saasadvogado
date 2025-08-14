from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

class Lawyer(AbstractUser):
    cpf = models.CharField(max_length=14, unique=True, blank=True, null=True, verbose_name="CPF")
    oab_number = models.CharField(max_length=20, blank=True, null=True, verbose_name="Número OAB")

    STATE_CHOICES = [
        ('AC', 'Acre'), ('AL', 'Alagoas'), ('AP', 'Amapá'), ('AM', 'Amazonas'),
        ('BA', 'Bahia'), ('CE', 'Ceará'), ('DF', 'Distrito Federal'), ('ES', 'Espírito Santo'),
        ('GO', 'Goiás'), ('MA', 'Maranhão'), ('MT', 'Mato Grosso'), ('MS', 'Mato Grosso do Sul'),
        ('MG', 'Minas Gerais'), ('PA', 'Pará'), ('PB', 'Paraíba'), ('PR', 'Paraná'),
        ('PE', 'Pernambuco'), ('PI', 'Piauí'), ('RJ', 'Rio de Janeiro'), ('RN', 'Rio Grande do Norte'),
        ('RS', 'Rio Grande do Sul'), ('RO', 'Rondônia'), ('RR', 'Roraima'), ('SC', 'Santa Catarina'),
        ('SP', 'São Paulo'), ('SE', 'Sergipe'), ('TO', 'Tocantins'),
    ]
    oab_section = models.CharField(max_length=2, choices=STATE_CHOICES, blank=True, null=True, verbose_name="Seccional OAB")

    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name="Telefone")
    pix_key = models.CharField(max_length=255, blank=True, null=True, verbose_name="Chave PIX")
    professional_address = models.TextField(blank=True, null=True, verbose_name="Endereço Profissional")
    registration_date = models.DateField(default=timezone.now, verbose_name="Data de Cadastro")
    enable_publications = models.BooleanField(default=False, verbose_name="Publicações Ativadas")
    enable_login = models.BooleanField(default=True, verbose_name="Login Ativado")

    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.',
        related_name="lawyer_set",
        related_query_name="lawyer",
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name="lawyer_set",
        related_query_name="lawyer",
    )

    def __str__(self):
        return self.username
