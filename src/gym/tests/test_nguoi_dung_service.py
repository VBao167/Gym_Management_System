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


class TaoNguoiDungServiceTests(TestCase):
    def test_tao_hoi_vien_kem_tai_khoan(self):
        hoi_vien = tao_hoi_vien(
            ho_ten="Hội viên kiểm thử",
            gioi_tinh="Nam",
            ngay_sinh=date(2000, 1, 1),
            sdt="0901000001",
            email="hoi.vien@example.com",
            dia_chi="TP.HCM",
        )

        self.assertRegex(hoi_vien.ma_hv, r"^HV\d+$")
        self.assertFalse(hoi_vien.trang_thai)

        tai_khoan = hoi_vien.tai_khoan

        self.assertRegex(tai_khoan.ma_tk, r"^TK\d+$")
        self.assertEqual(tai_khoan.username, hoi_vien.ma_hv)
        self.assertEqual(
            tai_khoan.vai_tro,
            TaiKhoan.VaiTro.HOI_VIEN,
        )
        self.assertTrue(tai_khoan.is_active)
        self.assertTrue(tai_khoan.check_password("1"))

    def test_tao_le_tan_va_huan_luyen_vien(self):
        le_tan = tao_le_tan(
            ho_ten="Lễ tân kiểm thử",
            gioi_tinh="Nữ",
            ngay_sinh=date(2000, 2, 2),
            sdt="0901000002",
            email="le.tan@example.com",
            dia_chi="TP.HCM",
        )

        huan_luyen_vien = tao_huan_luyen_vien(
            ho_ten="PT kiểm thử",
            gioi_tinh="Nam",
            ngay_sinh=date(1999, 3, 3),
            sdt="0901000003",
            email="pt@example.com",
            dia_chi="TP.HCM",
        )

        self.assertRegex(le_tan.ma_lt, r"^LT\d+$")
        self.assertEqual(
            le_tan.tai_khoan.vai_tro,
            TaiKhoan.VaiTro.LE_TAN,
        )
        self.assertTrue(le_tan.tai_khoan.is_active)
        self.assertTrue(le_tan.tai_khoan.check_password("1"))

        self.assertRegex(
            huan_luyen_vien.ma_pt,
            r"^PT\d+$",
        )
        self.assertEqual(
            huan_luyen_vien.tai_khoan.vai_tro,
            TaiKhoan.VaiTro.PT,
        )
        self.assertTrue(
            huan_luyen_vien.tai_khoan.is_active
        )
        self.assertTrue(
            huan_luyen_vien.tai_khoan.check_password("1")
        )

    def test_du_lieu_hoi_vien_loi_duoc_rollback(self):
        with self.assertRaises(ValidationError):
            tao_hoi_vien(
                ho_ten="Hội viên lỗi",
                gioi_tinh="Nam",
                ngay_sinh=date(2000, 4, 4),
                sdt="0901000004",
                email="email-khong-hop-le",
                dia_chi="TP.HCM",
            )

        self.assertEqual(HoiVien.objects.count(), 0)
        self.assertEqual(TaiKhoan.objects.count(), 0)

    def test_ma_ho_so_duoc_sinh_khac_nhau(self):
        hoi_vien_1 = tao_hoi_vien(
            ho_ten="Hội viên thứ nhất",
            gioi_tinh="Nam",
            ngay_sinh=date(2000, 5, 5),
            sdt="0901000005",
            email="hoi.vien.1@example.com",
            dia_chi="TP.HCM",
        )

        hoi_vien_2 = tao_hoi_vien(
            ho_ten="Hội viên thứ hai",
            gioi_tinh="Nữ",
            ngay_sinh=date(2000, 6, 6),
            sdt="0901000006",
            email="hoi.vien.2@example.com",
            dia_chi="TP.HCM",
        )

        self.assertNotEqual(
            hoi_vien_1.ma_hv,
            hoi_vien_2.ma_hv,
        )
        self.assertNotEqual(
            hoi_vien_1.tai_khoan_id,
            hoi_vien_2.tai_khoan_id,
        )
