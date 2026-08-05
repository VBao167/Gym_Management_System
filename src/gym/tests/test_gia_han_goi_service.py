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


class GiaHanGoiServiceTests(TestCase):
    def setUp(self):
        self.hom_nay = timezone.localdate()

        self.hoi_vien = tao_hoi_vien(
            ho_ten="Hội viên gia hạn",
            gioi_tinh="Nam",
            ngay_sinh=date(2000, 1, 1),
            sdt="0921000001",
            email="gia.han@example.com",
            dia_chi="TP.HCM",
        )

        self.le_tan = tao_le_tan(
            ho_ten="Lễ tân gia hạn",
            gioi_tinh="Nữ",
            ngay_sinh=date(2000, 2, 2),
            sdt="0921000002",
            email="le.tan.gia.han@example.com",
            dia_chi="TP.HCM",
        )

        self.goi_tap = GoiTap.objects.create(
            ten_goi="Gói gia hạn kiểm thử",
            thoi_han_ngay=10,
            gia_tien=300000,
            co_pt=False,
            so_buoi_pt=0,
            mo_ta="Kiểm thử gia hạn",
            trang_thai=True,
        )

    def test_chua_co_goi_thi_bat_dau_tu_ngay_dang_ky(self):
        dang_ky, hoa_don = gia_han_goi(
            hoi_vien=self.hoi_vien,
            goi_tap=self.goi_tap,
            le_tan=self.le_tan,
            ngay_dang_ky=self.hom_nay,
            phuong_thuc_thanh_toan=(
                HoaDon.PhuongThucThanhToan.TIEN_MAT
            ),
        )

        self.assertEqual(
            dang_ky.ngay_bat_dau,
            self.hom_nay,
        )
        self.assertEqual(
            dang_ky.ngay_ket_thuc,
            self.hom_nay + timedelta(days=9),
        )
        self.assertEqual(hoa_don.dang_ky, dang_ky)

    def test_goi_moi_noi_tiep_sau_goi_hien_tai(self):
        dang_ky_hien_tai, _ = tao_dang_ky_va_hoa_don(
            hoi_vien=self.hoi_vien,
            goi_tap=self.goi_tap,
            le_tan=self.le_tan,
            ngay_dang_ky=self.hom_nay,
            ngay_bat_dau=self.hom_nay,
            phuong_thuc_thanh_toan=(
                HoaDon.PhuongThucThanhToan.TIEN_MAT
            ),
        )

        dang_ky_gia_han, _ = gia_han_goi(
            hoi_vien=self.hoi_vien,
            goi_tap=self.goi_tap,
            le_tan=self.le_tan,
            ngay_dang_ky=self.hom_nay,
            phuong_thuc_thanh_toan=(
                HoaDon.PhuongThucThanhToan.CHUYEN_KHOAN
            ),
        )

        self.assertEqual(
            dang_ky_gia_han.ngay_bat_dau,
            dang_ky_hien_tai.ngay_ket_thuc
            + timedelta(days=1),
        )
        self.assertEqual(
            dang_ky_hien_tai.trang_thai,
            DangKyGoiTap.TrangThai.HOAT_DONG,
        )
        self.assertEqual(
            dang_ky_gia_han.trang_thai,
            DangKyGoiTap.TrangThai.CHUA_KICH_HOAT,
        )

    def test_goi_cu_da_het_thi_mua_lai_tu_hom_nay(self):
        ngay_bat_dau_cu = self.hom_nay - timedelta(days=20)

        dang_ky_cu, _ = tao_dang_ky_va_hoa_don(
            hoi_vien=self.hoi_vien,
            goi_tap=self.goi_tap,
            le_tan=self.le_tan,
            ngay_dang_ky=ngay_bat_dau_cu,
            ngay_bat_dau=ngay_bat_dau_cu,
            phuong_thuc_thanh_toan=(
                HoaDon.PhuongThucThanhToan.TIEN_MAT
            ),
        )

        dang_ky_moi, _ = gia_han_goi(
            hoi_vien=self.hoi_vien,
            goi_tap=self.goi_tap,
            le_tan=self.le_tan,
            ngay_dang_ky=self.hom_nay,
            phuong_thuc_thanh_toan=(
                HoaDon.PhuongThucThanhToan.TIEN_MAT
            ),
        )

        self.assertLess(
            dang_ky_cu.ngay_ket_thuc,
            self.hom_nay,
        )
        self.assertEqual(
            dang_ky_moi.ngay_bat_dau,
            self.hom_nay,
        )

        self.hoi_vien.refresh_from_db()
        self.assertTrue(self.hoi_vien.trang_thai)
