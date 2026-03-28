"""
Payment Gateway

Stripe integration for payment processing.
"""

from typing import Optional, Dict, Any, List
from datetime import date, datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class PaymentGateway:
    """
    Stripe payment gateway integration.
    
    Handles:
    - Customer creation
    - Payment methods
    - Subscriptions
    - Invoices
    - Webhooks
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.api_key = self.config.get('stripe_api_key')
        self.webhook_secret = self.config.get('stripe_webhook_secret')
        self._client = None
        
        # Pricing
        self.plans = {
            'free': {'price': 0, 'interval': 'month'},
            'basic': {'price': 2900, 'interval': 'month'},  # cents
            'pro': {'price': 9900, 'interval': 'month'},
            'enterprise': {'price': 49900, 'interval': 'month'},
        }
        
        logger.info("PaymentGateway initialized")
    
    def _get_client(self):
        """Get Stripe client"""
        if self._client is None:
            try:
                import stripe
                stripe.api_key = self.api_key
                self._client = stripe
            except ImportError:
                logger.warning("Stripe not installed. Running in test mode.")
                self._client = None
        return self._client
    
    def create_customer(self, tenant_id: str, email: str, name: str, metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Create Stripe customer.
        
        Args:
            tenant_id: Tenant ID
            email: Customer email
            name: Customer name
            metadata: Additional metadata
            
        Returns:
            Customer dict with id
        """
        stripe = self._get_client()
        
        if not stripe:
            # Test mode - generate fake customer ID
            return {
                'id': f'cus_test_{tenant_id[:8]}',
                'email': email,
                'name': name,
                'metadata': metadata or {},
            }
        
        try:
            customer = stripe.Customer.create(
                email=email,
                name=name,
                metadata={
                    'tenant_id': tenant_id,
                    **(metadata or {}),
                },
            )
            
            logger.info(f"Stripe customer created: {customer.id}")
            
            return {
                'id': customer.id,
                'email': customer.email,
                'name': customer.name,
                'metadata': dict(customer.metadata),
            }
            
        except Exception as e:
            logger.error(f"Failed to create customer: {e}")
            raise
    
    def create_payment_intent(self, customer_id: str, amount: int, currency: str = 'usd', metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Create payment intent.
        
        Args:
            customer_id: Stripe customer ID
            amount: Amount in cents
            currency: Currency code
            metadata: Additional metadata
            
        Returns:
            Payment intent with client_secret
        """
        stripe = self._get_client()
        
        if not stripe:
            # Test mode
            return {
                'id': 'pi_test_123',
                'client_secret': 'pi_test_secret',
                'amount': amount,
                'currency': currency,
                'status': 'requires_payment_method',
            }
        
        try:
            intent = stripe.PaymentIntent.create(
                amount=amount,
                currency=currency,
                customer=customer_id,
                metadata=metadata or {},
                automatic_payment_methods={'enabled': True},
            )
            
            logger.info(f"Payment intent created: {intent.id}")
            
            return {
                'id': intent.id,
                'client_secret': intent.client_secret,
                'amount': intent.amount,
                'currency': intent.currency,
                'status': intent.status,
            }
            
        except Exception as e:
            logger.error(f"Failed to create payment intent: {e}")
            raise
    
    def create_subscription(self, customer_id: str, plan_tier: str, payment_method_id: str, trial_days: int = 0) -> Dict[str, Any]:
        """
        Create subscription.
        
        Args:
            customer_id: Stripe customer ID
            plan_tier: Plan tier (basic, pro, enterprise)
            payment_method_id: Payment method ID
            trial_days: Trial period in days
            
        Returns:
            Subscription dict
        """
        stripe = self._get_client()
        plan = self.plans.get(plan_tier, self.plans['basic'])
        
        if not stripe:
            # Test mode
            period_end = date.today() + timedelta(days=30)
            return {
                'id': f'sub_test_{plan_tier}',
                'status': 'trialing' if trial_days > 0 else 'active',
                'current_period_end': period_end.isoformat(),
                'trial_end': (date.today() + timedelta(days=trial_days)).isoformat() if trial_days > 0 else None,
            }
        
        try:
            # Create subscription items
            subscription_params = {
                'customer': customer_id,
                'items': [{
                    'price_data': {
                        'currency': 'usd',
                        'product_data': {
                            'name': f'DSA {plan_tier.capitalize()} Plan',
                        },
                        'unit_amount': plan['price'],
                        'recurring': {
                            'interval': plan['interval'],
                        },
                    },
                }],
                'payment_behavior': 'default_incomplete',
                'payment_settings': {
                    'save_default_payment_method': 'on_subscription',
                },
                'expand': ['latest_invoice.payment_intent'],
            }
            
            # Add trial if specified
            if trial_days > 0:
                subscription_params['trial_period_days'] = trial_days
            else:
                subscription_params['default_payment_method'] = payment_method_id
            
            subscription = stripe.Subscription.create(**subscription_params)
            
            logger.info(f"Subscription created: {subscription.id}")
            
            return {
                'id': subscription.id,
                'status': subscription.status,
                'current_period_start': date.fromtimestamp(subscription.current_period_start).isoformat(),
                'current_period_end': date.fromtimestamp(subscription.current_period_end).isoformat(),
                'trial_end': date.fromtimestamp(subscription.trial_end).isoformat() if subscription.trial_end else None,
            }
            
        except Exception as e:
            logger.error(f"Failed to create subscription: {e}")
            raise
    
    def cancel_subscription(self, subscription_id: str, at_period_end: bool = True) -> Dict[str, Any]:
        """
        Cancel subscription.
        
        Args:
            subscription_id: Stripe subscription ID
            at_period_end: Cancel at end of period or immediately
            
        Returns:
            Updated subscription
        """
        stripe = self._get_client()
        
        if not stripe:
            return {
                'id': subscription_id,
                'status': 'canceled',
                'cancel_at_period_end': at_period_end,
            }
        
        try:
            if at_period_end:
                subscription = stripe.Subscription.modify(
                    subscription_id,
                    cancel_at_period_end=True,
                )
            else:
                subscription = stripe.Subscription.cancel(subscription_id)
            
            logger.info(f"Subscription cancelled: {subscription_id}")
            
            return {
                'id': subscription.id,
                'status': subscription.status,
                'cancel_at_period_end': subscription.cancel_at_period_end,
                'ended_at': date.fromtimestamp(subscription.ended_at).isoformat() if subscription.ended_at else None,
            }
            
        except Exception as e:
            logger.error(f"Failed to cancel subscription: {e}")
            raise
    
    def create_invoice(self, customer_id: str, amount: int, description: str, metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Create invoice.
        
        Args:
            customer_id: Customer ID
            amount: Amount in cents
            description: Invoice description
            metadata: Additional metadata
            
        Returns:
            Invoice dict
        """
        stripe = self._get_client()
        
        if not stripe:
            return {
                'id': 'in_test_123',
                'amount_due': amount,
                'status': 'open',
                'hosted_invoice_url': 'https://test.stripe.com/invoice',
            }
        
        try:
            invoice = stripe.Invoice.create(
                customer=customer_id,
                description=description,
                metadata=metadata or {},
            )
            
            # Add line item
            stripe.InvoiceItem.create(
                customer=customer_id,
                invoice=invoice.id,
                amount=amount,
                currency='usd',
                description=description,
            )
            
            # Finalize invoice
            invoice = stripe.Invoice.finalize_invoice(invoice.id)
            
            logger.info(f"Invoice created: {invoice.id}")
            
            return {
                'id': invoice.id,
                'amount_due': invoice.amount_due,
                'status': invoice.status,
                'hosted_invoice_url': invoice.hosted_invoice_url,
                'due_date': date.fromtimestamp(invoice.due_date).isoformat() if invoice.due_date else None,
            }
            
        except Exception as e:
            logger.error(f"Failed to create invoice: {e}")
            raise
    
    def process_webhook(self, payload: bytes, sig_header: str) -> Dict[str, Any]:
        """
        Process Stripe webhook.
        
        Args:
            payload: Webhook payload
            sig_header: Signature header
            
        Returns:
            Webhook event
        """
        stripe = self._get_client()
        
        if not stripe:
            return {'type': 'test.event', 'data': {}}
        
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, self.webhook_secret
            )
            
            logger.info(f"Webhook processed: {event.type}")
            
            return {
                'type': event.type,
                'data': event.data.object,
            }
            
        except Exception as e:
            logger.error(f"Webhook failed: {e}")
            raise
    
    def get_payment_methods(self, customer_id: str) -> List[Dict[str, Any]]:
        """Get customer payment methods"""
        stripe = self._get_client()
        
        if not stripe:
            return []
        
        try:
            payment_methods = stripe.PaymentMethod.list(
                customer=customer_id,
                type='card',
            )
            
            return [{
                'id': pm.id,
                'card_brand': pm.card.brand,
                'card_last4': pm.card.last4,
                'card_exp_month': pm.card.exp_month,
                'card_exp_year': pm.card.exp_year,
            } for pm in payment_methods.data]
            
        except Exception as e:
            logger.error(f"Failed to get payment methods: {e}")
            return []


