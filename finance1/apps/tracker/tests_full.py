from django.test import TestCase, Client
from django.contrib.auth.models import User
from finance.models import Category, Transaction, Budget, Profile
from django.urls import reverse
from decimal import Decimal
import json

class FullSystemTests(TestCase):
    def setUp(self):
        # Create a test user
        self.user = User.objects.create_user(username='testuser', email='test@example.com', password='password123')
        self.client.login(username='testuser', password='password123')
        # Setup initial categories
        self.cat_income = Category.objects.create(name='Salary', type='income', owner=self.user)
        self.cat_expense = Category.objects.create(name='Food', type='expense', owner=self.user)

    def test_auth_pages(self):
        """Verify login/register pages load"""
        self.client.logout()
        resp = self.client.get(reverse('login'))
        self.assertEqual(resp.status_code, 200)
        resp = self.client.get(reverse('register'))
        self.assertEqual(resp.status_code, 200)

    def test_profile_view_and_edit(self):
        """Verify profile visualization and editing"""
        # View
        resp = self.client.get(reverse('profile'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'testuser')
        
        # Edit
        # Note: The view expects form data
        resp = self.client.post(reverse('profile'), {
            'bio': 'Updated Bio',
            'target_savings': '5000'
        })
        self.assertEqual(resp.status_code, 302) # Redirects back to profile
        
        self.user.profile.refresh_from_db()
        self.assertEqual(self.user.profile.bio, 'Updated Bio')
        self.assertEqual(self.user.profile.target_savings, Decimal('5000'))

    def test_transaction_flow(self):
        """Test adding income and expenses and balance calculation"""
        # Add Income
        resp = self.client.post(reverse('add_income'), {
            'date': '2025-01-01',
            'amount': '1000',
            'category': 'Salary',
            'description': 'Jan Salary',
            'currency': 'USD'
        })
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(Transaction.objects.filter(transaction_type='income').count(), 1)
        
        # Add Expense
        resp = self.client.post(reverse('add_expense'), {
            'date': '2025-01-02',
            'amount': '200',
            'category': 'Food',
            'description': 'Groceries',
            'currency': 'USD'
        })
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(Transaction.objects.filter(transaction_type='expense').count(), 1)
        
        # Verify Reports Page loads (status 200)
        resp = self.client.get(reverse('reports'))
        self.assertEqual(resp.status_code, 200)

    def test_budget_logic(self):
        """Verify budget creation"""
        resp = self.client.post(reverse('budgets'), {
            'category_name': 'Food',
            'amount': '500',
            'currency': 'USD'
        })
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(Budget.objects.count(), 1)
        
        resp = self.client.get(reverse('budgets'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Food')

    def test_finalize_signup_flow(self):
        """Test the new OAuth finalization flow logic"""
        # Simulate session data from OAuth callback
        session = self.client.session
        session['oauth_email'] = 'newuser@gmail.com'
        session['oauth_name'] = 'New User'
        session.save()
        
        # Get page
        resp = self.client.get(reverse('finalize_signup'))
        self.assertEqual(resp.status_code, 200)
        
        # Submit form with existing username (should fail)
        resp = self.client.post(reverse('finalize_signup'), {'username': 'testuser'})
        self.assertContains(resp, 'Username is already taken')
        
        # Submit with new username
        resp = self.client.post(reverse('finalize_signup'), {'username': 'newuser123'})
        self.assertEqual(resp.status_code, 302) # Redirect to index
        
        # Verify user created
        new_user = User.objects.get(username='newuser123')
        self.assertEqual(new_user.email, 'newuser@gmail.com')
        # User should be logged in
        self.assertEqual(int(self.client.session['_auth_user_id']), new_user.pk)
