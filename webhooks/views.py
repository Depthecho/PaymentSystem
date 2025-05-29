from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.request import Request
from .serializers import WebhookSerializer
from .services import PaymentService, OrganizationService


class BankWebhookView(APIView):
    def post(self, request: Request) -> Response:
        serializer = WebhookSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        success, message, status_code = PaymentService.process_payment(serializer.validated_data)
        return Response(
            {"status": "success" if success else "error", "message": message},
            status=status_code
        )


class OrganizationBalanceView(APIView):
    def get(self, request: Request, inn: str) -> Response:
        balance, error_message, status_code = OrganizationService.get_balance(inn)

        if error_message:
            return Response({"error": error_message}, status=status_code)

        return Response({
            "inn": inn,
            "balance": balance
        })