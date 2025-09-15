"""
Authentication service for user authentication and authorization.

This service handles user login, logout, token management, and password operations.
It integrates with the security system and session management.
"""

import bcrypt
import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from passlib.context import CryptContext

from .base_service import BaseService
from ..db.models import User, Session, Role, UserRole
from ..core.settings import settings
from ..core.constants import UserRole as UserRoleEnum
from ..utils.logger import logger


class AuthService(BaseService[User]):
    """
    Service for handling user authentication and authorization.
    
    This service provides methods for user login, logout, password management,
    and session handling with JWT token support.
    """
    
    def __init__(self):
        """Initialize the authentication service."""
        super().__init__(User)
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.jwt_secret = settings.security.jwt_secret_key
        self.jwt_algorithm = settings.security.jwt_algorithm
        self.access_token_expire_minutes = settings.security.jwt_access_token_expire_minutes
        self.refresh_token_expire_days = settings.security.jwt_refresh_token_expire_days
        self.password_hash_rounds = settings.security.bcrypt_rounds
    
    async def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """
        Authenticate a user with username and password.
        
        Args:
            username: The username to authenticate
            password: The plain text password
            
        Returns:
            The authenticated user or None if authentication failed
        """
        try:
            # Get user by username
            user = User.get_or_none(User.username == username)
            if not user:
                self.logger.warning(f"Authentication failed: User '{username}' not found")
                return None
            
            # Check if user is active
            if not user.is_active:
                self.logger.warning(f"Authentication failed: User '{username}' is inactive")
                return None
            
            # Verify password
            if not self.verify_password(password, user.password_hash):
                self.logger.warning(f"Authentication failed: Invalid password for user '{username}'")
                return None
            
            # Update last login
            user.last_login = datetime.now()
            user.save()
            
            self.logger.info(f"User '{username}' authenticated successfully")
            return user
            
        except Exception as e:
            self.logger.error(f"Authentication error for user '{username}': {e}")
            return None
    
    def authenticate_user_sync(self, username: str, password: str) -> Dict[str, Any]:
        """
        Synchronous version of authenticate_user for GUI usage.
        
        Args:
            username: The username to authenticate
            password: The plain text password
            
        Returns:
            Dictionary with success status and user data or error message
        """
        try:
            # Get user from database
            user = User.get_or_none(User.username == username, User.is_active == True)
            
            if not user:
                return {
                    'success': False,
                    'message': 'Invalid username or password'
                }
            
            # Verify password
            if not self.verify_password(password, user.password_hash):
                return {
                    'success': False,
                    'message': 'Invalid username or password'
                }
            
            # Update last login
            user.last_login = datetime.now()
            user.save()
            
            # Get user roles
            roles = [user_role.role.name for user_role in UserRole.select().where(
                UserRole.user == user, 
                UserRole.is_active == True
            )]
            
            # Return user data
            user_data = {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'full_name': user.full_name,
                'is_active': user.is_active,
                'is_verified': user.is_verified,
                'is_superuser': user.is_superuser,
                'roles': roles,
                'last_login': user.last_login.isoformat() if user.last_login else None
            }
            
            self.logger.info(f"User '{username}' authenticated successfully")
            return {
                'success': True,
                'user': user_data
            }
            
        except Exception as e:
            self.logger.error(f"Authentication error for user '{username}': {e}")
            return {
                'success': False,
                'message': 'Authentication failed'
            }
    
    async def create_session(self, user: User, ip_address: str = None, user_agent: str = None) -> Optional[Session]:
        """
        Create a new session for a user.
        
        Args:
            user: The user to create a session for
            ip_address: The client IP address
            user_agent: The client user agent
            
        Returns:
            The created session or None if creation failed
        """
        try:
            # Generate tokens
            access_token = self.create_access_token(user)
            refresh_token = self.create_refresh_token(user)
            
            # Calculate expiration time
            expires_at = datetime.now() + timedelta(minutes=self.access_token_expire_minutes)
            
            # Create session
            session = Session.create(
                user=user,
                token=access_token,
                refresh_token=refresh_token,
                ip_address=ip_address,
                user_agent=user_agent,
                expires_at=expires_at,
                is_active=True
            )
            
            self.logger.info(f"Session created for user '{user.username}'")
            return session
            
        except Exception as e:
            self.logger.error(f"Failed to create session for user '{user.username}': {e}")
            return None
    
    async def login(self, username: str, password: str, ip_address: str = None, user_agent: str = None) -> Optional[Dict[str, Any]]:
        """
        Perform user login and return session information.
        
        Args:
            username: The username to login
            password: The plain text password
            ip_address: The client IP address
            user_agent: The client user agent
            
        Returns:
            Dictionary with session information or None if login failed
        """
        try:
            # Authenticate user
            user = await self.authenticate_user(username, password)
            if not user:
                return None
            
            # Create session
            session = await self.create_session(user, ip_address, user_agent)
            if not session:
                return None
            
            # Get user roles
            roles = await self.get_user_roles(user)
            
            return {
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "full_name": user.full_name,
                    "is_active": user.is_active,
                    "is_verified": user.is_verified,
                    "last_login": user.last_login.isoformat() if user.last_login else None
                },
                "session": {
                    "id": session.id,
                    "token": session.token,
                    "refresh_token": session.refresh_token,
                    "expires_at": session.expires_at.isoformat()
                },
                "roles": [role.name for role in roles]
            }
            
        except Exception as e:
            self.logger.error(f"Login error for user '{username}': {e}")
            return None
    
    async def logout(self, session_id: int) -> bool:
        """
        Logout a user by invalidating their session.
        
        Args:
            session_id: The session ID to invalidate
            
        Returns:
            True if logout was successful, False otherwise
        """
        try:
            # Deactivate session
            session = Session.get_or_none(Session.id == session_id)
            if session:
                session.is_active = False
                session.save()
                self.logger.info(f"User '{session.user.username}' logged out")
                return True
            else:
                self.logger.warning(f"Session {session_id} not found for logout")
                return False
                
        except Exception as e:
            self.logger.error(f"Logout error for session {session_id}: {e}")
            return False
    
    async def refresh_token(self, refresh_token: str) -> Optional[Dict[str, Any]]:
        """
        Refresh an access token using a refresh token.
        
        Args:
            refresh_token: The refresh token
            
        Returns:
            Dictionary with new tokens or None if refresh failed
        """
        try:
            # Find session by refresh token
            session = Session.get_or_none(
                (Session.refresh_token == refresh_token) & 
                (Session.is_active == True)
            )
            
            if not session:
                self.logger.warning("Invalid refresh token")
                return None
            
            # Check if session is expired
            if session.expires_at < datetime.now():
                self.logger.warning("Refresh token expired")
                session.is_active = False
                session.save()
                return None
            
            # Generate new tokens
            new_access_token = self.create_access_token(session.user)
            new_refresh_token = self.create_refresh_token(session.user)
            new_expires_at = datetime.now() + timedelta(minutes=self.access_token_expire_minutes)
            
            # Update session
            session.token = new_access_token
            session.refresh_token = new_refresh_token
            session.expires_at = new_expires_at
            session.last_activity = datetime.now()
            session.save()
            
            self.logger.info(f"Token refreshed for user '{session.user.username}'")
            
            return {
                "access_token": new_access_token,
                "refresh_token": new_refresh_token,
                "expires_at": new_expires_at.isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Token refresh error: {e}")
            return None
    
    async def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Verify a JWT token and return user information.
        
        Args:
            token: The JWT token to verify
            
        Returns:
            Dictionary with user information or None if token is invalid
        """
        try:
            # Decode token
            payload = jwt.decode(token, self.jwt_secret, algorithms=[self.jwt_algorithm])
            
            # Get user and session
            user_id = payload.get("user_id")
            session_id = payload.get("session_id")
            
            if not user_id or not session_id:
                return None
            
            # Verify session is active
            session = Session.get_or_none(
                (Session.id == session_id) & 
                (Session.user_id == user_id) & 
                (Session.is_active == True)
            )
            
            if not session:
                return None
            
            # Check if session is expired
            if session.expires_at < datetime.now():
                session.is_active = False
                session.save()
                return None
            
            # Update last activity
            session.last_activity = datetime.now()
            session.save()
            
            # Get user roles
            roles = await self.get_user_roles(session.user)
            
            return {
                "user_id": user_id,
                "session_id": session_id,
                "username": session.user.username,
                "roles": [role.name for role in roles]
            }
            
        except jwt.ExpiredSignatureError:
            self.logger.warning("Token has expired")
            return None
        except jwt.InvalidTokenError as e:
            self.logger.warning(f"Invalid token: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Token verification error: {e}")
            return None
    
    async def change_password(self, user_id: int, old_password: str, new_password: str) -> bool:
        """
        Change a user's password.
        
        Args:
            user_id: The user ID
            old_password: The current password
            new_password: The new password
            
        Returns:
            True if password was changed successfully, False otherwise
        """
        try:
            # Get user
            user = await self.get_by_id(user_id)
            if not user:
                return False
            
            # Verify old password
            if not self.verify_password(old_password, user.password_hash):
                self.logger.warning(f"Invalid old password for user '{user.username}'")
                return False
            
            # Hash new password
            new_password_hash = self.hash_password(new_password)
            
            # Update password
            user.password_hash = new_password_hash
            user.updated_at = datetime.now()
            user.save()
            
            self.logger.info(f"Password changed for user '{user.username}'")
            return True
            
        except Exception as e:
            self.logger.error(f"Password change error for user {user_id}: {e}")
            return False
    
    async def reset_password(self, username: str, new_password: str) -> bool:
        """
        Reset a user's password (admin operation).
        
        Args:
            username: The username
            new_password: The new password
            
        Returns:
            True if password was reset successfully, False otherwise
        """
        try:
            # Get user
            user = User.get_or_none(User.username == username)
            if not user:
                self.logger.warning(f"User '{username}' not found for password reset")
                return False
            
            # Hash new password
            new_password_hash = self.hash_password(new_password)
            
            # Update password
            user.password_hash = new_password_hash
            user.updated_at = datetime.now()
            user.save()
            
            self.logger.info(f"Password reset for user '{username}'")
            return True
            
        except Exception as e:
            self.logger.error(f"Password reset error for user '{username}': {e}")
            return False
    
    async def get_user_roles(self, user: User) -> List[Role]:
        """
        Get all roles for a user.
        
        Args:
            user: The user to get roles for
            
        Returns:
            List of user roles
        """
        try:
            roles = (Role.select()
                    .join(UserRole)
                    .where(UserRole.user == user))
            return list(roles)
        except Exception as e:
            self.logger.error(f"Failed to get roles for user '{user.username}': {e}")
            return []
    
    async def has_permission(self, user: User, resource: str, action: str) -> bool:
        """
        Check if a user has a specific permission.
        
        Args:
            user: The user to check
            resource: The resource name
            action: The action name
            
        Returns:
            True if user has permission, False otherwise
        """
        try:
            # Get user roles
            roles = await self.get_user_roles(user)
            
            # Check if any role has the permission
            for role in roles:
                if role.permissions:
                    import json
                    permissions = json.loads(role.permissions)
                    if f"{resource}:{action}" in permissions:
                        return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Permission check error for user '{user.username}': {e}")
            return False
    
    def hash_password(self, password: str) -> str:
        """
        Hash a password using bcrypt.
        
        Args:
            password: The plain text password
            
        Returns:
            The hashed password
        """
        return self.pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        Verify a password against its hash.
        
        Args:
            plain_password: The plain text password
            hashed_password: The hashed password
            
        Returns:
            True if password matches, False otherwise
        """
        return self.pwd_context.verify(plain_password, hashed_password)
    
    def create_access_token(self, user: User) -> str:
        """
        Create a JWT access token for a user.
        
        Args:
            user: The user to create token for
            
        Returns:
            The JWT access token
        """
        expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        payload = {
            "user_id": user.id,
            "username": user.username,
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access"
        }
        return jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)
    
    def create_refresh_token(self, user: User) -> str:
        """
        Create a JWT refresh token for a user.
        
        Args:
            user: The user to create token for
            
        Returns:
            The JWT refresh token
        """
        expire = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)
        payload = {
            "user_id": user.id,
            "username": user.username,
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "refresh"
        }
        return jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)
    
    async def validate_data(self, data: Dict[str, Any]) -> List[str]:
        """
        Validate authentication data.
        
        Args:
            data: The data to validate
            
        Returns:
            List of validation error messages
        """
        errors = []
        
        # Validate username
        if "username" in data:
            username = data["username"]
            if not username or len(username) < 3:
                errors.append("Username must be at least 3 characters long")
            elif len(username) > 50:
                errors.append("Username must be less than 50 characters")
            elif not username.replace("_", "").replace("-", "").isalnum():
                errors.append("Username can only contain letters, numbers, underscores, and hyphens")
        
        # Validate password
        if "password" in data:
            password = data["password"]
            if not password or len(password) < 6:
                errors.append("Password must be at least 6 characters long")
            elif len(password) > 128:
                errors.append("Password must be less than 128 characters")
        
        # Validate email
        if "email" in data and data["email"]:
            email = data["email"]
            if "@" not in email or "." not in email:
                errors.append("Invalid email format")
            elif len(email) > 100:
                errors.append("Email must be less than 100 characters")
        
        return errors
