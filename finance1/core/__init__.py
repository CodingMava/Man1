"""Finance package initializer.

Provides a minimal template loader so settings can reference `finance.DictTemplateLoader`.
Avoid importing models or executing Django DB code at import time.
"""
from django.template import Origin, TemplateDoesNotExist
from django.template.loaders.base import Loader as BaseLoader
from django import forms
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import path, reverse
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.utils import timezone
# from django.db import models
from decimal import Decimal
import json
import urllib.parse
import os
from pathlib import Path
import time
from django.http import HttpResponse, HttpResponseRedirect

# Minimal templates mapping used by the custom loader. Keep small and static.
TEMPLATES_DATA = {
    'base.html': '''<!DOCTYPE html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Personal Finance Tracker</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<style>
  :root{--bg:#f4f6f8;--card:#fff;--accent:#0d6efd;--muted:#666;--success:#28a745;--danger:#dc3545}
  body{font-family:Inter,Segoe UI,Arial,sans-serif;margin:0;background:var(--bg);color:#222;-webkit-font-smoothing:antialiased}
  .nav{background:var(--accent);color:#fff;padding:12px 18px;display:flex;flex-wrap:wrap;align-items:center;gap:8px}
  .nav .left{display:flex;gap:12px;align-items:center;flex-wrap:wrap}.nav a{color:#fff;text-decoration:none;padding:6px 8px;border-radius:6px;font-size:0.95rem}.nav .user{margin-left:auto;font-size:0.95rem}
  .container{max-width:1200px;margin:20px auto;padding:20px;background:var(--card);border-radius:10px;box-shadow:0 6px 18px rgba(0,0,0,0.06)}
  .grid{display:flex;gap:12px;flex-wrap:wrap}.card{flex:1;min-width:200px;padding:16px;border:1px solid rgba(0,0,0,0.04);border-radius:8px;background:linear-gradient(180deg,rgba(255,255,255,0.4),rgba(255,255,255,0.2));text-align:center}
  .card-big{min-width:100%;height:300px}
  .stat-value{font-size:2em;font-weight:bold;color:var(--accent);margin:8px 0}
  .stat-label{color:var(--muted);font-size:0.9rem}
  table{width:100%;border-collapse:collapse}th,td{padding:10px;border-bottom:1px solid #eee;text-align:left}th{background:#f9f9f9;font-weight:600}
  .muted{color:var(--muted);font-size:0.95rem}.btn{display:inline-block;padding:10px 14px;background:var(--accent);color:#fff;border-radius:8px;text-decoration:none;cursor:pointer;border:none;font-size:0.95rem;margin:4px 2px}
  .btn-success{background:var(--success)}.btn-danger{background:var(--danger)}.btn:hover{opacity:0.9}
  input,select,textarea{width:100%;padding:10px;border:1px solid #e6e6e6;border-radius:8px;font-family:inherit;margin-bottom:8px}
  img.receipt{max-width:64px;max-height:64px;border-radius:6px;object-fit:cover}.small{font-size:0.9rem;color:var(--muted)}
  .progress-bar{width:100%;height:20px;background:#e6e6e6;border-radius:4px;overflow:hidden;margin:8px 0}
  .progress-fill{height:100%;background:var(--accent);transition:width 0.3s}
  .budget-card{padding:16px;background:#f9f9f9;margin:12px 0;border-radius:8px;border-left:4px solid var(--accent)}
  .budget-card.warn{border-left-color:var(--danger);background:#fff5f5}
  .budget-header{display:flex;justify-content:space-between;margin-bottom:12px}
  .budget-amount{font-size:1.4em;font-weight:bold;color:var(--accent)}
  .budget-spent{color:var(--danger)}
  .budget-remaining{color:var(--success);font-weight:bold;font-size:1.2em}
  form div{margin-bottom:10px}
  h2,h3{margin-top:20px;color:var(--accent)}
  @media (max-width:720px){.nav{padding:10px}.nav .left{flex-wrap:wrap}.nav .user{width:100%;margin-top:6px}.container{margin:12px;padding:14px}.grid{flex-direction:column}.card{min-width:100%}}
</style>
</head>
<body>
  <div class="nav">
    <div class="left">
      <a href="/">Dashboard</a>
      <a href="/income/">Income</a>
      <a href="/expenses/">Expenses</a>
      <a href="/budgets/">Budgets</a>
      <a href="/reports/">Reports</a>
    </div>
    <div class="user">
      {% if user.is_authenticated %}
        Hello {{ user.username }} | <a href="{% url 'profile' %}">Profile</a> | <a href="/logout/">Logout</a>
      {% else %}
        <a href="/login/">Login</a> | <a href="/register/">Register</a>
      {% endif %}
    </div>
  </div>
  <div class="container">
    {% block content %}{% endblock %}
  </div>
</body>
</html>''',
    'index.html': '{% extends "base.html" %}{% block content %}<h2>Dashboard</h2><div class="grid">{% for curr, data in totals.items %}<div class="card"><div class="stat-label">Income ({{ curr }})</div><div class="stat-value" style="color:var(--success)">{{ data.income }}</div></div><div class="card"><div class="stat-label">Expense ({{ curr }})</div><div class="stat-value" style="color:var(--danger)">{{ data.expense }}</div></div><div class="card"><div class="stat-label">Savings ({{ curr }})</div><div class="stat-value">{{ data.savings }}</div></div>{% empty %}<div class="card"><p>No transactions yet.</p></div>{% endfor %}</div><h3>Expense Breakdown by Category</h3><div class="grid"><div class="card card-big"><canvas id="expenseChart"></canvas></div><div class="card card-big"><canvas id="trendChart"></canvas></div></div><h3>Quick Links</h3><div class="grid"><div class="card" style="text-align:center"><p><a class="btn btn-success" href="/income/">View Income</a></p></div><div class="card" style="text-align:center"><p><a class="btn btn-danger" href="/expenses/">View Expenses</a></p></div><div class="card" style="text-align:center"><p><a class="btn" href="/budgets/">Manage Budgets</a></p></div></div><script>\nvar expenseData = {{ expense_breakdown|safe }};\nvar trendData = {{ trend_data|safe }};\nif(expenseData && Object.keys(expenseData).length > 0) {\n  var expCtx = document.getElementById("expenseChart").getContext("2d");\n  new Chart(expCtx, {type:"doughnut", data:{labels:Object.keys(expenseData),datasets:[{data:Object.values(expenseData),backgroundColor:["#FF6384","#36A2EB","#FFCE56","#4BC0C0","#9966FF","#FF9F40","#C9CBCF","#4BC0C0","#FF6384"],borderWidth:0}]},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{position:"bottom"}}}});\n}\nif(trendData && trendData.months.length > 0) {\n  var trendCtx = document.getElementById("trendChart").getContext("2d");\n  new Chart(trendCtx, {type:"line", data:{labels:trendData.months,datasets:[{label:"Income",data:trendData.income,borderColor:"#28a745",backgroundColor:"rgba(40,167,69,0.1)",tension:0.4},{label:"Expense",data:trendData.expense,borderColor:"#dc3545",backgroundColor:"rgba(220,53,69,0.1)",tension:0.4}]},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{position:"top"}},scales:{y:{beginAtZero:true}}}});\n}\n</script>{% endblock %}',
    'register.html': '{% extends "base.html" %}{% block content %}<h2>Register</h2>{% if error %}<div style="color:var(--danger);padding:10px;background:#ffe6e6;border-radius:6px;margin-bottom:12px">{{ error }}</div>{% endif %}<form method="post">{% csrf_token %}{{ form.as_p }}<button class="btn">Create account</button></form>{% endblock %}',
    'login.html': '{% extends "base.html" %}{% block content %}<h2>Login</h2>{% if error %}<div style="color:var(--danger);padding:10px;background:#ffe6e6;border-radius:6px;margin-bottom:12px">{{ error }}</div>{% endif %}<form method="post">{% csrf_token %}<div><input name="username" placeholder="Username" required></div><div><input name="password" type="password" placeholder="Password" required></div><button class="btn">Login</button><a class="btn btn-success" href="/oauth/google/login/">Login with Google</a></form>{% endblock %}',
    'finalize_signup.html': '''{% extends "base.html" %}
{% block content %}
<div class="auth-wrap">
  <div class="auth-card">
    <div style="text-align:center;margin-bottom:24px">
      <h2>Complete Signup</h2>
      <p style="color:var(--muted)">One last step! Choose a username for your account.</p>
    </div>
    {% if error %}
    <div class="alert alert-danger">{{ error }}</div>
    {% endif %}
    <form method="post">
      {% csrf_token %}
      <div class="form-group">
        <label>Authenticated Email</label>
        <input type="text" value="{{ email }}" disabled style="background:#f9fafb;color:#6b7280">
      </div>
      <div class="form-group">
        <label for="id_username">Choose Username</label>
        <input type="text" name="username" id="id_username" required placeholder="e.g. finance_guru_99" autofocus>
        <div class="helptext">This will be your unique display name.</div>
      </div>
      <button type="submit" class="btn btn-primary btn-block">Create Account</button>
    </form>
  </div>
</div>
{% endblock %}''',
    
    'profile.html': '''{% extends "base.html" %}
{% block content %}
<style>
  .profile-header {
    background: linear-gradient(135deg, #4f46e5 0%, #3b82f6 100%);
    color: white;
    padding: 40px;
    border-radius: 20px;
    margin-bottom: 30px;
    box-shadow: 0 10px 25px -5px rgba(59, 130, 246, 0.5);
    display: flex;
    align-items: center;
    gap: 24px;
  }
  .profile-avatar {
    width: 80px;
    height: 80px;
    background: rgba(255,255,255,0.2);
    border: 2px solid rgba(255,255,255,0.4);
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 2.5rem;
    font-weight: 700;
  }
  .profile-info h1 { margin: 0; font-size: 2rem; }
  .profile-info p { margin: 4px 0 0 0; opacity: 0.9; }

  .stats-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 20px;
    margin-bottom: 30px;
  }
  .stat-card {
    background: white;
    padding: 24px;
    border-radius: 16px;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    border: 1px solid #f3f4f6;
  }
  .stat-label { font-size: 0.875rem; color: #6b7280; font-weight: 500; margin-bottom: 8px; }
  .stat-value { font-size: 1.5rem; font-weight: 700; color: #111827; }
  .stat-value.positive { color: #10b981; }

  .profile-section {
    background: white;
    border-radius: 16px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    padding: 30px;
    margin-bottom: 30px;
  }
  .section-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 24px;
    padding-bottom: 16px;
    border-bottom: 1px solid #e5e7eb;
  }
  .section-title { font-size: 1.25rem; font-weight: 600; color: #1f2937; margin: 0; }
  
  /* Edit Mode Toggle */
  .edit-form { display: none; }
  .view-mode.hidden { display: none; }
  .edit-form.visible { display: block; }
  
  .detail-row {
    display: flex;
    margin-bottom: 16px;
    align-items: center;
  }
  .detail-label { width: 150px; color: #6b7280; font-weight: 500; }
  .detail-value { font-weight: 600; color: #111827; }
</style>

<div class="container">
  <div class="profile-header">
    <div class="profile-avatar">{{ request.user.username|make_list|first|upper }}</div>
    <div class="profile-info">
      <h1>{{ request.user.username }}</h1>
      <p>Member since {{ join_date|date:"F Y" }}</p>
    </div>
  </div>

  <div class="stats-grid">
    <div class="stat-card">
      <div class="stat-label">Total Transactions</div>
      <div class="stat-value">{{ total_tx }}</div>
    </div>
    <div class="stat-card">
      <div class="stat-label">Net Savings</div>
      <div class="stat-value {% if net_savings >= 0 %}positive{% endif %}">₹{{ net_savings }}</div>
    </div>
    <div class="stat-card">
      <div class="stat-label">Goal Progress</div>
      <div class="stat-value">{{ progress }}%</div>
      <div style="width:100%;height:6px;background:#e5e7eb;border-radius:3px;margin-top:8px;overflow:hidden">
        <div style="width:{{ progress }}%;height:100%;background:#3b82f6;border-radius:3px"></div>
      </div>
    </div>
  </div>

  <div class="profile-section">
    <div class="section-header">
      <h3 class="section-title">Profile Details</h3>
      <button class="btn btn-outline" id="toggleEditBtn" onclick="toggleEdit()">Edit Profile</button>
    </div>

    <!-- View Mode -->
    <div id="viewMode" class="view-mode">
      <div class="detail-row">
        <div class="detail-label">Monthly Goal</div>
        <div class="detail-value">₹{{ profile.target_savings }}</div>
      </div>
      <div class="detail-row">
        <div class="detail-label">Bio</div>
        <div class="detail-value">{{ profile.bio|default:"No bio set" }}</div>
      </div>
      <div class="detail-row">
        <div class="detail-label">Email</div>
        <div class="detail-value">{{ request.user.email }}</div>
      </div>
    </div>

    <!-- Edit Mode -->
    <div id="editForm" class="edit-form">
      <form method="post">
        {% csrf_token %}
        {% for field in form %}
        <div class="form-group">
          <label for="{{ field.id_for_label }}">{{ field.label }}</label>
          {{ field }}
          {% if field.help_text %}<div class="helptext">{{ field.help_text }}</div>{% endif %}
          {% if field.errors %}<div style="color:var(--danger)">{{ field.errors }}</div>{% endif %}
        </div>
        {% endfor %}
        <div style="display:flex;gap:12px;margin-top:20px">
          <button type="submit" class="btn btn-primary">Save Changes</button>
          <button type="button" class="btn btn-outline" onclick="toggleEdit()">Cancel</button>
        </div>
      </form>
    </div>
  </div>
</div>

<script>
function toggleEdit() {
  const viewMode = document.getElementById('viewMode');
  const editForm = document.getElementById('editForm');
  const btn = document.getElementById('toggleEditBtn');
  
  if (editForm.classList.contains('visible')) {
    editForm.classList.remove('visible');
    viewMode.classList.remove('hidden');
    btn.textContent = 'Edit Profile';
    btn.style.display = 'block';
  } else {
    editForm.classList.add('visible');
    viewMode.classList.add('hidden');
    btn.style.display = 'none';
  }
}
</script>
{% endblock %}''',
    'income.html': '{% extends "base.html" %}{% block content %}<h2>Income</h2><p><a class="btn btn-success" href="/income/add/">+ Add Income</a></p><table><tr><th>Date</th><th>Category</th><th>Amount</th><th>Currency</th><th>Description</th><th>Actions</th></tr>{% for t in transactions %}<tr><td>{{ t.date }}</td><td>{{ t.category.name }}</td><td style="color:var(--success);font-weight:bold">+{{ t.amount }}</td><td>{{ t.currency }}</td><td>{{ t.description }}</td><td><a href="/transactions/{{ t.id }}/edit/">Edit</a> | <a href="/transactions/{{ t.id }}/delete/">Delete</a></td></tr>{% empty %}<tr><td colspan="6" class="muted">No income records yet</td></tr>{% endfor %}</table>{% endblock %}',
    'expenses.html': '{% extends "base.html" %}{% block content %}<h2>Expenses</h2><p><a class="btn btn-danger" href="/expenses/add/">+ Add Expense</a></p><table><tr><th>Date</th><th>Category</th><th>Amount</th><th>Currency</th><th>Description</th><th>Receipt</th><th>Actions</th></tr>{% for t in transactions %}<tr><td>{{ t.date }}</td><td>{{ t.category.name }}</td><td style="color:var(--danger);font-weight:bold">-{{ t.amount }}</td><td>{{ t.currency }}</td><td>{{ t.description }}</td><td>{% if t.receipt %}<a href="{{ t.receipt.url }}">View</a>{% endif %}</td><td><a href="/transactions/{{ t.id }}/edit/">Edit</a> | <a href="/transactions/{{ t.id }}/delete/">Delete</a></td></tr>{% empty %}<tr><td colspan="7" class="muted">No expenses recorded yet</td></tr>{% endfor %}</table>{% endblock %}',
    'transactions.html': '{% extends "base.html" %}{% block content %}<h2>Transactions</h2><p><a class="btn" href="/transactions/add/">Add Transaction</a></p><table><tr><th>Date</th><th>Type</th><th>Category</th><th>Amount</th><th>Actions</th></tr>{% for t in transactions %}<tr><td>{{ t.date }}</td><td>{{ t.transaction_type }}</td><td>{{ t.category.name }}</td><td>{{ t.amount }}</td><td><a href="/transactions/{{ t.id }}/edit/">Edit</a> | <a href="/transactions/{{ t.id }}/delete/">Delete</a></td></tr>{% empty %}<tr><td colspan="5">No transactions yet</td></tr>{% endfor %}</table>{% endblock %}',
    'add_edit_transaction.html': '{% extends "base.html" %}{% block content %}<h2>{% if tx %}Edit{% else %}Add{% endif %} Transaction</h2><form method="post" enctype="multipart/form-data">{% csrf_token %}{{ form.as_p }}<button class="btn">Save</button></form>{% endblock %}',
    'categories.html': '{% extends "base.html" %}{% block content %}<h2>Categories</h2><h3>Add New Category</h3><form method="post"><div><input name="name" placeholder="Category name" required></div><div><select name="type"><option value="income">Income</option><option value="expense">Expense</option></select></div><button class="btn">Add Category</button></form><h3>Your Categories</h3><table><tr><th>Name</th><th>Type</th><th>Status</th><th>Action</th></tr>{% for c in categories %}<tr><td>{{ c.name }}</td><td><strong>{{ c.type|upper }}</strong></td><td>{% if c.is_active %}<span style="color:var(--success)">✓ Active</span>{% else %}<span style="color:var(--muted)">✗ Inactive</span>{% endif %}</td><td><a href="/categories/{{ c.id }}/delete/" class="btn btn-danger">Delete</a></td></tr>{% empty %}<tr><td colspan="4" class="muted">No categories created yet. Create one to get started.</td></tr>{% endfor %}</table>{% endblock %}',
    'budgets.html': '''{% extends "base.html" %}
{% block content %}
<h2>Budget Management</h2>
<p class="small muted" style="margin-bottom:20px">Set a monthly limit for any category (e.g. Food, Travel). When you add expenses in that category, we subtract from the limit and show how much is left. If you go over, we warn you.</p>

<div class="card" style="margin-bottom:24px">
  <h3>Set a Budget</h3>
  <p class="small">Type any category name or pick from your existing expense categories below.</p>
  <form method="post">
    {% csrf_token %}
    <div>
      <label class="small">Category name</label>
      <input type="text" name="category_name" value="{{ form.category_name.value|default:'' }}" list="category-list" placeholder="e.g. Food, Travel, Shopping" maxlength="100" required id="id_category_name">
      {% if expense_categories %}
      <datalist id="category-list">
        {% for c in expense_categories %}<option value="{{ c }}">{% endfor %}
      </datalist>
      {% endif %}
      {% if form.category_name.errors %}<div style="color:var(--danger);font-size:0.9rem">{{ form.category_name.errors }}</div>{% endif %}
    </div>
    <div>
      <label class="small">Budget amount</label>
      <div style="display:flex;gap:4px">
        {{ form.currency }}
        {{ form.amount }}
      </div>
      {% if form.amount.errors %}<div style="color:var(--danger);font-size:0.9rem">{{ form.amount.errors }}</div>{% endif %}
    </div>
    <button class="btn btn-success">Set Budget</button>
  </form>
</div>

<h3>Your Budgets & Spending — {{ month_label|default:"this month" }}</h3>
<p class="small muted" style="margin-top:-8px;margin-bottom:12px">Only expenses with a date in {{ month_label }} count here. When you add an expense, the date defaults to today so it appears in this month.</p>
{% if budgets %}
  <div>
    {% for b in budgets %}
    <div class="budget-card {% if b.remaining < 0 %}warn{% endif %}">
      <div class="budget-header">
        <div>
          <strong style="font-size:1.2em">{{ b.category.name }}</strong>
        </div>
        <div style="text-align:right;display:flex;align-items:center;gap:8px">
          <span class="small">This month</span>
          <form method="post" action="{% url 'budget_delete' b.id %}" style="display:inline" onsubmit="return confirm('Remove this budget?');">
            {% csrf_token %}
            <button type="submit" class="btn btn-danger" style="padding:4px 10px;font-size:0.85rem">Remove</button>
          </form>
        </div>
      </div>
      
      <div class="grid" style="margin-bottom:12px;gap:8px">
        <div class="card" style="padding:10px;text-align:left">
          <div class="small">Budget</div>
          <div class="budget-amount">{{ b.currency }} {{ b.amount }}</div>
        </div>
        <div class="card" style="padding:10px;text-align:left">
          <div class="small">Spent</div>
          <div class="budget-spent">{{ b.currency }} {{ b.spent }}</div>
        </div>
        <div class="card" style="padding:10px;text-align:left;background:{% if b.remaining >= 0 %}#f0f9ff{% else %}#fff5f5{% endif %}">
          <div class="small">Left</div>
          <div class="budget-remaining" style="color:{% if b.remaining < 0 %}var(--danger){% else %}var(--success){% endif %}">
            {{ b.currency }} {{ b.remaining }}
          </div>
        </div>
      </div>

      <div class="progress-bar">
        <div class="progress-fill" style="width:{{ b.percentage }}%;background:{% if b.remaining < 0 %}var(--danger){% elif b.percentage >= 75 %}#ff9800{% else %}var(--success){% endif %}"></div>
      </div>

      {% if b.remaining < 0 %}
        <p style="color:var(--danger);font-size:0.95rem;margin:8px 0;font-weight:bold;background:#ffe6e6;padding:8px;border-radius:4px">
          ⚠️ Overspent by ₹{{ b.overspent }}. You went over your {{ b.category.name }} budget.
        </p>
      {% elif b.percentage >= 75 %}
        <p style="color:#ff9800;font-size:0.95rem;margin:8px 0;font-weight:bold">
          ⚠️ Warning: You have used {{ b.percentage }}% of your budget.
        </p>
      {% else %}
        <p style="color:var(--success);font-size:0.95rem;margin:8px 0">
          ✓ On track: {{ b.percentage }}% spent
        </p>
      {% endif %}
    </div>
    {% endfor %}
  </div>
{% else %}
  <p class="muted">No budgets set yet. Add a category and amount above to start tracking (e.g. Food ₹5,000).</p>
{% endif %}
<p class="small muted" style="margin-top:16px"><a href="/categories/">Manage categories</a> · <a href="/expenses/">Add expense</a></p>
{% endblock %}''',
    'reports.html': '{% extends "base.html" %}{% block content %}<h2>Financial Reports</h2><div class="grid"><div class="card card-big"><h4>Income by Category</h4><canvas id="incomeChartCat"></canvas></div><div class="card card-big"><h4>Expense by Category</h4><canvas id="expenseChartCat"></canvas></div></div><h3>Monthly Summary</h3><table><tr><th>Month</th><th>Currency</th><th>Income</th><th>Expense</th><th>Net</th></tr>{% for m in monthly_data %}<tr><td>{{ m.month }}</td><td><strong>{{ m.currency }}</strong></td><td style="color:var(--success)">{{ m.income }}</td><td style="color:var(--danger)">{{ m.expense }}</td><td style="font-weight:bold">{{ m.net }}</td></tr>{% endfor %}</table><script>\nvar incomeCatData = {{ income_cat_json|safe }};\nvar expenseCatData = {{ expense_cat_json|safe }};\nif(incomeCatData && incomeCatData.labels && incomeCatData.labels.length > 0) {\n  var iCtx = document.getElementById("incomeChartCat").getContext("2d");\n  new Chart(iCtx, {type:"doughnut", data:{labels:incomeCatData.labels,datasets:[{data:incomeCatData.data,backgroundColor:["#36A2EB","#FFCE56","#4BC0C0","#9966FF","#FF9F40","#C9CBCF"],borderWidth:0}]},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{position:"bottom"}}}});\n}\nif(expenseCatData && expenseCatData.labels && expenseCatData.labels.length > 0) {\n  var eCtx = document.getElementById("expenseChartCat").getContext("2d");\n  new Chart(eCtx, {type:"doughnut", data:{labels:expenseCatData.labels,datasets:[{data:expenseCatData.data,backgroundColor:["#FF6384","#36A2EB","#FFCE56","#4BC0C0","#9966FF","#FF9F40"],borderWidth:0}]},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{position:"bottom"}}}});\n}\n</script>{% endblock %}',
    'confirm_delete.html': '{% extends "base.html" %}{% block content %}<h2>Confirm delete</h2><p>{% if message %}{{ message }}{% else %}Are you sure?{% endif %}</p><form method="post">{% csrf_token %}<button class="btn btn-danger">Delete</button><a class="btn" href="{{ cancel_url|default:"/" }}">Cancel</a></form>{% endblock %}',
}


