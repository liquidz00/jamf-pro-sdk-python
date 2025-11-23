from pydantic import ConfigDict

from .. import BaseModel


class Package(BaseModel):
    """Represents a full package record."""

    model_config = ConfigDict(extra="allow")

    id: str | None = None
    packageName: str | None = None
    fileName: str | None = None
    categoryId: str | None = None
    info: str | None = None
    notes: str | None = None
    priority: int | None = None
    osRequirements: str | None = None
    fillUserTemplate: bool | None = None
    indexed: bool | None = None
    fillExistingUsers: bool | None = None
    swu: bool | None = None
    rebootRequired: bool | None = None
    selfHealNotify: bool | None = None
    selfHealingAction: str | None = None
    osInstall: bool | None = None
    serialNumber: str | None = None
    parentPackageId: str | None = None
    basePath: str | None = None
    suppressUpdates: bool | None = None
    cloudTransferStatus: str | None = None
    ignoreConflicts: bool | None = None
    suppressFromDock: bool | None = None
    suppressEula: bool | None = None
    suppressRegistration: bool | None = None
    installLanguage: str | None = None
    md5: str | None = None
    sha256: str | None = None
    hashType: str | None = None
    hashValue: str | None = None
    size: str | None = None
    osInstallerVersion: str | None = None
    manifest: str | None = None
    manifestFileName: str | None = None
    format: str | None = None
