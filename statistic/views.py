from django.db.models import Sum
from django.db.models.functions import TruncMonth, TruncDate
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.utils import timezone
from datetime import datetime
import calendar
from base.models import Transaction

@api_view(['GET'])
def get_expense_analytics(request):
    user = request.user
    print(request.GET)
    # Lấy tham số từ query
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    # Lấy ngày đầu năm và ngày hiện tại
    
    year = request.GET.get('year')
    print("-----------------")
    print(year)

    if not year:
        year = timezone.now().year
    print(year)
    year = int(year)  
    if not start_date and not end_date:
        start_date = f'{year}-01-01'
        end_date = f'{year}-12-31'
    current_year = timezone.now().year
    year_start = timezone.datetime(current_year, 1, 1).date()
    today = timezone.now().date()
    
    # Nếu có ngày bắt đầu và kết thúc, chuyển đổi sang định dạng date
    if start_date and end_date:
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            return Response({'error': 'Invalid date format'}, status=400)
    
    # 1. Pie Chart tổng thể: Tổng thu và chi
    pie_data = Transaction.objects.filter(
        user=user,
        transaction_date__range=(start_date or year_start, end_date or today)
    ).values(
        'category__type__name'
    ).annotate(
        total=Sum('amount')
    )
    
    # 2. Pie Chart thu nhập: Các danh mục thu
    income_categories = Transaction.objects.filter(
        user=user,
        category__type__name="Thu",
        transaction_date__range=(start_date or year_start, end_date or today)
    ).values(
        'category__name'
    ).annotate(
        total=Sum('amount')
    )
    
    # 3. Pie Chart chi tiêu: Các danh mục chi
    expense_categories = Transaction.objects.filter(
        user=user,
        category__type__name="Chi",
        transaction_date__range=(start_date or year_start, end_date or today)
    ).values(
        'category__name'
    ).annotate(
        total=Sum('amount')
    )
    
    # 4. Bar Chart: Thu và chi theo tháng
    monthly_transactions = Transaction.objects.filter(
        user=user,
        transaction_date__year=year
    ).annotate(
        month=TruncMonth('transaction_date')
    ).values('month', 'category__type__name').annotate(
        total=Sum('amount')
    ).order_by('month')

    # Xử lý dữ liệu theo tháng
    monthly_data = []
    current_year = timezone.now().year
    current_month = timezone.now().month

    # Xác định số tháng cần hiển thị
    if year == current_year:
        # Năm hiện tại: hiển thị từ tháng 1 đến tháng hiện tại
        num_months = current_month
    else:
        # Năm khác: hiển thị đủ 12 tháng
        num_months = 12

    for month in range(1, num_months + 1):
        month_data = {
            'month': calendar.month_abbr[month],  # Tên tháng viết tắt (ví dụ: "Jan")
            'thu': 0,  # Tổng thu
            'chi': 0   # Tổng chi
        }
        
        # Lọc dữ liệu giao dịch trong tháng hiện tại
        for trans in monthly_transactions:
            if trans['month'].month == month:
                if trans['category__type__name'] == 'Thu':
                    month_data['thu'] = trans['total']
                else:
                    month_data['chi'] = abs(trans['total'])  # Chi tiêu là số âm, lấy giá trị tuyệt đối
        
        monthly_data.append(month_data)
        
    # 5. Line Chart: Chi tiêu hàng ngày
    date_range = (start_date, end_date) if start_date and end_date else (today - timezone.timedelta(days=6), today)
    
    daily_transactions = Transaction.objects.filter(
        user=user,
        transaction_date__range=date_range
    ).annotate(
        date=TruncDate('transaction_date')
    ).values('date', 'category__type__name').annotate(
        total=Sum('amount')
    ).order_by('date')
    
    # Xử lý dữ liệu hàng ngày
    daily_data = []
    current_date = date_range[0]
    while current_date <= date_range[1]:
        day_data = {
            'date': current_date.strftime('%d/%m'),
            'thu': 0,
            'chi': 0
        }
        
        for trans in daily_transactions:
            if trans['date'] == current_date:
                if trans['category__type__name'] == 'Thu':
                    day_data['thu'] = trans['total']
                else:
                    day_data['chi'] = abs(trans['total'])
        
        daily_data.append(day_data)
        current_date += timezone.timedelta(days=1)
    
    # Trả về dữ liệu
    return Response({
        'pie_data': list(pie_data),
        'income_categories': list(income_categories),
        'expense_categories': list(expense_categories),
        'monthly_data': monthly_data,
        'daily_data': daily_data
    })