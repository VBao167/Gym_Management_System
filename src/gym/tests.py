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

class BuoiTapPTServiceTests(TestCase):
    def setUp(self):
        self.hom_nay = timezone.localdate()

        self.le_tan = tao_le_tan(
            ho_ten="Lễ tân xếp lịch PT",
            gioi_tinh="Nữ",
            ngay_sinh=date(2000, 1, 1),
            sdt="0941000001",
            email="le.tan.pt@example.com",
            dia_chi="TP.HCM",
        )

        self.pt_1 = tao_huan_luyen_vien(
            ho_ten="PT thứ nhất",
            gioi_tinh="Nam",
            ngay_sinh=date(1998, 2, 2),
            sdt="0941000002",
            email="pt.1@example.com",
            dia_chi="TP.HCM",
        )

        self.pt_2 = tao_huan_luyen_vien(
            ho_ten="PT thứ hai",
            gioi_tinh="Nữ",
            ngay_sinh=date(1999, 3, 3),
            sdt="0941000003",
            email="pt.2@example.com",
            dia_chi="TP.HCM",
        )

        self.hoi_vien_1 = tao_hoi_vien(
            ho_ten="Hội viên dùng PT sớm",
            gioi_tinh="Nam",
            ngay_sinh=date(2000, 4, 4),
            sdt="0941000004",
            email="hoi.vien.pt.1@example.com",
            dia_chi="TP.HCM",
        )

        self.hoi_vien_2 = tao_hoi_vien(
            ho_ten="Hội viên PT thứ hai",
            gioi_tinh="Nữ",
            ngay_sinh=date(2000, 5, 5),
            sdt="0941000005",
            email="hoi.vien.pt.2@example.com",
            dia_chi="TP.HCM",
        )

        self.goi_vao_gym = GoiTap.objects.create(
            ten_goi="Gói vào gym kiểm thử",
            thoi_han_ngay=30,
            gia_tien=300000,
            co_pt=False,
            so_buoi_pt=0,
            mo_ta="Gói bảo đảm quyền vào gym",
            trang_thai=True,
        )

        self.goi_pt = GoiTap.objects.create(
            ten_goi="Gói PT kiểm thử",
            thoi_han_ngay=10,
            gia_tien=500000,
            co_pt=True,
            so_buoi_pt=2,
            mo_ta="Gói có hai buổi PT",
            trang_thai=True,
        )

        dang_ky_vao_gym, _ = tao_dang_ky_va_hoa_don(
            hoi_vien=self.hoi_vien_1,
            goi_tap=self.goi_vao_gym,
            le_tan=self.le_tan,
            ngay_dang_ky=self.hom_nay,
            ngay_bat_dau=self.hom_nay,
            phuong_thuc_thanh_toan=(
                HoaDon.PhuongThucThanhToan.TIEN_MAT
            ),
        )

        self.dang_ky_pt_tuong_lai, _ = (
            tao_dang_ky_va_hoa_don(
                hoi_vien=self.hoi_vien_1,
                goi_tap=self.goi_pt,
                le_tan=self.le_tan,
                ngay_dang_ky=self.hom_nay,
                ngay_bat_dau=(
                    dang_ky_vao_gym.ngay_ket_thuc
                    + timedelta(days=1)
                ),
                phuong_thuc_thanh_toan=(
                    HoaDon.PhuongThucThanhToan.TIEN_MAT
                ),
            )
        )

        self.dang_ky_pt_hien_tai, _ = (
            tao_dang_ky_va_hoa_don(
                hoi_vien=self.hoi_vien_2,
                goi_tap=self.goi_pt,
                le_tan=self.le_tan,
                ngay_dang_ky=self.hom_nay,
                ngay_bat_dau=self.hom_nay,
                phuong_thuc_thanh_toan=(
                    HoaDon.PhuongThucThanhToan.TIEN_MAT
                ),
            )
        )

    def assert_loi_truong(self, truong, ham):
        with self.assertRaises(ValidationError) as context:
            ham()

        self.assertIn(
            truong,
            context.exception.message_dict,
        )

    def test_duoc_dung_som_buoi_pt_khi_co_quyen_vao_gym(self):
        buoi_tap = tao_buoi_tap_pt(
            dang_ky=self.dang_ky_pt_tuong_lai,
            huan_luyen_vien=self.pt_1,
            le_tan=self.le_tan,
            ngay_tap=self.hom_nay,
            gio_bat_dau=time(8, 0),
            gio_ket_thuc=time(9, 0),
        )

        self.assertRegex(buoi_tap.ma_buoi, r"^Buoi\d+$")
        self.assertEqual(
            buoi_tap.trang_thai,
            BuoiTapPT.TrangThai.DA_LEN_LICH,
        )
        self.assertEqual(
            self.dang_ky_pt_tuong_lai.trang_thai,
            DangKyGoiTap.TrangThai.CHUA_KICH_HOAT,
        )

    def test_chan_trung_lich_hoi_vien(self):
        tao_buoi_tap_pt(
            dang_ky=self.dang_ky_pt_tuong_lai,
            huan_luyen_vien=self.pt_1,
            le_tan=self.le_tan,
            ngay_tap=self.hom_nay,
            gio_bat_dau=time(8, 0),
            gio_ket_thuc=time(9, 0),
        )

        self.assert_loi_truong(
            "dang_ky",
            lambda: tao_buoi_tap_pt(
                dang_ky=self.dang_ky_pt_tuong_lai,
                huan_luyen_vien=self.pt_2,
                le_tan=self.le_tan,
                ngay_tap=self.hom_nay,
                gio_bat_dau=time(8, 30),
                gio_ket_thuc=time(9, 30),
            ),
        )

    def test_chan_trung_lich_huan_luyen_vien(self):
        tao_buoi_tap_pt(
            dang_ky=self.dang_ky_pt_tuong_lai,
            huan_luyen_vien=self.pt_1,
            le_tan=self.le_tan,
            ngay_tap=self.hom_nay,
            gio_bat_dau=time(8, 0),
            gio_ket_thuc=time(9, 0),
        )

        self.assert_loi_truong(
            "huan_luyen_vien",
            lambda: tao_buoi_tap_pt(
                dang_ky=self.dang_ky_pt_hien_tai,
                huan_luyen_vien=self.pt_1,
                le_tan=self.le_tan,
                ngay_tap=self.hom_nay,
                gio_bat_dau=time(8, 30),
                gio_ket_thuc=time(9, 30),
            ),
        )

    def test_chan_vuot_so_buoi_pt(self):
        tao_buoi_tap_pt(
            dang_ky=self.dang_ky_pt_tuong_lai,
            huan_luyen_vien=self.pt_1,
            le_tan=self.le_tan,
            ngay_tap=self.hom_nay,
            gio_bat_dau=time(8, 0),
            gio_ket_thuc=time(9, 0),
        )

        tao_buoi_tap_pt(
            dang_ky=self.dang_ky_pt_tuong_lai,
            huan_luyen_vien=self.pt_1,
            le_tan=self.le_tan,
            ngay_tap=self.hom_nay,
            gio_bat_dau=time(9, 0),
            gio_ket_thuc=time(10, 0),
        )

        self.assert_loi_truong(
            "dang_ky",
            lambda: tao_buoi_tap_pt(
                dang_ky=self.dang_ky_pt_tuong_lai,
                huan_luyen_vien=self.pt_1,
                le_tan=self.le_tan,
                ngay_tap=self.hom_nay,
                gio_bat_dau=time(10, 0),
                gio_ket_thuc=time(11, 0),
            ),
        )

        self.assertEqual(BuoiTapPT.objects.count(), 2)

    def test_chan_pt_nghi_viec_hoac_bi_khoa(self):
        self.pt_2.trang_thai = False
        self.pt_2.save(update_fields=["trang_thai"])

        self.assert_loi_truong(
            "huan_luyen_vien",
            lambda: tao_buoi_tap_pt(
                dang_ky=self.dang_ky_pt_hien_tai,
                huan_luyen_vien=self.pt_2,
                le_tan=self.le_tan,
                ngay_tap=self.hom_nay,
                gio_bat_dau=time(10, 0),
                gio_ket_thuc=time(11, 0),
            ),
        )

        self.pt_2.trang_thai = True
        self.pt_2.save(update_fields=["trang_thai"])
        self.pt_2.tai_khoan.is_active = False
        self.pt_2.tai_khoan.save(
            update_fields=["is_active"],
        )

        self.assert_loi_truong(
            "huan_luyen_vien",
            lambda: tao_buoi_tap_pt(
                dang_ky=self.dang_ky_pt_hien_tai,
                huan_luyen_vien=self.pt_2,
                le_tan=self.le_tan,
                ngay_tap=self.hom_nay,
                gio_bat_dau=time(10, 0),
                gio_ket_thuc=time(11, 0),
            ),
        )

    def test_chan_le_tan_nghi_viec_hoac_bi_khoa(self):
        self.le_tan.trang_thai = False
        self.le_tan.save(update_fields=["trang_thai"])

        self.assert_loi_truong(
            "le_tan",
            lambda: tao_buoi_tap_pt(
                dang_ky=self.dang_ky_pt_hien_tai,
                huan_luyen_vien=self.pt_1,
                le_tan=self.le_tan,
                ngay_tap=self.hom_nay,
                gio_bat_dau=time(10, 0),
                gio_ket_thuc=time(11, 0),
            ),
        )

        self.le_tan.trang_thai = True
        self.le_tan.save(update_fields=["trang_thai"])
        self.le_tan.tai_khoan.is_active = False
        self.le_tan.tai_khoan.save(
            update_fields=["is_active"],
        )

        self.assert_loi_truong(
            "le_tan",
            lambda: tao_buoi_tap_pt(
                dang_ky=self.dang_ky_pt_hien_tai,
                huan_luyen_vien=self.pt_1,
                le_tan=self.le_tan,
                ngay_tap=self.hom_nay,
                gio_bat_dau=time(10, 0),
                gio_ket_thuc=time(11, 0),
            ),
        )

    def test_buoi_moi_bat_buoc_la_da_len_lich(self):
        buoi_tap = BuoiTapPT(
            dang_ky=self.dang_ky_pt_hien_tai,
            huan_luyen_vien=self.pt_1,
            le_tan=self.le_tan,
            ngay_tap=self.hom_nay,
            gio_bat_dau=time(11, 0),
            gio_ket_thuc=time(12, 0),
            trang_thai=BuoiTapPT.TrangThai.HOAN_THANH,
        )

        self.assert_loi_truong(
            "trang_thai",
            lambda: tao_buoi_tap_pt_tu_doi_tuong(
                buoi_tap
            ),
        )

        self.assertEqual(BuoiTapPT.objects.count(), 0)

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
                "Khu vực Huấn luyện viên.",
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
                "users/quan_tri.html",
            TaiKhoan.VaiTro.LE_TAN:
                "users/le_tan.html",
            TaiKhoan.VaiTro.PT:
                "users/pt.html",
            TaiKhoan.VaiTro.HOI_VIEN:
                "users/hoi_vien.html",
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
            "users/quan_tri.html",
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

