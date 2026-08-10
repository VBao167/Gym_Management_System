import re
from datetime import date

from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse

from accounts.models import TaiKhoan
from gym.models import HoiVien, HuanLuyenVien, LeTan


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

        self.hoi_vien = HoiVien.objects.create(
            tai_khoan=self.tai_khoan_hoat_dong,
            ho_ten="Hội viên kiểm thử xác thực",
            gioi_tinh="Nam",
            ngay_sinh=date(2001, 1, 1),
            sdt="0919000001",
            email="hoi.vien.xac.thuc@example.com",
            dia_chi="TP.HCM",
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
            fetch_redirect_response=False,
        )

        response = self.client.get(
            reverse("accounts:trang_chu")
        )

        self.assertRedirects(
            response,
            reverse("gym:trang_hoi_vien"),
        )
        self.assertTrue(
            response.wsgi_request.user.is_authenticated
        )

        response = self.client.get(
            reverse("gym:trang_hoi_vien")
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "Tổng quan Hội viên",
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
            fetch_redirect_response=False,
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

        self.assertRedirects(
            response,
            reverse("gym:trang_hoi_vien"),
        )
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

class QuanLyTaiKhoanTests(TestCase):
    def setUp(self):
        self.admin = TaiKhoan.objects.create_user(
            username="admin_quan_ly_tai_khoan",
            password="1",
            vai_tro=TaiKhoan.VaiTro.ADMIN,
        )

        self.admin_khac = TaiKhoan.objects.create_user(
            username="admin_khac",
            password="1",
            vai_tro=TaiKhoan.VaiTro.ADMIN,
        )

        self.tai_khoan_hoi_vien = (
            TaiKhoan.objects.create_user(
                username="hoi_vien_tai_khoan",
                password="1",
                vai_tro=TaiKhoan.VaiTro.HOI_VIEN,
            )
        )

        self.hoi_vien = HoiVien.objects.create(
            tai_khoan=self.tai_khoan_hoi_vien,
            ho_ten="Hội viên quản lý tài khoản",
            gioi_tinh="Nam",
            ngay_sinh=date(2001, 1, 1),
            sdt="0919000101",
            email="hoi.vien.tai.khoan@example.com",
            dia_chi="TP.HCM",
        )

        self.tai_khoan_le_tan = (
            TaiKhoan.objects.create_user(
                username="le_tan_tai_khoan",
                password="1",
                vai_tro=TaiKhoan.VaiTro.LE_TAN,
            )
        )

        self.le_tan = LeTan.objects.create(
            tai_khoan=self.tai_khoan_le_tan,
            ho_ten="Lễ tân quản lý tài khoản",
            gioi_tinh="Nữ",
            ngay_sinh=date(2000, 1, 1),
            sdt="0919000102",
            email="le.tan.tai.khoan@example.com",
            dia_chi="TP.HCM",
            trang_thai=True,
        )

        self.tai_khoan_pt = (
            TaiKhoan.objects.create_user(
                username="pt_tai_khoan",
                password="1",
                vai_tro=TaiKhoan.VaiTro.PT,
                is_active=False,
            )
        )

        self.pt = HuanLuyenVien.objects.create(
            tai_khoan=self.tai_khoan_pt,
            ho_ten="PT quản lý tài khoản",
            gioi_tinh="Nam",
            ngay_sinh=date(1999, 1, 1),
            sdt="0919000103",
            email="pt.tai.khoan@example.com",
            dia_chi="TP.HCM",
            trang_thai=False,
        )

    def test_admin_xem_duoc_danh_sach_tai_khoan(self):
        self.client.force_login(self.admin)

        response = self.client.get(
            reverse("accounts:danh_sach_tai_khoan")
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            "accounts/danh_sach_tai_khoan.html",
        )
        self.assertContains(
            response,
            "admin_quan_ly_tai_khoan",
        )
        self.assertContains(
            response,
            "hoi_vien_tai_khoan",
        )
        self.assertContains(
            response,
            "le_tan_tai_khoan",
        )

    def test_hoi_vien_khong_duoc_xem_danh_sach_tai_khoan(
        self,
    ):
        self.client.force_login(
            self.tai_khoan_hoi_vien
        )

        response = self.client.get(
            reverse("accounts:danh_sach_tai_khoan")
        )

        self.assertEqual(response.status_code, 403)

    def test_loc_tai_khoan_theo_vai_tro(self):
        self.client.force_login(self.admin)

        response = self.client.get(
            reverse("accounts:danh_sach_tai_khoan"),
            {
                "vai_tro": TaiKhoan.VaiTro.HOI_VIEN,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "hoi_vien_tai_khoan",
        )
        self.assertNotContains(
            response,
            "le_tan_tai_khoan",
        )
        self.assertNotContains(
            response,
            "pt_tai_khoan",
        )

    def test_tim_tai_khoan_theo_ten_nguoi_dung(self):
        self.client.force_login(self.admin)

        response = self.client.get(
            reverse("accounts:danh_sach_tai_khoan"),
            {
                "tu_khoa": (
                    "Hội viên quản lý tài khoản"
                ),
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "hoi_vien_tai_khoan",
        )
        self.assertNotContains(
            response,
            "le_tan_tai_khoan",
        )

    def test_admin_khoa_duoc_tai_khoan_hoi_vien(
        self,
    ):
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse(
                "accounts:doi_trang_thai_tai_khoan",
                args=[
                    self.tai_khoan_hoi_vien.ma_tk
                ],
            ),
            {
                "hanh_dong": "khoa",
            },
        )

        self.assertRedirects(
            response,
            reverse(
                "accounts:danh_sach_tai_khoan"
            ),
        )

        self.tai_khoan_hoi_vien.refresh_from_db()

        self.assertFalse(
            self.tai_khoan_hoi_vien.is_active
        )

    def test_admin_mo_khoa_duoc_tai_khoan_hoi_vien(
        self,
    ):
        self.tai_khoan_hoi_vien.is_active = False
        self.tai_khoan_hoi_vien.save(
            update_fields=["is_active"],
        )

        self.client.force_login(self.admin)

        response = self.client.post(
            reverse(
                "accounts:doi_trang_thai_tai_khoan",
                args=[
                    self.tai_khoan_hoi_vien.ma_tk
                ],
            ),
            {
                "hanh_dong": "mo_khoa",
            },
        )

        self.assertRedirects(
            response,
            reverse(
                "accounts:danh_sach_tai_khoan"
            ),
        )

        self.tai_khoan_hoi_vien.refresh_from_db()

        self.assertTrue(
            self.tai_khoan_hoi_vien.is_active
        )

    def test_admin_mo_khoa_duoc_nhan_vien_dang_lam(
        self,
    ):
        self.tai_khoan_le_tan.is_active = False
        self.tai_khoan_le_tan.save(
            update_fields=["is_active"],
        )

        self.client.force_login(self.admin)

        response = self.client.post(
            reverse(
                "accounts:doi_trang_thai_tai_khoan",
                args=[
                    self.tai_khoan_le_tan.ma_tk
                ],
            ),
            {
                "hanh_dong": "mo_khoa",
            },
        )

        self.assertRedirects(
            response,
            reverse(
                "accounts:danh_sach_tai_khoan"
            ),
        )

        self.tai_khoan_le_tan.refresh_from_db()

        self.assertTrue(
            self.tai_khoan_le_tan.is_active
        )

    def test_khong_mo_khoa_nhan_vien_da_nghi(
        self,
    ):
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse(
                "accounts:doi_trang_thai_tai_khoan",
                args=[self.tai_khoan_pt.ma_tk],
            ),
            {
                "hanh_dong": "mo_khoa",
            },
        )

        self.assertEqual(response.status_code, 400)

        self.tai_khoan_pt.refresh_from_db()

        self.assertFalse(
            self.tai_khoan_pt.is_active
        )

    def test_admin_khong_duoc_khoa_admin_khac(
        self,
    ):
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse(
                "accounts:doi_trang_thai_tai_khoan",
                args=[self.admin_khac.ma_tk],
            ),
            {
                "hanh_dong": "khoa",
            },
        )

        self.assertEqual(response.status_code, 403)

        self.admin_khac.refresh_from_db()

        self.assertTrue(self.admin_khac.is_active)

    def test_admin_dat_lai_mat_khau_hoi_vien(
        self,
    ):
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse(
                "accounts:dat_lai_mat_khau",
                args=[
                    self.tai_khoan_hoi_vien.ma_tk
                ],
            ),
            {
                "new_password1": "MatKhauMoi123",
                "new_password2": "MatKhauMoi123",
            },
        )

        self.assertRedirects(
            response,
            reverse(
                "accounts:danh_sach_tai_khoan"
            ),
        )

        self.tai_khoan_hoi_vien.refresh_from_db()

        self.assertTrue(
            self.tai_khoan_hoi_vien.check_password(
                "MatKhauMoi123"
            )
        )
        self.assertFalse(
            self.tai_khoan_hoi_vien.check_password(
                "1"
            )
        )

    def test_admin_khong_dat_lai_mat_khau_admin_khac(
        self,
    ):
        self.client.force_login(self.admin)

        response = self.client.get(
            reverse(
                "accounts:dat_lai_mat_khau",
                args=[self.admin_khac.ma_tk],
            )
        )

        self.assertEqual(response.status_code, 403)

        self.admin_khac.refresh_from_db()

        self.assertTrue(
            self.admin_khac.check_password("1")
        )

