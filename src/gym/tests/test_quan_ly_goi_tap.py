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


class QuanLyGoiTapTests(TestCase):
    def setUp(self):
        self.admin = TaiKhoan.objects.create_user(
            username="admin_quan_ly_goi_tap",
            password="1",
            vai_tro=TaiKhoan.VaiTro.ADMIN,
        )

        self.le_tan = TaiKhoan.objects.create_user(
            username="le_tan_khong_duoc_quan_ly_goi",
            password="1",
            vai_tro=TaiKhoan.VaiTro.LE_TAN,
        )

        self.goi_tap = GoiTap.objects.create(
            ten_goi="Gói kiểm thử ban đầu",
            thoi_han_ngay=30,
            gia_tien=500000,
            co_pt=False,
            so_buoi_pt=0,
            mo_ta="Gói dùng để kiểm thử giao diện",
            trang_thai=True,
        )

        self.url_danh_sach = reverse(
            "gym:danh_sach_goi_tap"
        )

        self.url_tao_moi = reverse(
            "gym:tao_goi_tap_moi"
        )

        self.url_chinh_sua = reverse(
            "gym:chinh_sua_goi_tap",
            args=[self.goi_tap.ma_goi],
        )

        self.url_doi_trang_thai = reverse(
            "gym:doi_trang_thai_goi_tap",
            args=[self.goi_tap.ma_goi],
        )

    def test_admin_xem_duoc_danh_sach_goi_tap(self):
        self.client.force_login(self.admin)

        response = self.client.get(
            self.url_danh_sach
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            "gym/goi_tap/danh_sach_goi_tap.html",
        )
        self.assertContains(
            response,
            "Gói kiểm thử ban đầu",
        )
        self.assertContains(
            response,
            self.goi_tap.ma_goi,
        )

    def test_tai_khoan_khong_phai_admin_bi_tu_choi_danh_sach(
        self
    ):
        self.client.force_login(self.le_tan)

        response = self.client.get(
            self.url_danh_sach
        )

        self.assertEqual(response.status_code, 403)

    def test_admin_tao_goi_khong_pt_tu_dong_luu_0_buoi(self):
        self.client.force_login(self.admin)

        response = self.client.post(
            self.url_tao_moi,
            {
                "ten_goi": "Gói thường mới",
                "thoi_han_ngay": "45",
                "gia_tien": "650000",
                "so_buoi_pt": "9",
                "mo_ta": "Không chọn PT",
            },
        )

        self.assertRedirects(
            response,
            self.url_danh_sach,
        )

        goi_tap = GoiTap.objects.get(
            ten_goi="Gói thường mới"
        )

        self.assertRegex(
            goi_tap.ma_goi,
            r"^Goi\d+$",
        )
        self.assertFalse(goi_tap.co_pt)
        self.assertEqual(goi_tap.so_buoi_pt, 0)
        self.assertTrue(goi_tap.trang_thai)

    def test_admin_tao_goi_co_pt_thanh_cong(self):
        self.client.force_login(self.admin)

        response = self.client.post(
            self.url_tao_moi,
            {
                "ten_goi": "Gói PT mới",
                "thoi_han_ngay": "60",
                "gia_tien": "1200000",
                "co_pt": "on",
                "so_buoi_pt": "12",
                "mo_ta": "Gói có huấn luyện viên",
            },
        )

        self.assertRedirects(
            response,
            self.url_danh_sach,
        )

        goi_tap = GoiTap.objects.get(
            ten_goi="Gói PT mới"
        )

        self.assertTrue(goi_tap.co_pt)
        self.assertEqual(goi_tap.so_buoi_pt, 12)

    def test_goi_co_pt_bat_buoc_co_so_buoi_duong(self):
        self.client.force_login(self.admin)

        so_luong_ban_dau = GoiTap.objects.count()

        response = self.client.post(
            self.url_tao_moi,
            {
                "ten_goi": "Gói PT lỗi",
                "thoi_han_ngay": "30",
                "gia_tien": "800000",
                "co_pt": "on",
                "so_buoi_pt": "0",
                "mo_ta": "",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(
            "so_buoi_pt",
            response.context["form"].errors,
        )
        self.assertEqual(
            GoiTap.objects.count(),
            so_luong_ban_dau,
        )

    def test_thoi_han_va_gia_khong_hop_le_bi_tu_choi(self):
        self.client.force_login(self.admin)

        response = self.client.post(
            self.url_tao_moi,
            {
                "ten_goi": "Gói dữ liệu lỗi",
                "thoi_han_ngay": "0",
                "gia_tien": "-1000",
                "so_buoi_pt": "0",
                "mo_ta": "",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(
            "thoi_han_ngay",
            response.context["form"].errors,
        )
        self.assertIn(
            "gia_tien",
            response.context["form"].errors,
        )
        self.assertFalse(
            GoiTap.objects.filter(
                ten_goi="Gói dữ liệu lỗi"
            ).exists()
        )

    def test_admin_chinh_sua_goi_tap_thanh_cong(self):
        self.client.force_login(self.admin)

        ma_goi_ban_dau = self.goi_tap.ma_goi
        trang_thai_ban_dau = self.goi_tap.trang_thai

        response = self.client.post(
            self.url_chinh_sua,
            {
                "ten_goi": "Gói đã cập nhật",
                "thoi_han_ngay": "90",
                "gia_tien": "900000",
                "co_pt": "on",
                "so_buoi_pt": "15",
                "mo_ta": "Thông tin mới",
            },
        )

        self.assertRedirects(
            response,
            self.url_danh_sach,
        )

        self.goi_tap.refresh_from_db()

        self.assertEqual(
            self.goi_tap.ten_goi,
            "Gói đã cập nhật",
        )
        self.assertEqual(
            self.goi_tap.thoi_han_ngay,
            90,
        )
        self.assertEqual(
            str(self.goi_tap.gia_tien),
            "900000.00",
        )
        self.assertTrue(self.goi_tap.co_pt)
        self.assertEqual(
            self.goi_tap.so_buoi_pt,
            15,
        )

        self.assertEqual(
            self.goi_tap.ma_goi,
            ma_goi_ban_dau,
        )
        self.assertEqual(
            self.goi_tap.trang_thai,
            trang_thai_ban_dau,
        )

    def test_ma_goi_khong_ton_tai_tra_ve_404(self):
        self.client.force_login(self.admin)

        response = self.client.get(
            reverse(
                "gym:chinh_sua_goi_tap",
                args=["Goi999999"],
            )
        )

        self.assertEqual(response.status_code, 404)

    def test_admin_ngung_kinh_doanh_goi_tap(self):
        self.client.force_login(self.admin)

        response = self.client.post(
            self.url_doi_trang_thai,
            {
                "hanh_dong": "ngung_kinh_doanh",
            },
        )

        self.assertRedirects(
            response,
            self.url_danh_sach,
        )

        self.goi_tap.refresh_from_db()

        self.assertFalse(self.goi_tap.trang_thai)

    def test_admin_mo_lai_kinh_doanh_goi_tap(self):
        self.goi_tap.trang_thai = False
        self.goi_tap.save(
            update_fields=["trang_thai"],
        )

        self.client.force_login(self.admin)

        response = self.client.post(
            self.url_doi_trang_thai,
            {
                "hanh_dong": "mo_kinh_doanh",
            },
        )

        self.assertRedirects(
            response,
            self.url_danh_sach,
        )

        self.goi_tap.refresh_from_db()

        self.assertTrue(self.goi_tap.trang_thai)

    def test_get_khong_duoc_dung_de_doi_trang_thai(self):
        self.client.force_login(self.admin)

        response = self.client.get(
            self.url_doi_trang_thai
        )

        self.assertEqual(response.status_code, 405)

        self.goi_tap.refresh_from_db()

        self.assertTrue(self.goi_tap.trang_thai)

    def test_hanh_dong_doi_trang_thai_sai_bi_tu_choi(self):
        self.client.force_login(self.admin)

        response = self.client.post(
            self.url_doi_trang_thai,
            {
                "hanh_dong": "xoa_goi",
            },
        )

        self.assertEqual(response.status_code, 400)

        self.goi_tap.refresh_from_db()

        self.assertTrue(self.goi_tap.trang_thai)

    def test_tai_khoan_khong_phai_admin_khong_duoc_doi_trang_thai(
        self
    ):
        self.client.force_login(self.le_tan)

        response = self.client.post(
            self.url_doi_trang_thai,
            {
                "hanh_dong": "ngung_kinh_doanh",
            },
        )

        self.assertEqual(response.status_code, 403)

        self.goi_tap.refresh_from_db()

        self.assertTrue(self.goi_tap.trang_thai)
