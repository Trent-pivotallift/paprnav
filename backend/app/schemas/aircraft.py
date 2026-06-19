from datetime import date
from typing import Optional

from pydantic import BaseModel, Field


class AircraftBase(BaseModel):
    nNumber: str = Field(min_length=2, max_length=32)
    make: str = Field(min_length=1, max_length=128)
    model: str = Field(min_length=1, max_length=128)
    serialNumber: Optional[str] = Field(default=None, max_length=128)
    year: Optional[int] = Field(default=None, ge=1900, le=2100)
    airframeSerialNumber: Optional[str] = Field(default=None, max_length=128)
    engineMake: Optional[str] = Field(default=None, max_length=128)
    engineModel: Optional[str] = Field(default=None, max_length=128)
    engineSerialNumber: Optional[str] = Field(default=None, max_length=128)
    propellerMake: Optional[str] = Field(default=None, max_length=128)
    propellerModel: Optional[str] = Field(default=None, max_length=128)
    propellerSerialNumber: Optional[str] = Field(default=None, max_length=128)


class AircraftCreateRequest(AircraftBase):
    pass


class AircraftUpdateRequest(BaseModel):
    nNumber: Optional[str] = Field(default=None, min_length=2, max_length=32)
    make: Optional[str] = Field(default=None, min_length=1, max_length=128)
    model: Optional[str] = Field(default=None, min_length=1, max_length=128)
    serialNumber: Optional[str] = Field(default=None, max_length=128)
    year: Optional[int] = Field(default=None, ge=1900, le=2100)
    airframeSerialNumber: Optional[str] = Field(default=None, max_length=128)
    engineMake: Optional[str] = Field(default=None, max_length=128)
    engineModel: Optional[str] = Field(default=None, max_length=128)
    engineSerialNumber: Optional[str] = Field(default=None, max_length=128)
    propellerMake: Optional[str] = Field(default=None, max_length=128)
    propellerModel: Optional[str] = Field(default=None, max_length=128)
    propellerSerialNumber: Optional[str] = Field(default=None, max_length=128)


class AircraftResponse(BaseModel):
    id: str
    nNumber: str
    nNumberNormalized: str
    make: str
    model: str
    serialNumber: Optional[str]
    year: Optional[int]
    airframeSerialNumber: Optional[str]
    engineMake: Optional[str]
    engineModel: Optional[str]
    engineSerialNumber: Optional[str]
    propellerMake: Optional[str]
    propellerModel: Optional[str]
    propellerSerialNumber: Optional[str]
    lastLogEntryDate: Optional[date]
    complianceStatus: str


class AircraftListResponse(BaseModel):
    aircraft: list[AircraftResponse]


class AircraftAssignmentCreateRequest(BaseModel):
    maintenanceUserEmail: str = Field(min_length=3, max_length=255)
    role: str = Field(default="maintainer", min_length=1, max_length=64)


class AircraftAssignmentResponse(BaseModel):
    id: str
    aircraftId: str
    organizationId: str
    organizationName: str
    organizationType: str
    role: str
    status: str


class AircraftAssignmentListResponse(BaseModel):
    assignments: list[AircraftAssignmentResponse]
