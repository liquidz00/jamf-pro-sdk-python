get_computer_inventory_v1_allowed_sections = [
    "ALL",
    "GENERAL",
    "DISK_ENCRYPTION",
    "PURCHASING",
    "APPLICATIONS",
    "STORAGE",
    "USER_AND_LOCATION",
    "CONFIGURATION_PROFILES",
    "PRINTERS",
    "SERVICES",
    "HARDWARE",
    "LOCAL_USER_ACCOUNTS",
    "CERTIFICATES",
    "ATTACHMENTS",
    "PLUGINS",
    "PACKAGE_RECEIPTS",
    "FONTS",
    "SECURITY",
    "OPERATING_SYSTEM",
    "LICENSED_SOFTWARE",
    "IBEACONS",
    "SOFTWARE_UPDATES",
    "EXTENSION_ATTRIBUTES",
    "CONTENT_CACHING",
    "GROUP_MEMBERSHIPS",
]

get_computer_inventory_v1_allowed_sort_fields = [
    "general.name",
    "udid",
    "id",
    "general.assetTag",
    "general.jamfBinaryVersion",
    "general.lastContactTime",
    "general.lastEnrolledDate",
    "general.lastCloudBackupDate",
    "general.reportDate",
    "general.remoteManagement.managementUsername",
    "general.mdmCertificateExpiration",
    "general.platform",
    "hardware.make",
    "hardware.model",
    "operatingSystem.build",
    "operatingSystem.supplementalBuildVersion",
    "operatingSystem.rapidSecurityResponse",
    "operatingSystem.name",
    "operatingSystem.version",
    "userAndLocation.realname",
    "purchasing.lifeExpectancy",
    "purchasing.warrantyDate",
]

get_computer_inventory_v1_allowed_filter_fields = [
    "general.name",
    "udid",
    "id",
    "general.assetTag",
    "general.barcode1",
    "general.barcode2",
    "general.enrolledViaAutomatedDeviceEnrollment",
    "general.lastIpAddress",
    "general.itunesStoreAccountActive",
    "general.jamfBinaryVersion",
    "general.lastContactTime",
    "general.lastEnrolledDate",
    "general.lastCloudBackupDate",
    "general.reportDate",
    "general.lastReportedIp",
    "general.remoteManagement.managed",
    "general.remoteManagement.managementUsername",
    "general.mdmCapable.capable",
    "general.mdmCertificateExpiration",
    "general.platform",
    "general.supervised",
    "general.userApprovedMdm",
    "general.declarativeDeviceManagementEnabled",
    "hardware.bleCapable",
    "hardware.macAddress",
    "hardware.make",
    "hardware.model",
    "hardware.modelIdentifier",
    "hardware.serialNumber",
    "hardware.supportsIosAppInstalls,hardware.isAppleSilicon",
    "operatingSystem.activeDirectoryStatus",
    "operatingSystem.fileVault2Status",
    "operatingSystem.build",
    "operatingSystem.supplementalBuildVersion",
    "operatingSystem.rapidSecurityResponse",
    "operatingSystem.name",
    "operatingSystem.version",
    "operatingSystem.softwareUpdateDeviceId",
    "security.activationLockEnabled",
    "security.recoveryLockEnabled,security.firewallEnabled,userAndLocation.buildingId",
    "userAndLocation.departmentId",
    "userAndLocation.email",
    "userAndLocation.realname",
    "userAndLocation.phone",
    "userAndLocation.position,userAndLocation.room",
    "userAndLocation.username",
    "purchasing.appleCareId",
    "purchasing.lifeExpectancy",
    "purchasing.purchased",
    "purchasing.leased",
    "purchasing.vendor",
    "purchasing.warrantyDate",
]