class DoiMatKhauTests(TestCase):
    def setUp(self):
        self.admin = TaiKhoan.objects.create_user(
            username="admin_doi_mat_khau",
            password="1",
            vai_tro=TaiKhoan.VaiTro.ADMIN,
        )

        self.tai_khoan_hoi_vien = (
            TaiKhoan.objects.create_user(
                username="hoi_vien_doi_mat_khau",
                password="1",
                vai_tro=TaiKhoan.VaiTro.HOI_VIEN,
            )
        )

        self.hoi_vien = HoiVien.objects.create(
            tai_khoan=self.tai_khoan_hoi_vien,
            ho_ten="Hội viên đổi mật khẩu",
            gioi_tinh="Nam",
            ngay_sinh=date(2001, 1, 1),
            sdt="0919000201",
            email="hoi.vien.doi.mat.khau@example.com",
            dia_chi="TP.HCM",
        )

        self.le_tan = TaiKhoan.objects.create_user(
            username="le_tan_doi_mat_khau",
            password="1",
            vai_tro=TaiKhoan.VaiTro.LE_TAN,
        )

        self.pt = TaiKhoan.objects.create_user(
            username="pt_doi_mat_khau",
            password="1",
            vai_tro=TaiKhoan.VaiTro.PT,
        )

    def test_hoi_vien_xem_duoc_trang_doi_mat_khau(
        self,
    ):
        self.client.force_login(
            self.tai_khoan_hoi_vien
        )

        response = self.client.get(
            reverse(
                "accounts:doi_mat_khau_cua_toi"
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            "accounts/doi_mat_khau.html",
        )

    def test_hoi_vien_doi_mat_khau_thanh_cong(
        self,
    ):
        self.client.force_login(
            self.tai_khoan_hoi_vien
        )

        response = self.client.post(
            reverse(
                "accounts:doi_mat_khau_cua_toi"
            ),
            {
                "old_password": "1",
                "new_password1": "MatKhauMoi123",
                "new_password2": "MatKhauMoi123",
            },
        )

        self.assertRedirects(
            response,
            reverse("gym:trang_hoi_vien"),
        )

        self.tai_khoan_hoi_vien.refresh_from_db()

        self.assertTrue(
            self.tai_khoan_hoi_vien.check_password(
                "MatKhauMoi123"
            )
        )
        self.assertFalse(
            self.tai_khoan_hoi_vien.check_password(
                "1"
            )
        )

        response = self.client.get(
            reverse("gym:trang_hoi_vien")
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            response.wsgi_request.user.is_authenticated
        )

    def test_sai_mat_khau_hien_tai_khong_doi_duoc(
        self,
    ):
        self.client.force_login(
            self.tai_khoan_hoi_vien
        )

        response = self.client.post(
            reverse(
                "accounts:doi_mat_khau_cua_toi"
            ),
            {
                "old_password": "sai_mat_khau",
                "new_password1": "MatKhauMoi123",
                "new_password2": "MatKhauMoi123",
            },
        )

        self.assertEqual(response.status_code, 200)

        self.tai_khoan_hoi_vien.refresh_from_db()

        self.assertTrue(
            self.tai_khoan_hoi_vien.check_password(
                "1"
            )
        )

    def test_admin_tu_doi_mat_khau_duoc(self):
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse(
                "accounts:doi_mat_khau_cua_toi"
            ),
            {
                "old_password": "1",
                "new_password1": "AdminMoi123",
                "new_password2": "AdminMoi123",
            },
        )

        self.assertRedirects(
            response,
            reverse(
                "accounts:danh_sach_tai_khoan"
            ),
        )

        self.admin.refresh_from_db()

        self.assertTrue(
            self.admin.check_password("AdminMoi123")
        )

        response = self.client.get(
            reverse(
                "accounts:danh_sach_tai_khoan"
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            response.wsgi_request.user.is_authenticated
        )

    def test_le_tan_khong_duoc_tu_doi_mat_khau(
        self,
    ):
        self.client.force_login(self.le_tan)

        response = self.client.get(
            reverse(
                "accounts:doi_mat_khau_cua_toi"
            )
        )

        self.assertEqual(response.status_code, 403)

    def test_pt_khong_duoc_tu_doi_mat_khau(self):
        self.client.force_login(self.pt)

        response = self.client.get(
            reverse(
                "accounts:doi_mat_khau_cua_toi"
            )
        )

        self.assertEqual(response.status_code, 403)

    def test_chua_dang_nhap_khong_duoc_doi_mat_khau(
        self,
    ):
        url = reverse(
            "accounts:doi_mat_khau_cua_toi"
        )

        response = self.client.get(url)

        self.assertRedirects(
            response,
            (
                f"{reverse('accounts:dang_nhap')}"
                f"?next={url}"
            ),
        )