class DictTemplateLoader(BaseLoader):
    is_usable = True

    def get_template_sources(self, template_name):
        if template_name in TEMPLATES_DATA:
            yield Origin(name=template_name, template_name=template_name, loader=self)

    def get_contents(self, origin):
        try:
            return TEMPLATES_DATA[origin.template_name]
        except KeyError:
            raise TemplateDoesNotExist(origin.template_name)


# -------------------------
# Forms
# -------------------------

class RegistrationForm(forms.Form):
    username = forms.CharField(max_length=150)
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)

    def clean_username(self):
        from django.contrib.auth.models import User
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError('Username already taken.')
        return username

    def clean_email(self):
        from django.contrib.auth.models import User
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('Email already registered.')
        return email


# -------------------------
# Helpers
# -------------------------

def _month_range(dt):
    start = dt.replace(day=1)
    if dt.month == 12:
        end = dt.replace(year=dt.year + 1, month=1, day=1)
    else:
        end = dt.replace(month=dt.month + 1, day=1)
    return start, end


def _get_or_create_category(owner, name, cat_type):
    """Resolve category by name (case-insensitive) so budget and expenses use the same category."""
    from .models import Category
    name = (name or '').strip()
    if not name:
        return None
    cat = Category.objects.filter(owner=owner, name__iexact=name, type=cat_type).first()
    if not cat:
        cat = Category.objects.create(owner=owner, name=name, type=cat_type)
    return cat


