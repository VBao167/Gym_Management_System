from django.contrib.auth import views as auth_views
from django.urls import path

from . import views


app_name = "accounts"

urlpatterns = [
    path(
        "dang-nhap/",
        auth_views.LoginView.as_view(
            template_name="accounts/dang_nhap.html",
            redirect_authenticated_user=True,
        ),
        name="dang_nhap",
    ),
    path(
        "dang-xuat/",
        auth_views.LogoutView.as_view(),
        name="dang_xuat",
    ),
    path(
        "",
        views.trang_chu,
        name="trang_chu",
    ),
]