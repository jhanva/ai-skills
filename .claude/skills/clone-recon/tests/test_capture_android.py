import io
import json
import os
import struct
import sys
import tempfile
import unittest
import zlib
from contextlib import redirect_stderr, redirect_stdout

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "scripts"))

import capture_android  # noqa: E402

FIXTURES = os.path.join(HERE, "fixtures")
ACTIVITY_LINE = (b"  topResumedActivity=ActivityRecord{1a2b3c u0 "
                 b"com.example.notes/.MainActivity t42}\n")


def raw_screencap(width, height, pixel=b"\x10\x20\x30\xff", varied=True, header=16):
    pixels = bytearray(pixel * (width * height))
    if varied:
        pixels[0:4] = b"\xff\xff\xff\xff"
    head = struct.pack("<III", width, height, 1)
    if header == 16:
        head += struct.pack("<I", 0)
    return head + bytes(pixels)


class FakeAdb:
    """Responde a los comandos de adb segun el escenario."""

    def __init__(self, devices=("emulator-5554",), dump_failures=0, screen=None):
        with open(os.path.join(FIXTURES, "android_basic.xml"), "rb") as fh:
            self.xml = fh.read()
        self.devices = devices
        self.dump_failures = dump_failures
        self.screen = screen if screen is not None else raw_screencap(4, 2)
        self.calls = []

    def __call__(self, cmd):
        self.calls.append(cmd)
        args = cmd[1:]
        if args == ["devices"]:
            body = "List of devices attached\n" + "".join(
                "%s\tdevice\n" % d for d in self.devices)
            return 0, body.encode(), b""
        if "uiautomator" in args:
            if self.dump_failures > 0:
                self.dump_failures -= 1
                return 1, b"", b"ERROR: could not get idle state.\n"
            return 0, b"UI hierchary dumped to: /sdcard/clone_dump.xml\n", b""
        if args[-2:] == ["cat", capture_android.DUMP_PATH]:
            return 0, self.xml, b""
        if args[-1] == "screencap":
            return 0, self.screen, b""
        if "dumpsys" in args:
            return 0, ACTIVITY_LINE, b""
        return 1, b"", b"comando inesperado"


def run_main(fake, out_dir, *extra):
    argv = ["--id", "S01", "--out", out_dir, "--adb", "adb"] + list(extra)
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = capture_android.main(argv, run=fake, sleep=lambda s: None)
    return code, out.getvalue(), err.getvalue()


class FindAdbTest(unittest.TestCase):
    def test_explicit_path_wins(self):
        self.assertEqual(capture_android.find_adb("C:/sdk/adb.exe", env={}), "C:/sdk/adb.exe")

    def test_android_home_is_searched(self):
        home = os.path.join("X", "sdk")
        expected = os.path.join(home, "platform-tools", "adb.exe" if os.name == "nt" else "adb")
        found = capture_android.find_adb(env={"ANDROID_HOME": home}, which=lambda n: None,
                                         isfile=lambda p: p == expected)
        self.assertEqual(found, expected)

    def test_missing_adb_returns_none(self):
        self.assertIsNone(capture_android.find_adb(env={}, which=lambda n: None,
                                                   isfile=lambda p: False))


class DeviceTest(unittest.TestCase):
    def test_list_devices_keeps_only_ready_devices(self):
        listing = b"List of devices attached\nemulator-5554\tdevice\nR58M\tunauthorized\n"
        devices = capture_android.list_devices("adb", lambda cmd: (0, listing, b""))
        self.assertEqual(devices, ["emulator-5554"])

    def test_single_device_is_picked_without_serial(self):
        self.assertEqual(capture_android.pick_serial(["emulator-5554"]), "emulator-5554")

    def test_two_devices_without_serial_raise(self):
        with self.assertRaisesRegex(capture_android.CaptureError, "Usa --serial"):
            capture_android.pick_serial(["aaa", "bbb"])

    def test_unknown_serial_raises(self):
        with self.assertRaisesRegex(capture_android.CaptureError, "no esta conectado"):
            capture_android.pick_serial(["aaa"], "zzz")