# JSON fallback persistence helpers
def _data_dir():
    base = getattr(settings, 'BASE_DIR', None)
    if not base:
        base = os.getcwd()
    d = Path(base) / 'finance_data'
    d.mkdir(parents=True, exist_ok=True)
    return d


def _data_file_for(user):
    d = _data_dir()
    return d / f'user_{user.id}.json'


def _load_user_data(user):
    path = _data_file_for(user)
    if not path.exists():
        return {'transactions': [], 'budgets': []}
    try:
        with path.open('r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {'transactions': [], 'budgets': []}


def _save_user_data(user, data):
    path = _data_file_for(user)
    with path.open('w', encoding='utf-8') as f:
        json.dump(data, f, default=str, ensure_ascii=False)


def _append_user_tx(user, tx_dict):
    data = _load_user_data(user)
    if 'id' not in tx_dict:
        tx_dict['id'] = int(time.time() * 1000) * -1
    data['transactions'].append(tx_dict)
    _save_user_data(user, data)


def _remove_user_tx(user, tx_id):
    data = _load_user_data(user)
    data['transactions'] = [t for t in data['transactions'] if t.get('id') != tx_id and t.get('db_id') != tx_id]
    _save_user_data(user, data)


def _update_user_tx(user, tx_id, tx_dict):
    data = _load_user_data(user)
    updated = False
    for i, t in enumerate(data['transactions']):
        if t.get('db_id') == tx_id or t.get('id') == tx_id:
            data['transactions'][i] = {**t, **tx_dict}
            updated = True
            break
    if not updated:
        data['transactions'].append(tx_dict)
    _save_user_data(user, data)


class _CategoryStub:
    def __init__(self, name):
        self.name = name


class _SimpleTx:
    def __init__(self, d):
        self.id = d.get('id')
        self.date = d.get('date')
        self.amount = d.get('amount')
        self.description = d.get('description', '')
        self.category = _CategoryStub(d.get('category', 'Unknown'))
        self.transaction_type = d.get('transaction_type', 'expense')
        self.currency = d.get('currency', 'USD')
        self.receipt = None


def check_and_notify_budget(user, category, currency='USD'):
    from django.core.mail import send_mail
    from .models import Budget, Transaction
    from django.db.models import Sum
    try:
        budget = Budget.objects.get(owner=user, category=category, currency=currency)
    except Budget.DoesNotExist:
        return
    today = timezone.now().date()
    start, end = _month_range(today)
    spent = Transaction.objects.filter(owner=user, category=category, currency=currency, transaction_type='expense', date__gte=start, date__lt=end).aggregate(total=Sum('amount'))['total'] or Decimal('0')
    if spent > budget.amount:
        try:
            send_mail(
                subject=f'Budget Exceeded ({currency})!', 
                message=f'You have exceeded your {currency} budget for {category.name}.\nSpent: {spent} {currency}\nBudget: {budget.amount} {currency}', 
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'no-reply@finance.app'), 
                recipient_list=[user.email or '']
            )
            print(f"DEBUG: Notification sent to {user.email}")
        except Exception as e:
            print(f"ERROR: Failed to send budget notification: {e}")


