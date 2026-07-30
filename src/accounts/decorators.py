from functools import wraps

from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied


def vai_tro_required(*vai_tro_cho_phep):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect_to_login(
                    request.get_full_path()
                )

            if request.user.vai_tro not in vai_tro_cho_phep:
                raise PermissionDenied(
                    "Bạn không có quyền truy cập khu vực này."
                )

            return view_func(request, *args, **kwargs)

        return wrapper

    return decorator