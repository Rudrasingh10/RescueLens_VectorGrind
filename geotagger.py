import io
from PIL import Image, ExifTags

def _to_deg(value):
    d, m, s = value
    return float(d) + float(m) / 60.0 + float(s) / 3600.0

def extract_gps(raw_bytes):
    """Reads real GPS coords from image EXIF. Returns (lat, lng) or None."""
    try:
        image = Image.open(io.BytesIO(raw_bytes))
        exif = image._getexif()
        if not exif:
            return None

        gps_info = None
        for tag_id, value in exif.items():
            if ExifTags.TAGS.get(tag_id, tag_id) == "GPSInfo":
                gps_info = value
                break
        if not gps_info:
            return None

        gps_data = {ExifTags.GPSTAGS.get(k, k): v for k, v in gps_info.items()}
        if "GPSLatitude" not in gps_data or "GPSLongitude" not in gps_data:
            return None

        lat = _to_deg(gps_data["GPSLatitude"])
        if gps_data.get("GPSLatitudeRef") == "S":
            lat = -lat
        lng = _to_deg(gps_data["GPSLongitude"])
        if gps_data.get("GPSLongitudeRef") == "W":
            lng = -lng

        return round(lat, 6), round(lng, 6)
    except Exception:
        return None