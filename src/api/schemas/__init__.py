"""
API Schemas module - API şemaları

Bu modül tüm API şemalarını içerir:
- Auth schemas
- User schemas
- Config schemas
- Server schemas
- Monitor schemas
- Log schemas
- Response schemas
"""

from .auth_schemas import (
    LoginRequest, LoginResponse, LogoutRequest, LogoutResponse,
    RefreshTokenRequest, RefreshTokenResponse, VerifyTokenResponse,
    ForgotPasswordRequest, ForgotPasswordResponse,
    ResetPasswordRequest, ResetPasswordResponse
)

from .user_schemas import (
    UserBase, UserCreate, UserUpdate, UserResponse, UserListResponse,
    UserProfile, UserProfileUpdate, UserPasswordChange,
    UserRoleAssign, UserRoleResponse
)

from .config_schemas import (
    ConfigBase, ConfigCreate, ConfigUpdate, ConfigResponse,
    ConfigListResponse, ConfigCategoryResponse
)

from .server_schemas import (
    ServerStatusResponse, ServerConfigRequest, ServerConfigResponse,
    ServerStartResponse, ServerStopResponse, ServerRestartResponse
)

from .monitor_schemas import (
    SystemMetricsResponse, DatabaseMetricsResponse, ApiMetricsResponse,
    AlertResponse, AlertListResponse, AlertResolveRequest
)

from .log_schemas import (
    LogEntry, LogListResponse, LogExportRequest, LogExportResponse,
    LogStatsResponse
)

from .response_schemas import (
    BaseResponse, SuccessResponse, ErrorResponse, PaginationResponse,
    ValidationErrorResponse
)

__all__ = [
    # Auth schemas
    "LoginRequest", "LoginResponse", "LogoutRequest", "LogoutResponse",
    "RefreshTokenRequest", "RefreshTokenResponse", "VerifyTokenResponse",
    "ForgotPasswordRequest", "ForgotPasswordResponse",
    "ResetPasswordRequest", "ResetPasswordResponse",
    
    # User schemas
    "UserBase", "UserCreate", "UserUpdate", "UserResponse", "UserListResponse",
    "UserProfile", "UserProfileUpdate", "UserPasswordChange",
    "UserRoleAssign", "UserRoleResponse",
    
    # Config schemas
    "ConfigBase", "ConfigCreate", "ConfigUpdate", "ConfigResponse",
    "ConfigListResponse", "ConfigCategoryResponse",
    
    # Server schemas
    "ServerStatusResponse", "ServerConfigRequest", "ServerConfigResponse",
    "ServerStartResponse", "ServerStopResponse", "ServerRestartResponse",
    
    # Monitor schemas
    "SystemMetricsResponse", "DatabaseMetricsResponse", "ApiMetricsResponse",
    "AlertResponse", "AlertListResponse", "AlertResolveRequest",
    
    # Log schemas
    "LogEntry", "LogListResponse", "LogExportRequest", "LogExportResponse",
    "LogStatsResponse",
    
    # Response schemas
    "BaseResponse", "SuccessResponse", "ErrorResponse", "PaginationResponse",
    "ValidationErrorResponse"
]
