import re

from django.db import IntegrityError, transaction
from django.test import TestCase

from accounts.models import TaiKhoan


class TaiKhoanModelTests(TestCase):
    def test_tao_tai_khoan_tu_sinh_ma_va_bam_mat_khau(self):
        tai_khoan = TaiKhoan.objects.create_user(
            username="kiem_thu_tai_khoan",
            password="1",
            vai_tro=TaiKhoan.VaiTro.LE_TAN,
        )

        self.assertTrue(
            re.fullmatch(r"TK\d+", tai_khoan.ma_tk)
        )
        self.assertEqual(
            tai_khoan.username,
            "kiem_thu_tai_khoan",
        )
        self.assertEqual(
            tai_khoan.vai_tro,
            TaiKhoan.VaiTro.LE_TAN,
        )
        self.assertNotEqual(tai_khoan.password, "1")
        self.assertTrue(tai_khoan.check_password("1"))
        self.assertTrue(tai_khoan.is_active)

    def test_nhieu_tai_khoan_co_ma_khac_nhau(self):
        tai_khoan_1 = TaiKhoan.objects.create_user(
            username="kiem_thu_1",
            password="1",
            vai_tro=TaiKhoan.VaiTro.HOI_VIEN,
        )

        tai_khoan_2 = TaiKhoan.objects.create_user(
            username="kiem_thu_2",
            password="1",
            vai_tro=TaiKhoan.VaiTro.PT,
        )

        self.assertNotEqual(
            tai_khoan_1.ma_tk,
            tai_khoan_2.ma_tk,
        )
        self.assertNotEqual(
            tai_khoan_1.username,
            tai_khoan_2.username,
        )

    def test_username_khong_duoc_trung(self):
        TaiKhoan.objects.create_user(
            username="username_trung",
            password="1",
            vai_tro=TaiKhoan.VaiTro.HOI_VIEN,
        )

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                TaiKhoan.objects.create_user(
                    username="username_trung",
                    password="1",
                    vai_tro=TaiKhoan.VaiTro.LE_TAN,
                )