class DanhSachHoiVienTests(TestCase):
    def setUp(self):
        self.admin = TaiKhoan.objects.create_user(
            username="admin_danh_sach_hoi_vien",
            password="1",
            vai_tro=TaiKhoan.VaiTro.ADMIN,
        )

        self.tai_khoan_le_tan = TaiKhoan.objects.create_user(
            username="le_tan_khong_co_quyen",
            password="1",
            vai_tro=TaiKhoan.VaiTro.LE_TAN,
        )

        self.hoi_vien_1 = tao_hoi_vien(
            ho_ten="Nguyễn Văn An",
            gioi_tinh="Nam",
            ngay_sinh=date(2001, 1, 1),
            sdt="0951000001",
            email="nguyen.van.an@example.com",
            dia_chi="TP.HCM",
        )

        self.hoi_vien_2 = tao_hoi_vien(
            ho_ten="Trần Thị Bình",
            gioi_tinh="Nữ",
            ngay_sinh=date(2002, 2, 2),
            sdt="0951000002",
            email="tran.thi.binh@example.com",
            dia_chi="TP.HCM",
        )

    def test_admin_xem_duoc_danh_sach_hoi_vien(self):
        self.client.force_login(self.admin)

        response = self.client.get(
            reverse("gym:danh_sach_hoi_vien")
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            "users/quan_tri/danh_sach_hoi_vien.html",
        )

        cac_hoi_vien = list(
            response.context["cac_hoi_vien"]
        )

        self.assertEqual(len(cac_hoi_vien), 2)
        self.assertEqual(
            [hoi_vien.ma_hv for hoi_vien in cac_hoi_vien],
            sorted(
                [
                    self.hoi_vien_1.ma_hv,
                    self.hoi_vien_2.ma_hv,
                ]
            ),
        )

        self.assertContains(response, "Nguyễn Văn An")
        self.assertContains(response, "Trần Thị Bình")

    def test_danh_sach_rong_hien_thi_thong_bao(self):
        HoiVien.objects.all().delete()

        self.client.force_login(self.admin)

        response = self.client.get(
            reverse("gym:danh_sach_hoi_vien")
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "Chưa có hội viên trong hệ thống.",
        )

    def test_tai_khoan_khong_phai_admin_bi_tu_choi(self):
        self.client.force_login(self.tai_khoan_le_tan)

        response = self.client.get(
            reverse("gym:danh_sach_hoi_vien")
        )

        self.assertEqual(response.status_code, 403)

    def test_danh_sach_dong_bo_trang_thai_truoc_khi_hien_thi(self):
        self.client.force_login(self.admin)

        with patch(
            "gym.views.cap_nhat_trang_thai_toan_bo"
        ) as ham_dong_bo:
            response = self.client.get(
                reverse("gym:danh_sach_hoi_vien")
            )

        self.assertEqual(response.status_code, 200)
        ham_dong_bo.assert_called_once_with()

