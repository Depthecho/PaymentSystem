from django.db import transaction
from rest_framework import status
from typing import Tuple, Optional, Union
from .models import Organization, Payment, BalanceLog
import logging

logger = logging.getLogger(__name__)


class PaymentService:
    @classmethod
    def process_payment(cls, payment_data: dict) -> Tuple[bool, str, int]:
        try:
            with transaction.atomic():
                # Проверка дубля
                if Payment.objects.filter(operation_id=payment_data['operation_id']).exists():
                    return False, "Payment already processed", status.HTTP_200_OK

                # Создание платежа
                payment = Payment.objects.create(**payment_data)

                # Обновление баланса
                organization, _ = Organization.objects.get_or_create(
                    inn=payment_data['payer_inn'],
                    defaults={'balance': 0}
                )

                organization.balance += payment_data['amount']
                organization.save()

                # Логирование
                BalanceLog.objects.create(
                    organization=organization,
                    amount=payment_data['amount'],
                    new_balance=organization.balance,
                    payment=payment
                )

                logger.info(
                    f"Начислен баланс для организации {organization.inn}. "
                    f"Сумма: {payment_data['amount']}, новый баланс: {organization.balance}"
                )

                return True, "Payment processed successfully", status.HTTP_201_CREATED

        except Exception as e:
            logger.error(f"Payment processing failed: {str(e)}")
            return False, "Internal server error", status.HTTP_500_INTERNAL_SERVER_ERROR


class OrganizationService:
    @classmethod
    def get_balance(cls, inn: str) -> Tuple[Optional[float], Optional[str], int]:
        try:
            organization = Organization.objects.get(inn=inn)
            return organization.balance, None, status.HTTP_200_OK
        except Organization.DoesNotExist:
            return None, "Organization not found", status.HTTP_404_NOT_FOUND
        except Exception as e:
            logger.error(f"Balance check failed: {str(e)}")
            return None, "Internal server error", status.HTTP_500_INTERNAL_SERVER_ERROR