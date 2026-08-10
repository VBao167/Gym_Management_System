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
        "quan-ly-tai-khoan/",
        views.danh_sach_tai_khoan,
        name="danh_sach_tai_khoan",
    ),
    path(
        "quan-ly-tai-khoan/<str:ma_tk>/"
        "dat-lai-mat-khau/",
        views.dat_lai_mat_khau,
        name="dat_lai_mat_khau",
    ),
    path(
        "quan-ly-tai-khoan/<str:ma_tk>/"
        "doi-trang-thai/",
        views.doi_trang_thai_tai_khoan,
        name="doi_trang_thai_tai_khoan",
    ),
    path(
        "doi-mat-khau/",
        views.doi_mat_khau_cua_toi,
        name="doi_mat_khau_cua_toi",
    ),
    path(
        "",
        views.trang_chu,
        name="trang_chu",
    ),
]