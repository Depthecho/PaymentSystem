from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.utils import timezone
from uuid import uuid4
from decimal import Decimal
from .models import Organization, Payment, BalanceLog


class BankWebhookViewTests(APITestCase):
    def setUp(self):
        self.url = reverse('bank-webhook')
        self.valid_payload = {
            "operation_id": str(uuid4()),
            "amount": "1000.50",
            "payer_inn": "123456789012",
            "document_number": "DOC123",
            "document_date": timezone.now().isoformat()
        }

    def test_process_valid_payment_creates_payment_and_updates_balance(self):
        """
        Тест проверяет, что при отправке валидного платежа:
        - создается объект Payment;
        - создается или обновляется Organization с правильным балансом;
        - создается запись BalanceLog;
        - API возвращает статус 201 и статус "success".
        """
        response = self.client.post(self.url, self.valid_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], 'success')
        self.assertTrue(Organization.objects.filter(inn=self.valid_payload['payer_inn']).exists())
        org = Organization.objects.get(inn=self.valid_payload['payer_inn'])
        self.assertEqual(org.balance, Decimal(self.valid_payload['amount']))
        self.assertTrue(Payment.objects.filter(operation_id=self.valid_payload['operation_id']).exists())
        self.assertTrue(BalanceLog.objects.filter(organization=org).exists())

    def test_duplicate_payment_returns_success_without_creating_new(self):
        """
        Тест проверяет, что при повторной отправке платежа с тем же operation_id:
        - новый платеж не создается;
        - API возвращает статус 200 и сообщение об уже обработанном платеже.
        """
        # Создаем платеж вручную
        Payment.objects.create(
            operation_id=self.valid_payload['operation_id'],
            amount=Decimal(self.valid_payload['amount']),
            payer_inn=self.valid_payload['payer_inn'],
            document_number=self.valid_payload['document_number'],
            document_date=self.valid_payload['document_date']
        )
        # Повторный запрос с тем же operation_id
        response = self.client.post(self.url, self.valid_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'error')
        self.assertEqual(response.data['message'], 'Payment already processed')

    def test_invalid_payload_returns_400(self):
        """
        Тест проверяет, что при отправке некорректных данных (отсутствует обязательное поле):
        - API возвращает статус 400 с описанием ошибок валидации.
        """
        invalid_payload = self.valid_payload.copy()
        invalid_payload.pop('operation_id')  # Удаляем обязательное поле
        response = self.client.post(self.url, invalid_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('operation_id', response.data)


class OrganizationBalanceViewTests(APITestCase):
    def setUp(self):
        self.organization = Organization.objects.create(inn="987654321098", balance=Decimal('5000.00'))
        self.url = reverse('organization-balance', args=[self.organization.inn])  # Имя маршрута в urls.py

    def test_get_existing_organization_balance(self):
        """
        Тест проверяет, что при запросе баланса существующей организации:
        - возвращается статус 200;
        - в ответе содержится правильный ИНН и баланс.
        """
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['inn'], self.organization.inn)
        self.assertEqual(Decimal(response.data['balance']), self.organization.balance)

    def test_get_nonexistent_organization_returns_404(self):
        """
        Тест проверяет, что при запросе баланса несуществующей организации:
        - возвращается статус 404;
        - в ответе содержится сообщение об ошибке "Organization not found".
        """
        url = reverse('organization-balance', args=['000000000000'])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('error', response.data)
        self.assertEqual(response.data['error'], 'Organization not found')


class PaymentServiceTests(APITestCase):
    def test_process_payment_creates_payment_and_updates_balance(self):
        """
        Тест проверяет, что метод PaymentService.process_payment:
        - создает объект Payment;
        - обновляет или создает Organization с правильным балансом;
        - создает запись BalanceLog;
        - возвращает успешный результат с кодом 201.
        """
        payment_data = {
            "operation_id": uuid4(),
            "amount": Decimal('1200.00'),
            "payer_inn": "111222333444",
            "document_number": "DOC999",
            "document_date": timezone.now()
        }
        from .services import PaymentService

        success, message, status_code = PaymentService.process_payment(payment_data)
        self.assertTrue(success)
        self.assertEqual(status_code, status.HTTP_201_CREATED)
        org = Organization.objects.get(inn=payment_data['payer_inn'])
        self.assertEqual(org.balance, payment_data['amount'])
        payment = Payment.objects.get(operation_id=payment_data['operation_id'])
        self.assertEqual(payment.amount, payment_data['amount'])
        balance_log = BalanceLog.objects.filter(organization=org, payment=payment).first()
        self.assertIsNotNone(balance_log)
        self.assertEqual(balance_log.new_balance, org.balance)

    def test_process_payment_duplicate_returns_error(self):
        """
        Тест проверяет, что при попытке повторной обработки платежа с существующим operation_id:
        - метод возвращает ошибку с сообщением "Payment already processed";
        - код статуса 200 (т.к. дубликат не является ошибкой сервера).
        """
        from .services import PaymentService
        operation_id = uuid4()
        Payment.objects.create(
            operation_id=operation_id,
            amount=Decimal('100.00'),
            payer_inn="555666777888",
            document_number="DOC111",
            document_date=timezone.now()
        )
        payment_data = {
            "operation_id": operation_id,
            "amount": Decimal('100.00'),
            "payer_inn": "555666777888",
            "document_number": "DOC111",
            "document_date": timezone.now()
        }
        success, message, status_code = PaymentService.process_payment(payment_data)
        self.assertFalse(success)
        self.assertEqual(message, "Payment already processed")
        self.assertEqual(status_code, status.HTTP_200_OK)


class OrganizationServiceTests(APITestCase):
    def test_get_balance_existing_organization(self):
        """
        Тест проверяет, что метод OrganizationService.get_balance:
        - возвращает корректный баланс для существующей организации;
        - не возвращает ошибку;
        - возвращает статус 200.
        """
        org = Organization.objects.create(inn="333222111000", balance=Decimal('2500.00'))
        from .services import OrganizationService
        balance, error, status_code = OrganizationService.get_balance(org.inn)
        self.assertIsNone(error)
        self.assertEqual(status_code, status.HTTP_200_OK)
        self.assertEqual(balance, org.balance)

    def test_get_balance_nonexistent_organization(self):
        """
        Тест проверяет, что метод OrganizationService.get_balance:
        - возвращает ошибку при отсутствии организации;
        - возвращает статус 404;
        - баланс отсутствует (None).
        """
        from .services import OrganizationService
        balance, error, status_code = OrganizationService.get_balance("000000000000")
        self.assertIsNone(balance)
        self.assertEqual(error, "Organization not found")
        self.assertEqual(status_code, status.HTTP_404_NOT_FOUND)
