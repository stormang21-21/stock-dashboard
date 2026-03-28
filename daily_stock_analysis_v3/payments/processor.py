"""
Payment Processor

Orchestrates payment flow between tenants and gateway.
"""

from typing import Optional, Dict, Any, List
from datetime import date, datetime, timedelta
import logging

logger = logging.getLogger(__name__)

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from payments.gateway import PaymentGateway, get_payment_gateway
from payments.models import (
    Subscription, Invoice, PaymentMethod, PaymentIntent,
    PaymentStatus, BillingPeriod, Refund
)


class PaymentProcessor:
    """
    Payment processing orchestrator.
    
    Handles:
    - Subscription lifecycle
    - Invoice generation
    - Payment processing
    - Refunds
    """
    
    def __init__(self):
        self.gateway = get_payment_gateway()
        self.subscriptions: Dict[str, Subscription] = {}
        self.invoices: Dict[str, Invoice] = {}
        self.payment_methods: Dict[str, PaymentMethod] = {}
        self.payment_intents: Dict[str, PaymentIntent] = {}
        self.customers: Dict[str, str] = {}  # tenant_id -> customer_id
        logger.info("PaymentProcessor initialized")
    
    def setup_customer(self, tenant_id: str, email: str, name: str) -> str:
        """
        Setup Stripe customer for tenant.
        
        Args:
            tenant_id: Tenant ID
            email: Email
            name: Name
            
        Returns:
            Customer ID
        """
        # Check if already exists
        if tenant_id in self.customers:
            return self.customers[tenant_id]
        
        # Create customer
        customer = self.gateway.create_customer(
            tenant_id=tenant_id,
            email=email,
            name=name,
        )
        
        self.customers[tenant_id] = customer['id']
        logger.info(f"Customer setup: {tenant_id} -> {customer['id']}")
        
        return customer['id']
    
    def create_subscription(
        self,
        tenant_id: str,
        plan_tier: str,
        payment_method_id: str,
        trial_days: int = 0,
    ) -> Dict[str, Any]:
        """
        Create subscription for tenant.
        
        Args:
            tenant_id: Tenant ID
            plan_tier: Plan tier
            payment_method_id: Payment method ID
            trial_days: Trial period
            
        Returns:
            Subscription result
        """
        # Ensure customer exists
        if tenant_id not in self.customers:
            return {
                'success': False,
                'error': 'Customer not setup. Call setup_customer first.',
            }
        
        customer_id = self.customers[tenant_id]
        
        # Create subscription in Stripe
        try:
            sub_data = self.gateway.create_subscription(
                customer_id=customer_id,
                plan_tier=plan_tier,
                payment_method_id=payment_method_id,
                trial_days=trial_days,
            )
            
            # Create local subscription record
            subscription = Subscription(
                tenant_id=tenant_id,
                plan_tier=plan_tier,
                plan_amount=self.gateway.plans.get(plan_tier, {}).get('price', 0) / 100,
                status=sub_data['status'],
                provider_subscription_id=sub_data['id'],
            )
            
            if sub_data.get('trial_end'):
                subscription.trial_start = date.today()
                subscription.trial_end = date.fromisoformat(sub_data['trial_end'])
            
            subscription.current_period_end = date.fromisoformat(sub_data['current_period_end'])
            
            self.subscriptions[subscription.id] = subscription
            
            logger.info(f"Subscription created: {subscription.id} for {tenant_id}")
            
            return {
                'success': True,
                'subscription_id': subscription.id,
                'subscription': subscription.to_dict(),
                'trial_end': sub_data.get('trial_end'),
            }
            
        except Exception as e:
            logger.error(f"Subscription creation failed: {e}")
            return {
                'success': False,
                'error': str(e),
            }
    
    def create_payment_intent(
        self,
        tenant_id: str,
        amount: float,
        payment_type: str = 'subscription',
    ) -> Dict[str, Any]:
        """
        Create payment intent.
        
        Args:
            tenant_id: Tenant ID
            amount: Amount in dollars
            payment_type: Payment type
            
        Returns:
            Payment intent with client_secret
        """
        if tenant_id not in self.customers:
            return {
                'success': False,
                'error': 'Customer not setup',
            }
        
        customer_id = self.customers[tenant_id]
        amount_cents = int(amount * 100)
        
        try:
            intent_data = self.gateway.create_payment_intent(
                customer_id=customer_id,
                amount=amount_cents,
                metadata={'tenant_id': tenant_id},
            )
            
            # Create local record
            intent = PaymentIntent(
                tenant_id=tenant_id,
                amount=amount,
                payment_type=payment_type,
                client_secret=intent_data['client_secret'],
            )
            
            self.payment_intents[intent.id] = intent
            
            return {
                'success': True,
                'payment_intent': intent.to_dict(),
            }
            
        except Exception as e:
            logger.error(f"Payment intent creation failed: {e}")
            return {
                'success': False,
                'error': str(e),
            }
    
    def create_invoice(
        self,
        tenant_id: str,
        amount: float,
        description: str,
        due_days: int = 30,
    ) -> Dict[str, Any]:
        """
        Create invoice.
        
        Args:
            tenant_id: Tenant ID
            amount: Amount in dollars
            description: Description
            due_days: Days until due
            
        Returns:
            Invoice with hosted URL
        """
        if tenant_id not in self.customers:
            return {
                'success': False,
                'error': 'Customer not setup',
            }
        
        customer_id = self.customers[tenant_id]
        amount_cents = int(amount * 100)
        
        try:
            invoice_data = self.gateway.create_invoice(
                customer_id=customer_id,
                amount=amount_cents,
                description=description,
            )
            
            # Create local invoice
            invoice = Invoice(
                tenant_id=tenant_id,
                amount=amount,
                total_amount=amount,
                description=description,
                provider_invoice_id=invoice_data['id'],
                period_start=date.today(),
                period_end=date.today() + timedelta(days=due_days),
            )
            
            self.invoices[invoice.id] = invoice
            
            return {
                'success': True,
                'invoice': invoice.to_dict(),
                'hosted_invoice_url': invoice_data.get('hosted_invoice_url'),
            }
            
        except Exception as e:
            logger.error(f"Invoice creation failed: {e}")
            return {
                'success': False,
                'error': str(e),
            }
    
    def cancel_subscription(self, subscription_id: str, at_period_end: bool = True) -> Dict[str, Any]:
        """Cancel subscription"""
        if subscription_id not in self.subscriptions:
            return {
                'success': False,
                'error': 'Subscription not found',
            }
        
        subscription = self.subscriptions[subscription_id]
        
        try:
            result = self.gateway.cancel_subscription(
                subscription.provider_subscription_id,
                at_period_end=at_period_end,
            )
            
            subscription.cancel_at_period_end = at_period_end
            subscription.status = result['status']
            
            if not at_period_end:
                subscription.cancelled_at = datetime.now()
            
            return {
                'success': True,
                'subscription': subscription.to_dict(),
            }
            
        except Exception as e:
            logger.error(f"Subscription cancellation failed: {e}")
            return {
                'success': False,
                'error': str(e),
            }
    
    def get_subscription(self, tenant_id: str) -> Optional[Subscription]:
        """Get subscription for tenant"""
        for sub in self.subscriptions.values():
            if sub.tenant_id == tenant_id:
                return sub
        return None
    
    def get_invoices(self, tenant_id: str) -> List[Invoice]:
        """Get invoices for tenant"""
        return [inv for inv in self.invoices.values() if inv.tenant_id == tenant_id]
    
    def process_webhook(self, payload: bytes, sig_header: str) -> Dict[str, Any]:
        """Process webhook from payment gateway"""
        try:
            event = self.gateway.process_webhook(payload, sig_header)
            
            # Handle different event types
            if event['type'] == 'invoice.payment_succeeded':
                # Mark invoice as paid
                invoice_data = event['data']
                for invoice in self.invoices.values():
                    if invoice.provider_invoice_id == invoice_data.get('id'):
                        invoice.status = PaymentStatus.COMPLETED
                        invoice.paid_at = datetime.now()
                        break
            
            elif event['type'] == 'customer.subscription.updated':
                # Update subscription status
                sub_data = event['data']
                for sub in self.subscriptions.values():
                    if sub.provider_subscription_id == sub_data.get('id'):
                        sub.status = sub_data.get('status', sub.status)
                        break
            
            logger.info(f"Webhook processed: {event['type']}")
            
            return {
                'success': True,
                'event': event,
            }
            
        except Exception as e:
            logger.error(f"Webhook processing failed: {e}")
            return {
                'success': False,
                'error': str(e),
            }


# Global processor instance
payment_processor = PaymentProcessor()


def get_payment_processor() -> PaymentProcessor:
    """Get payment processor instance"""
    return payment_processor
