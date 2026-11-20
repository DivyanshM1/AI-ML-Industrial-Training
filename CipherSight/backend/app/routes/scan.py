
import stat
import tempfile
import zipfile

from pathlib import Path, PurePosixPath

from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel

from app.scanner.directory_scanner import scan_directory
from app.scanner.report_engine import build_report


router = APIRouter(
    prefix="/scan",
    tags=["Security Scanning"],
)

BACKEND_ROOT = Path(__file__).resolve().parents[2]
ALLOWED_SCAN_ROOT = (BACKEND_ROOT / "sample_code").resolve()

MAX_ARCHIVE_SIZE = 25 * 1024 * 1024
MAX_EXTRACTED_SIZE = 100 * 1024 * 1024
MAX_FILES = 1000
MAX_SINGLE_FILE_SIZE = 10 * 1024 * 1024
CHUNK_SIZE = 64 * 1024


class ScanRequest(BaseModel):
    directory: str = "sample_code"


def safe_extract_zip(archive: zipfile.ZipFile, destination: Path):
    """
    Validate and safely extract a ZIP archive.

    Protections:
    - Path traversal
    - Absolute paths and Windows path syntax
    - Symbolic links and special filesystem entries
    - Duplicate and case-insensitive path collisions
    - File/directory conflicts
    - Encrypted entries
    - Excessive entry counts
    - Oversized files and archives
    - Excessive compression ratios
    - Actual extracted-size enforcement
    """

    entries = archive.infolist()

    if not entries:
        raise ValueError("ZIP archive contains no entries.")

    if len(entries) > MAX_FILES:
        raise ValueError("Archive contains too many entries.")

    destination = destination.resolve()

    validated_entries = []
    entry_types = {}
    declared_total_size = 0

    for entry in entries:
        name = entry.filename

        if (
            not name
            or "\x00" in name
            or "\\" in name
            or ":" in name
        ):
            raise ValueError("Archive contains an invalid file path.")

        relative_path = PurePosixPath(name)

        if (
            relative_path.is_absolute()
            or ".." in relative_path.parts
            or not relative_path.parts
        ):
            raise ValueError("Archive contains an unsafe file path.")

        if entry.flag_bits & 0x1:
            raise ValueError("Encrypted ZIP entries are not supported.")

        mode = entry.external_attr >> 16
        file_type = stat.S_IFMT(mode)

        is_directory = entry.is_dir()

        if file_type not in (0, stat.S_IFREG, stat.S_IFDIR):
            raise ValueError(
                "Archive contains an unsupported filesystem entry."
            )

        if file_type == stat.S_IFDIR and not is_directory:
            raise ValueError("Archive contains an invalid directory entry.")

        if file_type == stat.S_IFREG and is_directory:
            raise ValueError("Archive contains an invalid file entry.")

        if entry.file_size > MAX_SINGLE_FILE_SIZE:
            raise ValueError("An archive file exceeds the 10 MB limit.")

        if entry.file_size < 0 or entry.compress_size < 0:
            raise ValueError("Archive contains invalid file metadata.")

        if entry.file_size > 0 and entry.compress_size == 0:
            raise ValueError("Archive contains an invalid compressed file.")

        if (
            entry.compress_size > 0
            and entry.file_size / entry.compress_size > 200
        ):
            raise ValueError("Archive compression ratio is too high.")

        declared_total_size += entry.file_size

        if declared_total_size > MAX_EXTRACTED_SIZE:
            raise ValueError("Extracted archive exceeds the 100 MB limit.")

        target = (
            destination / Path(*relative_path.parts)
        ).resolve()

        try:
            target.relative_to(destination)
        except ValueError:
            raise ValueError("Archive contains an unsafe extraction path.")

        relative_key = target.relative_to(destination).as_posix().casefold()

        if relative_key in entry_types:
            raise ValueError(
                "Archive contains duplicate or conflicting file paths."
            )

        entry_types[relative_key] = "directory" if is_directory else "file"

        validated_entries.append((entry, target, relative_key, is_directory))

    # Reject file/directory conflicts, including conflicts with parent paths.
    for _, _, relative_key, is_directory in validated_entries:
        parts = relative_key.split("/")

        for index in range(1, len(parts)):
            parent_key = "/".join(parts[:index])

            if entry_types.get(parent_key) == "file":
                raise ValueError(
                    "Archive contains conflicting file and directory paths."
                )

        if not is_directory:
            prefix = relative_key + "/"

            if any(key.startswith(prefix) for key in entry_types):
                raise ValueError(
                    "Archive contains conflicting file and directory paths."
                )

    # Extract only after all entries have passed validation.
    actual_total_size = 0

    for entry, target, _, is_directory in validated_entries:
        if is_directory:
            target.mkdir(parents=True, exist_ok=True)
            continue

        target.parent.mkdir(parents=True, exist_ok=True)

        actual_file_size = 0

        with archive.open(entry, "r") as source:
            with target.open("xb") as output:
                while True:
                    chunk = source.read(CHUNK_SIZE)

                    if not chunk:
                        break

                    actual_file_size += len(chunk)
                    actual_total_size += len(chunk)

                    if actual_file_size > MAX_SINGLE_FILE_SIZE:
                        raise ValueError(
                            "An extracted file exceeds the 10 MB limit."
                        )

                    if actual_file_size > entry.file_size:
                        raise ValueError(
                            "Archive file exceeds its declared size."
                        )

                    if actual_total_size > MAX_EXTRACTED_SIZE:
                        raise ValueError(
                            "Extracted archive exceeds the 100 MB limit."
                        )

                    output.write(chunk)

        if actual_file_size != entry.file_size:
            raise ValueError(
                "Archive file size does not match its declared size."
            )