# -------------------------
# Views
# -------------------------

def index(request):
    from django.db.models import Sum
    from .models import Transaction, Budget
    
    if not request.user.is_authenticated:
        return redirect('login')
    
    user = request.user
    
    # Calculate totals per currency
    income_by_curr = Transaction.objects.filter(owner=user, transaction_type='income').values('currency').annotate(total=Sum('amount'))
    expense_by_curr = Transaction.objects.filter(owner=user, transaction_type='expense').values('currency').annotate(total=Sum('amount'))
    
    totals = {}
    for i in income_by_curr:
        curr = i['currency']
        totals.setdefault(curr, {'income': Decimal('0'), 'expense': Decimal('0')})
        totals[curr]['income'] = i['total'] or Decimal('0')
    
    for e in expense_by_curr:
        curr = e['currency']
        totals.setdefault(curr, {'income': Decimal('0'), 'expense': Decimal('0')})
        totals[curr]['expense'] = e['total'] or Decimal('0')
        
    for curr in totals:
        totals[curr]['savings'] = totals[curr]['income'] - totals[curr]['expense']
    
    # For backward compatibility with template (if logic not updated yet), pick 'USD' or first
    # But we will update template next.
    # Pass 'totals' dict.

    
    # Expense breakdown by category
    expense_breakdown = {}
    exp_by_cat = Transaction.objects.filter(owner=user, transaction_type='expense').values('category__name').annotate(total=Sum('amount')).order_by('-total')
    for item in exp_by_cat:
        expense_breakdown[item['category__name']] = float(item['total'] or 0)
    
    # Monthly trend data
    from django.db.models.functions import TruncMonth
    qs = Transaction.objects.filter(owner=user).annotate(month=TruncMonth('date')).values('month', 'transaction_type').annotate(total=Sum('amount')).order_by('month')
    months = []
    income_trend = []
    expense_trend = []
    for row in qs:
        m = row['month'].strftime('%Y-%m')
        if m not in months:
            months.append(m)
            income_trend.append(0)
            expense_trend.append(0)
        idx = months.index(m)
        if row['transaction_type'] == 'income':
            income_trend[idx] = float(row['total'] or 0)
        else:
            expense_trend[idx] = float(row['total'] or 0)
    
    trend_data = {'months': months, 'income': income_trend, 'expense': expense_trend}
    
    return render(request, 'index.html', {
        'totals': totals,
        'expense_breakdown': json.dumps(expense_breakdown),
        'trend_data': json.dumps(trend_data),
    })


