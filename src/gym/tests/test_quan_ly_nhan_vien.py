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
            "gym/nhan_vien/danh_sach_nhan_vien.html",
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
                        "gym/nhan_vien/"
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
                        "gym/nhan_vien/"
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
