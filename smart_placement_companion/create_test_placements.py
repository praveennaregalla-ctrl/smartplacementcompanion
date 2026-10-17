import django
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'spc.settings')
django.setup()

from core.models import Student, Company, Placement
from django.utils import timezone
from datetime import timedelta

# Get or create test data
student = Student.objects.get(id=1)
company = Company.objects.get(id=1)

# Create or get placements for demonstration
placements_data = [
    {'status': 'APPLIED', 'interview_date': None},
    {'status': 'SHORTLISTED', 'interview_date': timezone.now().date() + timedelta(days=5), 'interview_round': 'Technical Round 1'},
    {'status': 'SELECTED', 'interview_date': timezone.now().date() - timedelta(days=2), 'interview_round': 'Final Round'},
]

print("Creating test placements for Student 1...")
for i, data in enumerate(placements_data):
    company_id = i + 1
    try:
        c = Company.objects.get(id=company_id)
        placement, created = Placement.objects.get_or_create(
            student=student,
            company=c,
            defaults={
                'status': data['status'],
                'interview_date': data.get('interview_date'),
                'interview_round': data.get('interview_round'),
                'notes': f"Test placement {i+1}"
            }
        )
        if created:
            print(f"✓ Created placement: {c.name} - {data['status']}")
        else:
            print(f"✓ Placement already exists: {c.name} - {placement.status}")
            # Update status for testing
            placement.status = data['status']
            placement.interview_date = data.get('interview_date')
            placement.interview_round = data.get('interview_round')
            placement.save()
            print(f"  Updated to status: {data['status']}")
    except Company.DoesNotExist:
        print(f"✗ Company with id={company_id} not found")

print("\nStudent placements summary:")
placements = student.placements.all()
print(f"Total placements: {placements.count()}")
for p in placements:
    print(f"  - {p.company.name}: {p.status}")
