from datetime import date, time, timedelta
from unittest.mock import patch
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from accounts.models import TaiKhoan
from gym.models import (
    BuoiTapPT,
    DangKyGoiTap,
    DiemDanh,
    GoiTap,
    HoaDon,
    HoiVien,
    HuanLuyenVien,
    LeTan,
)
from gym.services.buoi_tap_pt import (
    tao_buoi_tap_pt,
    tao_buoi_tap_pt_tu_doi_tuong,
)
from gym.services.dang_ky_goi import tao_dang_ky_va_hoa_don
from gym.services.diem_danh import tao_diem_danh
from gym.services.gia_han_goi import gia_han_goi
from gym.services.nguoi_dung import (
    tao_hoi_vien,
    tao_huan_luyen_vien,
    tao_le_tan,
)
from gym.services.trang_thai_hoi_vien import (
    cap_nhat_trang_thai_hoi_vien,
    cap_nhat_trang_thai_toan_bo,
)


class DashboardQuanTriTests(TestCase):
    def setUp(self):
        self.hom_nay = timezone.localdate()

        self.admin = TaiKhoan.objects.create_user(
            username="admin_dashboard",
            password="1",
            vai_tro=TaiKhoan.VaiTro.ADMIN,
        )

        self.le_tan = tao_le_tan(
            ho_ten="Lễ tân Dashboard",
            gioi_tinh="Nữ",
            ngay_sinh=date(2000, 1, 1),
            sdt="0941000001",
            email="le.tan.dashboard@example.com",
            dia_chi="TP.HCM",
        )

        self.goi_tap_dang_kinh_doanh = GoiTap.objects.create(
            ten_goi="Gói Dashboard hoạt động",
            thoi_han_ngay=10,
            gia_tien=300000,
            co_pt=False,
            so_buoi_pt=0,
            mo_ta="Gói đang kinh doanh",
            trang_thai=True,
        )

        GoiTap.objects.create(
            ten_goi="Gói Dashboard ngừng kinh doanh",
            thoi_han_ngay=10,
            gia_tien=200000,
            co_pt=False,
            so_buoi_pt=0,
            mo_ta="Gói đã ngừng kinh doanh",
            trang_thai=False,
        )

        self.hoi_vien_dang_hoat_dong = tao_hoi_vien(
            ho_ten="Hội viên đang hoạt động",
            gioi_tinh="Nam",
            ngay_sinh=date(2001, 1, 1),
            sdt="0941000002",
            email="hoi.vien.hoat.dong@example.com",
            dia_chi="TP.HCM",
        )

        self.hoi_vien_het_han = tao_hoi_vien(
            ho_ten="Hội viên hết hạn",
            gioi_tinh="Nữ",
            ngay_sinh=date(2002, 2, 2),
            sdt="0941000003",
            email="hoi.vien.het.han.dashboard@example.com",
            dia_chi="TP.HCM",
        )

        tao_hoi_vien(
            ho_ten="Hội viên chưa có gói",
            gioi_tinh="Nam",
            ngay_sinh=date(2003, 3, 3),
            sdt="0941000004",
            email="hoi.vien.chua.co.goi.dashboard@example.com",
            dia_chi="TP.HCM",
        )

        tao_dang_ky_va_hoa_don(
            hoi_vien=self.hoi_vien_dang_hoat_dong,
            goi_tap=self.goi_tap_dang_kinh_doanh,
            le_tan=self.le_tan,
            ngay_dang_ky=self.hom_nay,
            ngay_bat_dau=self.hom_nay,
            phuong_thuc_thanh_toan=(
                HoaDon.PhuongThucThanhToan.TIEN_MAT
            ),
        )

        ngay_cu = self.hom_nay - timedelta(days=20)

        tao_dang_ky_va_hoa_don(
            hoi_vien=self.hoi_vien_het_han,
            goi_tap=self.goi_tap_dang_kinh_doanh,
            le_tan=self.le_tan,
            ngay_dang_ky=ngay_cu,
            ngay_bat_dau=ngay_cu,
            phuong_thuc_thanh_toan=(
                HoaDon.PhuongThucThanhToan.TIEN_MAT
            ),
        )

        tao_diem_danh(
            hoi_vien=self.hoi_vien_dang_hoat_dong,
            le_tan=self.le_tan,
        )

        diem_danh_hom_qua = tao_diem_danh(
            hoi_vien=self.hoi_vien_dang_hoat_dong,
            le_tan=self.le_tan,
        )

        DiemDanh.objects.filter(
            pk=diem_danh_hom_qua.pk,
        ).update(
            thoi_gian_diem_danh=(
                timezone.now() - timedelta(days=1)
            ),
        )

    def test_dashboard_hien_thi_dung_so_lieu(self):
        self.client.force_login(self.admin)

        response = self.client.get(
            reverse("gym:trang_quan_tri")
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            "gym/trang_chu/quan_tri.html",
        )

        self.assertEqual(
            response.context["tong_hoi_vien"],
            3,
        )
        self.assertEqual(
            response.context["hoi_vien_dang_hoat_dong"],
            1,
        )
        self.assertEqual(
            response.context["goi_tap_dang_kinh_doanh"],
            1,
        )
        self.assertEqual(
            response.context["diem_danh_hom_nay"],
            1,
        )

        self.assertContains(
            response,
            "Tổng quan hệ thống",
        )
