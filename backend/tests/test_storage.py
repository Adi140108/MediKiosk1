import os
import sys
import pytest

# Ensure backend path is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.modules.documents.cloudinary import CloudinaryStorageProvider
from app.modules.documents.backblaze import BackblazeB2StorageProvider
from app.modules.documents.firestore_service import FirestoreDocumentService
from app.modules.documents.storage_service import StorageService
from app.modules.documents.models import DocumentMetadata

# 1. Cloudinary configuration
def test_cloudinary_configuration():
    provider = CloudinaryStorageProvider(
        cloud_name="test_cloud",
        api_key="123456789",
        api_secret="secret123",
        folder="MediKiosk"
    )
    assert provider.cloud_name == "test_cloud"
    assert provider.api_key == "123456789"
    assert provider.api_secret == "secret123"
    assert provider.folder == "MediKiosk"

# 2. Cloudinary upload
def test_cloudinary_upload(mocker):
    mock_upload = mocker.patch("cloudinary.uploader.upload", return_value={
        "asset_id": "asset_123",
        "public_id": "MediKiosk/patient_photo_1",
        "secure_url": "https://res.cloudinary.com/test_cloud/image/upload/v1/MediKiosk/patient_photo_1.jpg",
        "resource_type": "image",
        "format": "jpg",
        "bytes": 1024
    })

    provider = CloudinaryStorageProvider(
        cloud_name="test_cloud",
        api_key="123456789",
        api_secret="secret123"
    )
    res = provider.upload_file(b"fake_image_bytes", "photo.jpg", "image/jpeg", folder_or_prefix="profile")

    mock_upload.assert_called_once()
    assert res["asset_id"] == "asset_123"
    assert res["public_id"] == "MediKiosk/patient_photo_1"
    assert res["secure_url"].startswith("https://res.cloudinary.com")
    assert res["resource_type"] == "image"

# 3. Backblaze connection
def test_backblaze_connection(mocker):
    mock_boto_client = mocker.patch("boto3.client")
    mock_s3_instance = mocker.MagicMock()
    mock_boto_client.return_value = mock_s3_instance
    mock_s3_instance.head_bucket.return_value = {}

    provider = BackblazeB2StorageProvider(
        key_id="005c17d83b1dd8a0000000001",
        application_key="K005E5VDl1vEf2pW7kQwU38VoO1G/jE",
        bucket_name="medikiosk-documents"
    )

    healthy, msg = provider.health_check()
    assert healthy is True
    assert "passed" in msg
    mock_s3_instance.head_bucket.assert_called_once_with(Bucket="medikiosk-documents")

# 4. Backblaze upload
def test_backblaze_upload(mocker):
    mock_boto_client = mocker.patch("boto3.client")
    mock_s3_instance = mocker.MagicMock()
    mock_boto_client.return_value = mock_s3_instance

    provider = BackblazeB2StorageProvider(
        key_id="005c17d83b1dd8a0000000001",
        application_key="K005E5VDl1vEf2pW7kQwU38VoO1G/jE",
        bucket_name="medikiosk-documents"
    )

    res = provider.upload_file(b"pdf_binary_content", "blood_report.pdf", "application/pdf", folder_or_prefix="reports")

    mock_s3_instance.put_object.assert_called_once()
    call_args = mock_s3_instance.put_object.call_args[1]
    
    assert call_args["Bucket"] == "medikiosk-documents"
    assert call_args["ContentType"] == "application/pdf"
    # Ensure no PII/PHI (like ABHA ID or patient name) in object key
    assert "blood_report" not in call_args["Key"]
    assert "ABHA" not in call_args["Key"]
    assert call_args["Key"].startswith("reports/")
    assert res["object_key"] == call_args["Key"]

# 5. Private document retrieval
def test_private_document_retrieval(mocker):
    mock_boto_client = mocker.patch("boto3.client")
    mock_s3_instance = mocker.MagicMock()
    mock_boto_client.return_value = mock_s3_instance
    mock_s3_instance.generate_presigned_url.return_value = "https://s3.us-west-005.backblazeb2.com/medikiosk-documents/reports/abc.pdf?token=secret_signed_token"

    provider = BackblazeB2StorageProvider(
        key_id="005c17d83b1dd8a0000000001",
        application_key="K005E5VDl1vEf2pW7kQwU38VoO1G/jE",
        bucket_name="medikiosk-documents"
    )

    url = provider.generate_signed_url("reports/abc.pdf", expires_in_seconds=1800)

    mock_s3_instance.generate_presigned_url.assert_called_once_with(
        "get_object",
        Params={"Bucket": "medikiosk-documents", "Key": "reports/abc.pdf"},
        ExpiresIn=1800
    )
    assert "token=secret_signed_token" in url