class TaoHoiVienTuGiaoDienTests(TestCase):
    def setUp(self):
        self.admin = TaiKhoan.objects.create_user(
            username="admin_tao_hoi_vien",
            password="1",
            vai_tro=TaiKhoan.VaiTro.ADMIN,
        )

        self.le_tan = TaiKhoan.objects.create_user(
            username="le_tan_khong_duoc_tao_hoi_vien",
            password="1",
            vai_tro=TaiKhoan.VaiTro.LE_TAN,
        )

        self.url = reverse("gym:tao_hoi_vien_moi")

        self.du_lieu_hop_le = {
            "ho_ten": "Nguyễn Minh Khang",
            "gioi_tinh": "Nam",
            "ngay_sinh": "2002-01-01",
            "sdt": "0961000001",
            "email": "minh.khang@example.com",
            "dia_chi": "TP.HCM",
        }

    def test_admin_xem_duoc_form_tao_hoi_vien(self):
        self.client.force_login(self.admin)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            "users/quan_tri/tao_hoi_vien.html",
        )
        self.assertContains(
            response,
            "Thông tin hội viên mới",
        )

    def test_admin_tao_hoi_vien_kem_tai_khoan_thanh_cong(self):
        self.client.force_login(self.admin)

        response = self.client.post(
            self.url,
            self.du_lieu_hop_le,
        )

        self.assertRedirects(
            response,
            reverse("gym:danh_sach_hoi_vien"),
        )

        self.assertEqual(HoiVien.objects.count(), 1)

        hoi_vien = HoiVien.objects.select_related(
            "tai_khoan"
        ).get()

        self.assertEqual(
            hoi_vien.ho_ten,
            "Nguyễn Minh Khang",
        )
        self.assertFalse(hoi_vien.trang_thai)

        self.assertEqual(
            hoi_vien.tai_khoan.username,
            hoi_vien.ma_hv,
        )
        self.assertEqual(
            hoi_vien.tai_khoan.vai_tro,
            TaiKhoan.VaiTro.HOI_VIEN,
        )
        self.assertTrue(hoi_vien.tai_khoan.is_active)
        self.assertTrue(
            hoi_vien.tai_khoan.check_password("1")
        )

    def test_du_lieu_khong_hop_le_khong_tao_hoi_vien(self):
        self.client.force_login(self.admin)

        du_lieu_loi = self.du_lieu_hop_le.copy()
        du_lieu_loi["email"] = "email-khong-hop-le"

        response = self.client.post(
            self.url,
            du_lieu_loi,
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(
            response.context["form"].is_valid()
        )
        self.assertIn(
            "email",
            response.context["form"].errors,
        )
        self.assertEqual(HoiVien.objects.count(), 0)

    def test_tai_khoan_khong_phai_admin_bi_tu_choi(self):
        self.client.force_login(self.le_tan)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 403)

class ChiTietHoiVienTests(TestCase):
    def setUp(self):
        self.admin = TaiKhoan.objects.create_user(
            username="admin_chi_tiet_hoi_vien",
            password="1",
            vai_tro=TaiKhoan.VaiTro.ADMIN,
        )

        self.le_tan = TaiKhoan.objects.create_user(
            username="le_tan_khong_duoc_xem_chi_tiet",
            password="1",
            vai_tro=TaiKhoan.VaiTro.LE_TAN,
        )

        self.hoi_vien = tao_hoi_vien(
            ho_ten="Nguyễn Minh Khang",
            gioi_tinh="Nam",
            ngay_sinh=date(2002, 1, 1),
            sdt="0961000001",
            email="minh.khang.chi.tiet@example.com",
            dia_chi="TP.HCM",
        )

        self.url = reverse(
            "gym:chi_tiet_hoi_vien",
            args=[self.hoi_vien.ma_hv],
        )

    def test_admin_xem_duoc_chi_tiet_hoi_vien(self):
        self.client.force_login(self.admin)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            "users/quan_tri/chi_tiet_hoi_vien.html",
        )
        self.assertEqual(
            response.context["hoi_vien"],
            self.hoi_vien,
        )

        self.assertContains(response, "Nguyễn Minh Khang")
        self.assertContains(response, self.hoi_vien.ma_hv)
        self.assertContains(
            response,
            self.hoi_vien.tai_khoan.username,
        )

    def test_chi_tiet_dong_bo_trang_thai_truoc_khi_hien_thi(self):
        self.client.force_login(self.admin)

        with patch(
            "gym.views.cap_nhat_trang_thai_toan_bo"
        ) as ham_dong_bo:
            response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        ham_dong_bo.assert_called_once_with()

    def test_ma_hoi_vien_khong_ton_tai_tra_ve_404(self):
        self.client.force_login(self.admin)

        response = self.client.get(
            reverse(
                "gym:chi_tiet_hoi_vien",
                args=["HV999999"],
            )
        )

        self.assertEqual(response.status_code, 404)

    def test_tai_khoan_khong_phai_admin_bi_tu_choi(self):
        self.client.force_login(self.le_tan)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 403)

class ChinhSuaHoiVienTests(TestCase):
    def setUp(self):
        self.admin = TaiKhoan.objects.create_user(
            username="admin_chinh_sua_hoi_vien",
            password="1",
            vai_tro=TaiKhoan.VaiTro.ADMIN,
        )

        self.le_tan = TaiKhoan.objects.create_user(
            username="le_tan_khong_duoc_chinh_sua",
            password="1",
            vai_tro=TaiKhoan.VaiTro.LE_TAN,
        )

        self.hoi_vien = tao_hoi_vien(
            ho_ten="Nguyễn Minh Khang",
            gioi_tinh="Nam",
            ngay_sinh=date(2002, 1, 1),
            sdt="0962000001",
            email="minh.khang.chinh.sua@example.com",
            dia_chi="TP.HCM",
        )

        self.url = reverse(
            "gym:chinh_sua_hoi_vien",
            args=[self.hoi_vien.ma_hv],
        )

        self.du_lieu_cap_nhat = {
            "ho_ten": "Nguyễn Minh Khang",
            "gioi_tinh": "Nam",
            "ngay_sinh": "2002-01-01",
            "sdt": "0962000010",
            "email": "minh.khang.chinh.sua@example.com",
            "dia_chi": "Bình Chánh, TP.HCM",
        }

    def test_admin_xem_duoc_form_chinh_sua(self):
        self.client.force_login(self.admin)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            "users/quan_tri/tao_hoi_vien.html",
        )
        self.assertEqual(
            response.context["form"].instance,
            self.hoi_vien,
        )
        self.assertContains(
            response,
            "Cập nhật thông tin hội viên",
        )

    def test_admin_chinh_sua_hoi_vien_thanh_cong(self):
        self.client.force_login(self.admin)

        ma_hv_ban_dau = self.hoi_vien.ma_hv
        ma_tk_ban_dau = self.hoi_vien.tai_khoan_id
        username_ban_dau = self.hoi_vien.tai_khoan.username
        trang_thai_ban_dau = self.hoi_vien.trang_thai

        response = self.client.post(
            self.url,
            self.du_lieu_cap_nhat,
        )

        self.assertRedirects(
            response,
            reverse(
                "gym:chi_tiet_hoi_vien",
                args=[ma_hv_ban_dau],
            ),
        )

        self.hoi_vien.refresh_from_db()
        self.hoi_vien.tai_khoan.refresh_from_db()

        self.assertEqual(
            self.hoi_vien.sdt,
            "0962000010",
        )
        self.assertEqual(
            self.hoi_vien.dia_chi,
            "Bình Chánh, TP.HCM",
        )

        self.assertEqual(
            self.hoi_vien.ma_hv,
            ma_hv_ban_dau,
        )
        self.assertEqual(
            self.hoi_vien.tai_khoan_id,
            ma_tk_ban_dau,
        )
        self.assertEqual(
            self.hoi_vien.tai_khoan.username,
            username_ban_dau,
        )
        self.assertEqual(
            self.hoi_vien.trang_thai,
            trang_thai_ban_dau,
        )

    def test_du_lieu_khong_hop_le_khong_duoc_cap_nhat(self):
        self.client.force_login(self.admin)

        du_lieu_loi = self.du_lieu_cap_nhat.copy()
        du_lieu_loi["email"] = "email-khong-hop-le"

        response = self.client.post(
            self.url,
            du_lieu_loi,
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(
            "email",
            response.context["form"].errors,
        )

        self.hoi_vien.refresh_from_db()

        self.assertEqual(
            self.hoi_vien.sdt,
            "0962000001",
        )
        self.assertEqual(
            self.hoi_vien.dia_chi,
            "TP.HCM",
        )

    def test_ma_hoi_vien_khong_ton_tai_tra_ve_404(self):
        self.client.force_login(self.admin)

        response = self.client.get(
            reverse(
                "gym:chinh_sua_hoi_vien",
                args=["HV999999"],
            )
        )

        self.assertEqual(response.status_code, 404)

    def test_tai_khoan_khong_phai_admin_bi_tu_choi(self):
        self.client.force_login(self.le_tan)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 403)

