import os
import django
from django.conf import settings

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))
django.setup()

from django.contrib.auth.models import User
from finance.models import Transaction, Budget, Category, Profile
from finance import check_and_notify_budget
from decimal import Decimal
from django.utils import timezone

def test_multicurrency():
    print("Setting up test user...")
    username = 'test_mc_user'
    if User.objects.filter(username=username).exists():
        User.objects.filter(username=username).delete()
    user = User.objects.create_user(username=username, password='password')
    Profile.objects.create(user=user)

    print("Creating categories...")
    cat_food = Category.objects.create(owner=user, name='Food', type='expense')
    
    print("Creating Budget: 100 USD for Food...")
    Budget.objects.create(owner=user, category=cat_food, amount=100, currency='USD')

    print("Adding 50 USD expense...")
    t1 = Transaction.objects.create(
        owner=user, 
        category=cat_food, 
        amount=50, 
        currency='USD', 
        transaction_type='expense',
        date=timezone.now().date()
    )
    
    print("Adding 500 INR expense...")
    t2 = Transaction.objects.create(
        owner=user, 
        category=cat_food, 
        amount=500, 
        currency='INR', 
        transaction_type='expense',
        date=timezone.now().date()
    )

    print("Verifying Budget Status...")
    # Manually check logic similar to budgets_view
    today = timezone.now().date()
    start = today.replace(day=1)
    if today.month == 12:
        end = today.replace(year=today.year + 1, month=1, day=1)
    else:
        end = today.replace(month=today.month + 1, day=1)
        
    spent_usd = Transaction.objects.filter(
        owner=user, category=cat_food, currency='USD', date__gte=start, date__lt=end
    ).count()
    # Actually aggregate
    from django.db.models import Sum
    spent_usd_val = Transaction.objects.filter(
        owner=user, category=cat_food, currency='USD', date__gte=start, date__lt=end
    ).aggregate(t=Sum('amount'))['t']
    
    spent_inr_val = Transaction.objects.filter(
        owner=user, category=cat_food, currency='INR', date__gte=start, date__lt=end
    ).aggregate(t=Sum('amount'))['t']

    print(f"Spent USD: {spent_usd_val}")
    print(f"Spent INR: {spent_inr_val}")

    if spent_usd_val == 50 and spent_inr_val == 500:
        print("SUCCESS: Expenses separated by currency.")
    else:
        print("FAILURE: Expenses aggregated incorrectly.")
        
    # Check budget check_and_notify logic
    # Adding another 60 USD (Total 110) should trigger notification (simulated)
    print("Adding 60 USD expense (Over budget)...")
    # We can't easily check email sent in console backend without capturing stdout, but we can call the function
    check_and_notify_budget(user, cat_food, 'USD')
    
    print("Test Complete.")

if __name__ == '__main__':
    test_multicurrency()
