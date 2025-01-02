from datetime import datetime, timedelta
from rest_framework import status, permissions
from rest_framework.response import Response
from django.utils.timezone import make_aware, get_current_timezone
from rest_framework.decorators import api_view, permission_classes
from django.utils import timezone
from .models import Category, Transaction, TransactionType
from .serializers import CategorySerializer, TransactionSerializer, TransactionTypeSerializer, TransactionUpdateSerializer
from authenticate.permissions import IsOwnerOrReadonly, IsAuthenticatedAndTokenValid

# TransactionType API
@api_view(['GET'])
def transaction_type_list(request):
    if request.method == 'GET':
        transaction_types = TransactionType.objects.all()
        serializer = TransactionTypeSerializer(transaction_types, many=True)
        return Response(serializer.data)
   
@api_view(['GET',])
def transaction_type_detail(request, pk):
    try:
        transaction_type = TransactionType.objects.get(pk=pk)
    except TransactionType.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)
    if request.method == 'GET':
        serializer = TransactionTypeSerializer(transaction_type)
        return Response(serializer.data)
    
# Category API
@api_view(['GET'])
def category_list(request):
    if request.method == 'GET':
        categories = Category.objects.all()
        serializer = CategorySerializer(categories, many=True)
        return Response(serializer.data)

# hàm lấy ra các tên của category với truyền vào là transaction_type_id 
@api_view(['GET'])
def get_category_names(request,transaction_type_id):
    categories = Category.objects.filter(type__id=transaction_type_id)
    data = [category.name for category in categories]
    return Response(data)

@api_view(['GET'])
def category_detail(request, pk):
    try:
        category = Category.objects.get(pk=pk)
    except Category.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)
    if request.method == 'GET':
        serializer = CategorySerializer(category)
        return Response(serializer.data)

# Transaction API
@api_view(['GET', 'POST'])
@permission_classes([permissions.IsAuthenticatedOrReadOnly])
def transaction_list(request):
    if request.method == 'GET':
        start_date = request.query_params.get('start_date', None)
        end_date = request.query_params.get('end_date', None)
        year = request.query_params.get('year', None)
        transactions = Transaction.objects.filter(user=request.user)

        if year:
            try:
                year = int(year)
                current_year = datetime.now().year

                start_of_year = datetime(year, 1, 1)
                if year == current_year:
                    end_of_year = datetime.now()  
                else:
                    end_of_year = datetime(year, 12, 31, 23, 59, 59)

                current_timezone = get_current_timezone()
                start_of_year = make_aware(start_of_year, current_timezone)
                end_of_year = make_aware(end_of_year, current_timezone)

                transactions = transactions.filter(transaction_date__range=(start_of_year, end_of_year))
            except (ValueError, TypeError):
                return Response({"error": "Invalid year format. Use YYYY."}, status=status.HTTP_400_BAD_REQUEST)

        elif start_date and end_date:
            try:
                start_date = datetime.strptime(start_date, '%Y-%m-%d')
                end_date = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1) - timedelta(seconds=1)

                current_timezone = get_current_timezone()
                start_date = make_aware(start_date, current_timezone)
                end_date = make_aware(end_date, current_timezone)

                # Lọc giao dịch trong khoảng thời gian
                transactions = transactions.filter(transaction_date__range=(start_date, end_date))
            except (ValueError, TypeError):
                return Response({"error": "Invalid date format. Use YYYY-MM-DD."}, status=status.HTTP_400_BAD_REQUEST)

        transactions = transactions.order_by('-transaction_date')

        serializer = TransactionSerializer(transactions, many=True)
        response_data = {
            "response": "Success",
            "data": serializer.data,
            "status": status.HTTP_200_OK,
        }
        return Response(response_data, status=status.HTTP_200_OK)

    elif request.method == 'POST':
        try:
            category_name = request.data.get('categoryName')
            category = Category.objects.get(name=category_name)

            transaction = Transaction(
                user=request.user,
                category=category,
                amount=request.data.get('amount'),
                description=request.data.get('description'),
                transaction_date=request.data.get('transactionDate')
            )
            transaction.save()

            return Response(TransactionSerializer(transaction).data, status=status.HTTP_201_CREATED)
        except Category.DoesNotExist:
            return Response({"error": "Danh mục không tồn tại"}, status=status.HTTP_400_BAD_REQUEST)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
# @permission_classes([IsOwnerOrReadonly])
def transaction_detail(request, pk):
    try:
        transaction = Transaction.objects.get(pk=pk)
    except Transaction.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)
    
    if request.user != transaction.user:
        return Response(status=status.HTTP_403_FORBIDDEN)
    
    if request.method == 'GET':
        serializer = TransactionSerializer(transaction)
        return Response(serializer.data)
    
    elif request.method == 'PUT' or request.method == 'PATCH':
        try:
            print(request.data)
            category_name = request.data.get('categoryName')
            category = Category.objects.get(name=category_name)
            
            # Cập nhật transaction
            transaction.category = category
            transaction.amount = request.data.get('amount')
            transaction.description = request.data.get('description')
            transaction.transaction_date = request.data.get('transactionDate')
            
            transaction.save()
            return Response(status=status.HTTP_200_OK, data=TransactionSerializer(transaction).data)
        except Category.DoesNotExist:
            return Response({"error": "Invalid category name"}, status=status.HTTP_400_BAD_REQUEST)
        except ValueError as e:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        transaction.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


def obj_update(obj, validated_data):
    for key, value in validated_data.items():
        if key == 'categoryName':
            try:
                category = Category.objects.get(__name__=value)
                setattr(obj, key, category)
            except Category.DoesNotExist:
                raise ValueError(f"Invalid Category Name provided: {value}")

        else:
            setattr(obj, key, value)

    obj.save()