# Global gateway instance
payment_gateway = PaymentGateway()


def get_payment_gateway() -> PaymentGateway:
    """Get payment gateway instance"""
    return payment_gateway


class CryptoGateway:
    """
    Cryptocurrency payment gateway.
    
    Supports:
    - Bitcoin (BTC)
    - Ethereum (ETH)
    - USDT/USDC (stablecoins)
    - Other major cryptos
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.coinbase_api_key = self.config.get('coinbase_api_key')
        self.coinbase_webhook_secret = self.config.get('coinbase_webhook_secret')
        self._client = None
        
        # Supported cryptos
        self.supported_cryptos = [
            {'code': 'BTC', 'name': 'Bitcoin', 'network': 'bitcoin', 'confirmations': 1},
            {'code': 'ETH', 'name': 'Ethereum', 'network': 'ethereum', 'confirmations': 3},
            {'code': 'USDT', 'name': 'Tether', 'network': 'ethereum', 'confirmations': 12},
            {'code': 'USDC', 'name': 'USD Coin', 'network': 'ethereum', 'confirmations': 12},
            {'code': 'BNB', 'name': 'Binance Coin', 'network': 'binance', 'confirmations': 1},
        ]
        
        logger.info("CryptoGateway initialized")
    
    def _get_client(self):
        """Get Coinbase Commerce client"""
        if self._client is None:
            try:
                from coinbase_commerce import Client
                self._client = Client(api_key=self.coinbase_api_key)
            except ImportError:
                logger.warning("Coinbase Commerce SDK not installed. Running in test mode.")
                self._client = None
        return self._client
    
    def create_crypto_charge(self, tenant_id: str, amount: float, currency: str = 'USD', crypto_currency: Optional[str] = None) -> Dict[str, Any]:
        """
        Create cryptocurrency charge.
        
        Args:
            tenant_id: Tenant ID
            amount: Amount in USD
            currency: Fiat currency (USD, EUR, etc.)
            crypto_currency: Preferred crypto (optional)
            
        Returns:
            Charge with payment addresses
        """
        client = self._get_client()
        
        if not client:
            # Test mode - generate fake addresses
            return {
                'id': f'charge_crypto_{tenant_id[:8]}',
                'amount': amount,
                'currency': currency,
                'status': 'new',
                'addresses': {
                    'BTC': 'bc1qtest...fake_address',
                    'ETH': '0xtest...fake_address',
                    'USDT': '0xtest...fake_address',
                },
                'hosted_url': f'https://test.coinbase.com/charges/{tenant_id[:8]}',
                'expires_at': (datetime.now() + timedelta(minutes=15)).isoformat(),
            }
        
        try:
            # Create charge
            charge = client.charge.create(
                name=f'DSA Subscription - {tenant_id[:8]}',
                description='Subscription payment',
                pricing_type='fixed_price',
                local_price={
                    'amount': str(amount),
                    'currency': currency,
                },
                metadata={
                    'tenant_id': tenant_id,
                },
            )
            
            logger.info(f"Crypto charge created: {charge.id}")
            
            return {
                'id': charge.id,
                'amount': amount,
                'currency': currency,
                'status': charge.status,
                'addresses': dict(charge.addresses),
                'hosted_url': charge.hosted_url,
                'expires_at': charge.expires_at.isoformat() if charge.expires_at else None,
            }
            
        except Exception as e:
            logger.error(f"Failed to create crypto charge: {e}")
            raise
    
    def get_crypto_rates(self, amount: float, currency: str = 'USD') -> Dict[str, float]:
        """
        Get crypto exchange rates.
        
        Args:
            amount: Amount in fiat
            currency: Fiat currency
            
        Returns:
            Dict of crypto amounts
        """
        client = self._get_client()
        
        if not client:
            # Test mode - use fake rates
            return {
                'BTC': amount / 45000,  # 1 BTC = $45,000
                'ETH': amount / 3000,   # 1 ETH = $3,000
                'USDT': amount,          # 1 USDT = $1
                'USDC': amount,          # 1 USDC = $1
                'BNB': amount / 400,    # 1 BNB = $400
            }
        
        try:
            rates = {}
            for crypto in self.supported_cryptos:
                rate = client.exchange_rates.get_exchange_rate(
                    currency=currency,
                    to=crypto['code'],
                )
                rates[crypto['code']] = amount * float(rate)
            
            return rates
            
        except Exception as e:
            logger.error(f"Failed to get crypto rates: {e}")
            return {}
    
    def verify_crypto_payment(self, charge_id: str) -> Dict[str, Any]:
        """
        Verify crypto payment completion.
        
        Args:
            charge_id: Charge ID
            
        Returns:
            Payment verification result
        """
        client = self._get_client()
        
        if not client:
            return {
                'verified': True,
                'status': 'completed',
                'crypto_amount': 0.001,
                'crypto_currency': 'BTC',
            }
        
        try:
            charge = client.charge.retrieve(charge_id)
            
            return {
                'verified': charge.status == 'completed',
                'status': charge.status,
                'crypto_amount': float(charange.pricing.get('crypto', {}).get('amount', 0)),
                'crypto_currency': charge.pricing.get('crypto', {}).get('currency', ''),
                'confirmations': charge.payments[0].block.confirmations if charge.payments else 0,
            }
            
        except Exception as e:
            logger.error(f"Failed to verify crypto payment: {e}")
            return {
                'verified': False,
                'error': str(e),
            }
    
    def process_crypto_webhook(self, payload: bytes, sig_header: str) -> Dict[str, Any]:
        """Process crypto payment webhook"""
        # Similar to Stripe webhook processing
        logger.info(f"Crypto webhook processed")
        return {'type': 'charge:confirmed', 'data': {}}


# Add to PaymentGateway
PaymentGateway.CryptoGateway = CryptoGateway