def register(request):
    from django.contrib.auth.models import User
    from django.contrib.auth import authenticate, login as auth_login
    print("DEBUG: Register view called")
    error = None
    if request.method == 'POST':
        print("DEBUG: POST request received")
        form = RegistrationForm(request.POST)
        if form.is_valid():
            print("DEBUG: Form is valid")
            username = form.cleaned_data['username']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            try:
                print(f"DEBUG: Creating user {username}")
                user = User.objects.create_user(username=username, email=email, password=password)
                print("DEBUG: User created, creating profile")
                from .models import Profile
                Profile.objects.get_or_create(user=user)
                print("DEBUG: Profile created, authenticating")
                user = authenticate(username=username, password=password)
                print(f"DEBUG: Authenticate result: {user}")
                auth_login(request, user)
                print("DEBUG: Login successful, redirecting to index")
                return redirect('index')
            except Exception as e:
                print(f"DEBUG: Exception caught: {e}")
                import traceback
                traceback.print_exc()
                error = str(e)
        else:
            print(f"DEBUG: Form invalid. Errors: {form.errors}")
            # collect field errors
            error_messages = []
            for field, errors in form.errors.items():
                for e in errors:
                    error_messages.append(f"{field}: {e}")
            error = 'Reference errors: ' + ' | '.join(error_messages)
    else:
        print("DEBUG: GET request")
        form = RegistrationForm()
    return render(request, 'register.html', {'form': form, 'error': error})


def login_view(request):
    from django.contrib.auth import authenticate, login as auth_login
    error = None
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        if not username or not password:
            error = 'Please enter both username and password.'
        else:
            user = authenticate(username=username, password=password)
            if user:
                auth_login(request, user)
                return redirect('index')
            else:
                error = 'Invalid credentials.'
        return render(request, 'login.html', {'error': error})
    return render(request, 'login.html')


def logout_view(request):
    from django.contrib.auth import logout as auth_logout
    auth_logout(request)
    return redirect('login')


@login_required
def profile(request):
    from .models import Profile, Transaction
    from django import forms
    from django.db.models import Sum

    class ProfileForm(forms.ModelForm):
        class Meta:
            model = Profile
            fields = ['bio', 'target_savings']
            labels = {
                'target_savings': 'Monthly Savings Goal'
            }

    profile, _ = Profile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            return redirect(reverse('profile'))
    else:
        form = ProfileForm(instance=profile)
    
    # Calculate stats
    total_income = Transaction.objects.filter(owner=request.user, transaction_type='income').aggregate(t=Sum('amount'))['t'] or 0
    total_expense = Transaction.objects.filter(owner=request.user, transaction_type='expense').aggregate(t=Sum('amount'))['t'] or 0
    net_savings = total_income - total_expense
    
    # Check goal progress
    goal = profile.target_savings
    progress = 0
    if goal > 0:
        progress = int((net_savings / goal) * 100)
    
    context = {
        'form': form,
        'profile': profile,
        'join_date': request.user.date_joined,
        'total_tx': Transaction.objects.filter(owner=request.user).count(),
        'net_savings': net_savings,
        'progress': progress
    }
    return render(request, 'profile.html', context)


@login_required
def income_view(request):
    from .models import Transaction
    # DB transactions
    db_txs = list(Transaction.objects.filter(owner=request.user, transaction_type='income').order_by('-date'))
    # JSON fallback transactions (skip those that reference DB ids)
    user_data = _load_user_data(request.user)
    db_ids = {t.id for t in db_txs}
    for d in user_data.get('transactions', []):
        if d.get('transaction_type') == 'income' and d.get('db_id') not in db_ids:
            db_txs.append(_SimpleTx(d))
    return render(request, 'income.html', {'transactions': db_txs})