class ScreencapTest(unittest.TestCase):
    def test_parses_12_and_16_byte_headers(self):
        for header in (12, 16):
            w, h, pixels = capture_android.parse_raw_screencap(raw_screencap(4, 2, header=header))
            self.assertEqual((w, h, len(pixels)), (4, 2, 32))

    def test_unsupported_format_raises(self):
        data = struct.pack("<III", 2, 1, 4) + b"\x00" * 4
        with self.assertRaises(capture_android.CaptureError):
            capture_android.parse_raw_screencap(data)

    def test_encoded_png_roundtrips_pixels(self):
        pixels = bytes(range(32))
        png = capture_android.encode_png(4, 2, pixels)
        self.assertTrue(png.startswith(b"\x89PNG\r\n\x1a\n"))
        idat_len = struct.unpack(">I", png[33:37])[0]
        raw = zlib.decompress(png[41:41 + idat_len])
        self.assertEqual(raw, b"\x00" + pixels[:16] + b"\x00" + pixels[16:])


class SerialTest(unittest.TestCase):
    def test_two_devices_without_serial_exits_two(self):
        fake = FakeAdb(devices=("aaa", "bbb"))
        with tempfile.TemporaryDirectory() as tmp:
            code, _, err = run_main(fake, tmp)
        self.assertEqual(code, 2)
        self.assertIn("aaa, bbb", err)

    def test_serial_selects_device(self):
        fake = FakeAdb(devices=("aaa", "bbb"))
        with tempfile.TemporaryDirectory() as tmp:
            code, _, _ = run_main(fake, tmp, "--serial", "bbb")
        self.assertEqual(code, 0)
        self.assertIn(["adb", "-s", "bbb", "exec-out", "screencap"], fake.calls)

    def test_no_devices_exits_two(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, _, err = run_main(FakeAdb(devices=()), tmp)
        self.assertEqual(code, 2)
        self.assertIn("no hay dispositivos", err)


class CaptureTest(unittest.TestCase):
    def test_happy_path_writes_three_files_and_exits_zero(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, out, _ = run_main(FakeAdb(), tmp)
            self.assertEqual(code, 0)
            self.assertEqual(sorted(os.listdir(tmp)), ["S01.png", "S01.raw.xml", "S01.tree.json"])
            with open(os.path.join(tmp, "S01.tree.json"), encoding="utf-8") as fh:
                tree = json.load(fh)
        self.assertEqual(tree["source"], "com.example.notes/.MainActivity")
        self.assertEqual(tree["tree_quality"], "full")
        self.assertTrue(out.startswith("S01 android full com.example.notes/.MainActivity"))

    def test_dump_failing_every_retry_gives_quality_none_and_exit_one(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, _, err = run_main(FakeAdb(dump_failures=3), tmp)
            with open(os.path.join(tmp, "S01.tree.json"), encoding="utf-8") as fh:
                tree = json.load(fh)
            self.assertFalse(os.path.exists(os.path.join(tmp, "S01.raw.xml")))
        self.assertEqual(code, 1)
        self.assertEqual(tree["tree_quality"], "none")
        self.assertIn("uiautomator dump fallo 3 veces", err)

    def test_dump_recovers_on_second_try(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, _, _ = run_main(FakeAdb(dump_failures=1), tmp)
        self.assertEqual(code, 0)

    def test_uniform_screenshot_warns_and_exits_one(self):
        fake = FakeAdb(screen=raw_screencap(4, 2, b"\x00\x00\x00\xff", varied=False))
        with tempfile.TemporaryDirectory() as tmp:
            code, _, err = run_main(fake, tmp)
        self.assertEqual(code, 1)
        self.assertIn("un solo color", err)


if __name__ == "__main__":
    unittest.main()
