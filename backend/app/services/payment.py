import uuid
from typing import NamedTuple

class PaymentResult(NamedTuple):
    success: bool
    transaction_reference: str
    message: str
    masked_token: str

class TokenizedPaymentGatewayAdapter:
    """
    Simulates a PCI-DSS compliant external payment processor (like Stripe Elements).
    Operates strictly on opaque tokens (tok_...), ensuring QuickBite never handles raw PAN/CVVs.
    """
    @staticmethod
    def process_charge(token: str, amount: float, customer_email: str) -> PaymentResult:
        # Simulate validation of payment token
        if not token or not token.startswith("tok_"):
            return PaymentResult(
                success=False,
                transaction_reference="",
                message="Invalid payment token format. Token must begin with 'tok_'.",
                masked_token=""  # nosec: B106
            )

        # Simulation: specific test token to test declined transactions
        if "declined" in token.lower():
            return PaymentResult(
                success=False,
                transaction_reference="",
                message="Transaction declined by card issuer: Insufficient funds.",
                masked_token=token[:4] + "****" + token[-4:] if len(token) > 8 else "tok_****"
            )

        # Successful charge
        tx_ref = f"tx_qb_{uuid.uuid4().hex[:12]}"
        masked = token[:4] + "****" + token[-4:] if len(token) > 8 else "tok_****"

        return PaymentResult(
            success=True,
            transaction_reference=tx_ref,
            message="Charge approved successfully by gateway.",
            masked_token=masked
        )
