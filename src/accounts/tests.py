import re

from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse

from accounts.models import TaiKhoan


class TaiKhoanModelTests(TestCase):
    def test_tao_tai_khoan_tu_sinh_ma_va_bam_mat_khau(self):
        tai_khoan = TaiKhoan.objects.create_user(
            username="kiem_thu_tai_khoan",
            password="1",
            vai_tro=TaiKhoan.VaiTro.LE_TAN,
        )

        self.assertTrue(
            re.fullmatch(r"TK\d+", tai_khoan.ma_tk)
        )
        self.assertEqual(
            tai_khoan.username,
            "kiem_thu_tai_khoan",
        )
        self.assertEqual(
            tai_khoan.vai_tro,
            TaiKhoan.VaiTro.LE_TAN,
        )
        self.assertNotEqual(tai_khoan.password, "1")
        self.assertTrue(tai_khoan.check_password("1"))
        self.assertTrue(tai_khoan.is_active)

    def test_nhieu_tai_khoan_co_ma_khac_nhau(self):
        tai_khoan_1 = TaiKhoan.objects.create_user(
            username="kiem_thu_1",
            password="1",
            vai_tro=TaiKhoan.VaiTro.HOI_VIEN,
        )

        tai_khoan_2 = TaiKhoan.objects.create_user(
            username="kiem_thu_2",
            password="1",
            vai_tro=TaiKhoan.VaiTro.PT,
        )

        self.assertNotEqual(
            tai_khoan_1.ma_tk,
            tai_khoan_2.ma_tk,
        )
        self.assertNotEqual(
            tai_khoan_1.username,
            tai_khoan_2.username,
        )

    def test_username_khong_duoc_trung(self):
        TaiKhoan.objects.create_user(
            username="username_trung",
            password="1",
            vai_tro=TaiKhoan.VaiTro.HOI_VIEN,
        )

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                TaiKhoan.objects.create_user(
                    username="username_trung",
                    password="1",
                    vai_tro=TaiKhoan.VaiTro.LE_TAN,
                )


class XacThucTaiKhoanTests(TestCase):
    def setUp(self):
        self.tai_khoan_hoat_dong = TaiKhoan.objects.create_user(
            username="tai_khoan_hoat_dong",
            password="1",
            vai_tro=TaiKhoan.VaiTro.HOI_VIEN,
        )

        self.tai_khoan_bi_khoa = TaiKhoan.objects.create_user(
            username="tai_khoan_bi_khoa",
            password="1",
            vai_tro=TaiKhoan.VaiTro.LE_TAN,
            is_active=False,
        )

    def test_trang_dang_nhap_hien_thi_binh_thuong(self):
        response = self.client.get(
            reverse("accounts:dang_nhap")
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            "accounts/dang_nhap.html",
        )
        self.assertContains(response, "Đăng nhập")

    def test_trang_chu_bat_buoc_dang_nhap(self):
        trang_chu_url = reverse("accounts:trang_chu")
        dang_nhap_url = reverse("accounts:dang_nhap")

        response = self.client.get(trang_chu_url)

        self.assertRedirects(
            response,
            f"{dang_nhap_url}?next={trang_chu_url}",
        )

    def test_dang_nhap_dung_thanh_cong(self):
        response = self.client.post(
            reverse("accounts:dang_nhap"),
            {
                "username": "tai_khoan_hoat_dong",
                "password": "1",
            },
        )

        self.assertRedirects(
            response,
            reverse("accounts:trang_chu"),
        )

        response = self.client.get(
            reverse("accounts:trang_chu")
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "tai_khoan_hoat_dong",
        )
        self.assertTrue(
            response.wsgi_request.user.is_authenticated
        )

    def test_sai_mat_khau_khong_dang_nhap(self):
        response = self.client.post(
            reverse("accounts:dang_nhap"),
            {
                "username": "tai_khoan_hoat_dong",
                "password": "sai_mat_khau",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "Tên đăng nhập hoặc mật khẩu không đúng",
        )
        self.assertFalse(
            response.wsgi_request.user.is_authenticated
        )

    def test_tai_khoan_bi_khoa_khong_dang_nhap(self):
        response = self.client.post(
            reverse("accounts:dang_nhap"),
            {
                "username": "tai_khoan_bi_khoa",
                "password": "1",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "Tên đăng nhập hoặc mật khẩu không đúng",
        )
        self.assertFalse(
            response.wsgi_request.user.is_authenticated
        )

    def test_da_dang_nhap_khong_xem_lai_trang_dang_nhap(self):
        self.client.force_login(
            self.tai_khoan_hoat_dong
        )

        response = self.client.get(
            reverse("accounts:dang_nhap")
        )

        self.assertRedirects(
            response,
            reverse("accounts:trang_chu"),
        )

    def test_get_khong_the_dung_de_dang_xuat(self):
        self.client.force_login(
            self.tai_khoan_hoat_dong
        )

        response = self.client.get(
            reverse("accounts:dang_xuat")
        )

        self.assertEqual(response.status_code, 405)

        response = self.client.get(
            reverse("accounts:trang_chu")
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            response.wsgi_request.user.is_authenticated
        )

    def test_dang_xuat_bang_post_thanh_cong(self):
        self.client.force_login(
            self.tai_khoan_hoat_dong
        )

        response = self.client.post(
            reverse("accounts:dang_xuat")
        )

        self.assertRedirects(
            response,
            reverse("accounts:dang_nhap"),
        )

        response = self.client.get(
            reverse("accounts:trang_chu")
        )

        self.assertFalse(
            response.wsgi_request.user.is_authenticated
        )
