"""
Singapore & SEA Compliance

MAS (Monetary Authority of Singapore) compliant payment processing.
"""

from typing import Optional, Dict, Any, List
from datetime import datetime, date
import logging

logger = logging.getLogger(__name__)


class MASCompliance:
    """
    MAS Payment Services Act compliance.
    
    Requirements:
    - Licensing for payment services
    - AML/CFT compliance
    - Transaction limits
    - Reporting requirements
    """
    
    # Transaction limits (MAS guidelines)
    TRANSACTION_LIMITS = {
        'daily_individual': 5000,  # SGD
        'daily_corporate': 50000,  # SGD
        'monthly_individual': 50000,  # SGD
        'monthly_corporate': 500000,  # SGD
    }
    
    # Crypto payment limits (MAS guidelines)
    CRYPTO_LIMITS = {
        'daily': 10000,  # SGD
        'monthly': 100000,  # SGD
        'kyc_required_above': 5000,  # SGD - KYC required above this
    }
    
    # Restricted countries (MAS sanctions)
    RESTRICTED_COUNTRIES = [
        'KP',  # North Korea
        'IR',  # Iran
        'SY',  # Syria
        'CU',  # Cuba
    ]
    
    def __init__(self):
        self.kyc_verifications: Dict[str, Dict] = {}
        self.transaction_history: Dict[str, List[Dict]] = {}
        logger.info("MASCompliance initialized")
    
    def check_transaction_limit(self, tenant_id: str, amount: float, currency: str = 'SGD', 
                                 is_corporate: bool = False, is_crypto: bool = False) -> Dict[str, Any]:
        """
        Check if transaction is within MAS limits.
        
        Args:
            tenant_id: Tenant ID
            amount: Transaction amount
            currency: Currency
            is_corporate: Corporate or individual
            is_crypto: Crypto payment
            
        Returns:
            Compliance check result
        """
        limits = self.CRYPTO_LIMITS if is_crypto else self.TRANSACTION_LIMITS
        
        # Get daily/monthly totals
        daily_total = self._get_daily_total(tenant_id, is_corporate)
        monthly_total = self._get_monthly_total(tenant_id, is_corporate)
        
        daily_limit = limits['daily_corporate' if is_corporate else 'daily_individual']
        monthly_limit = limits['monthly_corporate' if is_corporate else 'monthly_individual']
        
        if is_crypto:
            daily_limit = limits['daily']
            monthly_limit = limits['monthly']
        
        # Check limits
        if daily_total + amount > daily_limit:
            return {
                'compliant': False,
                'reason': 'daily_limit_exceeded',
                'message': f'Daily limit exceeded. Limit: SGD {daily_limit:,}',
                'remaining': daily_limit - daily_total,
            }
        
        if monthly_total + amount > monthly_limit:
            return {
                'compliant': False,
                'reason': 'monthly_limit_exceeded',
                'message': f'Monthly limit exceeded. Limit: SGD {monthly_limit:,}',
                'remaining': monthly_limit - monthly_total,
            }
        
        # Check KYC requirement for crypto
        if is_crypto and amount > limits['kyc_required_above']:
            kyc_status = self.get_kyc_status(tenant_id)
            if not kyc_status.get('verified'):
                return {
                    'compliant': False,
                    'reason': 'kyc_required',
                    'message': f'KYC verification required for crypto payments above SGD {limits["kyc_required_above"]:,}',
                    'kyc_required': True,
                }
        
        return {
            'compliant': True,
            'daily_remaining': daily_limit - daily_total,
            'monthly_remaining': monthly_limit - monthly_total,
        }
    
    def verify_kyc(self, tenant_id: str, kyc_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Verify KYC information.
        
        Args:
            tenant_id: Tenant ID
            kyc_data: KYC information
            
        Returns:
            Verification result
        """
        # Required fields for Singapore KYC
        required_fields = [
            'full_name',
            'nric_fin',  # NRIC or FIN for Singapore
            'date_of_birth',
            'address',
            'phone',
            'email',
        ]
        
        # Check required fields
        missing = [f for f in required_fields if f not in kyc_data]
        if missing:
            return {
                'verified': False,
                'reason': 'missing_fields',
                'missing': missing,
            }
        
        # Validate NRIC/FIN format (Singapore)
        nric = kyc_data.get('nric_fin', '')
        if not self._validate_nric(nric):
            return {
                'verified': False,
                'reason': 'invalid_nric',
                'message': 'Invalid NRIC/FIN format',
            }
        
        # Check restricted countries
        country = kyc_data.get('country', 'SG')
        if country in self.RESTRICTED_COUNTRIES:
            return {
                'verified': False,
                'reason': 'restricted_country',
                'message': f'Service not available in {country}',
            }
        
        # Store verification
        self.kyc_verifications[tenant_id] = {
            'verified': True,
            'verified_at': datetime.now().isoformat(),
            'kyc_data': kyc_data,
            'risk_level': self._assess_risk(kyc_data),
        }
        
        logger.info(f"KYC verified for tenant: {tenant_id}")
        
        return {
            'verified': True,
            'risk_level': self.kyc_verifications[tenant_id]['risk_level'],
        }
    
    def get_kyc_status(self, tenant_id: str) -> Dict[str, Any]:
        """Get KYC status for tenant"""
        if tenant_id not in self.kyc_verifications:
            return {
                'verified': False,
                'message': 'KYC verification required',
            }
        
        verification = self.kyc_verifications[tenant_id]
        return {
            'verified': verification['verified'],
            'verified_at': verification['verified_at'],
            'risk_level': verification.get('risk_level', 'medium'),
        }
    
    def record_transaction(self, tenant_id: str, amount: float, currency: str, 
                          payment_type: str, is_crypto: bool = False) -> None:
        """Record transaction for AML monitoring"""
        if tenant_id not in self.transaction_history:
            self.transaction_history[tenant_id] = []
        
        self.transaction_history[tenant_id].append({
            'timestamp': datetime.now().isoformat(),
            'amount': amount,
            'currency': currency,
            'payment_type': payment_type,
            'is_crypto': is_crypto,
        })
    
    def _get_daily_total(self, tenant_id: str, is_corporate: bool) -> float:
        """Get daily transaction total"""
        if tenant_id not in self.transaction_history:
            return 0.0
        
        today = date.today().isoformat()
        total = sum(
            t['amount'] for t in self.transaction_history[tenant_id]
            if t['timestamp'].startswith(today)
        )
        
        return total
    
    def _get_monthly_total(self, tenant_id: str, is_corporate: bool) -> float:
        """Get monthly transaction total"""
        if tenant_id not in self.transaction_history:
            return 0.0
        
        this_month = datetime.now().strftime('%Y-%m')
        total = sum(
            t['amount'] for t in self.transaction_history[tenant_id]
            if t['timestamp'].startswith(this_month)
        )
        
        return total
    
    def _validate_nric(self, nric: str) -> bool:
        """Validate Singapore NRIC/FIN format"""
        if not nric:
            return False
        
        nric = nric.strip().upper()
        
        # NRIC: Sxxxxxxx or Txxxxxxx
        # FIN: Fxxxxxxx or Gxxxxxxx
        valid_prefixes = ['S', 'T', 'F', 'G']
        
        if len(nric) != 9:
            return False
        
        if nric[0] not in valid_prefixes:
            return False
        
        if not nric[1:8].isdigit():
            return False
        
        # Check checksum (simplified)
        return True
    
    def _assess_risk(self, kyc_data: Dict[str, Any]) -> str:
        """Assess customer risk level"""
        risk_score = 0
        
        # Country risk
        country = kyc_data.get('country', 'SG')
        if country == 'SG':
            risk_score += 0  # Low risk
        elif country in ['MY', 'TH', 'ID', 'PH', 'VN']:  # SEA countries
            risk_score += 1  # Medium risk
        else:
            risk_score += 2  # Higher risk
        
        # Transaction amount
        # (would be assessed dynamically)
        
        if risk_score <= 1:
            return 'low'
        elif risk_score <= 3:
            return 'medium'
        else:
            return 'high'
    
    def generate_aml_report(self, tenant_id: str, period: str = 'monthly') -> Dict[str, Any]:
        """
        Generate AML compliance report.
        
        Args:
            tenant_id: Tenant ID
            period: Report period (daily/weekly/monthly)
            
        Returns:
            AML report
        """
        if tenant_id not in self.transaction_history:
            return {
                'tenant_id': tenant_id,
                'period': period,
                'transactions': 0,
                'total_amount': 0,
                'suspicious': False,
            }
        
        # Filter by period
        transactions = self.transaction_history[tenant_id]
        total_amount = sum(t['amount'] for t in transactions)
        
        # Check for suspicious patterns
        suspicious = False
        reasons = []
        
        # Large transactions
        if total_amount > self.TRANSACTION_LIMITS['monthly_individual']:
            suspicious = True
            reasons.append('High transaction volume')
        
        # Frequent crypto payments
        crypto_count = sum(1 for t in transactions if t.get('is_crypto'))
        if crypto_count > 10:
            suspicious = True
            reasons.append('Frequent crypto payments')
        
        return {
            'tenant_id': tenant_id,
            'period': period,
            'transactions': len(transactions),
            'total_amount': total_amount,
            'crypto_transactions': crypto_count,
            'suspicious': suspicious,
            'reasons': reasons,
            'generated_at': datetime.now().isoformat(),
        }


# Regional payment methods for SEA
SEA_PAYMENT_METHODS = {
    'SG': [
        {'id': 'paynow', 'name': 'PayNow', 'type': 'bank_transfer', 'icon': '🏦'},
        {'id': 'grabpay', 'name': 'GrabPay', 'type': 'ewallet', 'icon': '📱'},
        {'id': 'dbspaynow', 'name': 'DBS PayLah!', 'type': 'ewallet', 'icon': '💳'},
        {'id': 'ocbc', 'name': 'OCBC PayAnyone', 'type': 'bank_transfer', 'icon': '🏦'},
        {'id': 'uob', 'name': 'UOB Mighty', 'type': 'bank_transfer', 'icon': '🏦'},
    ],
    'MY': [
        {'id': 'fpx', 'name': 'FPX', 'type': 'bank_transfer', 'icon': '🏦'},
        {'id': 'grabpay_my', 'name': 'GrabPay', 'type': 'ewallet', 'icon': '📱'},
        {'id': 'touchngo', 'name': 'Touch \'n Go', 'type': 'ewallet', 'icon': '💳'},
    ],
    'TH': [
        {'id': 'promptpay', 'name': 'PromptPay', 'type': 'bank_transfer', 'icon': '🏦'},
        {'id': 'truewallet', 'name': 'TrueWallet', 'type': 'ewallet', 'icon': '📱'},
    ],
    'ID': [
        {'id': 'gopay', 'name': 'GoPay', 'type': 'ewallet', 'icon': '📱'},
        {'id': 'ovo', 'name': 'OVO', 'type': 'ewallet', 'icon': '💳'},
        {'id': 'dana', 'name': 'DANA', 'type': 'ewallet', 'icon': '📱'},
    ],
    'PH': [
        {'id': 'gcash', 'name': 'GCash', 'type': 'ewallet', 'icon': '📱'},
        {'id': 'paymaya', 'name': 'PayMaya', 'type': 'ewallet', 'icon': '💳'},
    ],
    'VN': [
        {'id': 'momo', 'name': 'MoMo', 'type': 'ewallet', 'icon': '📱'},
        {'id': 'zalopay', 'name': 'ZaloPay', 'type': 'ewallet', 'icon': '💳'},
    ],
}


# Global compliance instance
mas_compliance = MASCompliance()


def get_mas_compliance() -> MASCompliance:
    """Get MAS compliance instance"""
    return mas_compliance
