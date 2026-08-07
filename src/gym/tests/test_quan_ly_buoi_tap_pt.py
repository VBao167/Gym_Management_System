from datetime import date, datetime, time, timedelta
from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import TaiKhoan
from gym.models import BuoiTapPT, GoiTap, HoaDon
from gym.services.buoi_tap_pt import tao_buoi_tap_pt
from gym.services.dang_ky_goi import (
    tao_dang_ky_va_hoa_don,
)
from gym.services.nguoi_dung import (
    tao_hoi_vien,
    tao_huan_luyen_vien,
    tao_le_tan,
)


class QuanLyBuoiTapPTTests(TestCase):
    def setUp(self):
        self.hom_nay = timezone.localdate()

        self.admin = TaiKhoan.objects.create_user(
            username="admin_quan_ly_buoi_pt",
            password="1",
            vai_tro=TaiKhoan.VaiTro.ADMIN,
        )

        self.tai_khoan_le_tan_khong_co_ho_so = (
            TaiKhoan.objects.create_user(
                username="le_tan_khong_co_ho_so_buoi_pt",
                password="1",
                vai_tro=TaiKhoan.VaiTro.LE_TAN,
            )
        )

        self.le_tan = tao_le_tan(
            ho_ten="Lễ tân kiểm thử buổi PT",
            gioi_tinh="Nữ",
            ngay_sinh=date(2000, 1, 1),
            sdt="0981000001",
            email="le.tan.buoi.pt@example.com",
            dia_chi="TP.HCM",
        )

        self.le_tan_2 = tao_le_tan(
            ho_ten="Lễ tân kiểm thử thay ca",
            gioi_tinh="Nam",
            ngay_sinh=date(2000, 1, 2),
            sdt="0981000006",
            email="le.tan.buoi.pt.2@example.com",
            dia_chi="TP.HCM",
        )

        self.pt_1 = tao_huan_luyen_vien(
            ho_ten="PT đang làm việc thứ nhất",
            gioi_tinh="Nam",
            ngay_sinh=date(1998, 2, 2),
            sdt="0981000002",
            email="pt.buoi.tap.1@example.com",
            dia_chi="TP.HCM",
        )

        self.pt_2 = tao_huan_luyen_vien(
            ho_ten="PT đang làm việc thứ hai",
            gioi_tinh="Nữ",
            ngay_sinh=date(1999, 3, 3),
            sdt="0981000003",
            email="pt.buoi.tap.2@example.com",
            dia_chi="TP.HCM",
        )

        self.pt_ngung_lam_viec = tao_huan_luyen_vien(
            ho_ten="PT đã ngừng làm việc",
            gioi_tinh="Nam",
            ngay_sinh=date(1997, 4, 4),
            sdt="0981000004",
            email="pt.ngung.buoi.tap@example.com",
            dia_chi="TP.HCM",
        )
        self.pt_ngung_lam_viec.trang_thai = False
        self.pt_ngung_lam_viec.save(
            update_fields=["trang_thai"],
        )

        self.hoi_vien = tao_hoi_vien(
            ho_ten="Hội viên kiểm thử lịch PT",
            gioi_tinh="Nam",
            ngay_sinh=date(2001, 5, 5),
            sdt="0981000005",
            email="hoi.vien.buoi.pt@example.com",
            dia_chi="TP.HCM",
        )

        self.goi_vao_gym = GoiTap.objects.create(
            ten_goi="Gói vào gym cho giao diện PT",
            thoi_han_ngay=30,
            gia_tien=300000,
            co_pt=False,
            so_buoi_pt=0,
            mo_ta="Bảo đảm quyền vào phòng gym",
            trang_thai=True,
        )

        self.goi_pt = GoiTap.objects.create(
            ten_goi="Gói PT cho kiểm thử giao diện",
            thoi_han_ngay=10,
            gia_tien=600000,
            co_pt=True,
            so_buoi_pt=2,
            mo_ta="Gói có hai buổi PT",
            trang_thai=True,
        )

        dang_ky_vao_gym, _ = (
            tao_dang_ky_va_hoa_don(
                hoi_vien=self.hoi_vien,
                goi_tap=self.goi_vao_gym,
                le_tan=self.le_tan,
                ngay_dang_ky=self.hom_nay,
                ngay_bat_dau=self.hom_nay,
                phuong_thuc_thanh_toan=(
                    HoaDon.PhuongThucThanhToan.TIEN_MAT
                ),
            )
        )

        self.dang_ky_pt_tuong_lai, _ = (
            tao_dang_ky_va_hoa_don(
                hoi_vien=self.hoi_vien,
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

        self.url_danh_sach = reverse(
            "gym:danh_sach_buoi_tap_pt"
        )
        self.url_tao = reverse(
            "gym:tao_buoi_tap_pt_moi"
        )
        self.url_trang_pt = reverse(
            "gym:trang_pt"
        )

    def tao_buoi_cho_lich_pt(
        self,
        *,
        huan_luyen_vien=None,
        ngay_tap=None,
        gio_bat_dau=time(9, 0),
        gio_ket_thuc=time(10, 0),
        trang_thai=None,
    ):
        self.dang_ky_pt_tuong_lai.so_buoi_pt_dang_ky = 20
        self.dang_ky_pt_tuong_lai.save(
            update_fields=["so_buoi_pt_dang_ky"],
        )

        buoi_tap = tao_buoi_tap_pt(
            dang_ky=self.dang_ky_pt_tuong_lai,
            huan_luyen_vien=(
                huan_luyen_vien or self.pt_1
            ),
            le_tan=self.le_tan,
            ngay_tap=(
                ngay_tap or self.hom_nay
            ),
            gio_bat_dau=gio_bat_dau,
            gio_ket_thuc=gio_ket_thuc,
        )

        if trang_thai is not None:
            BuoiTapPT.objects.filter(
                pk=buoi_tap.pk,
            ).update(
                trang_thai=trang_thai,
            )

            buoi_tap.refresh_from_db()

        return buoi_tap

    def test_trang_chu_pt_hien_lich_hom_nay_cua_minh_theo_gio(
        self
    ):
        buoi_muon = self.tao_buoi_cho_lich_pt(
            gio_bat_dau=time(10, 0),
            gio_ket_thuc=time(11, 0),
        )

        buoi_som = self.tao_buoi_cho_lich_pt(
            gio_bat_dau=time(8, 0),
            gio_ket_thuc=time(9, 0),
        )

        buoi_ngay_mai = self.tao_buoi_cho_lich_pt(
            ngay_tap=(
                self.hom_nay
                + timedelta(days=1)
            ),
            gio_bat_dau=time(13, 0),
            gio_ket_thuc=time(14, 0),
        )

        buoi_pt_khac = self.tao_buoi_cho_lich_pt(
            huan_luyen_vien=self.pt_2,
            gio_bat_dau=time(14, 0),
            gio_ket_thuc=time(15, 0),
        )

        self.client.force_login(
            self.pt_1.tai_khoan
        )

        response = self.client.get(
            self.url_trang_pt
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            list(
                response.context[
                    "cac_buoi_tap_hom_nay"
                ]
            ),
            [
                buoi_som,
                buoi_muon,
            ],
        )

        self.assertNotContains(
            response,
            buoi_ngay_mai.ma_buoi,
        )

        self.assertNotContains(
            response,
            buoi_pt_khac.ma_buoi,
        )

    def test_trang_chu_pt_loc_theo_trang_thai(
        self
    ):
        buoi_da_len_lich = (
            self.tao_buoi_cho_lich_pt(
                gio_bat_dau=time(8, 0),
                gio_ket_thuc=time(9, 0),
            )
        )

        buoi_vang = self.tao_buoi_cho_lich_pt(
            gio_bat_dau=time(10, 0),
            gio_ket_thuc=time(11, 0),
            trang_thai=(
                BuoiTapPT.TrangThai.VANG
            ),
        )

        self.client.force_login(
            self.pt_1.tai_khoan
        )

        response = self.client.get(
            self.url_trang_pt,
            {
                "trang_thai": (
                    BuoiTapPT.TrangThai.VANG
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
            BuoiTapPT.TrangThai.VANG,
        )

        self.assertEqual(
            list(
                response.context[
                    "cac_buoi_tap_hom_nay"
                ]
            ),
            [
                buoi_vang,
            ],
        )

        self.assertContains(
            response,
            buoi_vang.ma_buoi,
        )

        self.assertNotContains(
            response,
            buoi_da_len_lich.ma_buoi,
        )

    def test_trang_chu_pt_trang_thai_sai_quay_ve_tat_ca(
        self
    ):
        buoi_1 = self.tao_buoi_cho_lich_pt(
            gio_bat_dau=time(8, 0),
            gio_ket_thuc=time(9, 0),
        )

        buoi_2 = self.tao_buoi_cho_lich_pt(
            gio_bat_dau=time(10, 0),
            gio_ket_thuc=time(11, 0),
            trang_thai=(
                BuoiTapPT.TrangThai.VANG
            ),
        )

        self.client.force_login(
            self.pt_1.tai_khoan
        )

        response = self.client.get(
            self.url_trang_pt,
            {
                "trang_thai": "TrangThaiKhongTonTai",
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
                    "cac_buoi_tap_hom_nay"
                ]
            ),
            [
                buoi_1,
                buoi_2,
            ],
        )

    def test_lich_pt_cua_toi_mac_dinh_hom_nay(
        self
    ):
        buoi_hom_nay = (
            self.tao_buoi_cho_lich_pt()
        )

        buoi_ngay_mai = self.tao_buoi_cho_lich_pt(
            ngay_tap=(
                self.hom_nay
                + timedelta(days=1)
            ),
            gio_bat_dau=time(11, 0),
            gio_ket_thuc=time(12, 0),
        )

        self.client.force_login(
            self.pt_1.tai_khoan
        )

        response = self.client.get(
            self.url_danh_sach
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertTrue(
            response.context[
                "la_lich_ca_nhan"
            ]
        )

        self.assertEqual(
            response.context[
                "ngay_duoc_chon"
            ],
            self.hom_nay,
        )

        self.assertEqual(
            list(
                response.context[
                    "cac_buoi_tap"
                ]
            ),
            [
                buoi_hom_nay,
            ],
        )

        self.assertNotContains(
            response,
            buoi_ngay_mai.ma_buoi,
        )

    def test_lich_pt_cua_toi_chon_ngay_khac(
        self
    ):
        ngay_mai = (
            self.hom_nay
            + timedelta(days=1)
        )

        buoi_hom_nay = (
            self.tao_buoi_cho_lich_pt()
        )

        buoi_ngay_mai = self.tao_buoi_cho_lich_pt(
            ngay_tap=ngay_mai,
            gio_bat_dau=time(8, 0),
            gio_ket_thuc=time(9, 0),
        )

        self.client.force_login(
            self.pt_1.tai_khoan
        )

        response = self.client.get(
            self.url_danh_sach,
            {
                "ngay": ngay_mai.isoformat(),
            },
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            response.context[
                "ngay_duoc_chon"
            ],
            ngay_mai,
        )

        self.assertEqual(
            list(
                response.context[
                    "cac_buoi_tap"
                ]
            ),
            [
                buoi_ngay_mai,
            ],
        )

        self.assertNotContains(
            response,
            buoi_hom_nay.ma_buoi,
        )

    def test_lich_pt_cua_toi_loc_ngay_va_trang_thai(
        self
    ):
        ngay_mai = (
            self.hom_nay
            + timedelta(days=1)
        )

        buoi_da_len_lich = (
            self.tao_buoi_cho_lich_pt(
                ngay_tap=ngay_mai,
                gio_bat_dau=time(8, 0),
                gio_ket_thuc=time(9, 0),
            )
        )

        buoi_vang = self.tao_buoi_cho_lich_pt(
            ngay_tap=ngay_mai,
            gio_bat_dau=time(10, 0),
            gio_ket_thuc=time(11, 0),
            trang_thai=(
                BuoiTapPT.TrangThai.VANG
            ),
        )

        self.client.force_login(
            self.pt_1.tai_khoan
        )

        response = self.client.get(
            self.url_danh_sach,
            {
                "ngay": ngay_mai.isoformat(),
                "trang_thai": (
                    BuoiTapPT.TrangThai.VANG
                ),
            },
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            response.context[
                "ngay_duoc_chon"
            ],
            ngay_mai,
        )

        self.assertEqual(
            response.context[
                "trang_thai_duoc_chon"
            ],
            BuoiTapPT.TrangThai.VANG,
        )

        self.assertEqual(
            list(
                response.context[
                    "cac_buoi_tap"
                ]
            ),
            [
                buoi_vang,
            ],
        )

        self.assertNotContains(
            response,
            buoi_da_len_lich.ma_buoi,
        )

    def test_lich_pt_cua_toi_ngay_sai_quay_ve_hom_nay(
        self
    ):
        buoi_hom_nay = (
            self.tao_buoi_cho_lich_pt()
        )

        self.client.force_login(
            self.pt_1.tai_khoan
        )

        response = self.client.get(
            self.url_danh_sach,
            {
                "ngay": "khong-phai-ngay",
            },
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            response.context[
                "ngay_duoc_chon"
            ],
            self.hom_nay,
        )

        self.assertTrue(
            response.context[
                "ngay_khong_hop_le"
            ]
        )

        self.assertContains(
            response,
            buoi_hom_nay.ma_buoi,
        )

        self.assertContains(
            response,
            "Ngày được nhập không hợp lệ.",
        )

    def test_admin_xem_danh_sach_nhung_khong_co_nut_tao(
        self
    ):
        buoi_tap = tao_buoi_tap_pt(
            dang_ky=self.dang_ky_pt_tuong_lai,
            huan_luyen_vien=self.pt_1,
            le_tan=self.le_tan,
            ngay_tap=self.hom_nay,
            gio_bat_dau=time(8, 0),
            gio_ket_thuc=time(9, 0),
            ghi_chu="Buổi PT để Admin xem",
        )

        self.client.force_login(self.admin)

        response = self.client.get(
            self.url_danh_sach
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            (
                "gym/buoi_tap_pt/"
                "danh_sach_buoi_tap_pt.html"
            ),
        )
        self.assertContains(
            response,
            buoi_tap.ma_buoi,
        )
        self.assertContains(
            response,
            "Xem chi tiết",
        )
        self.assertContains(
            response,
            reverse(
                "gym:chi_tiet_buoi_tap_pt",
                args=[buoi_tap.ma_buoi],
            ),
        )
        self.assertNotContains(
            response,
            "Xếp buổi tập PT",
        )

        response_chi_tiet = self.client.get(
            reverse(
                "gym:chi_tiet_buoi_tap_pt",
                args=[buoi_tap.ma_buoi],
            )
        )

        self.assertEqual(
            response_chi_tiet.status_code,
            200,
        )
        self.assertContains(
            response_chi_tiet,
            "Buổi PT để Admin xem",
        )
        self.assertIsNone(
            response_chi_tiet.context["form_ket_qua"],
        )
        self.assertIsNone(
            response_chi_tiet.context["form_huy"],
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
            "Xếp buổi tập PT",
        )

    def test_pt_chi_xem_buoi_duoc_phan_cong(
        self
    ):
        buoi_cua_pt_1 = tao_buoi_tap_pt(
            dang_ky=self.dang_ky_pt_tuong_lai,
            huan_luyen_vien=self.pt_1,
            le_tan=self.le_tan,
            ngay_tap=self.hom_nay,
            gio_bat_dau=time(8, 0),
            gio_ket_thuc=time(9, 0),
        )

        buoi_cua_pt_2 = tao_buoi_tap_pt(
            dang_ky=self.dang_ky_pt_tuong_lai,
            huan_luyen_vien=self.pt_2,
            le_tan=self.le_tan,
            ngay_tap=self.hom_nay,
            gio_bat_dau=time(9, 0),
            gio_ket_thuc=time(10, 0),
        )

        self.client.force_login(
            self.pt_1.tai_khoan
        )

        response = self.client.get(
            self.url_danh_sach
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            buoi_cua_pt_1.ma_buoi,
        )
        self.assertNotContains(
            response,
            buoi_cua_pt_2.ma_buoi,
        )
        self.assertContains(
            response,
            "Lịch tập của tôi",
        )

    def test_admin_va_pt_khong_duoc_truy_cap_form_tao(
        self
    ):
        for tai_khoan in (
            self.admin,
            self.pt_1.tai_khoan,
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

    def test_form_co_dung_truong_va_du_lieu_lua_chon(
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
            "gym/buoi_tap_pt/tao_buoi_tap_pt.html",
        )

        form = response.context["form"]

        self.assertEqual(
            list(form.fields),
            [
                "hoi_vien",
                "huan_luyen_vien",
                "ngay_tap",
                "gio_bat_dau",
                "gio_ket_thuc",
                "ghi_chu",
            ],
        )

        self.assertTrue(
            form.fields["hoi_vien"].widget.is_hidden
        )

        queryset_hoi_vien = (
            form.fields["hoi_vien"].queryset
        )
        queryset_pt = (
            form.fields[
                "huan_luyen_vien"
            ].queryset
        )

        self.assertIn(
            self.hoi_vien,
            queryset_hoi_vien,
        )

        self.assertIn(self.pt_1, queryset_pt)
        self.assertIn(self.pt_2, queryset_pt)
        self.assertNotIn(
            self.pt_ngung_lam_viec,
            queryset_pt,
        )

        cac_hoi_vien = response.context[
            "cac_hoi_vien"
        ]

        self.assertEqual(
            len(cac_hoi_vien),
            1,
        )
        self.assertEqual(
            cac_hoi_vien[0]["hoi_vien"],
            self.hoi_vien,
        )
        self.assertEqual(
            cac_hoi_vien[0][
                "so_buoi_pt_co_the_xep"
            ],
            2,
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

    def test_le_tan_xep_buoi_pt_som_thanh_cong(
        self
    ):
        self.client.force_login(
            self.le_tan.tai_khoan
        )

        response = self.client.post(
            self.url_tao,
            {
               "hoi_vien": self.hoi_vien.pk,
                "huan_luyen_vien": self.pt_1.pk,
                "ngay_tap": self.hom_nay.isoformat(),
                "gio_bat_dau": "09:00",
                "gio_ket_thuc": "10:00",
                "ghi_chu": (
                    "Xếp sớm từ giao diện kiểm thử"
                ),
            },
        )

        self.assertRedirects(
            response,
            self.url_danh_sach,
        )
        self.assertEqual(
            BuoiTapPT.objects.count(),
            1,
        )

        buoi_tap = BuoiTapPT.objects.get()

        self.assertRegex(
            buoi_tap.ma_buoi,
            r"^Buoi\d+$",
        )
        self.assertEqual(
            buoi_tap.dang_ky,
            self.dang_ky_pt_tuong_lai,
        )
        self.assertEqual(
            buoi_tap.huan_luyen_vien,
            self.pt_1,
        )
        self.assertEqual(
            buoi_tap.le_tan,
            self.le_tan,
        )
        self.assertEqual(
            buoi_tap.ngay_tap,
            self.hom_nay,
        )
        self.assertEqual(
            buoi_tap.trang_thai,
            BuoiTapPT.TrangThai.DA_LEN_LICH,
        )
        self.assertEqual(
            buoi_tap.ghi_chu,
            "Xếp sớm từ giao diện kiểm thử",
        )

    def test_gio_ket_thuc_khong_hop_le_khong_tao_buoi(
        self
    ):
        self.client.force_login(
            self.le_tan.tai_khoan
        )

        response = self.client.post(
            self.url_tao,
            {
                "hoi_vien": self.hoi_vien.pk,
                "huan_luyen_vien": self.pt_1.pk,
                "ngay_tap": self.hom_nay.isoformat(),
                "gio_bat_dau": "10:00",
                "gio_ket_thuc": "09:00",
                "ghi_chu": "",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(
            "gio_ket_thuc",
            response.context["form"].errors,
        )
        self.assertEqual(
            BuoiTapPT.objects.count(),
            0,
        )

    def test_trung_lich_hoi_vien_khong_tao_buoi_thu_hai(
        self
    ):
        tao_buoi_tap_pt(
            dang_ky=self.dang_ky_pt_tuong_lai,
            huan_luyen_vien=self.pt_1,
            le_tan=self.le_tan,
            ngay_tap=self.hom_nay,
            gio_bat_dau=time(9, 0),
            gio_ket_thuc=time(10, 0),
        )

        self.client.force_login(
            self.le_tan.tai_khoan
        )

        response = self.client.post(
            self.url_tao,
            {
                "hoi_vien": self.hoi_vien.pk,
                "huan_luyen_vien": self.pt_2.pk,
                "ngay_tap": self.hom_nay.isoformat(),
                "gio_bat_dau": "09:30",
                "gio_ket_thuc": "10:30",
                "ghi_chu": "",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(
            "__all__",
            response.context["form"].errors,
        )
        self.assertEqual(
            BuoiTapPT.objects.count(),
            1,
        )
    def test_trang_chu_pt_co_duong_dan_den_lich_tap(
        self
    ):
        self.client.force_login(
            self.pt_1.tai_khoan
        )

        response = self.client.get(
            reverse("gym:trang_pt")
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "Xem lịch tập của tôi",
        )
        self.assertContains(
            response,
            self.url_danh_sach,
        )

    def test_pt_xem_chi_tiet_buoi_cua_minh_va_co_form(
        self
    ):
        buoi_tap = tao_buoi_tap_pt(
            dang_ky=self.dang_ky_pt_tuong_lai,
            huan_luyen_vien=self.pt_1,
            le_tan=self.le_tan,
            ngay_tap=self.hom_nay,
            gio_bat_dau=time(9, 0),
            gio_ket_thuc=time(10, 0),
        )

        self.client.force_login(
            self.pt_1.tai_khoan
        )

        response = self.client.get(
            reverse(
                "gym:chi_tiet_buoi_tap_pt",
                args=[buoi_tap.ma_buoi],
            )
        )

        self.assertEqual(response.status_code, 200)

        form = response.context["form_ket_qua"]

        self.assertIsNotNone(form)
        self.assertIsNone(
            response.context["form_huy"],
        )
        self.assertEqual(
            list(form.fields),
            [
                "trang_thai",
                "ghi_chu",
            ],
        )

        gia_tri_trang_thai = [
            choice[0]
            for choice in (
                form.fields["trang_thai"].choices
            )
        ]

        self.assertEqual(
            gia_tri_trang_thai,
            [
                BuoiTapPT.TrangThai.HOAN_THANH,
                BuoiTapPT.TrangThai.VANG,
            ],
        )
        self.assertNotIn(
            BuoiTapPT.TrangThai.HUY,
            gia_tri_trang_thai,
        )

    def test_pt_khong_xem_duoc_buoi_cua_pt_khac(
        self
    ):
        buoi_tap = tao_buoi_tap_pt(
            dang_ky=self.dang_ky_pt_tuong_lai,
            huan_luyen_vien=self.pt_2,
            le_tan=self.le_tan,
            ngay_tap=self.hom_nay,
            gio_bat_dau=time(9, 0),
            gio_ket_thuc=time(10, 0),
        )

        self.client.force_login(
            self.pt_1.tai_khoan
        )

        response = self.client.get(
            reverse(
                "gym:chi_tiet_buoi_tap_pt",
                args=[buoi_tap.ma_buoi],
            )
        )

        self.assertEqual(response.status_code, 403)

    def test_admin_chi_duoc_xem_chi_tiet(
        self
    ):
        buoi_tap = tao_buoi_tap_pt(
            dang_ky=self.dang_ky_pt_tuong_lai,
            huan_luyen_vien=self.pt_1,
            le_tan=self.le_tan,
            ngay_tap=self.hom_nay,
            gio_bat_dau=time(9, 0),
            gio_ket_thuc=time(10, 0),
        )

        url = reverse(
            "gym:chi_tiet_buoi_tap_pt",
            args=[buoi_tap.ma_buoi],
        )

        self.client.force_login(self.admin)

        response_get = self.client.get(url)

        self.assertEqual(response_get.status_code, 200)
        self.assertIsNone(
            response_get.context["form_ket_qua"],
        )
        self.assertIsNone(
            response_get.context["form_huy"],
        )

        response_post = self.client.post(
            url,
            {
                "ly_do_huy": "Admin thử hủy",
            },
        )

        self.assertEqual(
            response_post.status_code,
            403,
        )

    def test_le_tan_xem_chi_tiet_va_co_form_huy(
        self
    ):
        buoi_tap = tao_buoi_tap_pt(
            dang_ky=self.dang_ky_pt_tuong_lai,
            huan_luyen_vien=self.pt_1,
            le_tan=self.le_tan,
            ngay_tap=self.hom_nay,
            gio_bat_dau=time(9, 0),
            gio_ket_thuc=time(10, 0),
        )

        self.client.force_login(
            self.le_tan.tai_khoan
        )

        response = self.client.get(
            reverse(
                "gym:chi_tiet_buoi_tap_pt",
                args=[buoi_tap.ma_buoi],
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertIsNone(
            response.context["form_ket_qua"],
        )
        self.assertEqual(
            list(response.context["form_huy"].fields),
            ["ly_do_huy"],
        )

    def test_pt_hoan_thanh_buoi_sau_gio_ket_thuc(
        self
    ):
        buoi_tap = tao_buoi_tap_pt(
            dang_ky=self.dang_ky_pt_tuong_lai,
            huan_luyen_vien=self.pt_1,
            le_tan=self.le_tan,
            ngay_tap=self.hom_nay,
            gio_bat_dau=time(9, 0),
            gio_ket_thuc=time(10, 0),
        )

        thoi_diem_hien_tai = timezone.make_aware(
            datetime.combine(
                self.hom_nay,
                time(10, 30),
            )
        )

        self.client.force_login(
            self.pt_1.tai_khoan
        )

        url = reverse(
            "gym:chi_tiet_buoi_tap_pt",
            args=[buoi_tap.ma_buoi],
        )

        with patch(
            "gym.services.buoi_tap_pt.timezone.now",
            return_value=thoi_diem_hien_tai,
        ):
            response = self.client.post(
                url,
                {
                    "trang_thai": (
                        BuoiTapPT.TrangThai.HOAN_THANH
                    ),
                    "ghi_chu": (
                        "Hoàn thành từ giao diện"
                    ),
                },
            )

        self.assertRedirects(response, url)

        buoi_tap.refresh_from_db()

        self.assertEqual(
            buoi_tap.trang_thai,
            BuoiTapPT.TrangThai.HOAN_THANH,
        )
        self.assertEqual(
            buoi_tap.ghi_chu,
            "Hoàn thành từ giao diện",
        )

        response_get = self.client.get(url)
        self.assertIsNone(
            response_get.context["form_ket_qua"],
        )

    def test_pt_khong_hoan_thanh_truoc_gio_ket_thuc(
        self
    ):
        buoi_tap = tao_buoi_tap_pt(
            dang_ky=self.dang_ky_pt_tuong_lai,
            huan_luyen_vien=self.pt_1,
            le_tan=self.le_tan,
            ngay_tap=self.hom_nay,
            gio_bat_dau=time(9, 0),
            gio_ket_thuc=time(10, 0),
        )

        thoi_diem_hien_tai = timezone.make_aware(
            datetime.combine(
                self.hom_nay,
                time(8, 0),
            )
        )

        self.client.force_login(
            self.pt_1.tai_khoan
        )

        url = reverse(
            "gym:chi_tiet_buoi_tap_pt",
            args=[buoi_tap.ma_buoi],
        )

        with patch(
            "gym.services.buoi_tap_pt.timezone.now",
            return_value=thoi_diem_hien_tai,
        ):
            response = self.client.post(
                url,
                {
                    "trang_thai": (
                        BuoiTapPT.TrangThai.HOAN_THANH
                    ),
                    "ghi_chu": "",
                },
            )

        self.assertEqual(response.status_code, 200)
        self.assertIn(
            "trang_thai",
            response.context["form_ket_qua"].errors,
        )

        buoi_tap.refresh_from_db()
        self.assertEqual(
            buoi_tap.trang_thai,
            BuoiTapPT.TrangThai.DA_LEN_LICH,
        )

    def test_pt_khong_duoc_gui_trang_thai_huy(
        self
    ):
        buoi_tap = tao_buoi_tap_pt(
            dang_ky=self.dang_ky_pt_tuong_lai,
            huan_luyen_vien=self.pt_1,
            le_tan=self.le_tan,
            ngay_tap=self.hom_nay,
            gio_bat_dau=time(9, 0),
            gio_ket_thuc=time(10, 0),
        )

        self.client.force_login(
            self.pt_1.tai_khoan
        )

        url = reverse(
            "gym:chi_tiet_buoi_tap_pt",
            args=[buoi_tap.ma_buoi],
        )

        response = self.client.post(
            url,
            {
                "trang_thai": BuoiTapPT.TrangThai.HUY,
                "ghi_chu": "PT thử tự hủy",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(
            "trang_thai",
            response.context[
                "form_ket_qua"
            ].errors,
        )

        buoi_tap.refresh_from_db()

        self.assertEqual(
            buoi_tap.trang_thai,
            BuoiTapPT.TrangThai.DA_LEN_LICH,
        )

    def test_le_tan_khac_huy_duoc_buoi_do_le_tan_khac_xep(
        self
    ):
        buoi_tap = tao_buoi_tap_pt(
            dang_ky=self.dang_ky_pt_tuong_lai,
            huan_luyen_vien=self.pt_1,
            le_tan=self.le_tan,
            ngay_tap=self.hom_nay,
            gio_bat_dau=time(9, 0),
            gio_ket_thuc=time(10, 0),
        )

        thoi_diem_hien_tai = timezone.make_aware(
            datetime.combine(
                self.hom_nay,
                time(8, 0),
            )
        )

        self.client.force_login(
            self.le_tan_2.tai_khoan
        )

        url = reverse(
            "gym:chi_tiet_buoi_tap_pt",
            args=[buoi_tap.ma_buoi],
        )

        with patch(
            "gym.services.buoi_tap_pt.timezone.now",
            return_value=thoi_diem_hien_tai,
        ):
            response = self.client.post(
                url,
                {
                    "ly_do_huy": (
                        "Hội viên yêu cầu hủy với ca sau"
                    ),
                },
            )

        self.assertRedirects(response, url)

        buoi_tap.refresh_from_db()

        self.assertEqual(
            buoi_tap.le_tan,
            self.le_tan,
        )
        self.assertEqual(
            buoi_tap.trang_thai,
            BuoiTapPT.TrangThai.HUY,
        )
        self.assertEqual(
            buoi_tap.ghi_chu,
            (
                f"Hủy bởi {self.le_tan_2.ma_lt}: "
                "Hội viên yêu cầu hủy với ca sau"
            ),
        )

        response_get = self.client.get(url)

        self.assertIsNone(
            response_get.context["form_huy"],
        )
        self.assertNotContains(
            response_get,
            "Buổi tập này đã được chốt trạng thái",
        )

    def test_le_tan_phai_nhap_ly_do_huy(
        self
    ):
        buoi_tap = tao_buoi_tap_pt(
            dang_ky=self.dang_ky_pt_tuong_lai,
            huan_luyen_vien=self.pt_1,
            le_tan=self.le_tan,
            ngay_tap=self.hom_nay,
            gio_bat_dau=time(9, 0),
            gio_ket_thuc=time(10, 0),
        )

        self.client.force_login(
            self.le_tan.tai_khoan
        )

        response = self.client.post(
            reverse(
                "gym:chi_tiet_buoi_tap_pt",
                args=[buoi_tap.ma_buoi],
            ),
            {
                "ly_do_huy": "",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(
            "ly_do_huy",
            response.context["form_huy"].errors,
        )

    def test_le_tan_khong_duoc_huy_tu_gio_bat_dau(
        self
    ):
        buoi_tap = tao_buoi_tap_pt(
            dang_ky=self.dang_ky_pt_tuong_lai,
            huan_luyen_vien=self.pt_1,
            le_tan=self.le_tan,
            ngay_tap=self.hom_nay,
            gio_bat_dau=time(9, 0),
            gio_ket_thuc=time(10, 0),
        )

        thoi_diem_hien_tai = timezone.make_aware(
            datetime.combine(
                self.hom_nay,
                time(9, 0),
            )
        )

        self.client.force_login(
            self.le_tan.tai_khoan
        )

        url = reverse(
            "gym:chi_tiet_buoi_tap_pt",
            args=[buoi_tap.ma_buoi],
        )

        with patch(
            "gym.services.buoi_tap_pt.timezone.now",
            return_value=thoi_diem_hien_tai,
        ):
            response = self.client.post(
                url,
                {
                    "ly_do_huy": "Yêu cầu quá muộn",
                },
            )

        self.assertEqual(response.status_code, 200)
        self.assertIn(
            "ly_do_huy",
            response.context["form_huy"].errors,
        )

        buoi_tap.refresh_from_db()

        self.assertEqual(
            buoi_tap.trang_thai,
            BuoiTapPT.TrangThai.DA_LEN_LICH,
        )

    def test_chon_hoi_vien_hien_form_xep_lich(
        self
    ):
        self.client.force_login(
            self.le_tan.tai_khoan
        )

        response = self.client.get(
            self.url_tao,
            {
                "hoi_vien": self.hoi_vien.pk,
            },
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            response.context["hoi_vien_da_chon"],
            self.hoi_vien,
        )

        self.assertEqual(
            response.context[
                "so_buoi_pt_cua_hoi_vien_da_chon"
            ],
            2,
        )

        self.assertEqual(
            response.context[
                "form"
            ]["hoi_vien"].value(),
            self.hoi_vien.pk,
        )

        self.assertContains(
            response,
            "Thông tin buổi tập PT",
        )
        self.assertContains(
            response,
            self.hoi_vien.ho_ten,
        )

    def test_tim_hoi_vien_xep_pt_theo_nhieu_thong_tin(
        self
    ):
        self.client.force_login(
            self.le_tan.tai_khoan
        )

        cac_tu_khoa = (
            self.hoi_vien.ma_hv,
            "kiểm thử lịch PT",
            "0981000005",
            "hoi.vien.buoi.pt@example.com",
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

                cac_hoi_vien = (
                    response.context[
                        "cac_hoi_vien"
                    ]
                )

                self.assertEqual(
                    len(cac_hoi_vien),
                    1,
                )
                self.assertEqual(
                    cac_hoi_vien[0][
                        "hoi_vien"
                    ],
                    self.hoi_vien,
                )

    def test_nhieu_dang_ky_pt_chi_hien_mot_dong_hoi_vien(
        self
    ):
        dang_ky_pt_thu_hai, _ = (
            tao_dang_ky_va_hoa_don(
                hoi_vien=self.hoi_vien,
                goi_tap=self.goi_pt,
                le_tan=self.le_tan,
                ngay_dang_ky=self.hom_nay,
                ngay_bat_dau=(
                    self.dang_ky_pt_tuong_lai
                    .ngay_ket_thuc
                    + timedelta(days=1)
                ),
                phuong_thuc_thanh_toan=(
                    HoaDon.PhuongThucThanhToan.TIEN_MAT
                ),
            )
        )

        self.client.force_login(
            self.le_tan.tai_khoan
        )

        response = self.client.get(
            self.url_tao
        )

        cac_hoi_vien = response.context[
            "cac_hoi_vien"
        ]

        self.assertEqual(
            len(cac_hoi_vien),
            1,
        )
        self.assertEqual(
            cac_hoi_vien[0]["hoi_vien"],
            self.hoi_vien,
        )

        self.assertEqual(
            cac_hoi_vien[0][
                "so_buoi_pt_co_the_xep"
            ],
            4,
        )

        self.assertContains(
            response,
            self.hoi_vien.ma_hv,
        )

        self.assertNotContains(
            response,
            self.dang_ky_pt_tuong_lai.ma_dk,
        )
        self.assertNotContains(
            response,
            dang_ky_pt_thu_hai.ma_dk,
        )