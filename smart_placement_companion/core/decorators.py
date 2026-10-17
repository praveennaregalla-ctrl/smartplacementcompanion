from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages

def role_required(allowed_roles):
    """
    Decorator to restrict access based on session role.
    Supports 'admin' and 'student'.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            role = request.session.get('role')
            
            # Admins can also be authenticated via Django User
            if 'admin' in allowed_roles:
                if role == 'admin' or request.user.is_authenticated:
                    # Sync role if not set but authenticated
                    if not role and request.user.is_authenticated:
                        request.session['role'] = 'admin'
                    return view_func(request, *args, **kwargs)
            
            if role in allowed_roles:
                if role == 'student' and request.session.get('must_change_student_password') and view_func.__name__ != 'change_student_password':
                    return redirect('change_student_password')
                return view_func(request, *args, **kwargs)
            
            messages.warning(request, "Please login to access this page.")
            return redirect('welcome')
        return _wrapped_view
    return decorator
