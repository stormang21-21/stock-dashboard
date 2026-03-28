"""
Payment Models

Subscription, Invoice, and Payment Method models.
"""

from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Optional, Dict, Any, List
from enum import Enum
import uuid
import logging

logger = logging.getLogger(__name__)


class PaymentStatus(str, Enum):
    """Payment status"""
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"
    DISPUTED = "disputed"


class PaymentMethodType(str, Enum):
    """Payment method types"""
    CARD = "card"
    BANK = "bank"
    PAYPAL = "paypal"
    CRYPTO = "crypto"


class BillingPeriod(str, Enum):
    """Billing periods"""
    MONTHLY = "monthly"
    YEARLY = "yearly"
    QUARTERLY = "quarterly"


@dataclass
class PaymentMethod:
    """
    Customer payment method.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str = ""
    type: PaymentMethodType = PaymentMethodType.CARD
    provider_id: str = ""  # Stripe customer/payment method ID
    
    # Card details (masked)
    card_brand: str = ""
    card_last4: str = ""
    card_exp_month: int = 0
    card_exp_year: int = 0
    
    # Billing address
    billing_email: str = ""
    billing_country: str = ""
    billing_zip: str = ""
    
    is_default: bool = False
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'type': self.type.value,
            'card_brand': self.card_brand,
            'card_last4': self.card_last4,
            'card_exp': f"{self.card_exp_month:02d}/{self.card_exp_year}",
            'billing_email': self.billing_email,
            'is_default': self.is_default,
            'created_at': self.created_at.isoformat(),
        }


@dataclass
class Invoice:
    """
    Invoice for subscription or one-time payment.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str = ""
    invoice_number: str = ""
    
    # Amount
    amount: float = 0.0
    currency: str = "USD"
    tax_amount: float = 0.0
    discount_amount: float = 0.0
    total_amount: float = 0.0
    
    # Period
    period_start: date = field(default_factory=date.today)
    period_end: date = field(default_factory=date.today)
    billing_period: BillingPeriod = BillingPeriod.MONTHLY
    
    # Status
    status: PaymentStatus = PaymentStatus.PENDING
    paid_at: Optional[datetime] = None
    
    # Payment details
    payment_method_id: Optional[str] = None
    provider_invoice_id: str = ""  # Stripe invoice ID
    provider_charge_id: str = ""  # Stripe charge ID
    
    # Line items
    line_items: List[Dict[str, Any]] = field(default_factory=list)
    
    # Metadata
    description: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    created_at: datetime = field(default_factory=datetime.now)
    due_date: Optional[date] = None
    
    def __post_init__(self):
        if not self.invoice_number:
            self.invoice_number = f"INV-{datetime.now().strftime('%Y%m%d')}-{self.id[:8].upper()}"
        if not self.due_date:
            self.due_date = self.period_end
        self.total_amount = self.amount + self.tax_amount - self.discount_amount
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'invoice_number': self.invoice_number,
            'amount': self.amount,
            'tax_amount': self.tax_amount,
            'total_amount': self.total_amount,
            'currency': self.currency,
            'status': self.status.value,
            'period_start': self.period_start.isoformat(),
            'period_end': self.period_end.isoformat(),
            'paid_at': self.paid_at.isoformat() if self.paid_at else None,
            'created_at': self.created_at.isoformat(),
            'line_items': self.line_items,
            'description': self.description,
        }


@dataclass
class Subscription:
    """
    Customer subscription.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str = ""
    
    # Plan
    plan_tier: str = "free"  # free, basic, pro, enterprise
    plan_amount: float = 0.0
    billing_period: BillingPeriod = BillingPeriod.MONTHLY
    
    # Status
    status: str = "active"  # active, cancelled, past_due, trialing
    current_period_start: date = field(default_factory=date.today)
    current_period_end: date = field(default_factory=date.today)
    
    # Trial
    trial_start: Optional[date] = None
    trial_end: Optional[date] = None
    trial_used: bool = False
    
    # Payment
    payment_method_id: Optional[str] = None
    provider_subscription_id: str = ""  # Stripe subscription ID
    
    # Billing history
    invoices: List[str] = field(default_factory=list)  # Invoice IDs
    
    # Cancellation
    cancel_at_period_end: bool = False
    cancelled_at: Optional[datetime] = None
    cancellation_reason: str = ""
    
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'tenant_id': self.tenant_id,
            'plan_tier': self.plan_tier,
            'plan_amount': self.plan_amount,
            'billing_period': self.billing_period.value,
            'status': self.status,
            'current_period_start': self.current_period_start.isoformat(),
            'current_period_end': self.current_period_end.isoformat(),
            'trial_end': self.trial_end.isoformat() if self.trial_end else None,
            'cancel_at_period_end': self.cancel_at_period_end,
            'created_at': self.created_at.isoformat(),
        }
    
    def is_active(self) -> bool:
        """Check if subscription is active"""
        return self.status in ['active', 'trialing']
    
    def is_on_trial(self) -> bool:
        """Check if currently on trial"""
        if not self.trial_end:
            return False
        return date.today() <= self.trial_end


@dataclass
class PaymentIntent:
    """
    Payment intent for one-time or subscription payments.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str = ""
    
    # Amount
    amount: float = 0.0
    currency: str = "USD"
    
    # Type
    payment_type: str = "subscription"  # subscription, one_time, invoice
    
    # Status
    status: PaymentStatus = PaymentStatus.PENDING
    client_secret: str = ""  # Stripe client secret for frontend
    
    # Related entities
    subscription_id: Optional[str] = None
    invoice_id: Optional[str] = None
    
    # Payment method
    payment_method_id: Optional[str] = None
    
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'amount': self.amount,
            'currency': self.currency,
            'status': self.status.value,
            'client_secret': self.client_secret,
            'payment_type': self.payment_type,
            'created_at': self.created_at.isoformat(),
        }


@dataclass
class Refund:
    """
    Payment refund.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    invoice_id: str = ""
    payment_intent_id: str = ""
    
    amount: float = 0.0
    reason: str = ""
    status: PaymentStatus = PaymentStatus.PENDING
    
    provider_refund_id: str = ""
    
    created_at: datetime = field(default_factory=datetime.now)
    processed_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'invoice_id': self.invoice_id,
            'amount': self.amount,
            'reason': self.reason,
            'status': self.status.value,
            'created_at': self.created_at.isoformat(),
            'processed_at': self.processed_at.isoformat() if self.processed_at else None,
        }
