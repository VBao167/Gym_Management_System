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

    def tao_dang_ky_cho_danh_sach(
        self,
        *,
        thu_tu,
        ngay_dang_ky,
        trang_thai=None,
    ):
        hoi_vien = tao_hoi_vien(
            ho_ten=(
                f"Hội viên danh sách {thu_tu}"
            ),
            gioi_tinh="Nam",
            ngay_sinh=date(
                2001,
                3,
                thu_tu,
            ),
            sdt=f"09320000{thu_tu:02d}",
            email=(
                f"hoi.vien.danh.sach.{thu_tu}"
                "@example.com"
            ),
            dia_chi="TP.HCM",
        )

        dang_ky, _ = tao_dang_ky_va_hoa_don(
            hoi_vien=hoi_vien,
            goi_tap=self.goi_dang_kinh_doanh,
            le_tan=self.le_tan,
            ngay_dang_ky=ngay_dang_ky,
            ngay_bat_dau=ngay_dang_ky,
            phuong_thuc_thanh_toan=(
                HoaDon.PhuongThucThanhToan.TIEN_MAT
            ),
        )

        if trang_thai is not None:
            DangKyGoiTap.objects.filter(
                pk=dang_ky.pk,
            ).update(
                trang_thai=trang_thai,
            )

            dang_ky.refresh_from_db()

        return dang_ky

    def test_danh_sach_sap_xep_theo_ma_dang_ky(
        self
    ):
        hom_nay = timezone.localdate()

        dang_ky_1 = (
            self.tao_dang_ky_cho_danh_sach(
                thu_tu=1,
                ngay_dang_ky=(
                    hom_nay - timedelta(days=2)
                ),
            )
        )

        dang_ky_2 = (
            self.tao_dang_ky_cho_danh_sach(
                thu_tu=2,
                ngay_dang_ky=hom_nay,
            )
        )

        dang_ky_3 = (
            self.tao_dang_ky_cho_danh_sach(
                thu_tu=3,
                ngay_dang_ky=(
                    hom_nay - timedelta(days=1)
                ),
            )
        )

        self.client.force_login(self.admin)

        response = self.client.get(
            self.url_danh_sach
        )

        self.assertEqual(
            [
                dang_ky.ma_dk
                for dang_ky
                in response.context[
                    "cac_dang_ky"
                ]
            ],
            [
                dang_ky_1.ma_dk,
                dang_ky_2.ma_dk,
                dang_ky_3.ma_dk,
            ],
        )

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
                "gym/dang_ky_hoa_don/"
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

    def test_danh_sach_co_day_du_bo_loc_trang_thai(
        self
    ):
        self.client.force_login(self.admin)

        response = self.client.get(
            self.url_danh_sach
        )

        self.assertEqual(
            response.context[
                "cac_bo_loc_trang_thai"
            ],
            [
                (
                    "",
                    "Tất cả",
                ),
                (
                    DangKyGoiTap
                    .TrangThai
                    .HOAT_DONG,
                    "Hoạt động",
                ),
                (
                    DangKyGoiTap
                    .TrangThai
                    .CHUA_KICH_HOAT,
                    "Chưa kích hoạt",
                ),
                (
                    DangKyGoiTap
                    .TrangThai
                    .HET_HAN,
                    "Hết hạn",
                ),
            ],
        )

    def test_loc_dang_ky_theo_trang_thai(
        self
    ):
        hom_nay = timezone.localdate()

        dang_ky_hoat_dong = (
            self.tao_dang_ky_cho_danh_sach(
                thu_tu=1,
                ngay_dang_ky=hom_nay,
                trang_thai=(
                    DangKyGoiTap
                    .TrangThai
                    .HOAT_DONG
                ),
            )
        )

        dang_ky_chua_kich_hoat = (
            self.tao_dang_ky_cho_danh_sach(
                thu_tu=2,
                ngay_dang_ky=hom_nay,
                trang_thai=(
                    DangKyGoiTap
                    .TrangThai
                    .CHUA_KICH_HOAT
                ),
            )
        )

        dang_ky_het_han = (
            self.tao_dang_ky_cho_danh_sach(
                thu_tu=3,
                ngay_dang_ky=hom_nay,
                trang_thai=(
                    DangKyGoiTap
                    .TrangThai
                    .HET_HAN
                ),
            )
        )

        self.client.force_login(self.admin)

        cac_truong_hop = (
            (
                DangKyGoiTap
                .TrangThai
                .HOAT_DONG,
                dang_ky_hoat_dong,
            ),
            (
                DangKyGoiTap
                .TrangThai
                .CHUA_KICH_HOAT,
                dang_ky_chua_kich_hoat,
            ),
            (
                DangKyGoiTap
                .TrangThai
                .HET_HAN,
                dang_ky_het_han,
            ),
        )

        with patch(
            (
                "gym.views."
                "cap_nhat_trang_thai_toan_bo"
            )
        ):
            for trang_thai, dang_ky_mong_doi in (
                cac_truong_hop
            ):
                with self.subTest(
                    trang_thai=trang_thai
                ):
                    response = self.client.get(
                        self.url_danh_sach,
                        {
                            "trang_thai": (
                                trang_thai
                            ),
                        },
                    )

                    self.assertEqual(
                        response.status_code,
                        200,
                    )

                    self.assertEqual(
                        response.context[
                            "trang_thai_duoc_chon"
                        ],
                        trang_thai,
                    )

                    self.assertEqual(
                        list(
                            response.context[
                                "cac_dang_ky"
                            ]
                        ),
                        [
                            dang_ky_mong_doi
                        ],
                    )

    def test_trang_thai_loc_khong_hop_le_quay_ve_tat_ca(
        self
    ):
        hom_nay = timezone.localdate()

        dang_ky_1 = (
            self.tao_dang_ky_cho_danh_sach(
                thu_tu=1,
                ngay_dang_ky=hom_nay,
            )
        )

        dang_ky_2 = (
            self.tao_dang_ky_cho_danh_sach(
                thu_tu=2,
                ngay_dang_ky=hom_nay,
            )
        )

        self.client.force_login(self.admin)

        response = self.client.get(
            self.url_danh_sach,
            {
                "trang_thai": (
                    "TrangThaiKhongTonTai"
                ),
            },
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            response.context[
                "trang_thai_duoc_chon"
            ],
            "",
        )

        self.assertEqual(
            list(
                response.context[
                    "cac_dang_ky"
                ]
            ),
            [
                dang_ky_1,
                dang_ky_2,
            ],
        )