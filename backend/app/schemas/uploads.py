from pydantic import BaseModel


class UploadResponse(BaseModel):
    id: str
    aircraftId: str
    originalFilename: str
    contentType: str
    fileSizeBytes: int
    sha256: str
    status: str
    downloadUrl: str


class UploadCreateResponse(BaseModel):
    upload: UploadResponse
