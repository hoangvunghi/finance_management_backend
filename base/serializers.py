from rest_framework import serializers
from .models import TransactionType, Category, Transaction

class TransactionTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = TransactionType
        fields = '__all__'
        

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'

class TransactionSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    category_image = serializers.ImageField(source='category.icon', read_only=True)
    category_type_name = serializers.CharField(source='category.type.name', read_only=True)
    category_id = serializers.IntegerField(source='category.id', read_only=True)
    category_type_id = serializers.IntegerField(source='category.type.id', read_only=True)

    class Meta:
        model = Transaction
        fields = ['id', 'amount', 'description', 'transaction_date', 'category_name',"category_image", 'category_type_name', 'category', 'category_id', 'category_type_id']

class TransactionUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = ['amount', 'description', 'transaction_date', 'category']