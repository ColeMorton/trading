"""
API Versioning Infrastructure

This module provides version management, deprecation warnings,
and migration support for the Trading API.
"""

import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union
from enum import Enum
from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.routing import APIRoute
from pydantic import BaseModel


class APIVersion(Enum):
    """Supported API versions."""
    V1 = "v1"
    # Future versions would be added here
    # V2 = "v2"


class VersionStatus(Enum):
    """Version lifecycle status."""
    CURRENT = "current"
    DEPRECATED = "deprecated" 
    SUNSET = "sunset"


class VersionInfo(BaseModel):
    """Information about an API version."""
    version: APIVersion
    status: VersionStatus
    introduced: datetime
    deprecated_date: Optional[datetime] = None
    sunset_date: Optional[datetime] = None
    migration_guide_url: Optional[str] = None


class APIVersionManager:
    """Manages API versioning, deprecation, and migration."""
    
    def __init__(self):
        self.versions: Dict[APIVersion, VersionInfo] = {
            APIVersion.V1: VersionInfo(
                version=APIVersion.V1,
                status=VersionStatus.CURRENT,
                introduced=datetime(2025, 6, 3),
                migration_guide_url="/docs/api/migration/v1"
            )
        }
        self.default_version = APIVersion.V1
    
    def get_version_info(self, version: Union[str, APIVersion]) -> VersionInfo:
        """Get information about a specific version."""
        if isinstance(version, str):
            try:
                version = APIVersion(version)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Unsupported API version: {version}"
                )
        
        if version not in self.versions:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown API version: {version.value}"
            )
        
        return self.versions[version]
    
    def is_version_supported(self, version: Union[str, APIVersion]) -> bool:
        """Check if a version is still supported."""
        try:
            info = self.get_version_info(version)
            return info.status != VersionStatus.SUNSET
        except HTTPException:
            return False
    
    def get_version_from_request(self, request: Request) -> APIVersion:
        """Extract API version from request headers or path."""
        # Try to get version from Accept header
        accept_header = request.headers.get("Accept", "")
        if "application/vnd.trading-api" in accept_header:
            for version in APIVersion:
                if f"version={version.value}" in accept_header:
                    return version
        
        # Try to get version from custom header
        version_header = request.headers.get("API-Version", "")
        if version_header:
            try:
                return APIVersion(version_header)
            except ValueError:
                pass
        
        # Try to get version from path
        path_parts = request.url.path.split("/")
        if len(path_parts) >= 3 and path_parts[1] == "api":
            try:
                return APIVersion(path_parts[2])
            except ValueError:
                pass
        
        # Return default version
        return self.default_version
    
    def add_deprecation_headers(self, response: Response, version: APIVersion) -> None:
        """Add deprecation headers to response if version is deprecated."""
        info = self.get_version_info(version)
        
        if info.status == VersionStatus.DEPRECATED:
            response.headers["Deprecation"] = "true"
            if info.sunset_date:
                response.headers["Sunset"] = info.sunset_date.isoformat()
            if info.migration_guide_url:
                response.headers["Link"] = f'<{info.migration_guide_url}>; rel="deprecation"'
    
    def deprecate_version(
        self, 
        version: APIVersion, 
        sunset_date: Optional[datetime] = None,
        migration_guide_url: Optional[str] = None
    ) -> None:
        """Mark a version as deprecated."""
        if version not in self.versions:
            raise ValueError(f"Version {version.value} not found")
        
        self.versions[version].status = VersionStatus.DEPRECATED
        self.versions[version].deprecated_date = datetime.utcnow()
        
        if sunset_date:
            self.versions[version].sunset_date = sunset_date
        
        if migration_guide_url:
            self.versions[version].migration_guide_url = migration_guide_url
    
    def sunset_version(self, version: APIVersion) -> None:
        """Mark a version as sunset (no longer supported)."""
        if version not in self.versions:
            raise ValueError(f"Version {version.value} not found")
        
        self.versions[version].status = VersionStatus.SUNSET
    
    def get_all_versions(self) -> List[VersionInfo]:
        """Get information about all API versions."""
        return list(self.versions.values())


# Global version manager instance
version_manager = APIVersionManager()


async def version_middleware(request: Request, call_next):
    """Middleware to handle API versioning."""
    version = version_manager.get_version_from_request(request)
    
    # Check if version is supported
    if not version_manager.is_version_supported(version):
        version_info = version_manager.get_version_info(version)
        raise HTTPException(
            status_code=410,  # Gone
            detail=f"API version {version.value} is no longer supported",
            headers={
                "Sunset": version_info.sunset_date.isoformat() if version_info.sunset_date else None
            }
        )
    
    # Add version info to request state
    request.state.api_version = version
    request.state.version_info = version_manager.get_version_info(version)
    
    # Process request
    response = await call_next(request)
    
    # Add version headers to response
    response.headers["API-Version"] = version.value
    version_manager.add_deprecation_headers(response, version)
    
    return response


def get_current_version(request: Request) -> APIVersion:
    """Get the current API version from request state."""
    return getattr(request.state, 'api_version', version_manager.default_version)


def get_version_info_from_request(request: Request) -> VersionInfo:
    """Get version info from request state."""
    return getattr(request.state, 'version_info', 
                  version_manager.get_version_info(version_manager.default_version))


class VersionedAPIRoute(APIRoute):
    """Custom API route that includes version information."""
    
    def __init__(self, *args, **kwargs):
        self.api_version = kwargs.pop('api_version', APIVersion.V1)
        super().__init__(*args, **kwargs)


def create_versioned_app(version: APIVersion) -> FastAPI:
    """Create a FastAPI app instance for a specific version."""
    version_info = version_manager.get_version_info(version)
    
    app = FastAPI(
        title=f"Trading API {version.value}",
        description=f"Trading API version {version.value}",
        version=version_info.introduced.strftime("%Y.%m.%d"),
        openapi_url=f"/api/{version.value}/openapi.json",
        docs_url=f"/api/{version.value}/docs",
        redoc_url=f"/api/{version.value}/redoc"
    )
    
    return app