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


class TrangThaiVaDiemDanhServiceTests(TestCase):
    def setUp(self):
        self.hom_nay = timezone.localdate()

        self.hoi_vien = tao_hoi_vien(
            ho_ten="Hội viên điểm danh",
            gioi_tinh="Nam",
            ngay_sinh=date(2000, 1, 1),
            sdt="0931000001",
            email="diem.danh@example.com",
            dia_chi="TP.HCM",
        )

        self.le_tan = tao_le_tan(
            ho_ten="Lễ tân điểm danh",
            gioi_tinh="Nữ",
            ngay_sinh=date(2000, 2, 2),
            sdt="0931000002",
            email="le.tan.diem.danh@example.com",
            dia_chi="TP.HCM",
        )

        self.goi_tap = GoiTap.objects.create(
            ten_goi="Gói điểm danh kiểm thử",
            thoi_han_ngay=10,
            gia_tien=300000,
            co_pt=False,
            so_buoi_pt=0,
            mo_ta="Kiểm thử trạng thái và điểm danh",
            trang_thai=True,
        )

    def tao_dang_ky(self, ngay_bat_dau):
        dang_ky, _ = tao_dang_ky_va_hoa_don(
            hoi_vien=self.hoi_vien,
            goi_tap=self.goi_tap,
            le_tan=self.le_tan,
            ngay_dang_ky=ngay_bat_dau,
            ngay_bat_dau=ngay_bat_dau,
            phuong_thuc_thanh_toan=(
                HoaDon.PhuongThucThanhToan.TIEN_MAT
            ),
        )

        return dang_ky

    def test_dong_bo_goi_dang_hieu_luc(self):
        dang_ky = self.tao_dang_ky(self.hom_nay)

        DangKyGoiTap.objects.filter(
            pk=dang_ky.pk,
        ).update(
            trang_thai=DangKyGoiTap.TrangThai.HET_HAN,
        )

        HoiVien.objects.filter(
            pk=self.hoi_vien.pk,
        ).update(
            trang_thai=False,
        )

        ket_qua = cap_nhat_trang_thai_hoi_vien(
            self.hoi_vien,
        )

        dang_ky.refresh_from_db()
        self.hoi_vien.refresh_from_db()

        self.assertTrue(ket_qua)
        self.assertEqual(
            dang_ky.trang_thai,
            DangKyGoiTap.TrangThai.HOAT_DONG,
        )
        self.assertTrue(self.hoi_vien.trang_thai)
        self.assertTrue(
            self.hoi_vien.tai_khoan.is_active
        )

    def test_dong_bo_goi_het_han_khong_khoa_tai_khoan(self):
        ngay_bat_dau = self.hom_nay - timedelta(days=20)
        dang_ky = self.tao_dang_ky(ngay_bat_dau)

        DangKyGoiTap.objects.filter(
            pk=dang_ky.pk,
        ).update(
            trang_thai=DangKyGoiTap.TrangThai.HOAT_DONG,
        )

        HoiVien.objects.filter(
            pk=self.hoi_vien.pk,
        ).update(
            trang_thai=True,
        )

        ket_qua = cap_nhat_trang_thai_hoi_vien(
            self.hoi_vien,
        )

        dang_ky.refresh_from_db()
        self.hoi_vien.refresh_from_db()

        self.assertFalse(ket_qua)
        self.assertEqual(
            dang_ky.trang_thai,
            DangKyGoiTap.TrangThai.HET_HAN,
        )
        self.assertFalse(self.hoi_vien.trang_thai)
        self.assertTrue(
            self.hoi_vien.tai_khoan.is_active
        )

    def test_hoi_vien_con_han_duoc_diem_danh(self):
        self.tao_dang_ky(self.hom_nay)

        diem_danh = tao_diem_danh(
            hoi_vien=self.hoi_vien,
            le_tan=self.le_tan,
            ghi_chu="Điểm danh hợp lệ",
        )

        self.assertRegex(diem_danh.ma_dd, r"^DD\d+$")
        self.assertEqual(
            diem_danh.hoi_vien,
            self.hoi_vien,
        )
        self.assertEqual(
            diem_danh.le_tan,
            self.le_tan,
        )
        self.assertEqual(DiemDanh.objects.count(), 1)

    def test_dong_bo_trang_thai_toan_bo_hoi_vien(self):
        dang_ky_dang_hoat_dong = self.tao_dang_ky(
            self.hom_nay
        )

        hoi_vien_het_han = tao_hoi_vien(
            ho_ten="Hội viên đã hết hạn",
            gioi_tinh="Nam",
            ngay_sinh=date(2001, 1, 1),
            sdt="0931000011",
            email="hoi.vien.het.han@example.com",
            dia_chi="TP.HCM",
        )

        dang_ky_het_han, _ = tao_dang_ky_va_hoa_don(
            hoi_vien=hoi_vien_het_han,
            goi_tap=self.goi_tap,
            le_tan=self.le_tan,
            ngay_dang_ky=self.hom_nay - timedelta(days=20),
            ngay_bat_dau=self.hom_nay - timedelta(days=20),
            phuong_thuc_thanh_toan=(
                HoaDon.PhuongThucThanhToan.TIEN_MAT
            ),
        )

        hoi_vien_tuong_lai = tao_hoi_vien(
            ho_ten="Hội viên có gói tương lai",
            gioi_tinh="Nữ",
            ngay_sinh=date(2002, 2, 2),
            sdt="0931000012",
            email="hoi.vien.tuong.lai@example.com",
            dia_chi="TP.HCM",
        )

        dang_ky_tuong_lai, _ = tao_dang_ky_va_hoa_don(
            hoi_vien=hoi_vien_tuong_lai,
            goi_tap=self.goi_tap,
            le_tan=self.le_tan,
            ngay_dang_ky=self.hom_nay,
            ngay_bat_dau=self.hom_nay + timedelta(days=5),
            phuong_thuc_thanh_toan=(
                HoaDon.PhuongThucThanhToan.TIEN_MAT
            ),
        )

        hoi_vien_chua_co_goi = tao_hoi_vien(
            ho_ten="Hội viên chưa có gói",
            gioi_tinh="Nam",
            ngay_sinh=date(2003, 3, 3),
            sdt="0931000013",
            email="hoi.vien.chua.co.goi@example.com",
            dia_chi="TP.HCM",
        )

        DangKyGoiTap.objects.filter(
            pk=dang_ky_dang_hoat_dong.pk,
        ).update(
            trang_thai=DangKyGoiTap.TrangThai.HET_HAN,
        )

        DangKyGoiTap.objects.filter(
            pk=dang_ky_het_han.pk,
        ).update(
            trang_thai=DangKyGoiTap.TrangThai.HOAT_DONG,
        )

        DangKyGoiTap.objects.filter(
            pk=dang_ky_tuong_lai.pk,
        ).update(
            trang_thai=DangKyGoiTap.TrangThai.HOAT_DONG,
        )

        HoiVien.objects.update(trang_thai=True)

        so_hoi_vien = cap_nhat_trang_thai_toan_bo()

        dang_ky_dang_hoat_dong.refresh_from_db()
        dang_ky_het_han.refresh_from_db()
        dang_ky_tuong_lai.refresh_from_db()

        self.hoi_vien.refresh_from_db()
        hoi_vien_het_han.refresh_from_db()
        hoi_vien_tuong_lai.refresh_from_db()
        hoi_vien_chua_co_goi.refresh_from_db()

        self.assertEqual(so_hoi_vien, 4)

        self.assertEqual(
            dang_ky_dang_hoat_dong.trang_thai,
            DangKyGoiTap.TrangThai.HOAT_DONG,
        )
        self.assertTrue(self.hoi_vien.trang_thai)

        self.assertEqual(
            dang_ky_het_han.trang_thai,
            DangKyGoiTap.TrangThai.HET_HAN,
        )
        self.assertFalse(hoi_vien_het_han.trang_thai)

        self.assertEqual(
            dang_ky_tuong_lai.trang_thai,
            DangKyGoiTap.TrangThai.CHUA_KICH_HOAT,
        )
        self.assertFalse(hoi_vien_tuong_lai.trang_thai)

        self.assertFalse(hoi_vien_chua_co_goi.trang_thai)

        self.assertTrue(
            self.hoi_vien.tai_khoan.is_active
        )
        self.assertTrue(
            hoi_vien_het_han.tai_khoan.is_active
        )
        self.assertTrue(
            hoi_vien_tuong_lai.tai_khoan.is_active
        )
        self.assertTrue(
            hoi_vien_chua_co_goi.tai_khoan.is_active
        )

    def test_hoi_vien_het_han_bi_chan_diem_danh(self):
        ngay_bat_dau = self.hom_nay - timedelta(days=20)
        self.tao_dang_ky(ngay_bat_dau)

        with self.assertRaises(ValidationError):
            tao_diem_danh(
                hoi_vien=self.hoi_vien,
                le_tan=self.le_tan,
            )

        self.hoi_vien.refresh_from_db()

        self.assertEqual(DiemDanh.objects.count(), 0)
        self.assertFalse(self.hoi_vien.trang_thai)
        self.assertTrue(
            self.hoi_vien.tai_khoan.is_active
        )

    def test_tai_khoan_le_tan_bi_khoa_thi_khong_diem_danh(self):
        self.tao_dang_ky(self.hom_nay)

        self.le_tan.tai_khoan.is_active = False
        self.le_tan.tai_khoan.save(
            update_fields=["is_active"],
        )

        with self.assertRaises(ValidationError):
            tao_diem_danh(
                hoi_vien=self.hoi_vien,
                le_tan=self.le_tan,
            )

        self.assertEqual(DiemDanh.objects.count(), 0)
