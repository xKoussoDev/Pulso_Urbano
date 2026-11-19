from app.supabase_client import get_supabase_client


BUCKET = "report-photos"
MAX_BYTES = 5 * 1024 * 1024
MIME_TYPES = {"image/jpeg", "image/png"}


def main() -> None:
    storage = get_supabase_client().storage
    current = next((bucket for bucket in storage.list_buckets() if bucket.id == BUCKET), None)
    if current is None:
        storage.create_bucket(BUCKET, options={
            "public": False,
            "file_size_limit": MAX_BYTES,
            "allowed_mime_types": sorted(MIME_TYPES),
        })
        current = next((bucket for bucket in storage.list_buckets() if bucket.id == BUCKET), None)
    if current is None or current.public or current.file_size_limit != MAX_BYTES or set(current.allowed_mime_types or []) != MIME_TYPES:
        raise RuntimeError("El bucket report-photos no tiene la configuración privada esperada")
    print("Bucket report-photos privado y limitado a JPEG/PNG de 5 MB: OK")


if __name__ == "__main__":
    main()