@login_required
def add_income(request, tx_id=None):
    from .models import Transaction, Category
    from django import forms

    class TransactionForm(forms.Form):
        date = forms.DateField()
        amount = forms.DecimalField()
        description = forms.CharField(required=False, widget=forms.Textarea)
        category = forms.CharField(label='Income Category', help_text='Enter category name')
        currency = forms.CharField(initial='USD', required=False)
        receipt = forms.FileField(required=False)

    if tx_id:
        tx = get_object_or_404(Transaction, id=tx_id, owner=request.user, transaction_type='income')
    else:
        tx = None
    
    if request.method == 'POST':
        form = TransactionForm(request.POST, request.FILES)
        if form.is_valid():
            category_name = form.cleaned_data['category']
            cat = _get_or_create_category(request.user, category_name, 'income')
            if not cat:
                form.add_error('category', 'Category name is required.')
            else:
                if tx_id:
                    tx.date = form.cleaned_data['date']
                    tx.amount = form.cleaned_data['amount']
                    tx.description = form.cleaned_data['description']
                    tx.category = cat
                    tx.currency = form.cleaned_data['currency'] or 'USD'
                    if form.cleaned_data['receipt']:
                        tx.receipt = form.cleaned_data['receipt']
                    tx.save()
                    _update_user_tx(request.user, tx.id, {
                        'db_id': tx.id,
                        'date': str(tx.date),
                        'amount': str(tx.amount),
                        'description': tx.description,
                        'category': tx.category.name,
                        'transaction_type': tx.transaction_type,
                        'currency': tx.currency,
                    })
                else:
                    try:
                        new_tx = Transaction.objects.create(
                            owner=request.user,
                            date=form.cleaned_data['date'],
                            amount=form.cleaned_data['amount'],
                            description=form.cleaned_data['description'],
                            category=cat,
                            transaction_type='income',
                            currency=form.cleaned_data['currency'] or 'USD',
                            receipt=form.cleaned_data['receipt']
                        )
                        _append_user_tx(request.user, {
                            'db_id': new_tx.id,
                            'date': str(new_tx.date),
                            'amount': str(new_tx.amount),
                            'description': new_tx.description,
                            'category': new_tx.category.name,
                            'transaction_type': new_tx.transaction_type,
                            'currency': new_tx.currency,
                        })
                    except Exception:
                        _append_user_tx(request.user, {
                            'date': str(form.cleaned_data['date']),
                            'amount': str(form.cleaned_data['amount']),
                            'description': form.cleaned_data['description'],
                            'category': category_name,
                            'transaction_type': 'income',
                            'currency': form.cleaned_data['currency'] or 'USD',
                        })
                return redirect('income')
    else:
        if tx:
            form = TransactionForm(initial={
                'date': tx.date,
                'amount': tx.amount,
                'description': tx.description,
                'category': tx.category.name,
                'currency': tx.currency,
            })
        else:
            form = TransactionForm()
    return render(request, 'add_edit_transaction.html', {'form': form, 'tx': tx})


@login_required
def expense_view(request):
    from .models import Transaction
    db_txs = list(Transaction.objects.filter(owner=request.user, transaction_type='expense').order_by('-date'))
    user_data = _load_user_data(request.user)
    db_ids = {t.id for t in db_txs}
    for d in user_data.get('transactions', []):
        if d.get('transaction_type') == 'expense' and d.get('db_id') not in db_ids:
            db_txs.append(_SimpleTx(d))
    return render(request, 'expenses.html', {'transactions': db_txs})


@login_required
def add_edit_transaction(request, tx_id=None):
    from .models import Transaction, Category
    from django import forms

    class TransactionForm(forms.Form):
        date = forms.DateField()
        amount = forms.DecimalField()
        description = forms.CharField(required=False, widget=forms.Textarea)
        category = forms.CharField(label='Category', help_text='Enter category name')
        currency = forms.ChoiceField(choices=[('USD', 'USD'), ('INR', 'INR'), ('EUR', 'EUR'), ('GBP', 'GBP')], initial='USD', label='Currency')
        receipt = forms.FileField(required=False, label='Upload Receipt')

    if tx_id:
        tx = get_object_or_404(Transaction, id=tx_id, owner=request.user)
    else:
        tx = None
    
    if request.method == 'POST':
        form = TransactionForm(request.POST, request.FILES)
        if form.is_valid():
            category_name = form.cleaned_data['category']
            tx_type = tx.transaction_type if tx else 'expense'
            cat = _get_or_create_category(request.user, category_name, tx_type)
            if not cat:
                form.add_error('category', 'Category name is required.')
            elif tx_id:
                tx.date = form.cleaned_data['date']
                tx.amount = form.cleaned_data['amount']
                tx.description = form.cleaned_data['description']
                tx.category = cat
                tx.currency = form.cleaned_data['currency'] or 'USD'
                if form.cleaned_data['receipt']:
                    tx.receipt = form.cleaned_data['receipt']
                tx.save()
                check_and_notify_budget(request.user, cat, tx.currency)
                # update JSON fallback
                _update_user_tx(request.user, tx.id, {
                    'db_id': tx.id,
                    'date': str(tx.date),
                    'amount': str(tx.amount),
                    'description': tx.description,
                    'category': tx.category.name,
                    'transaction_type': tx.transaction_type,
                    'currency': tx.currency,
                })
                if tx.transaction_type == 'income':
                    return redirect('income')
                else:
                    return redirect('expenses')
    else:
        if tx:
            form = TransactionForm(initial={
                'date': tx.date,
                'amount': tx.amount,
                'description': tx.description,
                'category': tx.category.name,
                'currency': tx.currency,
            })
        else:
            form = TransactionForm()
    return render(request, 'add_edit_transaction.html', {'form': form, 'tx': tx})


@login_required
def add_expense(request, tx_id=None):
    from .models import Transaction, Category
    from django import forms

    class TransactionForm(forms.Form):
        date = forms.DateField()
        amount = forms.DecimalField()
        description = forms.CharField(required=False, widget=forms.Textarea)
        category = forms.CharField(label='Expense Category', help_text='Enter category name')
        currency = forms.ChoiceField(choices=[('USD', 'USD'), ('INR', 'INR'), ('EUR', 'EUR'), ('GBP', 'GBP')], initial='USD', label='Currency')
        receipt = forms.FileField(required=False, label='Upload Receipt')

    if tx_id:
        tx = get_object_or_404(Transaction, id=tx_id, owner=request.user, transaction_type='expense')
    else:
        tx = None
    
    if request.method == 'POST':
        form = TransactionForm(request.POST, request.FILES)
        if form.is_valid():
            category_name = form.cleaned_data['category']
            cat = _get_or_create_category(request.user, category_name, 'expense')
            if not cat:
                form.add_error('category', 'Category name is required.')
            else:
                if tx_id:
                    tx.date = form.cleaned_data['date']
                    tx.amount = form.cleaned_data['amount']
                    tx.description = form.cleaned_data['description']
                    tx.category = cat
                    tx.currency = form.cleaned_data['currency'] or 'USD'
                    if form.cleaned_data['receipt']:
                        tx.receipt = form.cleaned_data['receipt']
                    tx.save()
                    _update_user_tx(request.user, tx.id, {
                        'db_id': tx.id,
                        'date': str(tx.date),
                        'amount': str(tx.amount),
                        'description': tx.description,
                        'category': tx.category.name,
                        'transaction_type': tx.transaction_type,
                        'currency': tx.currency,
                    })
                else:
                    try:
                        receipt_file = form.cleaned_data.get('receipt')
                        if not receipt_file or not getattr(receipt_file, 'name', None):
                            receipt_file = None
                        new_tx = Transaction.objects.create(
                            owner=request.user,
                            date=form.cleaned_data['date'],
                            amount=form.cleaned_data['amount'],
                            description=form.cleaned_data['description'],
                            category=cat,
                            transaction_type='expense',
                            currency=form.cleaned_data['currency'] or 'USD',
                            receipt=receipt_file
                        )
                        _append_user_tx(request.user, {
                            'db_id': new_tx.id,
                            'date': str(new_tx.date),
                            'amount': str(new_tx.amount),
                            'description': new_tx.description,
                            'category': new_tx.category.name,
                            'transaction_type': new_tx.transaction_type,
                            'currency': new_tx.currency,
                        })
                    except Exception:
                        _append_user_tx(request.user, {
                            'date': str(form.cleaned_data['date']),
                            'amount': str(form.cleaned_data['amount']),
                            'description': form.cleaned_data['description'],
                            'category': category_name,
                            'transaction_type': 'expense',
                            'currency': form.cleaned_data['currency'] or 'USD',
                        })
                check_and_notify_budget(request.user, cat, form.cleaned_data['currency'] or 'USD')
                return redirect('expenses')
    else:
        if tx:
            form = TransactionForm(initial={
                'date': tx.date,
                'amount': tx.amount,
                'description': tx.description,
                'category': tx.category.name,
                'currency': tx.currency,
            })
        else:
            form = TransactionForm(initial={'date': timezone.now().date()})
    return render(request, 'add_edit_transaction.html', {'form': form, 'tx': tx})


