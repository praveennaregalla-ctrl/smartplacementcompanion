import django
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'spc.settings')
django.setup()

from django.template import loader
from core.models import Student, Placement, Company

# Get test data
student = Student.objects.get(id=1)
placements = student.placements.select_related('company').all()

# Create template context
context = {
    'student': student,
    'placements': placements,
}

# Try to render the template
try:
    template = loader.get_template('core/student_detail.html')
    html = template.render(context)
    print("✓ Template rendered successfully!")
    print(f"Generated HTML length: {len(html)} characters")
    
    # Check if "My Applications" section is present
    if "My Applications & Tracking" in html:
        print("✓ 'My Applications' section found in rendered template")
    else:
        print("✗ 'My Applications' section NOT found")
        
    # Check for status badges
    if "status-badge" in html:
        print("✓ Status badges CSS class found")
    else:
        print("✗ Status badges CSS class NOT found")
        
except Exception as e:
    print(f"✗ Template rendering failed: {e}")
    import traceback
    traceback.print_exc()
