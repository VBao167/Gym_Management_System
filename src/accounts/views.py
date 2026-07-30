from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required
def trang_chu(request):
    return render(
        request,
        "accounts/trang_chu.html",
    )