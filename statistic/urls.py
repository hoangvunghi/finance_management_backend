from django.urls import path
from . import views

urlpatterns = [
    path('analytics/', views.get_expense_analytics, name='expense_analytics'),
]