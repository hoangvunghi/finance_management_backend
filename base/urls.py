from django.urls import path
from . import views

urlpatterns = [
  path('transaction-types/', views.transaction_type_list, name='transaction-type-list'),
  path('transaction-types/<int:pk>/', views.transaction_type_detail, name='transaction-type-detail'),

  path('categories/', views.category_list, name='category-list'),
  path('categories/<int:pk>/', views.category_detail, name='category-detail'),
  path('categories/<int:transaction_type_id>/names/', views.get_category_names, name='category-names'),
  path('transactions/', views.transaction_list, name='transaction-list'),
  path('transactions/<int:pk>', views.transaction_detail, name='transaction-detail'),
]