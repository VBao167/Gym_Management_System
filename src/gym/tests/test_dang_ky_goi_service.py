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


class DangKyGoiVaHoaDonServiceTests(TestCase):
    def setUp(self):
        self.hom_nay = timezone.localdate()

        self.hoi_vien = tao_hoi_vien(
            ho_ten="Hội viên đăng ký gói",
            gioi_tinh="Nam",
            ngay_sinh=date(2000, 1, 1),
            sdt="0911000001",
            email="dang.ky@example.com",
            dia_chi="TP.HCM",
        )

        self.le_tan = tao_le_tan(
            ho_ten="Lễ tân lập hóa đơn",
            gioi_tinh="Nữ",
            ngay_sinh=date(2000, 2, 2),
            sdt="0911000002",
            email="lap.hoa.don@example.com",
            dia_chi="TP.HCM",
        )

        self.goi_tap = GoiTap.objects.create(
            ten_goi="Gói PT kiểm thử",
            thoi_han_ngay=30,
            gia_tien=500000,
            co_pt=True,
            so_buoi_pt=5,
            mo_ta="Kiểm thử đăng ký và hóa đơn",
            trang_thai=True,
        )

    def test_tao_dang_ky_va_hoa_don_thanh_cong(self):
        dang_ky, hoa_don = tao_dang_ky_va_hoa_don(
            hoi_vien=self.hoi_vien,
            goi_tap=self.goi_tap,
            le_tan=self.le_tan,
            ngay_dang_ky=self.hom_nay,
            ngay_bat_dau=self.hom_nay,
            phuong_thuc_thanh_toan=(
                HoaDon.PhuongThucThanhToan.TIEN_MAT
            ),
        )

        self.assertRegex(dang_ky.ma_dk, r"^DK\d+$")
        self.assertRegex(hoa_don.ma_hd, r"^HD\d+$")

        self.assertEqual(
            dang_ky.ngay_ket_thuc,
            self.hom_nay + timedelta(days=29),
        )
        self.assertEqual(dang_ky.so_buoi_pt_dang_ky, 5)
        self.assertEqual(
            dang_ky.trang_thai,
            DangKyGoiTap.TrangThai.HOAT_DONG,
        )

        self.assertEqual(hoa_don.dang_ky, dang_ky)
        self.assertEqual(hoa_don.le_tan, self.le_tan)
        self.assertEqual(
            hoa_don.tong_tien,
            self.goi_tap.gia_tien,
        )

        self.hoi_vien.refresh_from_db()
        self.assertTrue(self.hoi_vien.trang_thai)

    def test_gia_hoa_don_duoc_luu_theo_thoi_diem_dang_ky(self):
        _, hoa_don = tao_dang_ky_va_hoa_don(
            hoi_vien=self.hoi_vien,
            goi_tap=self.goi_tap,
            le_tan=self.le_tan,
            ngay_dang_ky=self.hom_nay,
            ngay_bat_dau=self.hom_nay,
            phuong_thuc_thanh_toan=(
                HoaDon.PhuongThucThanhToan.CHUYEN_KHOAN
            ),
        )

        tong_tien_ban_dau = hoa_don.tong_tien

        self.goi_tap.gia_tien = 750000
        self.goi_tap.save()

        hoa_don.refresh_from_db()

        self.assertEqual(
            hoa_don.tong_tien,
            tong_tien_ban_dau,
        )
        self.assertNotEqual(
            hoa_don.tong_tien,
            self.goi_tap.gia_tien,
        )

    def test_hoa_don_loi_thi_dang_ky_duoc_rollback(self):
        with self.assertRaises(ValidationError):
            tao_dang_ky_va_hoa_don(
                hoi_vien=self.hoi_vien,
                goi_tap=self.goi_tap,
                le_tan=self.le_tan,
                ngay_dang_ky=self.hom_nay,
                ngay_bat_dau=self.hom_nay,
                phuong_thuc_thanh_toan="KhongHopLe",
            )

        self.assertEqual(DangKyGoiTap.objects.count(), 0)
        self.assertEqual(HoaDon.objects.count(), 0)

        self.hoi_vien.refresh_from_db()
        self.assertFalse(self.hoi_vien.trang_thai)