# 6. Storage metadata persistence
def test_storage_metadata_persistence(mocker):
    mock_firestore_cls = mocker.patch("google.cloud.firestore.Client")
    mock_firestore_instance = mocker.MagicMock()
    mock_firestore_cls.return_value = mock_firestore_instance

    mock_doc_ref = mocker.MagicMock()
    mock_firestore_instance.collection.return_value.document.return_value = mock_doc_ref

    firestore_svc = FirestoreDocumentService(project_id="medikiosk1-cefd5", client=mock_firestore_instance)

    metadata = DocumentMetadata(
        document_id="doc_999",
        patient_id="ABHA123456",
        session_id="sess_001",
        storage_provider="backblaze_b2",
        storage_key="reports/uuid123.pdf",
        original_filename="lab_result.pdf",
        content_type="application/pdf",
        file_size=2048,
        document_type="lab_report",
        created_by="dr_smith"
    )

    saved_dict = firestore_svc.save_document_metadata(metadata)

    mock_firestore_instance.collection.assert_called_with("documents")
    mock_doc_ref.set.assert_called_once()
    assert saved_dict["document_id"] == "doc_999"
    assert saved_dict["patient_id"] == "ABHA123456"
    assert saved_dict["storage_provider"] == "backblaze_b2"
    assert saved_dict["storage_key"] == "reports/uuid123.pdf"

# 7. Invalid credentials
def test_invalid_credentials():
    cloud_provider = CloudinaryStorageProvider(cloud_name="", api_key="", api_secret="")
    healthy, msg = cloud_provider.health_check()
    assert healthy is False
    assert "incomplete" in msg

    with pytest.raises(ValueError, match="credentials are not configured"):
        cloud_provider.upload_file(b"test", "test.jpg", "image/jpeg")

    b2_provider = BackblazeB2StorageProvider(key_id="", application_key="")
    healthy, msg = b2_provider.health_check()
    assert healthy is False
    assert "incomplete" in msg

    with pytest.raises(ValueError, match="credentials are not configured"):
        b2_provider.upload_file(b"test", "test.pdf", "application/pdf")

# 8. Provider failure
def test_provider_failure(mocker):
    mocker.patch("cloudinary.uploader.upload", side_effect=Exception("API limit exceeded"))
    cloud_provider = CloudinaryStorageProvider(cloud_name="c", api_key="k", api_secret="s")

    with pytest.raises(RuntimeError, match="Cloudinary upload failed: API limit exceeded"):
        cloud_provider.upload_file(b"image_bytes", "img.jpg", "image/jpeg")

    mock_boto_client = mocker.patch("boto3.client")
    mock_s3_instance = mocker.MagicMock()
    mock_boto_client.return_value = mock_s3_instance
    mock_s3_instance.put_object.side_effect = Exception("Network connection timeout")

    b2_provider = BackblazeB2StorageProvider(key_id="k", application_key="s", bucket_name="b")
    with pytest.raises(RuntimeError, match="Backblaze B2 upload failed: Network connection timeout"):
        b2_provider.upload_file(b"doc_bytes", "doc.pdf", "application/pdf")

# 9. File type validation
def test_file_type_validation():
    mock_cloudinary = pytest.importorskip("unittest.mock").MagicMock()
    mock_backblaze = pytest.importorskip("unittest.mock").MagicMock()
    mock_firestore = pytest.importorskip("unittest.mock").MagicMock()

    service = StorageService(
        cloudinary_provider=mock_cloudinary,
        backblaze_provider=mock_backblaze,
        firestore_service=mock_firestore
    )

    # Valid image -> cloudinary
    assert service.validate_file(b"fake_image", "photo.png", "image/png") == "cloudinary"
    # Valid pdf -> backblaze_b2
    assert service.validate_file(b"fake_pdf", "report.pdf", "application/pdf") == "backblaze_b2"

    # Unsupported file type -> executable/zip
    with pytest.raises(ValueError, match="Unsupported file type"):
        service.validate_file(b"fake_exe", "malware.exe", "application/x-msdownload")

# 10. File size validation
def test_file_size_validation(mocker):
    service = StorageService(
        cloudinary_provider=mocker.MagicMock(),
        backblaze_provider=mocker.MagicMock(),
        firestore_service=mocker.MagicMock()
    )

    # Image size exceeding limit (e.g., 11 MB)
    large_image = b"x" * (11 * 1024 * 1024)
    with pytest.raises(ValueError, match="exceeds maximum limit"):
        service.validate_file(large_image, "huge.jpg", "image/jpeg")

    # Document size exceeding limit (e.g., 26 MB)
    large_doc = b"x" * (26 * 1024 * 1024)
    with pytest.raises(ValueError, match="exceeds maximum limit"):
        service.validate_file(large_doc, "huge.pdf", "application/pdf")
