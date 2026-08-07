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


class QuanLyDiemDanhTests(TestCase):
    def setUp(self):
        self.hom_nay = timezone.localdate()

        self.admin = TaiKhoan.objects.create_user(
            username="admin_diem_danh",
            password="1",
            vai_tro=TaiKhoan.VaiTro.ADMIN,
        )

        self.tai_khoan_pt = TaiKhoan.objects.create_user(
            username="pt_khong_duoc_diem_danh",
            password="1",
            vai_tro=TaiKhoan.VaiTro.PT,
        )

        self.tai_khoan_le_tan_khong_co_ho_so = (
            TaiKhoan.objects.create_user(
                username="le_tan_khong_co_ho_so_diem_danh",
                password="1",
                vai_tro=TaiKhoan.VaiTro.LE_TAN,
            )
        )

        self.le_tan = tao_le_tan(
            ho_ten="Lễ tân kiểm thử điểm danh",
            gioi_tinh="Nữ",
            ngay_sinh=date(2000, 1, 1),
            sdt="0971000001",
            email="le.tan.giao.dien.diem.danh@example.com",
            dia_chi="TP.HCM",
        )

        self.hoi_vien_hoat_dong = tao_hoi_vien(
            ho_ten="Hội viên đang hoạt động",
            gioi_tinh="Nam",
            ngay_sinh=date(2001, 2, 2),
            sdt="0971000002",
            email="hoi.vien.hoat.dong@example.com",
            dia_chi="TP.HCM",
        )

        self.hoi_vien_khong_co_goi = tao_hoi_vien(
            ho_ten="Hội viên chưa có gói",
            gioi_tinh="Nữ",
            ngay_sinh=date(2002, 3, 3),
            sdt="0971000003",
            email="hoi.vien.chua.co.goi.dd@example.com",
            dia_chi="TP.HCM",
        )

        self.goi_tap = GoiTap.objects.create(
            ten_goi="Gói kiểm thử giao diện điểm danh",
            thoi_han_ngay=30,
            gia_tien=500000,
            co_pt=False,
            so_buoi_pt=0,
            mo_ta="Gói dùng cho kiểm thử điểm danh",
            trang_thai=True,
        )

        tao_dang_ky_va_hoa_don(
            hoi_vien=self.hoi_vien_hoat_dong,
            goi_tap=self.goi_tap,
            le_tan=self.le_tan,
            ngay_dang_ky=self.hom_nay,
            ngay_bat_dau=self.hom_nay,
            phuong_thuc_thanh_toan=(
                HoaDon.PhuongThucThanhToan.TIEN_MAT
            ),
        )

        self.url_danh_sach = reverse(
            "gym:danh_sach_diem_danh"
        )
        self.url_tao = reverse(
            "gym:tao_diem_danh_moi"
        )

    def tao_hoi_vien_hoat_dong_bo_sung(
        self,
        thu_tu,
    ):
        hoi_vien = tao_hoi_vien(
            ho_ten=(
                f"Hội viên tìm kiếm {thu_tu}"
            ),
            gioi_tinh="Nam",
            ngay_sinh=date(2001, 4, 4),
            sdt=f"09720000{thu_tu:02d}",
            email=(
                f"hoi.vien.tim.kiem.{thu_tu}"
                "@example.com"
            ),
            dia_chi="TP.HCM",
        )

        tao_dang_ky_va_hoa_don(
            hoi_vien=hoi_vien,
            goi_tap=self.goi_tap,
            le_tan=self.le_tan,
            ngay_dang_ky=self.hom_nay,
            ngay_bat_dau=self.hom_nay,
            phuong_thuc_thanh_toan=(
                HoaDon.PhuongThucThanhToan.TIEN_MAT
            ),
        )

        return hoi_vien

    def test_mac_dinh_chi_hien_thi_toi_da_muoi_hoi_vien(
        self
    ):
        for thu_tu in range(1, 11):
            self.tao_hoi_vien_hoat_dong_bo_sung(
                thu_tu
            )

        self.client.force_login(
            self.le_tan.tai_khoan
        )

        response = self.client.get(
            self.url_tao
        )

        cac_hoi_vien = list(
            response.context[
                "cac_hoi_vien_hop_le"
            ]
        )

        self.assertEqual(
            len(cac_hoi_vien),
            10,
        )

        self.assertEqual(
            [
                hoi_vien.ma_hv
                for hoi_vien in cac_hoi_vien
            ],
            sorted(
                hoi_vien.ma_hv
                for hoi_vien in cac_hoi_vien
            ),
        )

    def test_admin_xem_danh_sach_nhung_khong_co_nut_tao(
        self
    ):
        diem_danh = tao_diem_danh(
            hoi_vien=self.hoi_vien_hoat_dong,
            le_tan=self.le_tan,
            ghi_chu="Điểm danh để Admin xem",
        )

        self.client.force_login(self.admin)
        response = self.client.get(
            self.url_danh_sach
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            "gym/diem_danh/danh_sach_diem_danh.html",
        )
        self.assertContains(
            response,
            diem_danh.ma_dd,
        )
        self.assertContains(
            response,
            "Điểm danh để Admin xem",
        )
        self.assertNotContains(
            response,
            "Điểm danh Hội viên",
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
            "Điểm danh Hội viên",
        )

    def test_pt_khong_duoc_xem_danh_sach(
        self
    ):
        self.client.force_login(
            self.tai_khoan_pt
        )

        response = self.client.get(
            self.url_danh_sach
        )

        self.assertEqual(response.status_code, 403)

    def test_admin_va_pt_khong_duoc_truy_cap_form_tao(
        self
    ):
        for tai_khoan in (
            self.admin,
            self.tai_khoan_pt,
        ):
            with self.subTest(
                username=tai_khoan.username
            ):
                self.client.force_login(tai_khoan)

                response = self.client.get(
                    self.url_tao
                )

                self.assertEqual(
                    response.status_code,
                    403,
                )

    def test_form_chi_hien_thi_hoi_vien_du_dieu_kien(
        self
    ):
        self.client.force_login(
            self.le_tan.tai_khoan
        )

        response = self.client.get(
            self.url_tao
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            "gym/diem_danh/tao_diem_danh.html",
        )

        form = response.context["form"]

        self.assertEqual(
            list(form.fields),
            [
                "hoi_vien",
                "ghi_chu",
            ],
        )

        self.assertTrue(
            form.fields["hoi_vien"].widget.is_hidden
        )

        queryset = (
            form.fields["hoi_vien"].queryset
        )

        self.assertIn(
            self.hoi_vien_hoat_dong,
            queryset,
        )
        self.assertNotIn(
            self.hoi_vien_khong_co_goi,
            queryset,
        )

        self.assertEqual(
            list(
                response.context[
                    "cac_hoi_vien_hop_le"
                ]
            ),
            [
                self.hoi_vien_hoat_dong,
            ],
        )

        self.assertNotContains(
            response,
            '<select name="hoi_vien"',
        )

        self.assertContains(
            response,
            self.hoi_vien_hoat_dong.ma_hv,
        )
        self.assertContains(
            response,
            self.hoi_vien_hoat_dong.ho_ten,
        )
        self.assertContains(
            response,
            self.hoi_vien_hoat_dong.sdt,
        )
        self.assertContains(
            response,
            self.hoi_vien_hoat_dong.email,
        )

    def test_tim_hoi_vien_diem_danh_theo_nhieu_thong_tin(
        self
    ):
        self.client.force_login(
            self.le_tan.tai_khoan
        )

        cac_tu_khoa = (
            self.hoi_vien_hoat_dong.ma_hv,
            "đang hoạt động",
            "0971000002",
            "hoi.vien.hoat.dong@example.com",
        )

        for tu_khoa in cac_tu_khoa:
            with self.subTest(
                tu_khoa=tu_khoa
            ):
                response = self.client.get(
                    self.url_tao,
                    {
                        "tu_khoa": tu_khoa,
                    },
                )

                self.assertEqual(
                    response.status_code,
                    200,
                )

                self.assertEqual(
                    list(
                        response.context[
                            "cac_hoi_vien_hop_le"
                        ]
                    ),
                    [
                        self.hoi_vien_hoat_dong,
                    ],
                )

                self.assertContains(
                    response,
                    self.hoi_vien_hoat_dong.ma_hv,
                )

    def test_tim_hoi_vien_khong_co_ket_qua(
        self
    ):
        self.client.force_login(
            self.le_tan.tai_khoan
        )

        response = self.client.get(
            self.url_tao,
            {
                "tu_khoa": (
                    "HoiVienKhongTonTai999"
                ),
            },
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            list(
                response.context[
                    "cac_hoi_vien_hop_le"
                ]
            ),
            [],
        )

        self.assertContains(
            response,
            "Không tìm thấy Hội viên đang có",
        )

        self.assertContains(
            response,
            "quyền tập phù hợp với từ khóa.",
        )

    def test_tim_kiem_khong_hien_hoi_vien_khong_co_quyen_tap(
        self
    ):
        self.client.force_login(
            self.le_tan.tai_khoan
        )

        response = self.client.get(
            self.url_tao,
            {
                "tu_khoa": (
                    self.hoi_vien_khong_co_goi.ma_hv
                ),
            },
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            list(
                response.context[
                    "cac_hoi_vien_hop_le"
                ]
            ),
            [],
        )

        self.assertNotContains(
            response,
            self.hoi_vien_khong_co_goi.ho_ten,
        )

    def test_le_tan_khong_co_ho_so_bi_tu_choi(
        self
    ):
        self.client.force_login(
            self.tai_khoan_le_tan_khong_co_ho_so
        )

        for url in (
            self.url_danh_sach,
            self.url_tao,
        ):
            with self.subTest(url=url):
                response = self.client.get(url)

                self.assertEqual(
                    response.status_code,
                    403,
                )

    def test_le_tan_ngung_lam_viec_bi_tu_choi(
        self
    ):
        self.le_tan.trang_thai = False
        self.le_tan.save(
            update_fields=["trang_thai"],
        )

        self.client.force_login(
            self.le_tan.tai_khoan
        )

        for url in (
            self.url_danh_sach,
            self.url_tao,
        ):
            with self.subTest(url=url):
                response = self.client.get(url)

                self.assertEqual(
                    response.status_code,
                    403,
                )

    def test_le_tan_tao_diem_danh_thanh_cong(
        self
    ):
        self.client.force_login(
            self.le_tan.tai_khoan
        )

        response = self.client.post(
            self.url_tao,
            {
                "hoi_vien": (
                    self.hoi_vien_hoat_dong.pk
                ),
                "ghi_chu": (
                    "Điểm danh từ giao diện kiểm thử"
                ),
            },
        )

        self.assertRedirects(
            response,
            self.url_danh_sach,
        )
        self.assertEqual(
            DiemDanh.objects.count(),
            1,
        )

        diem_danh = DiemDanh.objects.get()

        self.assertRegex(
            diem_danh.ma_dd,
            r"^DD\d+$",
        )
        self.assertEqual(
            diem_danh.hoi_vien,
            self.hoi_vien_hoat_dong,
        )
        self.assertEqual(
            diem_danh.le_tan,
            self.le_tan,
        )
        self.assertEqual(
            diem_danh.ghi_chu,
            "Điểm danh từ giao diện kiểm thử",
        )
        self.assertEqual(
            timezone.localdate(
                diem_danh.thoi_gian_diem_danh
            ),
            self.hom_nay,
        )

    def test_hoi_vien_khong_co_goi_khong_duoc_diem_danh(
        self
    ):
        self.client.force_login(
            self.le_tan.tai_khoan
        )

        response = self.client.post(
            self.url_tao,
            {
                "hoi_vien": (
                    self.hoi_vien_khong_co_goi.pk
                ),
                "ghi_chu": "",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(
            "hoi_vien",
            response.context["form"].errors,
        )
        self.assertEqual(
            DiemDanh.objects.count(),
            0,
        )
        self.assertFalse(
            DiemDanh.objects.filter(
                hoi_vien=self.hoi_vien_khong_co_goi,
            ).exists()
        )

    def test_cho_phep_diem_danh_nhieu_lan_trong_ngay(
        self
    ):
        self.client.force_login(
            self.le_tan.tai_khoan
        )

        for lan in range(1, 3):
            response = self.client.post(
                self.url_tao,
                {
                    "hoi_vien": (
                        self.hoi_vien_hoat_dong.pk
                    ),
                    "ghi_chu": (
                        f"Điểm danh lần {lan}"
                    ),
                },
            )

            self.assertEqual(
                response.status_code,
                302,
            )

        self.assertEqual(
            DiemDanh.objects.count(),
            2,
        )
        self.assertEqual(
            set(
                DiemDanh.objects.values_list(
                    "ghi_chu",
                    flat=True,
                )
            ),
            {
                "Điểm danh lần 1",
                "Điểm danh lần 2",
            },
        )
