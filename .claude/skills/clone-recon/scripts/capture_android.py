#!/usr/bin/env python3
"""
capture_android.py — Captura una pantalla de una app Android via adb. Zero dependencias.

Guarda screenshot, dump crudo de uiautomator y arbol normalizado:
  <out>/<SID>.png  <out>/<SID>.raw.xml  <out>/<SID>.tree.json
y muestra por stdout el resumen del arbol.

Uso:
  python capture_android.py --id S03@vacio --out clone/captures/original
         [--serial SERIAL] [--adb RUTA] [--max-depth 25] [--no-redact] [--retries 3]

Exit: 0 ok, 1 captura parcial (sin arbol o pantalla negra), 2 error de entorno.
"""

import argparse
import json
import os
import re
import shutil
import struct
import subprocess
import sys
import time
import zlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import uitree  # noqa: E402

DUMP_PATH = "/sdcard/clone_dump.xml"
_ACTIVITY = re.compile(
    r"(?:topResumedActivity|mResumedActivity)[=:]\s*ActivityRecord\{\S+ \S+ (\S+)")


class CaptureError(Exception):
    """Error de entorno: adb, dispositivo o captura imposible."""


def default_run(cmd):
    proc = subprocess.run(cmd, capture_output=True)
    return proc.returncode, proc.stdout, proc.stderr


def find_adb(explicit=None, env=None, which=shutil.which, isfile=os.path.isfile):
    if explicit:
        return explicit
    env = os.environ if env is None else env
    found = which("adb")
    if found:
        return found
    exe = "adb.exe" if os.name == "nt" else "adb"
    candidates = []
    if env.get("ANDROID_HOME"):
        candidates.append(os.path.join(env["ANDROID_HOME"], "platform-tools", exe))
    if env.get("LOCALAPPDATA"):
        candidates.append(os.path.join(env["LOCALAPPDATA"], "Android", "Sdk",
                                       "platform-tools", exe))
    if env.get("HOME"):
        candidates.append(os.path.join(env["HOME"], "Android", "Sdk", "platform-tools", exe))
    for path in candidates:
        if isfile(path):
            return path
    return None


def list_devices(adb, run):
    code, out, err = run([adb, "devices"])
    if code != 0:
        raise CaptureError("adb devices fallo: %s" % err.decode("utf-8", "replace").strip())
    serials = []
    for line in out.decode("utf-8", "replace").splitlines()[1:]:
        parts = line.split()
        if len(parts) >= 2 and parts[1] == "device":
            serials.append(parts[0])
    return serials


def pick_serial(devices, serial=None):
    if serial:
        if serial not in devices:
            raise CaptureError("el dispositivo %s no esta conectado. Conectados: %s"
                               % (serial, ", ".join(devices) or "ninguno"))
        return serial
    if not devices:
        raise CaptureError("no hay dispositivos. Conecta uno con depuracion USB activa "
                           "y acepta la huella RSA en el telefono.")
    if len(devices) > 1:
        raise CaptureError("hay %d dispositivos: %s. Usa --serial."
                           % (len(devices), ", ".join(devices)))
    return devices[0]


def parse_raw_screencap(data):
    """Header de screencap crudo (12 o 16 bytes) + RGBA. Devuelve (w, h, pixels)."""
    if len(data) < 12:
        raise CaptureError("screencap devolvio %d bytes" % len(data))
    width, height, fmt = struct.unpack_from("<III", data, 0)
    header = len(data) - width * height * 4
    if fmt not in (1, 2) or header not in (12, 16):
        raise CaptureError("formato de screencap no soportado (formato %d)" % fmt)
    return width, height, data[header:]


def is_uniform(pixels):
    first = pixels[:4]
    return pixels == first * (len(pixels) // 4)


def encode_png(width, height, pixels):
    stride = width * 4
    raw = b"".join(b"\x00" + pixels[y * stride:(y + 1) * stride] for y in range(height))

    def chunk(kind, body):
        return (struct.pack(">I", len(body)) + kind + body
                + struct.pack(">I", zlib.crc32(kind + body) & 0xFFFFFFFF))

    ihdr = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", zlib.compress(raw, 6)) + chunk(b"IEND", b""))
