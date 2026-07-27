from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel


class ADSourceSnapshotCostResponse(BaseModel):
    id: str
    contentHash: str
    filename: Optional[str]
    status: str
    capturedAt: Optional[datetime]
    storageBytes: int
    rowCount: Optional[int]


class ADCoverageClientResponse(BaseModel):
    organizationId: str
    organizationName: str
    aircraftId: str
    nNumber: str
    triggeredCreation: bool
    linkedAt: datetime


class ADCoverageCostResponse(BaseModel):
    id: str
    status: str
    coverageVersion: str
    productType: str
    productSubtype: Optional[str]
    make: Optional[str]
    model: Optional[str]
    directiveCount: int
    sourceDocumentCount: int
    derivedLogicalStorageBytes: int
    sourceSnapshotId: Optional[str]
    sourceContentHash: Optional[str]
    lastBuiltAt: Optional[datetime]
    lastResolvedAt: Optional[datetime]
    actualCostUsd: Decimal
    allocatedCostUsd: Decimal
    clients: list[ADCoverageClientResponse]


class ADCostTotalsResponse(BaseModel):
    sharedSourceStorageBytes: int
    derivedLogicalStorageBytes: int
    actualCostUsd: Decimal
    allocatedCostUsd: Decimal
    coverageSetCount: int
    clientCount: int
    aircraftCount: int


class ADCostAdminSummaryResponse(BaseModel):
    generatedAt: datetime
    allocationPolicyStatus: str
    allocationPolicyVersion: Optional[str]
    billingActive: bool
    totals: ADCostTotalsResponse
    sourceSnapshots: list[ADSourceSnapshotCostResponse]
    coverages: list[ADCoverageCostResponse]
