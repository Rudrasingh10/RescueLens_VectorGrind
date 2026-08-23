"""
Tests for geotagger.py + its integration into main.py's /api/analyze.

Run directly:  python3 test_geotagging.py
(Uses only Pillow — no piexif/exiftool required.)
"""
import io
from PIL import Image
from PIL.ExifTags import IFD

from geotagger import extract_gps


def _deg_to_dms_rational(value):
    """Convert a decimal degree float into the (deg,min,sec) rational tuple EXIF expects."""
    d = int(value)
    m_float = (value - d) * 60
    m = int(m_float)
    s = round((m_float - m) * 60, 4)
    return (d, m, s)


def make_jpeg_with_gps(lat, lng) -> bytes:
    """Build a real in-memory JPEG whose EXIF GPS IFD encodes (lat, lng)."""
    img = Image.new("RGB", (32, 32), color="red")

    exif = Image.Exif()
    gps_ifd = {
        1: "N" if lat >= 0 else "S",           
        2: _deg_to_dms_rational(abs(lat)),     
        3: "E" if lng >= 0 else "W",           
        4: _deg_to_dms_rational(abs(lng)),     
    }
    exif[34853] = gps_ifd  # GPSInfo tag

    buf = io.BytesIO()
    img.save(buf, format="JPEG", exif=exif)
    return buf.getvalue()


def make_jpeg_without_gps() -> bytes:
    img = Image.new("RGB", (32, 32), color="blue")
    buf = io.BytesIO()
    img.save(buf, format="JPEG")  # no exif at all
    return buf.getvalue()


def make_png_without_exif() -> bytes:
    img = Image.new("RGB", (32, 32), color="green")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def make_corrupt_bytes() -> bytes:
    return b"not a real image at all, just garbage bytes"


def run():
    results = []

    lat, lng = 21.251043, 81.628967
    raw = make_jpeg_with_gps(lat, lng)
    got = extract_gps(raw)
    ok = got is not None and abs(got[0] - lat) < 1e-4 and abs(got[1] - lng) < 1e-4
    results.append(("JPEG with GPS EXIF", ok, got))

    
    raw = make_jpeg_without_gps()
    got = extract_gps(raw)
    results.append(("JPEG without EXIF", got is None, got))

   
    raw = make_png_without_exif()
    got = extract_gps(raw)
    results.append(("PNG (no usable EXIF)", got is None, got))

    
    raw = make_corrupt_bytes()
    got = extract_gps(raw)
    results.append(("Corrupt/non-image bytes", got is None, got))

    
    lat, lng = -33.865143, -18.404100  # S / W
    raw = make_jpeg_with_gps(lat, lng)
    got = extract_gps(raw)
    ok = got is not None and got[0] < 0 and got[1] < 0
    results.append(("S/W hemisphere sign flip", ok, got))

    print(f"{'TEST':38} {'RESULT':6}  DETAIL")
    all_pass = True
    for name, passed, detail in results:
        all_pass &= passed
        print(f"{name:38} {'PASS' if passed else 'FAIL':6}  {detail}")

    print()
    print("ALL TESTS PASSED" if all_pass else "SOME TESTS FAILED")

    
    with open("/tmp/with_gps.jpg", "wb") as f:
        f.write(make_jpeg_with_gps(21.251043, 81.628967))
    with open("/tmp/without_gps.jpg", "wb") as f:
        f.write(make_jpeg_without_gps())
    print("\nSample files written: /tmp/with_gps.jpg, /tmp/without_gps.jpg")
    print("Integration test (with server running):")
    print('  curl -F "file=@/tmp/with_gps.jpg" http://localhost:8000/api/analyze | python3 -m json.tool')
    print('  curl -F "file=@/tmp/without_gps.jpg" http://localhost:8000/api/analyze | python3 -m json.tool')
    print('  -> first call: every event should have "geotag_source": "IMAGE_EXIF_GPS" and identical lat/lng')
    print('  -> second call: every event should have "geotag_source": "ESTIMATED"')


if __name__ == "__main__":
    run()