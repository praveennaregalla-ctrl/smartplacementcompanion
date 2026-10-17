from django.shortcuts import render
from core.decorators import role_required
from django.db.models import Count, Q
from django.db.models.functions import ExtractMonth
from core.models import Student, Company, Placement

@role_required(['admin', 'student'])
def dashboard(request):
    total_students = Student.objects.count()
    total_companies = Company.objects.count()
    total_placements = Placement.objects.count()
    
    selected = Placement.objects.filter(status='SELECTED').count()
    placement_rate = (selected / total_students * 100) if total_students > 0 else 0
    
    # Data for charts
    # 1. Placements by Status
    status_data = Placement.objects.values('status').annotate(count=Count('id'))
    
    # 2. Placements by Branch
    branch_data = Student.objects.values('branch').annotate(
        placed=Count('placements', filter=Q(placements__status='SELECTED')),
        total=Count('id')
    )
    
    # 3. Monthly Trends (last 6 months)
    from django.utils import timezone
    from datetime import timedelta
    import calendar

    six_months_ago = timezone.now() - timedelta(days=180)
    trend_data_qs = Placement.objects.filter(created_at__gte=six_months_ago).annotate(
        month=ExtractMonth('created_at')
    ).values('month').annotate(count=Count('id')).order_by('month')

    trend_data = [
        {'month': calendar.month_abbr[item['month']], 'count': item['count']}
        for item in trend_data_qs if item['month']
    ]

    context = {
        'total_students': total_students,
        'total_companies': total_companies,
        'selected': selected,
        'placement_rate': round(placement_rate, 1),
        'status_data': list(status_data),
        'branch_data': list(branch_data),
        'trend_data': trend_data
    }
    return render(request, 'analytics/dashboard.html', context)
