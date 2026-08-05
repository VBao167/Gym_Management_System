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


class PhanQuyenVaiTroTests(TestCase):
    def setUp(self):
        self.tai_khoan_theo_vai_tro = {
            TaiKhoan.VaiTro.ADMIN:
                TaiKhoan.objects.create_user(
                    username="kiem_thu_admin",
                    password="1",
                    vai_tro=TaiKhoan.VaiTro.ADMIN,
                ),
            TaiKhoan.VaiTro.LE_TAN:
                TaiKhoan.objects.create_user(
                    username="kiem_thu_le_tan",
                    password="1",
                    vai_tro=TaiKhoan.VaiTro.LE_TAN,
                ),
            TaiKhoan.VaiTro.PT:
                TaiKhoan.objects.create_user(
                    username="kiem_thu_pt",
                    password="1",
                    vai_tro=TaiKhoan.VaiTro.PT,
                ),
            TaiKhoan.VaiTro.HOI_VIEN:
                TaiKhoan.objects.create_user(
                    username="kiem_thu_hoi_vien",
                    password="1",
                    vai_tro=TaiKhoan.VaiTro.HOI_VIEN,
                ),
        }

        self.khu_vuc_theo_vai_tro = {
            TaiKhoan.VaiTro.ADMIN: (
                "gym:trang_quan_tri",
                "Tổng quan hệ thống",
            ),
            TaiKhoan.VaiTro.LE_TAN: (
                "gym:trang_le_tan",
                "Khu vực Lễ tân.",
            ),
            TaiKhoan.VaiTro.PT: (
                "gym:trang_pt",
                "Khu vực Huấn luyện viên",
            ),
            TaiKhoan.VaiTro.HOI_VIEN: (
                "gym:trang_hoi_vien",
                "Khu vực Hội viên.",
            ),
        }

    def test_chua_dang_nhap_bi_chuyen_den_trang_dang_nhap(self):
        dang_nhap_url = reverse("accounts:dang_nhap")

        for ten_url, _ in self.khu_vuc_theo_vai_tro.values():
            with self.subTest(ten_url=ten_url):
                khu_vuc_url = reverse(ten_url)

                response = self.client.get(khu_vuc_url)

                self.assertRedirects(
                    response,
                    f"{dang_nhap_url}?next={khu_vuc_url}",
                )

    def test_trang_chu_dieu_huong_dung_theo_vai_tro(self):
        for vai_tro, tai_khoan in (
            self.tai_khoan_theo_vai_tro.items()
        ):
            with self.subTest(vai_tro=vai_tro):
                self.client.force_login(tai_khoan)

                ten_url, _ = self.khu_vuc_theo_vai_tro[
                    vai_tro
                ]

                response = self.client.get(
                    reverse("accounts:trang_chu")
                )

                self.assertRedirects(
                    response,
                    reverse(ten_url),
                )

    def test_moi_vai_tro_truy_cap_duoc_khu_vuc_cua_minh(self):
        for vai_tro, tai_khoan in (
            self.tai_khoan_theo_vai_tro.items()
        ):
            with self.subTest(vai_tro=vai_tro):
                self.client.force_login(tai_khoan)

                ten_url, noi_dung = (
                    self.khu_vuc_theo_vai_tro[vai_tro]
                )

                response = self.client.get(
                    reverse(ten_url)
                )

                self.assertEqual(response.status_code, 200)
                self.assertContains(response, noi_dung)

    def test_truy_cap_khu_vuc_khac_bi_tu_choi(self):
        for vai_tro, tai_khoan in (
            self.tai_khoan_theo_vai_tro.items()
        ):
            self.client.force_login(tai_khoan)

            for vai_tro_muc_tieu, (
                ten_url,
                _,
            ) in self.khu_vuc_theo_vai_tro.items():
                if vai_tro_muc_tieu == vai_tro:
                    continue

                with self.subTest(
                    vai_tro=vai_tro,
                    vai_tro_muc_tieu=vai_tro_muc_tieu,
                ):
                    response = self.client.get(
                        reverse(ten_url)
                    )

                    self.assertEqual(
                        response.status_code,
                        403,
                    )

    def test_moi_khu_vuc_su_dung_dung_template(self):
        template_theo_vai_tro = {
            TaiKhoan.VaiTro.ADMIN:
                "gym/trang_chu/quan_tri.html",
            TaiKhoan.VaiTro.LE_TAN:
                "gym/trang_chu/le_tan.html",
            TaiKhoan.VaiTro.PT:
                "gym/trang_chu/pt.html",
            TaiKhoan.VaiTro.HOI_VIEN:
                "gym/trang_chu/hoi_vien.html",
        }

        for vai_tro, tai_khoan in (
            self.tai_khoan_theo_vai_tro.items()
        ):
            with self.subTest(vai_tro=vai_tro):
                self.client.force_login(tai_khoan)

                ten_url, _ = self.khu_vuc_theo_vai_tro[
                    vai_tro
                ]

                response = self.client.get(
                    reverse(ten_url)
                )

                self.assertTemplateUsed(
                    response,
                    template_theo_vai_tro[vai_tro],
                )
                self.assertTemplateUsed(
                    response,
                    "base.html",
                )

    def test_moi_trang_chinh_goi_dong_bo_toan_bo(self):
        for vai_tro, tai_khoan in (
            self.tai_khoan_theo_vai_tro.items()
        ):
            with self.subTest(vai_tro=vai_tro):
                self.client.force_login(tai_khoan)

                ten_url, _ = self.khu_vuc_theo_vai_tro[
                    vai_tro
                ]

                with patch(
                    "gym.views.cap_nhat_trang_thai_toan_bo"
                ) as ham_dong_bo:
                    response = self.client.get(
                        reverse(ten_url)
                    )

                self.assertEqual(response.status_code, 200)
                ham_dong_bo.assert_called_once_with()
