import unittest

AbstractQuota = __import__('crc-quota').AbstractQuota


class BytesUnitConversion(unittest.TestCase):
    """Test the conversion of bytes into human readable units"""

    def test_zero_bytes(self):
        """Test the conversion of zero bytes"""

        self.assertEqual('0.0 B', AbstractQuota.convert_size(0))

    def test_integer_conversion(self):
        """Test the conversion from bytes to known integer units"""

        inputs = (1, 2 ** 10, 2 ** 20, 2 ** 30, 2 ** 40, 2 ** 50, 2 ** 60, 2 ** 70, 2 ** 80)
        outputs = ('1.0 B', '1.0 KB', '1.0 MB', '1.0 GB', '1.0 TB', '1.0 PB', '1.0 EB', '1.0 ZB', '1.0 YB')

        for inp, oup in zip(inputs, outputs):
            self.assertEqual(oup, AbstractQuota.convert_size(inp))

    def test_non_integer_values(self):
        """Test the conversion from bytes to known non-integer units"""

        inputs = (5, 5.0E5, 5.0E7, 5.0E9, 5.0E12)
        outputs = ('5.0 B', '488.28 KB', '47.68 MB', '4.66 GB', '4.55 TB')

        for inp, oup in zip(inputs, outputs):
            self.assertEqual(oup, AbstractQuota.convert_size(inp))


if __name__ == '__main__':
    unittest.main()
