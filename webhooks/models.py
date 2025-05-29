from django.db import models

class Organization(models.Model):
    inn = models.CharField(max_length=12, unique=True, verbose_name="Organization's INN")
    balance = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="Balance")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date of creation")

    class Meta:
        verbose_name = "Organization"
        verbose_name_plural = "Organizations"
        ordering = ['-created_at']

    def __str__(self):
        return self.inn


class Payment(models.Model):
    operation_id = models.UUIDField(unique=True, verbose_name="Operation's ID")
    amount = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="Amount")
    payer_inn = models.CharField(max_length=12, verbose_name="Taxpayer's INN")
    document_number = models.CharField(max_length=50, verbose_name="Doc's number")
    document_date = models.DateTimeField(verbose_name="Doc's date")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date of record creation")

    class Meta:
        verbose_name = "Payment"
        verbose_name_plural = "Payments"

    def __str__(self):
        return f"{self.operation_id} - {self.amount}"


class BalanceLog(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='balance_logs')
    amount = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="Amount of change")
    new_balance = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="New balance")
    payment = models.ForeignKey(Payment, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date of record change")

    class Meta:
        verbose_name = "Balance log"
        verbose_name_plural = "Balance logs"

    def __str__(self):
        return f"{self.organization.inn} - {self.amount}"