class TrangThaiTaiKhoanHoiVienTests(TestCase):
    def setUp(self):
        self.admin = TaiKhoan.objects.create_user(
            username="admin_trang_thai_tai_khoan",
            password="1",
            vai_tro=TaiKhoan.VaiTro.ADMIN,
        )

        self.le_tan = TaiKhoan.objects.create_user(
            username="le_tan_khong_duoc_khoa_tai_khoan",
            password="1",
            vai_tro=TaiKhoan.VaiTro.LE_TAN,
        )

        self.hoi_vien = tao_hoi_vien(
            ho_ten="Hội viên kiểm thử tài khoản",
            gioi_tinh="Nam",
            ngay_sinh=date(2002, 1, 1),
            sdt="0971000001",
            email="tai.khoan.hoi.vien@example.com",
            dia_chi="TP.HCM",
        )

        self.url = reverse(
            "gym:doi_trang_thai_tai_khoan_hoi_vien",
            args=[self.hoi_vien.ma_hv],
        )

    def test_admin_khoa_tai_khoan_hoi_vien(self):
        self.client.force_login(self.admin)

        trang_thai_hoi_vien_ban_dau = (
            self.hoi_vien.trang_thai
        )

        response = self.client.post(
            self.url,
            {
                "hanh_dong": "khoa",
            },
        )

        self.assertRedirects(
            response,
            reverse(
                "gym:chi_tiet_hoi_vien",
                args=[self.hoi_vien.ma_hv],
            ),
        )

        self.hoi_vien.refresh_from_db()
        self.hoi_vien.tai_khoan.refresh_from_db()

        self.assertFalse(
            self.hoi_vien.tai_khoan.is_active
        )
        self.assertEqual(
            self.hoi_vien.trang_thai,
            trang_thai_hoi_vien_ban_dau,
        )

    def test_admin_mo_khoa_tai_khoan_hoi_vien(self):
        self.hoi_vien.tai_khoan.is_active = False
        self.hoi_vien.tai_khoan.save(
            update_fields=["is_active"],
        )

        self.client.force_login(self.admin)

        response = self.client.post(
            self.url,
            {
                "hanh_dong": "mo_khoa",
            },
        )

        self.assertRedirects(
            response,
            reverse(
                "gym:chi_tiet_hoi_vien",
                args=[self.hoi_vien.ma_hv],
            ),
        )

        self.hoi_vien.tai_khoan.refresh_from_db()

        self.assertTrue(
            self.hoi_vien.tai_khoan.is_active
        )

    def test_hanh_dong_khong_hop_le_bi_tu_choi(self):
        self.client.force_login(self.admin)

        response = self.client.post(
            self.url,
            {
                "hanh_dong": "xoa",
            },
        )

        self.assertEqual(response.status_code, 400)

        self.hoi_vien.tai_khoan.refresh_from_db()

        self.assertTrue(
            self.hoi_vien.tai_khoan.is_active
        )

    def test_get_khong_duoc_dung_de_thay_doi_trang_thai(self):
        self.client.force_login(self.admin)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 405)

        self.hoi_vien.tai_khoan.refresh_from_db()

        self.assertTrue(
            self.hoi_vien.tai_khoan.is_active
        )

    def test_tai_khoan_khong_phai_admin_bi_tu_choi(self):
        self.client.force_login(self.le_tan)

        response = self.client.post(
            self.url,
            {
                "hanh_dong": "khoa",
            },
        )

        self.assertEqual(response.status_code, 403)

        self.hoi_vien.tai_khoan.refresh_from_db()

        self.assertTrue(
            self.hoi_vien.tai_khoan.is_active
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
            "users/quan_tri/danh_sach_goi_tap.html",
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

class QuanLyNhanVienTests(TestCase):
    def setUp(self):
        self.admin = TaiKhoan.objects.create_user(
            username="admin_quan_ly_nhan_vien",
            password="1",
            vai_tro=TaiKhoan.VaiTro.ADMIN,
        )

        self.nguoi_dung_khong_phai_admin = (
            TaiKhoan.objects.create_user(
                username="nguoi_dung_khong_phai_admin",
                password="1",
                vai_tro=TaiKhoan.VaiTro.LE_TAN,
            )
        )

        self.le_tan = tao_le_tan(
            ho_ten="Lễ tân kiểm thử",
            gioi_tinh="Nam",
            ngay_sinh=date(2000, 1, 1),
            sdt="0911000001",
            email="le.tan.quan.ly@example.com",
            dia_chi="TP.HCM",
        )

        self.huan_luyen_vien = tao_huan_luyen_vien(
            ho_ten="Huấn luyện viên kiểm thử",
            gioi_tinh="Nữ",
            ngay_sinh=date(2000, 2, 2),
            sdt="0911000002",
            email="pt.quan.ly@example.com",
            dia_chi="TP.HCM",
        )

        self.url_danh_sach = reverse(
            "gym:danh_sach_nhan_vien"
        )

        self.url_tao_le_tan = reverse(
            "gym:tao_nhan_vien_moi",
            args=["le-tan"],
        )

        self.url_tao_pt = reverse(
            "gym:tao_nhan_vien_moi",
            args=["pt"],
        )

    def du_lieu_nhan_vien(
        self,
        *,
        ho_ten,
        sdt,
        email,
        gioi_tinh="Nam",
    ):
        return {
            "ho_ten": ho_ten,
            "gioi_tinh": gioi_tinh,
            "ngay_sinh": "2001-01-01",
            "sdt": sdt,
            "email": email,
            "dia_chi": "Bình Chánh, TP.HCM",
            "ngay_vao_lam": "2026-08-04",
        }

    def url_chi_tiet(
        self,
        loai_nhan_vien,
        ma_nhan_vien,
    ):
        return reverse(
            "gym:chi_tiet_nhan_vien",
            args=[
                loai_nhan_vien,
                ma_nhan_vien,
            ],
        )

    def url_chinh_sua(
        self,
        loai_nhan_vien,
        ma_nhan_vien,
    ):
        return reverse(
            "gym:chinh_sua_nhan_vien",
            args=[
                loai_nhan_vien,
                ma_nhan_vien,
            ],
        )

    def url_trang_thai_lam_viec(
        self,
        loai_nhan_vien,
        ma_nhan_vien,
    ):
        return reverse(
            "gym:doi_trang_thai_lam_viec_nhan_vien",
            args=[
                loai_nhan_vien,
                ma_nhan_vien,
            ],
        )

    def url_trang_thai_tai_khoan(
        self,
        loai_nhan_vien,
        ma_nhan_vien,
    ):
        return reverse(
            "gym:doi_trang_thai_tai_khoan_nhan_vien",
            args=[
                loai_nhan_vien,
                ma_nhan_vien,
            ],
        )

    def test_admin_xem_duoc_danh_sach_nhan_vien(self):
        self.client.force_login(self.admin)

        response = self.client.get(
            self.url_danh_sach
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            "users/quan_tri/danh_sach_nhan_vien.html",
        )
        self.assertContains(
            response,
            self.le_tan.ho_ten,
        )
        self.assertContains(
            response,
            self.huan_luyen_vien.ho_ten,
        )

    def test_tai_khoan_khong_phai_admin_bi_tu_choi_danh_sach(
        self
    ):
        self.client.force_login(
            self.nguoi_dung_khong_phai_admin
        )

        response = self.client.get(
            self.url_danh_sach
        )

        self.assertEqual(response.status_code, 403)

    def test_admin_xem_duoc_form_tao_ca_hai_loai(self):
        self.client.force_login(self.admin)

        cac_truong_hop = (
            (
                self.url_tao_le_tan,
                "Thêm Lễ tân",
            ),
            (
                self.url_tao_pt,
                "Thêm Huấn luyện viên",
            ),
        )

        for url, noi_dung in cac_truong_hop:
            with self.subTest(url=url):
                response = self.client.get(url)

                self.assertEqual(
                    response.status_code,
                    200,
                )
                self.assertTemplateUsed(
                    response,
                    (
                        "users/quan_tri/"
                        "bieu_mau_nhan_vien.html"
                    ),
                )
                self.assertContains(
                    response,
                    noi_dung,
                )

    def test_admin_tao_le_tan_kem_tai_khoan_thanh_cong(
        self
    ):
        self.client.force_login(self.admin)

        response = self.client.post(
            self.url_tao_le_tan,
            self.du_lieu_nhan_vien(
                ho_ten="Lễ tân giao diện",
                sdt="0911000011",
                email="le.tan.giao.dien@example.com",
            ),
        )

        le_tan = LeTan.objects.select_related(
            "tai_khoan"
        ).get(
            email="le.tan.giao.dien@example.com"
        )

        self.assertRedirects(
            response,
            self.url_chi_tiet(
                "le-tan",
                le_tan.ma_lt,
            ),
        )

        self.assertRegex(
            le_tan.ma_lt,
            r"^LT\d+$",
        )
        self.assertEqual(
            le_tan.tai_khoan.username,
            le_tan.ma_lt,
        )
        self.assertEqual(
            le_tan.tai_khoan.vai_tro,
            TaiKhoan.VaiTro.LE_TAN,
        )
        self.assertTrue(le_tan.trang_thai)
        self.assertTrue(
            le_tan.tai_khoan.is_active
        )
        self.assertTrue(
            le_tan.tai_khoan.check_password("1")
        )

    def test_admin_tao_pt_kem_tai_khoan_thanh_cong(
        self
    ):
        self.client.force_login(self.admin)

        response = self.client.post(
            self.url_tao_pt,
            self.du_lieu_nhan_vien(
                ho_ten="PT giao diện",
                gioi_tinh="Nữ",
                sdt="0911000012",
                email="pt.giao.dien@example.com",
            ),
        )

        huan_luyen_vien = (
            HuanLuyenVien.objects.select_related(
                "tai_khoan"
            ).get(
                email="pt.giao.dien@example.com"
            )
        )

        self.assertRedirects(
            response,
            self.url_chi_tiet(
                "pt",
                huan_luyen_vien.ma_pt,
            ),
        )

        self.assertRegex(
            huan_luyen_vien.ma_pt,
            r"^PT\d+$",
        )
        self.assertEqual(
            huan_luyen_vien.tai_khoan.username,
            huan_luyen_vien.ma_pt,
        )
        self.assertEqual(
            huan_luyen_vien.tai_khoan.vai_tro,
            TaiKhoan.VaiTro.PT,
        )
        self.assertTrue(
            huan_luyen_vien.trang_thai
        )
        self.assertTrue(
            huan_luyen_vien.tai_khoan.is_active
        )
        self.assertTrue(
            huan_luyen_vien.tai_khoan
            .check_password("1")
        )

    def test_du_lieu_khong_hop_le_khong_tao_nhan_vien(
        self
    ):
        self.client.force_login(self.admin)

        so_luong_ban_dau = LeTan.objects.count()

        du_lieu = self.du_lieu_nhan_vien(
            ho_ten="Lễ tân dữ liệu lỗi",
            sdt="0911000013",
            email="email-khong-hop-le",
        )

        response = self.client.post(
            self.url_tao_le_tan,
            du_lieu,
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(
            "email",
            response.context["form"].errors,
        )
        self.assertEqual(
            LeTan.objects.count(),
            so_luong_ban_dau,
        )

    def test_loai_nhan_vien_khong_hop_le_tra_ve_404(
        self
    ):
        self.client.force_login(self.admin)

        response = self.client.get(
            reverse(
                "gym:tao_nhan_vien_moi",
                args=["nhan-vien-khac"],
            )
        )

        self.assertEqual(response.status_code, 404)

    def test_admin_xem_duoc_chi_tiet_ca_hai_loai(self):
        self.client.force_login(self.admin)

        cac_truong_hop = (
            (
                "le-tan",
                self.le_tan.ma_lt,
                self.le_tan.ho_ten,
            ),
            (
                "pt",
                self.huan_luyen_vien.ma_pt,
                self.huan_luyen_vien.ho_ten,
            ),
        )

        for loai, ma_nhan_vien, ho_ten in cac_truong_hop:
            with self.subTest(
                loai=loai,
                ma_nhan_vien=ma_nhan_vien,
            ):
                response = self.client.get(
                    self.url_chi_tiet(
                        loai,
                        ma_nhan_vien,
                    )
                )

                self.assertEqual(
                    response.status_code,
                    200,
                )
                self.assertTemplateUsed(
                    response,
                    (
                        "users/quan_tri/"
                        "chi_tiet_nhan_vien.html"
                    ),
                )
                self.assertContains(
                    response,
                    ho_ten,
                )

    def test_admin_chinh_sua_ca_hai_loai_thanh_cong(
        self
    ):
        self.client.force_login(self.admin)

        cac_truong_hop = (
            (
                "le-tan",
                self.le_tan,
                self.le_tan.ma_lt,
                "Lễ tân đã cập nhật",
                "0911000021",
                "le.tan.cap.nhat@example.com",
            ),
            (
                "pt",
                self.huan_luyen_vien,
                self.huan_luyen_vien.ma_pt,
                "PT đã cập nhật",
                "0911000022",
                "pt.cap.nhat@example.com",
            ),
        )

        for (
            loai,
            nhan_vien,
            ma_nhan_vien,
            ho_ten_moi,
            sdt_moi,
            email_moi,
        ) in cac_truong_hop:
            with self.subTest(loai=loai):
                tai_khoan_id_ban_dau = (
                    nhan_vien.tai_khoan_id
                )
                username_ban_dau = (
                    nhan_vien.tai_khoan.username
                )
                trang_thai_ban_dau = (
                    nhan_vien.trang_thai
                )

                response = self.client.post(
                    self.url_chinh_sua(
                        loai,
                        ma_nhan_vien,
                    ),
                    self.du_lieu_nhan_vien(
                        ho_ten=ho_ten_moi,
                        sdt=sdt_moi,
                        email=email_moi,
                    ),
                )

                self.assertRedirects(
                    response,
                    self.url_chi_tiet(
                        loai,
                        ma_nhan_vien,
                    ),
                )

                nhan_vien.refresh_from_db()
                nhan_vien.tai_khoan.refresh_from_db()

                self.assertEqual(
                    nhan_vien.ho_ten,
                    ho_ten_moi,
                )
                self.assertEqual(
                    nhan_vien.sdt,
                    sdt_moi,
                )
                self.assertEqual(
                    nhan_vien.pk,
                    ma_nhan_vien,
                )
                self.assertEqual(
                    nhan_vien.tai_khoan_id,
                    tai_khoan_id_ban_dau,
                )
                self.assertEqual(
                    nhan_vien.tai_khoan.username,
                    username_ban_dau,
                )
                self.assertEqual(
                    nhan_vien.trang_thai,
                    trang_thai_ban_dau,
                )

    def test_ma_nhan_vien_khong_ton_tai_tra_ve_404(
        self
    ):
        self.client.force_login(self.admin)

        response = self.client.get(
            self.url_chi_tiet(
                "le-tan",
                "LT999999",
            )
        )

        self.assertEqual(response.status_code, 404)

    def test_ngung_lam_viec_tu_dong_khoa_tai_khoan(
        self
    ):
        self.client.force_login(self.admin)

        cac_truong_hop = (
            (
                "le-tan",
                self.le_tan,
                self.le_tan.ma_lt,
            ),
            (
                "pt",
                self.huan_luyen_vien,
                self.huan_luyen_vien.ma_pt,
            ),
        )

        for loai, nhan_vien, ma_nhan_vien in cac_truong_hop:
            with self.subTest(loai=loai):
                response = self.client.post(
                    self.url_trang_thai_lam_viec(
                        loai,
                        ma_nhan_vien,
                    ),
                    {
                        "hanh_dong": "ngung_lam_viec",
                    },
                )

                self.assertRedirects(
                    response,
                    self.url_chi_tiet(
                        loai,
                        ma_nhan_vien,
                    ),
                )

                nhan_vien.refresh_from_db()
                nhan_vien.tai_khoan.refresh_from_db()

                self.assertFalse(
                    nhan_vien.trang_thai
                )
                self.assertFalse(
                    nhan_vien.tai_khoan.is_active
                )

    def test_cho_lam_viec_lai_khong_tu_mo_tai_khoan(
        self
    ):
        self.le_tan.trang_thai = False
        self.le_tan.save(
            update_fields=["trang_thai"],
        )

        self.le_tan.tai_khoan.is_active = False
        self.le_tan.tai_khoan.save(
            update_fields=["is_active"],
        )

        self.client.force_login(self.admin)

        response = self.client.post(
            self.url_trang_thai_lam_viec(
                "le-tan",
                self.le_tan.ma_lt,
            ),
            {
                "hanh_dong": "cho_lam_viec_lai",
            },
        )

        self.assertRedirects(
            response,
            self.url_chi_tiet(
                "le-tan",
                self.le_tan.ma_lt,
            ),
        )

        self.le_tan.refresh_from_db()
        self.le_tan.tai_khoan.refresh_from_db()

        self.assertTrue(self.le_tan.trang_thai)
        self.assertFalse(
            self.le_tan.tai_khoan.is_active
        )

    def test_khong_mo_khoa_khi_nhan_vien_ngung_lam_viec(
        self
    ):
        self.le_tan.trang_thai = False
        self.le_tan.save(
            update_fields=["trang_thai"],
        )

        self.le_tan.tai_khoan.is_active = False
        self.le_tan.tai_khoan.save(
            update_fields=["is_active"],
        )

        self.client.force_login(self.admin)

        response = self.client.post(
            self.url_trang_thai_tai_khoan(
                "le-tan",
                self.le_tan.ma_lt,
            ),
            {
                "hanh_dong": "mo_khoa",
            },
        )

        self.assertEqual(response.status_code, 400)

        self.le_tan.tai_khoan.refresh_from_db()

        self.assertFalse(
            self.le_tan.tai_khoan.is_active
        )

    def test_khoa_va_mo_khoa_khi_nhan_vien_dang_lam_viec(
        self
    ):
        self.client.force_login(self.admin)

        url = self.url_trang_thai_tai_khoan(
            "pt",
            self.huan_luyen_vien.ma_pt,
        )

        response_khoa = self.client.post(
            url,
            {
                "hanh_dong": "khoa",
            },
        )

        self.assertRedirects(
            response_khoa,
            self.url_chi_tiet(
                "pt",
                self.huan_luyen_vien.ma_pt,
            ),
        )

        self.huan_luyen_vien.refresh_from_db()
        self.huan_luyen_vien.tai_khoan.refresh_from_db()

        self.assertTrue(
            self.huan_luyen_vien.trang_thai
        )
        self.assertFalse(
            self.huan_luyen_vien
            .tai_khoan.is_active
        )

        response_mo_khoa = self.client.post(
            url,
            {
                "hanh_dong": "mo_khoa",
            },
        )

        self.assertRedirects(
            response_mo_khoa,
            self.url_chi_tiet(
                "pt",
                self.huan_luyen_vien.ma_pt,
            ),
        )

        self.huan_luyen_vien.tai_khoan.refresh_from_db()

        self.assertTrue(
            self.huan_luyen_vien
            .tai_khoan.is_active
        )

    def test_get_khong_duoc_dung_de_thay_doi_trang_thai(
        self
    ):
        self.client.force_login(self.admin)

        cac_url = (
            self.url_trang_thai_lam_viec(
                "le-tan",
                self.le_tan.ma_lt,
            ),
            self.url_trang_thai_tai_khoan(
                "le-tan",
                self.le_tan.ma_lt,
            ),
        )

        for url in cac_url:
            with self.subTest(url=url):
                response = self.client.get(url)

                self.assertEqual(
                    response.status_code,
                    405,
                )

    def test_hanh_dong_khong_hop_le_bi_tu_choi(
        self
    ):
        self.client.force_login(self.admin)

        response = self.client.post(
            self.url_trang_thai_lam_viec(
                "le-tan",
                self.le_tan.ma_lt,
            ),
            {
                "hanh_dong": "xoa_nhan_vien",
            },
        )

        self.assertEqual(response.status_code, 400)

        self.le_tan.refresh_from_db()
        self.le_tan.tai_khoan.refresh_from_db()

        self.assertTrue(self.le_tan.trang_thai)
        self.assertTrue(
            self.le_tan.tai_khoan.is_active
        )

    def test_tai_khoan_khong_phai_admin_bi_tu_choi_thay_doi(
        self
    ):
        self.client.force_login(
            self.nguoi_dung_khong_phai_admin
        )

        response = self.client.post(
            self.url_trang_thai_lam_viec(
                "pt",
                self.huan_luyen_vien.ma_pt,
            ),
            {
                "hanh_dong": "ngung_lam_viec",
            },
        )

        self.assertEqual(response.status_code, 403)

        self.huan_luyen_vien.refresh_from_db()
        self.huan_luyen_vien.tai_khoan.refresh_from_db()

        self.assertTrue(
            self.huan_luyen_vien.trang_thai
        )
        self.assertTrue(
            self.huan_luyen_vien
            .tai_khoan.is_active
        )
class QuanLyDangKyHoaDonTests(TestCase):
    def setUp(self):
        self.admin = TaiKhoan.objects.create_user(
            username="admin_dang_ky_hoa_don",
            password="1",
            vai_tro=TaiKhoan.VaiTro.ADMIN,
        )

        self.tai_khoan_pt = TaiKhoan.objects.create_user(
            username="pt_khong_duoc_quan_ly_dang_ky",
            password="1",
            vai_tro=TaiKhoan.VaiTro.PT,
        )

        self.le_tan = tao_le_tan(
            ho_ten="Lễ tân lập hóa đơn",
            gioi_tinh="Nam",
            ngay_sinh=date(2000, 1, 1),
            sdt="0931000001",
            email="le.tan.hoa.don@example.com",
            dia_chi="TP.HCM",
        )

        self.hoi_vien = tao_hoi_vien(
            ho_ten="Hội viên đăng ký gói",
            gioi_tinh="Nữ",
            ngay_sinh=date(2001, 2, 2),
            sdt="0931000002",
            email="hoi.vien.dang.ky@example.com",
            dia_chi="TP.HCM",
        )

        self.goi_dang_kinh_doanh = GoiTap.objects.create(
            ten_goi="Gói đang kinh doanh",
            thoi_han_ngay=30,
            gia_tien=500000,
            co_pt=False,
            so_buoi_pt=0,
            mo_ta="Gói dùng để kiểm thử đăng ký",
            trang_thai=True,
        )

        self.goi_ngung_kinh_doanh = GoiTap.objects.create(
            ten_goi="Gói đã ngừng kinh doanh",
            thoi_han_ngay=60,
            gia_tien=900000,
            co_pt=True,
            so_buoi_pt=10,
            mo_ta="Không được xuất hiện khi đăng ký",
            trang_thai=False,
        )

        self.url_danh_sach = reverse(
            "gym:danh_sach_dang_ky_hoa_don"
        )

        self.url_tao = reverse(
            "gym:tao_dang_ky_hoa_don"
        )

    def du_lieu_hop_le(self):
        return {
            "hoi_vien": self.hoi_vien.pk,
            "goi_tap": self.goi_dang_kinh_doanh.pk,
            "ngay_bat_dau": (
                timezone.localdate().isoformat()
            ),
            "phuong_thuc_thanh_toan": (
                "ChuyenKhoan"
            ),
            "ghi_chu_dang_ky": (
                "Đăng ký từ giao diện kiểm thử"
            ),
            "ghi_chu_hoa_don": (
                "Hóa đơn từ giao diện kiểm thử"
            ),
        }

    def tao_dang_ky_qua_giao_dien(self):
        self.client.force_login(
            self.le_tan.tai_khoan
        )

        response = self.client.post(
            self.url_tao,
            self.du_lieu_hop_le(),
        )

        dang_ky = DangKyGoiTap.objects.get(
            hoi_vien=self.hoi_vien,
            goi_tap=self.goi_dang_kinh_doanh,
        )

        return response, dang_ky

    def test_admin_xem_danh_sach_nhung_khong_co_nut_tao(
        self
    ):
        self.client.force_login(self.admin)

        response = self.client.get(
            self.url_danh_sach
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            (
                "users/dang_ky_hoa_don/"
                "danh_sach_dang_ky_hoa_don.html"
            ),
        )
        self.assertNotContains(
            response,
            "Tạo đăng ký",
        )

    def test_le_tan_xem_danh_sach_va_co_nut_tao(
        self
    ):
        self.client.force_login(
            self.le_tan.tai_khoan
        )

        response = self.client.get(
            self.url_danh_sach
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "Tạo đăng ký",
        )

    def test_vai_tro_khac_bi_tu_choi_danh_sach(
        self
    ):
        self.client.force_login(
            self.tai_khoan_pt
        )

        response = self.client.get(
            self.url_danh_sach
        )

        self.assertEqual(response.status_code, 403)

    def test_admin_khong_duoc_truy_cap_form_tao(
        self
    ):
        self.client.force_login(self.admin)

        response = self.client.get(
            self.url_tao
        )

        self.assertEqual(response.status_code, 403)

    def test_form_chi_hien_thi_goi_dang_kinh_doanh(
        self
    ):
        self.client.force_login(
            self.le_tan.tai_khoan
        )

        response = self.client.get(
            self.url_tao
        )

        self.assertEqual(response.status_code, 200)

        queryset = (
            response.context["form"]
            .fields["goi_tap"]
            .queryset
        )

        self.assertIn(
            self.goi_dang_kinh_doanh,
            queryset,
        )
        self.assertNotIn(
            self.goi_ngung_kinh_doanh,
            queryset,
        )

    def test_le_tan_ngung_lam_viec_khong_duoc_tao(
        self
    ):
        self.le_tan.trang_thai = False
        self.le_tan.save(
            update_fields=["trang_thai"],
        )

        self.client.force_login(
            self.le_tan.tai_khoan
        )

        response = self.client.get(
            self.url_tao
        )

        self.assertEqual(response.status_code, 403)

    def test_le_tan_tao_dang_ky_va_hoa_don_thanh_cong(
        self
    ):
        response, dang_ky = (
            self.tao_dang_ky_qua_giao_dien()
        )

        self.assertRedirects(
            response,
            reverse(
                "gym:chi_tiet_dang_ky_hoa_don",
                args=[dang_ky.ma_dk],
            ),
        )

        hoa_don = dang_ky.hoa_don

        self.assertRegex(
            dang_ky.ma_dk,
            r"^DK\d+$",
        )
        self.assertRegex(
            hoa_don.ma_hd,
            r"^HD\d+$",
        )
        self.assertEqual(
            hoa_don.le_tan,
            self.le_tan,
        )
        self.assertEqual(
            hoa_don.tong_tien,
            self.goi_dang_kinh_doanh.gia_tien,
        )
        self.assertEqual(
            hoa_don.phuong_thuc_thanh_toan,
            "ChuyenKhoan",
        )
        self.assertEqual(
            dang_ky.so_buoi_pt_dang_ky,
            0,
        )

    def test_hoa_don_chot_gia_tai_thoi_diem_dang_ky(
        self
    ):
        _, dang_ky = (
            self.tao_dang_ky_qua_giao_dien()
        )

        tong_tien_ban_dau = (
            dang_ky.hoa_don.tong_tien
        )

        self.goi_dang_kinh_doanh.gia_tien = 800000
        self.goi_dang_kinh_doanh.save(
            update_fields=["gia_tien"],
        )

        dang_ky.hoa_don.refresh_from_db()

        self.assertEqual(
            dang_ky.hoa_don.tong_tien,
            tong_tien_ban_dau,
        )
        self.assertNotEqual(
            dang_ky.hoa_don.tong_tien,
            self.goi_dang_kinh_doanh.gia_tien,
        )

    def test_du_lieu_khong_hop_le_khong_tao_ban_ghi(
        self
    ):
        self.client.force_login(
            self.le_tan.tai_khoan
        )

        du_lieu = self.du_lieu_hop_le()
        du_lieu["hoi_vien"] = ""

        response = self.client.post(
            self.url_tao,
            du_lieu,
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(
            "hoi_vien",
            response.context["form"].errors,
        )
        self.assertEqual(
            DangKyGoiTap.objects.count(),
            0,
        )
        self.assertEqual(
            HoaDon.objects.count(),
            0,
        )

    def test_goi_ngung_kinh_doanh_khong_duoc_dang_ky(
        self
    ):
        self.client.force_login(
            self.le_tan.tai_khoan
        )

        du_lieu = self.du_lieu_hop_le()
        du_lieu["goi_tap"] = (
            self.goi_ngung_kinh_doanh.pk
        )

        response = self.client.post(
            self.url_tao,
            du_lieu,
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(
            "goi_tap",
            response.context["form"].errors,
        )
        self.assertEqual(
            DangKyGoiTap.objects.count(),
            0,
        )
        self.assertEqual(
            HoaDon.objects.count(),
            0,
        )

    def test_admin_va_le_tan_xem_duoc_chi_tiet(
        self
    ):
        _, dang_ky = (
            self.tao_dang_ky_qua_giao_dien()
        )

        url = reverse(
            "gym:chi_tiet_dang_ky_hoa_don",
            args=[dang_ky.ma_dk],
        )

        for tai_khoan in (
            self.admin,
            self.le_tan.tai_khoan,
        ):
            with self.subTest(
                username=tai_khoan.username
            ):
                self.client.force_login(tai_khoan)

                response = self.client.get(url)

                self.assertEqual(
                    response.status_code,
                    200,
                )
                self.assertContains(
                    response,
                    dang_ky.ma_dk,
                )
                self.assertContains(
                    response,
                    dang_ky.hoa_don.ma_hd,
                )

    def test_ma_dang_ky_khong_ton_tai_tra_ve_404(
        self
    ):
        self.client.force_login(self.admin)

        response = self.client.get(
            reverse(
                "gym:chi_tiet_dang_ky_hoa_don",
                args=["DK999999"],
            )
        )

        self.assertEqual(response.status_code, 404)

    def test_pt_khong_duoc_xem_chi_tiet(
        self
    ):
        _, dang_ky = (
            self.tao_dang_ky_qua_giao_dien()
        )

        self.client.force_login(
            self.tai_khoan_pt
        )

        response = self.client.get(
            reverse(
                "gym:chi_tiet_dang_ky_hoa_don",
                args=[dang_ky.ma_dk],
            )
        )

        self.assertEqual(response.status_code, 403)

    def test_form_gia_han_chi_co_cac_truong_can_thiet(
        self
    ):
        _, dang_ky_goc = (
            self.tao_dang_ky_qua_giao_dien()
        )
        url = reverse(
            "gym:gia_han_goi_hoi_vien",
            args=[dang_ky_goc.ma_dk],
        )

        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            list(response.context["form"].fields),
            [
                "goi_tap",
                "phuong_thuc_thanh_toan",
                "ghi_chu_dang_ky",
                "ghi_chu_hoa_don",
            ],
        )

        queryset = (
            response.context["form"]
            .fields["goi_tap"]
            .queryset
        )
        self.assertIn(
            self.goi_dang_kinh_doanh,
            queryset,
        )
        self.assertNotIn(
            self.goi_ngung_kinh_doanh,
            queryset,
        )

    def test_admin_va_pt_khong_duoc_truy_cap_gia_han(
        self
    ):
        _, dang_ky_goc = (
            self.tao_dang_ky_qua_giao_dien()
        )
        url = reverse(
            "gym:gia_han_goi_hoi_vien",
            args=[dang_ky_goc.ma_dk],
        )

        for tai_khoan in (
            self.admin,
            self.tai_khoan_pt,
        ):
            with self.subTest(
                username=tai_khoan.username
            ):
                self.client.force_login(tai_khoan)
                response = self.client.get(url)

                self.assertEqual(
                    response.status_code,
                    403,
                )

    def test_le_tan_ngung_lam_viec_khong_duoc_gia_han(
        self
    ):
        _, dang_ky_goc = (
            self.tao_dang_ky_qua_giao_dien()
        )
        self.le_tan.trang_thai = False
        self.le_tan.save(
            update_fields=["trang_thai"],
        )

        response = self.client.get(
            reverse(
                "gym:gia_han_goi_hoi_vien",
                args=[dang_ky_goc.ma_dk],
            )
        )

        self.assertEqual(response.status_code, 403)

    def test_ma_dang_ky_gia_han_khong_ton_tai_tra_404(
        self
    ):
        self.client.force_login(
            self.le_tan.tai_khoan
        )

        response = self.client.get(
            reverse(
                "gym:gia_han_goi_hoi_vien",
                args=["DK999999"],
            )
        )

        self.assertEqual(response.status_code, 404)

    def test_chi_le_tan_nhin_thay_nut_gia_han(
        self
    ):
        _, dang_ky_goc = (
            self.tao_dang_ky_qua_giao_dien()
        )
        url = reverse(
            "gym:chi_tiet_dang_ky_hoa_don",
            args=[dang_ky_goc.ma_dk],
        )

        response_le_tan = self.client.get(url)
        self.assertContains(
            response_le_tan,
            "Gia hạn gói",
        )

        self.client.force_login(self.admin)
        response_admin = self.client.get(url)
        self.assertNotContains(
            response_admin,
            "Gia hạn gói",
        )

    def test_le_tan_gia_han_va_lap_hoa_don_thanh_cong(
        self
    ):
        _, dang_ky_goc = (
            self.tao_dang_ky_qua_giao_dien()
        )
        url = reverse(
            "gym:gia_han_goi_hoi_vien",
            args=[dang_ky_goc.ma_dk],
        )

        so_dang_ky_ban_dau = (
            DangKyGoiTap.objects.count()
        )
        so_hoa_don_ban_dau = HoaDon.objects.count()

        response = self.client.post(
            url,
            {
                "goi_tap": (
                    self.goi_dang_kinh_doanh.pk
                ),
                "phuong_thuc_thanh_toan": (
                    "TienMat"
                ),
                "ghi_chu_dang_ky": (
                    "Gia hạn từ giao diện kiểm thử"
                ),
                "ghi_chu_hoa_don": (
                    "Hóa đơn gia hạn kiểm thử"
                ),
            },
        )

        self.assertEqual(
            DangKyGoiTap.objects.count(),
            so_dang_ky_ban_dau + 1,
        )
        self.assertEqual(
            HoaDon.objects.count(),
            so_hoa_don_ban_dau + 1,
        )

        dang_ky_moi = (
            DangKyGoiTap.objects
            .exclude(pk=dang_ky_goc.pk)
            .get()
        )
        hoa_don_moi = dang_ky_moi.hoa_don

        self.assertRedirects(
            response,
            reverse(
                "gym:chi_tiet_dang_ky_hoa_don",
                args=[dang_ky_moi.ma_dk],
            ),
        )
        self.assertEqual(
            dang_ky_moi.hoi_vien,
            dang_ky_goc.hoi_vien,
        )
        self.assertEqual(
            dang_ky_moi.ngay_bat_dau,
            dang_ky_goc.ngay_ket_thuc
            + timedelta(days=1),
        )
        self.assertEqual(
            dang_ky_moi.trang_thai,
            DangKyGoiTap.TrangThai.CHUA_KICH_HOAT,
        )
        self.assertEqual(
            dang_ky_moi.ghi_chu,
            "Gia hạn từ giao diện kiểm thử",
        )
        self.assertEqual(
            hoa_don_moi.le_tan,
            self.le_tan,
        )
        self.assertEqual(
            hoa_don_moi.tong_tien,
            self.goi_dang_kinh_doanh.gia_tien,
        )
        self.assertEqual(
            hoa_don_moi.phuong_thuc_thanh_toan,
            "TienMat",
        )
        self.assertEqual(
            hoa_don_moi.ghi_chu,
            "Hóa đơn gia hạn kiểm thử",
        )

    def test_goi_ngung_kinh_doanh_khong_duoc_gia_han(
        self
    ):
        _, dang_ky_goc = (
            self.tao_dang_ky_qua_giao_dien()
        )
        url = reverse(
            "gym:gia_han_goi_hoi_vien",
            args=[dang_ky_goc.ma_dk],
        )

        so_dang_ky_ban_dau = (
            DangKyGoiTap.objects.count()
        )
        so_hoa_don_ban_dau = HoaDon.objects.count()

        response = self.client.post(
            url,
            {
                "goi_tap": (
                    self.goi_ngung_kinh_doanh.pk
                ),
                "phuong_thuc_thanh_toan": (
                    "TienMat"
                ),
                "ghi_chu_dang_ky": "",
                "ghi_chu_hoa_don": "",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(
            "goi_tap",
            response.context["form"].errors,
        )
        self.assertEqual(
            DangKyGoiTap.objects.count(),
            so_dang_ky_ban_dau,
        )
        self.assertEqual(
            HoaDon.objects.count(),
            so_hoa_don_ban_dau,
        )