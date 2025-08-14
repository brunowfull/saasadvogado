from django.contrib import admin
from .models import Category, Transaction, Client, FinancialCase, Payment

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('date', 'lawyer', 'title', 'type', 'amount', 'category')
    list_filter = ('lawyer', 'type', 'category', 'date')
    search_fields = ('title', 'description')

@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone')
    search_fields = ('name', 'email')

class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 1
    readonly_fields = ('payment_date',)

@admin.register(FinancialCase)
class FinancialCaseAdmin(admin.ModelAdmin):
    list_display = ('case_name', 'client', 'total_amount', 'amount_paid', 'remaining_balance', 'status', 'creation_date')
    list_filter = ('status', 'client')
    search_fields = ('case_name', 'client__name')
    inlines = [PaymentInline]

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('case', 'amount', 'payment_date', 'payment_method')
    list_filter = ('payment_method', 'payment_date')
    search_fields = ('case__case_name',)
