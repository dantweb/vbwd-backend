#!/bin/bash
# Install demo data for development and testing
# Usage: ./bin/install_demo_data.sh
#
# Creates:
# - 2 currencies (EUR, USD)
# - 5 tarif plans (Free, Basic, Pro, Enterprise, Lifetime)
# - 2 demo users with subscriptions
# - 10 invoices with various statuses
# - 2 token bundles (100 tokens, 500 tokens)
# - 5 add-ons (3 global, 2 plan-dependent)

set -e

echo "Installing demo data..."

docker-compose exec -T api python << 'EOF'
import sys
sys.path.insert(0, '/app')

from datetime import datetime, timedelta
from decimal import Decimal
import bcrypt
import uuid

from src.extensions import Session
from src.models.user import User
from src.models.currency import Currency
from src.models.price import Price
from src.models.tarif_plan import TarifPlan
from src.models.subscription import Subscription
from src.models.invoice import UserInvoice
from src.models.addon import AddOn
from src.models.addon_subscription import AddOnSubscription
from src.models.token_bundle import TokenBundle
from src.models.enums import (
    UserStatus, UserRole, BillingPeriod,
    SubscriptionStatus, InvoiceStatus
)

session = Session()

try:
    print("\n=== Creating Currencies ===")

    # Check/create EUR currency
    eur = session.query(Currency).filter_by(code='EUR').first()
    if not eur:
        eur = Currency()
        eur.code = 'EUR'
        eur.name = 'Euro'
        eur.symbol = '€'
        eur.exchange_rate = Decimal('1.0')
        eur.is_default = True
        eur.is_active = True
        session.add(eur)
        session.flush()
        print(f"  Created: EUR (id={eur.id})")
    else:
        print(f"  Exists: EUR (id={eur.id})")

    # Check/create USD currency
    usd = session.query(Currency).filter_by(code='USD').first()
    if not usd:
        usd = Currency()
        usd.code = 'USD'
        usd.name = 'US Dollar'
        usd.symbol = '$'
        usd.exchange_rate = Decimal('1.08')
        usd.is_default = False
        usd.is_active = True
        session.add(usd)
        session.flush()
        print(f"  Created: USD (id={usd.id})")
    else:
        print(f"  Exists: USD (id={usd.id})")

    print("\n=== Creating Tarif Plans ===")

    plans_data = [
        {
            'name': 'Free',
            'slug': 'free',
            'description': 'Get started with basic features at no cost',
            'price': Decimal('0.00'),
            'billing_period': BillingPeriod.MONTHLY,
            'features': {'api_calls': 100, 'storage_gb': 1, 'support': 'community'},
            'sort_order': 0,
        },
        {
            'name': 'Basic',
            'slug': 'basic',
            'description': 'Perfect for individuals and small projects',
            'price': Decimal('9.99'),
            'billing_period': BillingPeriod.MONTHLY,
            'features': {'api_calls': 1000, 'storage_gb': 10, 'support': 'email'},
            'sort_order': 1,
        },
        {
            'name': 'Pro',
            'slug': 'pro',
            'description': 'Best for growing teams and businesses',
            'price': Decimal('29.99'),
            'billing_period': BillingPeriod.MONTHLY,
            'features': {'api_calls': 10000, 'storage_gb': 100, 'support': 'priority', 'analytics': True},
            'sort_order': 2,
        },
        {
            'name': 'Enterprise',
            'slug': 'enterprise',
            'description': 'Advanced features for large organizations',
            'price': Decimal('99.99'),
            'billing_period': BillingPeriod.MONTHLY,
            'features': {'api_calls': 'unlimited', 'storage_gb': 1000, 'support': 'dedicated', 'analytics': True, 'sso': True},
            'sort_order': 3,
        },
        {
            'name': 'Lifetime',
            'slug': 'lifetime',
            'description': 'One-time payment for lifetime access to Pro features',
            'price': Decimal('499.99'),
            'billing_period': BillingPeriod.ONE_TIME,
            'features': {'api_calls': 10000, 'storage_gb': 100, 'support': 'priority', 'analytics': True, 'lifetime': True},
            'sort_order': 4,
        },
    ]

    plans = {}
    for plan_data in plans_data:
        plan = session.query(TarifPlan).filter_by(slug=plan_data['slug']).first()
        if not plan:
            # Create Price object
            price_obj = Price()
            price_obj.price_float = float(plan_data['price'])
            price_obj.price_decimal = plan_data['price']
            price_obj.currency_id = eur.id
            price_obj.net_amount = plan_data['price']
            price_obj.gross_amount = plan_data['price']
            price_obj.taxes = {}
            session.add(price_obj)
            session.flush()

            # Create TarifPlan
            plan = TarifPlan()
            plan.name = plan_data['name']
            plan.slug = plan_data['slug']
            plan.description = plan_data['description']
            plan.price_float = float(plan_data['price'])
            plan.price_id = price_obj.id
            plan.price = plan_data['price']
            plan.currency = 'EUR'
            plan.billing_period = plan_data['billing_period']
            plan.features = plan_data['features']
            plan.is_active = True
            plan.sort_order = plan_data['sort_order']
            session.add(plan)
            session.flush()
            print(f"  Created: {plan.name} ({plan.slug}) - €{plan.price_float}")
        else:
            print(f"  Exists: {plan.name} ({plan.slug})")
        plans[plan_data['slug']] = plan

    print("\n=== Creating Demo Users ===")

    users_data = [
        {
            'email': 'user.free@demo.local',
            'password': 'demo123',
            'plan_slug': 'free',
        },
        {
            'email': 'user.pro@demo.local',
            'password': 'demo123',
            'plan_slug': 'pro',
        },
    ]

    users = {}
    for user_data in users_data:
        user = session.query(User).filter_by(email=user_data['email']).first()
        if not user:
            password_hash = bcrypt.hashpw(user_data['password'].encode(), bcrypt.gensalt()).decode()
            user = User()
            user.email = user_data['email']
            user.password_hash = password_hash
            user.status = UserStatus.ACTIVE
            user.role = UserRole.USER
            session.add(user)
            session.flush()
            print(f"  Created: {user.email} (id={user.id})")
        else:
            print(f"  Exists: {user.email} (id={user.id})")
        users[user_data['email']] = {'user': user, 'plan_slug': user_data['plan_slug']}

    print("\n=== Creating Subscriptions ===")

    for email, data in users.items():
        user = data['user']
        plan = plans[data['plan_slug']]

        # Check if subscription exists
        existing_sub = session.query(Subscription).filter_by(
            user_id=user.id,
            tarif_plan_id=plan.id,
            status=SubscriptionStatus.ACTIVE
        ).first()

        if not existing_sub:
            sub = Subscription()
            sub.user_id = user.id
            sub.tarif_plan_id = plan.id
            sub.status = SubscriptionStatus.ACTIVE
            sub.started_at = datetime.utcnow() - timedelta(days=15)
            sub.expires_at = datetime.utcnow() + timedelta(days=15)
            session.add(sub)
            session.flush()
            users[email]['subscription'] = sub
            print(f"  Created: {email} -> {plan.name} (sub_id={sub.id})")
        else:
            users[email]['subscription'] = existing_sub
            print(f"  Exists: {email} -> {plan.name}")

    print("\n=== Creating Invoices ===")

    # Define 10 invoices with various statuses and dates
    invoices_data = [
        # Paid invoices for Pro user
        {'user_email': 'user.pro@demo.local', 'status': InvoiceStatus.PAID, 'days_ago': 45, 'payment_method': 'stripe'},
        {'user_email': 'user.pro@demo.local', 'status': InvoiceStatus.PAID, 'days_ago': 15, 'payment_method': 'stripe'},
        {'user_email': 'user.pro@demo.local', 'status': InvoiceStatus.PENDING, 'days_ago': 0, 'payment_method': None},

        # Free user invoices (for plan upgrade attempts)
        {'user_email': 'user.free@demo.local', 'status': InvoiceStatus.PAID, 'days_ago': 60, 'payment_method': 'paypal', 'plan_slug': 'basic'},
        {'user_email': 'user.free@demo.local', 'status': InvoiceStatus.CANCELLED, 'days_ago': 30, 'payment_method': None, 'plan_slug': 'pro'},

        # More varied invoices
        {'user_email': 'user.pro@demo.local', 'status': InvoiceStatus.REFUNDED, 'days_ago': 75, 'payment_method': 'stripe'},
        {'user_email': 'user.pro@demo.local', 'status': InvoiceStatus.FAILED, 'days_ago': 50, 'payment_method': 'stripe'},
        {'user_email': 'user.free@demo.local', 'status': InvoiceStatus.PENDING, 'days_ago': 5, 'payment_method': None, 'plan_slug': 'basic'},
        {'user_email': 'user.pro@demo.local', 'status': InvoiceStatus.PAID, 'days_ago': 105, 'payment_method': 'paypal'},
        {'user_email': 'user.pro@demo.local', 'status': InvoiceStatus.PAID, 'days_ago': 135, 'payment_method': 'stripe'},
    ]

    invoice_count = session.query(UserInvoice).count()
    if invoice_count >= 10:
        print(f"  Already have {invoice_count} invoices, skipping creation")
    else:
        for i, inv_data in enumerate(invoices_data):
            user_data = users[inv_data['user_email']]
            user = user_data['user']
            plan_slug = inv_data.get('plan_slug', user_data['plan_slug'])
            plan = plans[plan_slug]
            subscription = user_data.get('subscription')

            invoice_date = datetime.utcnow() - timedelta(days=inv_data['days_ago'])

            invoice = UserInvoice()
            invoice.user_id = user.id
            invoice.tarif_plan_id = plan.id
            invoice.subscription_id = subscription.id if subscription else None
            invoice.invoice_number = f"INV-DEMO-{i+1:04d}"
            invoice.amount = plan.price if plan.price else Decimal('0.00')
            invoice.currency = 'EUR'
            invoice.status = inv_data['status']
            invoice.invoiced_at = invoice_date

            if inv_data['status'] == InvoiceStatus.PAID:
                invoice.payment_method = inv_data['payment_method']
                invoice.payment_ref = f"ref_{uuid.uuid4().hex[:12]}"
                invoice.paid_at = invoice_date + timedelta(hours=2)
            elif inv_data['status'] == InvoiceStatus.PENDING:
                invoice.expires_at = datetime.utcnow() + timedelta(days=7)

            session.add(invoice)
            print(f"  Created: {invoice.invoice_number} - {user.email} - €{invoice.amount} - {invoice.status.value}")

    print("\n=== Creating Token Bundles ===")

    token_bundles_data = [
        {
            'name': '100 Tokens',
            'description': 'Starter token pack',
            'token_amount': 100,
            'price': Decimal('3.00'),
            'sort_order': 0,
        },
        {
            'name': '500 Tokens',
            'description': 'Best value token pack',
            'token_amount': 500,
            'price': Decimal('10.00'),
            'sort_order': 1,
        },
    ]

    for bundle_data in token_bundles_data:
        bundle = session.query(TokenBundle).filter_by(name=bundle_data['name']).first()
        if not bundle:
            bundle = TokenBundle()
            bundle.name = bundle_data['name']
            bundle.description = bundle_data['description']
            bundle.token_amount = bundle_data['token_amount']
            bundle.price = bundle_data['price']
            bundle.is_active = True
            bundle.sort_order = bundle_data['sort_order']
            session.add(bundle)
            session.flush()
            print(f"  Created: {bundle.name} - {bundle.token_amount} tokens - €{bundle.price}")
        else:
            print(f"  Exists: {bundle.name}")

    print("\n=== Creating Add-Ons ===")

    # Global add-ons (available to all users)
    global_addons_data = [
        {
            'name': 'Priority Support',
            'slug': 'priority-support',
            'description': 'Get priority support with 24-hour response time',
            'price': Decimal('9.99'),
            'billing_period': BillingPeriod.MONTHLY.value,
            'config': {'support_level': 'priority', 'response_hours': 24},
            'sort_order': 0,
            'plans': [],  # Empty = global addon
        },
        {
            'name': 'Advanced Analytics',
            'slug': 'advanced-analytics',
            'description': 'Unlock advanced analytics and reporting tools',
            'price': Decimal('19.99'),
            'billing_period': BillingPeriod.MONTHLY.value,
            'config': {'analytics_level': 'advanced', 'custom_reports': True},
            'sort_order': 1,
            'plans': [],  # Empty = global addon
        },
        {
            'name': 'White Label',
            'slug': 'white-label',
            'description': 'Customize with your own branding',
            'price': Decimal('49.99'),
            'billing_period': BillingPeriod.MONTHLY.value,
            'config': {'custom_domain': True, 'custom_logo': True, 'custom_colors': True},
            'sort_order': 2,
            'plans': [],  # Empty = global addon
        },
    ]

    # Plan-dependent add-ons (only available for specific plans)
    plan_dependent_addons_data = [
        {
            'name': 'Extra Storage',
            'slug': 'extra-storage',
            'description': 'Add 100GB of additional storage to your plan',
            'price': Decimal('4.99'),
            'billing_period': BillingPeriod.MONTHLY.value,
            'config': {'storage_gb': 100},
            'sort_order': 3,
            'plans': ['basic', 'pro'],  # Only for Basic and Pro
        },
        {
            'name': 'API Rate Limit Increase',
            'slug': 'api-rate-limit-increase',
            'description': 'Increase API rate limits by 5x',
            'price': Decimal('14.99'),
            'billing_period': BillingPeriod.MONTHLY.value,
            'config': {'rate_limit_multiplier': 5},
            'sort_order': 4,
            'plans': ['pro', 'enterprise'],  # Only for Pro and Enterprise
        },
    ]

    all_addons_data = global_addons_data + plan_dependent_addons_data
    addons = {}

    for addon_data in all_addons_data:
        addon = session.query(AddOn).filter_by(slug=addon_data['slug']).first()
        if not addon:
            addon = AddOn()
            addon.name = addon_data['name']
            addon.slug = addon_data['slug']
            addon.description = addon_data['description']
            addon.price = addon_data['price']
            addon.currency = 'EUR'
            addon.billing_period = addon_data['billing_period']
            addon.config = addon_data['config']
            addon.is_active = True
            addon.sort_order = addon_data['sort_order']

            # Add to specific plans if specified
            if addon_data['plans']:
                for plan_slug in addon_data['plans']:
                    if plan_slug in plans:
                        addon.tarif_plans.append(plans[plan_slug])

            session.add(addon)
            session.flush()
            plan_info = f" (plans: {', '.join(addon_data['plans'])})" if addon_data['plans'] else " (global)"
            print(f"  Created: {addon.name}{plan_info} - €{addon.price}")
        else:
            plan_info = f" (plans: {', '.join(addon_data['plans'])})" if addon_data['plans'] else " (global)"
            print(f"  Exists: {addon.name}{plan_info}")
        addons[addon_data['slug']] = addon

    # Create some addon subscriptions for demo users
    print("\n=== Creating Add-On Subscriptions ===")

    pro_user = users['user.pro@demo.local']['user']
    pro_subscription = users['user.pro@demo.local']['subscription']

    addon_subscriptions_data = [
        {'user_email': 'user.pro@demo.local', 'addon_slug': 'priority-support', 'status': SubscriptionStatus.ACTIVE},
        {'user_email': 'user.pro@demo.local', 'addon_slug': 'advanced-analytics', 'status': SubscriptionStatus.ACTIVE},
        {'user_email': 'user.pro@demo.local', 'addon_slug': 'extra-storage', 'status': SubscriptionStatus.ACTIVE},
    ]

    for addon_sub_data in addon_subscriptions_data:
        addon = addons[addon_sub_data['addon_slug']]
        existing = session.query(AddOnSubscription).filter_by(
            addon_id=addon.id,
            user_id=pro_user.id
        ).first()

        if not existing:
            addon_sub = AddOnSubscription()
            addon_sub.user_id = pro_user.id
            addon_sub.addon_id = addon.id
            addon_sub.subscription_id = pro_subscription.id
            addon_sub.status = addon_sub_data['status']
            addon_sub.starts_at = datetime.utcnow() - timedelta(days=5)
            addon_sub.expires_at = datetime.utcnow() + timedelta(days=25)
            session.add(addon_sub)
            session.flush()
            print(f"  Created: {pro_user.email} -> {addon.name}")
        else:
            print(f"  Exists: {pro_user.email} -> {addon.name}")

    session.commit()
    print("\n=== Demo Data Installation Complete ===")
    print(f"  Currencies: {session.query(Currency).count()}")
    print(f"  Tarif Plans: {session.query(TarifPlan).count()}")
    print(f"  Users: {session.query(User).count()}")
    print(f"  Subscriptions: {session.query(Subscription).count()}")
    print(f"  Invoices: {session.query(UserInvoice).count()}")
    print(f"  Token Bundles: {session.query(TokenBundle).count()}")
    print(f"  Add-Ons: {session.query(AddOn).count()}")
    print(f"  Add-On Subscriptions: {session.query(AddOnSubscription).count()}")

except Exception as e:
    session.rollback()
    print(f"\nError: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
finally:
    session.close()
EOF

echo ""
echo "Demo data installation completed!"
echo ""
echo "Demo Users:"
echo "  user.free@demo.local / demo123 (Free plan)"
echo "  user.pro@demo.local / demo123 (Pro plan)"
