"""
Email Templates - Pre-designed HTML email templates
"""


class EmailTemplates:
    """Email template collection"""
    
    @staticmethod
    def _base_template(title: str, content: str, footer: str = "") -> str:
        """Base HTML template"""
        return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
        .content {{ background: #f8f9fa; padding: 30px; }}
        .button {{ display: inline-block; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
        .footer {{ background: #333; color: #aaa; padding: 20px; text-align: center; font-size: 12px; border-radius: 0 0 10px 10px; }}
        .highlight {{ background: #fff3cd; padding: 15px; border-left: 4px solid #ffc107; margin: 15px 0; }}
        .success {{ background: #d4edda; padding: 15px; border-left: 4px solid #28a745; margin: 15px 0; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>{title}</h1>
    </div>
    <div class="content">
        {content}
    </div>
    <div class="footer">
        {footer}
        <p>© 2026 Daily Stock Analysis. All rights reserved.</p>
        <p>You're receiving this email because you have a Daily Stock Analysis account.</p>
        <p><a href="#" style="color: #aaa;">Unsubscribe</a> | <a href="#" style="color: #aaa;">Privacy Policy</a></p>
    </div>
</body>
</html>
"""
    
    @staticmethod
    def welcome(user_name: str, api_key: str) -> str:
        """Welcome email template"""
        content = f"""
        <h2>Welcome to Daily Stock Analysis, {user_name}! 🎉</h2>
        
        <p>We're excited to have you on board! You now have access to AI-powered stock analysis from 6 global markets.</p>
        
        <div class="success">
            <strong>✅ Your Account is Ready!</strong>
            <p>Start analyzing stocks right away.</p>
        </div>
        
        <h3>Your API Key:</h3>
        <p style="background: #f0f0f0; padding: 10px; font-family: monospace; word-break: break-all;">{api_key}</p>
        <p><em>Keep this key secure! Don't share it with anyone.</em></p>
        
        <h3>Quick Start:</h3>
        <ol>
            <li><a href="http://localhost:8000/admin" class="button">Go to Dashboard</a></li>
            <li>Type a stock name (e.g., "Apple" or "AAPL")</li>
            <li>Click "Analyze"</li>
            <li>Get your AI-powered report!</li>
        </ol>
        
        <div class="highlight">
            <strong>💡 Pro Tip:</strong> Start with our Free plan to explore the platform. Upgrade anytime to unlock more features!
        </div>
        
        <p>Need help? Check out our <a href="http://localhost:8000/web/QUICK_START.md">Quick Start Guide</a> or reply to this email.</p>
        
        <p>Happy Investing! 🚀📈</p>
        <p><strong>The Daily Stock Analysis Team</strong></p>
        """
        
        footer = """
        <p>Daily Stock Analysis - AI-Powered Stock Analysis</p>
        <p>6 Markets | 20+ Payment Methods | MAS-Compliant</p>
        """
        
        return EmailTemplates._base_template("Welcome Aboard!", content, footer)
    
    @staticmethod
    def welcome_text(user_name: str, api_key: str) -> str:
        """Plain text welcome email"""
        return f"""
Welcome to Daily Stock Analysis, {user_name}! 🎉

We're excited to have you on board!

Your API Key: {api_key}
Keep this key secure!

Quick Start:
1. Go to: http://localhost:8000/admin
2. Type a stock name (e.g., "Apple" or "AAPL")
3. Click "Analyze"
4. Get your AI-powered report!

Need help? Check out our Quick Start Guide or reply to this email.

Happy Investing! 🚀📈

The Daily Stock Analysis Team
"""
    
    @staticmethod
    def payment_confirmation(plan: str, amount: float, transaction_id: str) -> str:
        """Payment confirmation template"""
        content = f"""
        <h2>Payment Successful! ✅</h2>
        
        <div class="success">
            <strong>Thank you for your payment!</strong>
            <p>Your {plan.capitalize()} plan is now active.</p>
        </div>
        
        <h3>Payment Details:</h3>
        <table style="width: 100%; border-collapse: collapse;">
            <tr>
                <td style="padding: 10px; border-bottom: 1px solid #ddd;"><strong>Plan:</strong></td>
                <td style="padding: 10px; border-bottom: 1px solid #ddd;">{plan.capitalize()}</td>
            </tr>
            <tr>
                <td style="padding: 10px; border-bottom: 1px solid #ddd;"><strong>Amount:</strong></td>
                <td style="padding: 10px; border-bottom: 1px solid #ddd;">${amount:.2f}/month</td>
            </tr>
            <tr>
                <td style="padding: 10px; border-bottom: 1px solid #ddd;"><strong>Transaction ID:</strong></td>
                <td style="padding: 10px; border-bottom: 1px solid #ddd;">{transaction_id}</td>
            </tr>
            <tr>
                <td style="padding: 10px;"><strong>Date:</strong></td>
                <td style="padding: 10px;">{__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M')}</td>
            </tr>
        </table>
        
        <h3>What's Next?</h3>
        <p>You now have access to all {plan.capitalize()} plan features:</p>
        <ul>
            <li>✅ Unlimited AI analysis</li>
            <li>✅ Advanced portfolio tracking</li>
            <li>✅ Priority support</li>
        </ul>
        
        <p><a href="http://localhost:8000/admin" class="button">Go to Dashboard</a></p>
        
        <p>Questions? Reply to this email or contact support@dailystockanalysis.com</p>
        """
        
        footer = "<p>Payment processed securely by Stripe/Coinbase</p>"
        
        return EmailTemplates._base_template("Payment Confirmed", content, footer)
    
    @staticmethod
    def payment_confirmation_text(plan: str, amount: float, transaction_id: str) -> str:
        """Plain text payment confirmation"""
        return f"""
Payment Successful! ✅

Thank you for your payment!
Your {plan.capitalize()} plan is now active.

Payment Details:
- Plan: {plan.capitalize()}
- Amount: ${amount:.2f}/month
- Transaction ID: {transaction_id}

You now have access to all {plan.capitalize()} plan features!

Go to Dashboard: http://localhost:8000/admin

Questions? Reply to this email.
"""
    
    @staticmethod
    def password_reset(reset_link: str, expires_in: int) -> str:
        """Password reset template"""
        expires_hours = expires_in // 3600
        
        content = f"""
        <h2>Reset Your Password</h2>
        
        <p>We received a request to reset your password. Click the button below to reset it:</p>
        
        <p><a href="{reset_link}" class="button">Reset Password</a></p>
        
        <div class="highlight">
            <strong>⏰ This link expires in {expires_hours} hour(s)</strong>
        </div>
        
        <p>Or copy and paste this link into your browser:</p>
        <p style="background: #f0f0f0; padding: 10px; font-family: monospace; font-size: 12px; word-break: break-all;">{reset_link}</p>
        
        <p><strong>Didn't request this?</strong> Just ignore this email. Your password won't change.</p>
        """
        
        footer = "<p>For security, this link can only be used once.</p>"
        
        return EmailTemplates._base_template("Password Reset Request", content, footer)
    
    @staticmethod
    def password_reset_text(reset_link: str, expires_in: int) -> str:
        """Plain text password reset"""
        expires_hours = expires_in // 3600
        return f"""
Reset Your Password

We received a request to reset your password.

Reset Link: {reset_link}

This link expires in {expires_hours} hour(s).

Didn't request this? Just ignore this email.

For security, this link can only be used once.
"""
    
    @staticmethod
    def subscription_reminder(plan: str, days_until_renewal: int) -> str:
        """Subscription renewal reminder"""
        content = f"""
        <h2>Subscription Renewing Soon</h2>
        
        <p>Your {plan.capitalize()} plan will renew in <strong>{days_until_renewal} day(s)</strong>.</p>
        
        <div class="highlight">
            <strong>💳 Amount: $99.00</strong><br>
            Next billing date: {__import__('datetime').datetime.now().strftime('%Y-%m-%d')}
        </div>
        
        <h3>What's Included:</h3>
        <ul>
            <li>✅ Unlimited AI analysis</li>
            <li>✅ All 6 global markets</li>
            <li>✅ Backtesting & risk analysis</li>
            <li>✅ Priority support</li>
        </ul>
        
        <p>Want to make changes?</p>
        <p><a href="http://localhost:8000/admin/subscription" class="button">Manage Subscription</a></p>
        
        <p>You can upgrade, downgrade, or cancel anytime.</p>
        """
        
        footer = "<p>Questions? Contact billing@dailystockanalysis.com</p>"
        
        return EmailTemplates._base_template("Subscription Renewal Notice", content, footer)
    
    @staticmethod
    def subscription_reminder_text(plan: str, days_until_renewal: int) -> str:
        """Plain text subscription reminder"""
        return f"""
Subscription Renewing Soon

Your {plan.capitalize()} plan will renew in {days_until_renewal} day(s).

Amount: $99.00
Next billing date: {__import__('datetime').datetime.now().strftime('%Y-%m-%d')}

Manage your subscription:
http://localhost:8000/admin/subscription

You can upgrade, downgrade, or cancel anytime.
"""
    
    @staticmethod
    def api_limit_warning(plan: str, usage_percent: float) -> str:
        """API usage warning"""
        content = f"""
        <h2>API Usage Alert</h2>
        
        <div class="highlight">
            <strong>⚠️ You've used {usage_percent:.0f}% of your daily API limit</strong>
        </div>
        
        <p>Your current plan ({plan.capitalize()}) includes:</p>
        <ul>
            <li>Free: 10 analyses/day</li>
            <li>Basic: 1,000 analyses/day</li>
            <li>Pro: 10,000 analyses/day</li>
        </ul>
        
        <h3>Need More?</h3>
        <p>Consider upgrading to get more API calls:</p>
        <p><a href="http://localhost:8000/upgrade" class="button">Upgrade Plan</a></p>
        
        <p>Usage resets at midnight (UTC).</p>
        """
        
        footer = "<p>Track your usage in Settings → API Usage</p>"
        
        return EmailTemplates._base_template("API Usage Alert", content, footer)
    
    @staticmethod
    def api_limit_warning_text(plan: str, usage_percent: float) -> str:
        """Plain text API warning"""
        return f"""
API Usage Alert

You've used {usage_percent:.0f}% of your daily API limit.

Your {plan.capitalize()} plan limits:
- Free: 10 analyses/day
- Basic: 1,000 analyses/day
- Pro: 10,000 analyses/day

Need more? Upgrade your plan:
http://localhost:8000/upgrade

Usage resets at midnight (UTC).
"""
    
    @staticmethod
    def trial_expiring(days_left: int, plan: str) -> str:
        """Trial expiring soon"""
        content = f"""
        <h2>Your Pro Trial Ends Soon! ⏰</h2>
        
        <div class="highlight">
            <strong>Only {days_left} day(s) left!</strong>
        </div>
        
        <p>You've been enjoying all Pro features:</p>
        <ul>
            <li>✅ All 6 global markets</li>
            <li>✅ Unlimited AI analysis</li>
            <li>✅ Backtesting</li>
            <li>✅ Risk analysis</li>
        </ul>
        
        <h3>Don't Lose Access!</h3>
        <p>Subscribe now to keep all Pro features:</p>
        <p><a href="http://localhost:8000/upgrade" class="button">Subscribe to Pro - $99/month</a></p>
        
        <div class="success">
            <strong>🎉 Special Offer:</strong> Subscribe today and get your first month at 20% off!
            <br>Use code: <strong>TRIAL20</strong>
        </div>
        
        <p>Questions? Reply to this email - we're here to help!</p>
        """
        
        footer = "<p>After trial ends, your account will revert to Free plan.</p>"
        
        return EmailTemplates._base_template("Trial Expiring Soon", content, footer)
    
    @staticmethod
    def trial_expiring_text(days_left: int, plan: str) -> str:
        """Plain text trial expiring"""
        return f"""
Your Pro Trial Ends Soon! ⏰

Only {days_left} day(s) left!

You've been enjoying all Pro features:
- All 6 global markets
- Unlimited AI analysis
- Backtesting
- Risk analysis

Don't lose access! Subscribe now:
http://localhost:8000/upgrade

Special Offer: Use code TRIAL20 for 20% off your first month!

After trial ends, your account will revert to Free plan.
"""