@login_required
def delete_transaction(request, tx_id):
    from .models import Transaction
    tx = get_object_or_404(Transaction, id=tx_id, owner=request.user)
    if request.method == 'POST':
        tx_type = tx.transaction_type
        try:
            tx.delete()
        except Exception:
            pass
        # remove from JSON fallback as well
        _remove_user_tx(request.user, tx_id)
        if tx_type == 'income':
            return redirect('income')
        else:
            return redirect('expenses')
    return render(request, 'confirm_delete.html', {'object': tx})


@login_required
def budgets_view(request):
    from .models import Budget, Category, Transaction
    from django import forms
    from django.db.models import Sum

    class BudgetForm(forms.Form):
        category_name = forms.CharField(label='Category Name', max_length=100, help_text='Enter a category name (e.g. Food, Travel)')
        amount = forms.DecimalField(label='Budget Amount', max_digits=12, decimal_places=2)
        currency = forms.ChoiceField(choices=[('USD', 'USD'), ('INR', 'INR'), ('EUR', 'EUR'), ('GBP', 'GBP')], initial='USD', widget=forms.Select(attrs={'style': 'width:100px;margin:0'}))

    if request.method == 'POST':
        form = BudgetForm(request.POST)
        if form.is_valid():
            cat_name = (form.cleaned_data['category_name'] or '').strip()
            if not cat_name:
                form.add_error('category_name', 'Enter a category name.')
            else:
                amount = form.cleaned_data['amount']
                currency = form.cleaned_data['currency']
                # Find or create category (manual: any name user types)
                category = Category.objects.filter(
                    owner=request.user, name__iexact=cat_name, type='expense'
                ).first()
                if not category:
                    category = Category.objects.create(
                        owner=request.user, name=cat_name, type='expense'
                    )
                # Find or create budget
                budget, created = Budget.objects.get_or_create(
                    owner=request.user,
                    category=category,
                    currency=currency,
                    defaults={'amount': amount}
                )
                if not created:
                    budget.amount = amount
                    budget.save()
                return redirect('budgets')
    else:
        form = BudgetForm()
    
    # Get budget status with remaining balance
    today = timezone.now().date()
    start, end = _month_range(today)
    budgets = []
    
    # helper for checking JSON txs
    user_data = _load_user_data(request.user)
    
    budget_cat_name_lower = None  # cache for JSON comparison

    for b in Budget.objects.filter(owner=request.user):
        # Sum by category name (case-insensitive) so all expenses for this category count
        spent = Transaction.objects.filter(
            owner=request.user,
            transaction_type='expense',
            date__gte=start,
            date__lt=end,
            category__name__iexact=b.category.name,
            currency=b.currency,
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')

        # Include JSON fallback transactions (match category name case-insensitively)
        try:
            db_ids = set(Transaction.objects.filter(
                owner=request.user, category__name__iexact=b.category.name
            ).values_list('id', flat=True))
        except Exception:
            db_ids = set()

        budget_cat_name_lower = (b.category.name or '').strip().lower()
        for d in user_data.get('transactions', []):
            d_cat = (d.get('category') or '').strip().lower()
            d_curr = d.get('currency', 'USD')
            if (d.get('transaction_type') == 'expense' and d_cat == budget_cat_name_lower
                    and d_curr == b.currency
                    and d.get('db_id') not in db_ids):
                try:
                    d_date = timezone.datetime.fromisoformat(d.get('date')).date() if isinstance(d.get('date'), str) else d.get('date')
                except Exception:
                    continue
                if d_date >= start and d_date < end:
                    try:
                        spent += Decimal(str(d.get('amount') or '0'))
                    except Exception:
                        pass
                        
        remaining = b.amount - spent
        percentage = min(100, int((spent / b.amount * 100) if b.amount > 0 else 0))
        overspent = abs(remaining) if remaining < 0 else 0
        
        budgets.append({
            'id': b.id,
            'category': b.category,
            'amount': b.amount,
            'currency': b.currency,
            'spent': spent,
            'remaining': remaining,
            'percentage': percentage,
            'overspent': overspent,
        })
    
    # Existing expense categories for suggestions (user can still type any new name)
    expense_categories = list(
        Category.objects.filter(owner=request.user, type='expense', is_active=True)
        .values_list('name', flat=True)
        .distinct()
    )
    month_label = today.strftime('%B %Y')  # e.g. "February 2026"
    return render(request, 'budgets.html', {
        'form': form,
        'budgets': budgets,
        'expense_categories': expense_categories,
        'month_label': month_label,
    })


@login_required
def budget_delete(request, budget_id):
    from .models import Budget
    budget = get_object_or_404(Budget, id=budget_id, owner=request.user)
    if request.method == 'POST':
        budget.delete()
        return redirect('budgets')
    return render(request, 'confirm_delete.html', {
        'object': budget,
        'message': f'Delete budget for "{budget.category.name}"? You can add it again later.',
        'cancel_url': '/budgets/',
    })


@login_required
def categories_view(request):
    from .models import Category
    if request.method == 'POST':
        name = (request.POST.get('name') or '').strip()
        tx_type = request.POST.get('type', 'expense')
        if name:
            existing = Category.objects.filter(owner=request.user, name__iexact=name).first()
            if not existing:
                Category.objects.create(owner=request.user, name=name, type=tx_type)
        return redirect('categories')
    categories = Category.objects.filter(owner=request.user).order_by('type', 'name')
    return render(request, 'categories.html', {'categories': categories})


@login_required
def category_delete(request, category_id):
    from .models import Category
    cat = get_object_or_404(Category, id=category_id, owner=request.user)
    if request.method == 'POST':
        cat.delete()
        return redirect('categories')
    return render(request, 'confirm_delete.html', {
        'object': cat,
        'message': f'Delete category "{cat.name}"? Transactions using it may need reassignment.',
        'cancel_url': '/categories/',
    })


@login_required
def monthly_report(request):
    from django.db.models.functions import TruncMonth
    from .models import Transaction
    from django.db.models import Sum
    
    # Monthly trend data by currency
    qs = Transaction.objects.filter(owner=request.user).annotate(month=TruncMonth('date')).values('month', 'transaction_type', 'currency').annotate(total=Sum('amount')).order_by('month', 'currency')
    
    monthly_data = {}
    for row in qs:
        m = row['month'].strftime('%Y-%m')
        curr = row['currency']
        key = (m, curr)
        if key not in monthly_data:
            monthly_data[key] = {'income': 0, 'expense': 0}
        
        val = float(row['total'] or 0)
        if row['transaction_type'] == 'income':
            monthly_data[key]['income'] = val
        else:
            monthly_data[key]['expense'] = val
            
    # Table data
    monthly_table = []
    for (m, curr), data in sorted(monthly_data.items()):
        monthly_table.append({
            'month': m,
            'currency': curr,
            'income': f"{data['income']:.2f}",
            'expense': f"{data['expense']:.2f}",
            'net': f"{data['income'] - data['expense']:.2f}"
        })
    
    # Prepare chart data (Note: charts still aggregate by month regardless of currency for simplicity, or we could separate them)
    # For now, let's keep charts simple (aggregate all) or just show data for first currency?
    # Let's aggregate for charts to show "activity volume" but warn about mixed currencies in UI if needed.
    # Actually, simpler to just use the new table for correctness.
    
    # Income by category
    income_by_cat = Transaction.objects.filter(owner=request.user, transaction_type='income').values('category__name').annotate(total=Sum('amount')).order_by('-total')
    income_cat_json = json.dumps({
        'labels': [item['category__name'] for item in income_by_cat],
        'data': [float(item['total'] or 0) for item in income_by_cat]
    })
    
    # Expense by category
    expense_by_cat = Transaction.objects.filter(owner=request.user, transaction_type='expense').values('category__name').annotate(total=Sum('amount')).order_by('-total')
    expense_cat_json = json.dumps({
        'labels': [item['category__name'] for item in expense_by_cat],
        'data': [float(item['total'] or 0) for item in expense_by_cat]
    })
    
    return render(request, 'reports.html', {
        'income_cat_json': income_cat_json,
        'expense_cat_json': expense_cat_json,
        'monthly_data': monthly_table,
    })


# small API + OAuth helpers (unchanged)

def api_transactions(request):
    from .models import Transaction
    if request.method != 'GET':
        return HttpResponse('Method not allowed', status=405)
    txs = Transaction.objects.all().order_by('-date')[:100]
    try:
        from rest_framework.response import Response
        data = [{'id': t.id, 'owner': t.owner.username, 'date': str(t.date), 'amount': str(t.amount), 'type': t.transaction_type, 'category': t.category.name} for t in txs]
        return Response(data)
    except Exception:
        return HttpResponse(json.dumps([{'id': t.id, 'owner': t.owner.username, 'date': str(t.date), 'amount': str(t.amount), 'type': t.transaction_type, 'category': t.category.name} for t in txs]), content_type='application/json')


def google_oauth_login(request):
    from django.conf import settings
    client_id = getattr(settings, 'GOOGLE_OAUTH_CLIENT_ID', None)
    if not client_id:
        return HttpResponse('Google OAuth Client ID is not configured in settings or .env', status=500)
    
    redirect_uri = request.build_absolute_uri('/oauth/google/callback/')
    auth_url = 'https://accounts.google.com/o/oauth2/v2/auth?' + urllib.parse.urlencode({'client_id': client_id, 'response_type': 'code', 'scope': 'email profile', 'redirect_uri': redirect_uri, 'access_type': 'offline', 'prompt': 'consent'})
    return HttpResponseRedirect(auth_url)


def google_oauth_callback(request):
    from django.contrib.auth.models import User
    from django.contrib.auth import login as auth_login
    from .models import Profile
    
    code = request.GET.get('code')
    if not code:
        return HttpResponse('No code provided', status=400)
    try:
        import urllib.request
        data = urllib.parse.urlencode({'code': code, 'client_id': settings.GOOGLE_OAUTH_CLIENT_ID, 'client_secret': settings.GOOGLE_OAUTH_CLIENT_SECRET, 'redirect_uri': request.build_absolute_uri('/oauth/google/callback/'), 'grant_type': 'authorization_code'}).encode()
        resp = urllib.request.urlopen('https://oauth2.googleapis.com/token', data=data)
        body = json.load(resp)
        access_token = body.get('access_token')
        info = json.load(urllib.request.urlopen('https://www.googleapis.com/oauth2/v1/userinfo?alt=json&access_token=' + urllib.parse.quote(access_token)))
        email = info.get('email')
        if not email:
            return HttpResponse('Email not provided by Google', status=400)
        
        # Check if user exists
        user = User.objects.filter(email=email).first()
        if user:
            # Login existing user
            user.backend = 'django.contrib.auth.backends.ModelBackend'
            auth_login(request, user)
            return redirect('index')
        else:
            # New user: redirect to finalize signup to choose username
            request.session['oauth_email'] = email
            request.session['oauth_name'] = info.get('name', '')
            request.session['oauth_token'] = access_token # Optional: store if needed later
            return redirect('finalize_signup')
    except Exception as e:
        return HttpResponse(f'OAuth failed: {e}', status=400)


def finalize_signup(request):
    from django.contrib.auth.models import User
    from django.contrib.auth import login as auth_login
    from .models import Profile
    
    email = request.session.get('oauth_email')
    if not email:
        return redirect('login')
    
    error = None
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        if not username:
            error = 'Username is required.'
        elif User.objects.filter(username=username).exists():
            error = 'Username is already taken. Please choose another.'
        else:
            try:
                user = User.objects.create_user(username=username, email=email)
                Profile.objects.get_or_create(user=user)
                
                # Cleanup session
                del request.session['oauth_email']
                if 'oauth_name' in request.session: del request.session['oauth_name']
                if 'oauth_token' in request.session: del request.session['oauth_token']
                
                user.backend = 'django.contrib.auth.backends.ModelBackend'
                auth_login(request, user)
                return redirect('index')
            except Exception as e:
                error = f'Error creating account: {e}'

    return render(request, 'finalize_signup.html', {'email': email, 'error': error})


def persistence_test(request):
    """Quick endpoint to append a JSON-only transaction for testing persistence across restarts."""
    if not request.user.is_authenticated:
        return HttpResponse('Login required', status=401)
    ttype = request.GET.get('type', 'expense')
    cat = request.GET.get('category', 'Test')
    amount = request.GET.get('amount', '100')
    # create JSON-only transaction
    _append_user_tx(request.user, {
        'date': str(timezone.now().date()),
        'amount': str(amount),
        'description': 'Persistence test',
        'category': cat,
        'transaction_type': ttype,
        'currency': 'INR',
    })
    return redirect('expenses' if ttype == 'expense' else 'income')


# -------------------------
# URLs
# -------------------------

urlpatterns = [
    path('', index, name='index'),
    path('register/', register, name='register'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('profile/', profile, name='profile'),
    path('income/', income_view, name='income'),
    path('income/add/', add_income, name='add_income'),
    path('expenses/', expense_view, name='expenses'),
    path('expenses/add/', add_expense, name='add_expense'),
    path('budgets/', budgets_view, name='budgets'),
    path('budgets/<int:budget_id>/delete/', budget_delete, name='budget_delete'),
    path('categories/', categories_view, name='categories'),
    path('categories/<int:category_id>/delete/', category_delete, name='category_delete'),
    path('transactions/<int:tx_id>/edit/', add_edit_transaction, name='edit_transaction'),
    path('transactions/<int:tx_id>/delete/', delete_transaction, name='delete_transaction'),
    path('reports/', monthly_report, name='reports'),
    path('api/transactions/', api_transactions, name='api_transactions'),
    path('oauth/google/login/', google_oauth_login, name='google_oauth_login'),
    path('oauth/google/callback/', google_oauth_callback, name='google_oauth_callback'),
    path('oauth/google/finalize/', finalize_signup, name='finalize_signup'),
    path('persistence-test/', lambda req: persistence_test(req), name='persistence_test'),
]

if settings.DEBUG:
    from django.conf.urls.static import static
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


# Lazy-model access: export model names from finance.models when requested.
_LAZY_MODELS = {'Profile', 'Category', 'Transaction', 'Budget'}

def __getattr__(name):
    if name in _LAZY_MODELS:
        from importlib import import_module
        mod = import_module('.models', __package__)
        return getattr(mod, name)
    raise AttributeError(f"module {__name__} has no attribute {name}")

def __dir__():
    return list(globals().keys()) + list(_LAZY_MODELS)
