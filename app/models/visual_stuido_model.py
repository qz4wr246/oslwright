from dataclasses import dataclass, field
from dataclasses_json import dataclass_json
from typing import Optional, List, Dict


@dataclass_json
@dataclass
class Catalog:
    buildBranch: str
    buildVersion: str
    id: str
    localBuild: str
    manifestName: str
    manifestType: str
    productDisplayVersion: str
    productLine: str
    productLineVersion: str
    productMilestone: str
    productMilestoneIsPreRelease: str
    productName: str
    productPatchVersion: str
    productPreReleaseMilestoneSuffix: str
    productSemanticVersion: str
    requiredEngineVersion: str
    featureReleaseMonth: str = field(default="")
    featureReleaseYear: str = field(default="")
    includeBuildVersionInDisplayVersion: str = field(default="")
    productRelease: str = field(default="")
    productReleaseNameSuffix: str = field(default="")


@dataclass_json
@dataclass
class Properties:
    appLocalWPF: str
    campaignId: str
    channelManifestId: str
    nickname: str
    setupEngineFilePath: str


@dataclass_json
@dataclass
class VisualStudioInstallation:
    instanceId: str
    installDate: str
    installationName: str
    installationPath: str
    installationVersion: str
    productId: str
    productPath: str
    state: int
    isComplete: bool
    isLaunchable: bool
    isPrerelease: bool
    isRebootRequired: bool
    displayName: str
    description: str
    channelId: str
    channelUri: str
    enginePath: str
    installedChannelId: str
    installedChannelUri: str
    releaseNotes: str
    resolvedInstallationPath: str
    thirdPartyNotices: str
    updateDate: str
    catalog: Catalog
    properties: Properties


@dataclass_json
@dataclass
class MsvcToolSet:
    name: str
    version: str
    default: bool = False


@dataclass_json
@dataclass
class VisualStuioInfomation:
    displayname: str
    description: str
    installationpath: str
    installationVersion: str
    generator: str
    msvc_toolset_versions: List[MsvcToolSet]
    msvc_toolset_version_default: Optional[MsvcToolSet]
    msvc_versions: Optional[Dict]