@router.post("/")
def run_scan(request: ScanRequest):
    requested_path = Path(request.directory)

    if not requested_path.is_absolute():
        requested_path = BACKEND_ROOT / requested_path

    scan_path = requested_path.resolve()

    try:
        scan_path.relative_to(ALLOWED_SCAN_ROOT)
    except ValueError:
        raise HTTPException(
            status_code=403,
            detail="Scanning is restricted to the sample_code directory.",
        )

    if not scan_path.exists() or not scan_path.is_dir():
        raise HTTPException(
            status_code=400,
            detail="The requested scan directory does not exist.",
        )

    try:
        scan_results = scan_directory(scan_path)
        return build_report(scan_results)

    except (OSError, ValueError) as error:
        raise HTTPException(
            status_code=500,
            detail=f"Scan failed: {error}",
        )


@router.post("/upload")
async def scan_uploaded_project(file: UploadFile = File(...)):
    try:
        if (
            not file.filename
            or Path(file.filename).suffix.lower() != ".zip"
        ):
            raise HTTPException(
                status_code=400,
                detail="Only ZIP archives are supported.",
            )

        with tempfile.TemporaryDirectory(prefix="ciphersight_") as temp:
            temp_path = Path(temp)
            archive_path = temp_path / "upload.zip"
            extraction_path = temp_path / "project"

            extraction_path.mkdir()

            uploaded_size = 0

            with archive_path.open("wb") as output:
                while True:
                    chunk = await file.read(CHUNK_SIZE)

                    if not chunk:
                        break

                    uploaded_size += len(chunk)

                    if uploaded_size > MAX_ARCHIVE_SIZE:
                        raise HTTPException(
                            status_code=413,
                            detail="ZIP archive exceeds the 25 MB upload limit.",
                        )

                    output.write(chunk)

            if uploaded_size == 0:
                raise HTTPException(
                    status_code=400,
                    detail="Uploaded archive is empty.",
                )

            if not zipfile.is_zipfile(archive_path):
                raise HTTPException(
                    status_code=400,
                    detail="Uploaded file is not a valid ZIP archive.",
                )

            with zipfile.ZipFile(archive_path) as archive:
                safe_extract_zip(archive, extraction_path)

            scan_results = scan_directory(extraction_path)
            report = build_report(scan_results)

            report["project"] = Path(file.filename).stem

            return report

    except HTTPException:
        raise

    except (zipfile.BadZipFile, zipfile.LargeZipFile):
        raise HTTPException(
            status_code=400,
            detail="Invalid or unsupported ZIP archive.",
        )

    except (ValueError, NotImplementedError, RuntimeError) as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )

    except OSError:
        raise HTTPException(
            status_code=500,
            detail="An error occurred while processing the uploaded project.",
        )

    finally:
        await file.close()
