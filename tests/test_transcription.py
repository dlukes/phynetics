#!/usr/bin/env python3

import unittest as ut
import phynetics.cstrans as t

class TestPhoneticTranscription(ut.TestCase):

    def test_complex(self):
        """Test a lot of stuff at once.

        """
        ort = "hřích by za ty choutky stál leč dobře"
        fon_expected = "hříɣ bi za ti choutki stál leʒʒ dobře"
        fon_obtained = t.Transcription(ort).fon
        print("expected: ", fon_expected)
        print("obtained: ", fon_obtained)
        self.assertTrue(fon_expected == fon_obtained)

if __name__ == '__main__':
    ut.main()
