"""
User management service for CRUD operations on users.

This service handles user creation, updates, deletion, and role management.
It provides business logic for user operations and integrates with authentication.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from peewee import fn

from .base_service import BaseService
from .auth_service import AuthService
from ..db.models import User, Role, UserRole, Session
from ..core.constants import UserRole as UserRoleEnum
from ..utils.logger import logger


class UserService(BaseService[User]):
    """
    Service for managing users and their operations.
    
    This service provides methods for user CRUD operations, role management,
    and user-related business logic.
    """
    
    def __init__(self):
        """Initialize the user service."""
        super().__init__(User)
        self.auth_service = AuthService()
    
    async def create_user(self, username: str, email: str, password: str, 
                         full_name: str = None, roles: List[str] = None) -> Optional[User]:
        """
        Create a new user with specified roles.
        
        Args:
            username: The username
            email: The email address
            password: The plain text password
            full_name: The full name (optional)
            roles: List of role names to assign (optional)
            
        Returns:
            The created user or None if creation failed
        """
        try:
            # Validate input data
            data = {
                "username": username,
                "email": email,
                "password": password,
                "full_name": full_name
            }
            validation_errors = await self.validate_data(data)
            if validation_errors:
                self.logger.warning(f"User creation validation failed: {validation_errors}")
                return None
            
            # Check if username already exists
            if await self.username_exists(username):
                self.logger.warning(f"Username '{username}' already exists")
                return None
            
            # Check if email already exists
            if email and await self.email_exists(email):
                self.logger.warning(f"Email '{email}' already exists")
                return None
            
            # Hash password
            password_hash = self.auth_service.hash_password(password)
            
            # Create user
            user = await self.create(
                username=username,
                email=email,
                password_hash=password_hash,
                full_name=full_name,
                is_active=True,
                is_verified=False
            )
            
            if user and roles:
                # Assign roles
                await self.assign_roles(user, roles)
            
            self.logger.info(f"User '{username}' created successfully")
            return user
            
        except Exception as e:
            self.logger.error(f"Failed to create user '{username}': {e}")
            return None
    
    async def update_user(self, user_id: int, **kwargs) -> Optional[User]:
        """
        Update a user's information.
        
        Args:
            user_id: The user ID to update
            **kwargs: Fields to update
            
        Returns:
            The updated user or None if update failed
        """
        try:
            # Get current user
            user = await self.get_by_id(user_id)
            if not user:
                return None
            
            # Validate data
            validation_errors = await self.validate_data(kwargs)
            if validation_errors:
                self.logger.warning(f"User update validation failed: {validation_errors}")
                return None
            
            # Check for username conflicts
            if "username" in kwargs and kwargs["username"] != user.username:
                if await self.username_exists(kwargs["username"]):
                    self.logger.warning(f"Username '{kwargs['username']}' already exists")
                    return None
            
            # Check for email conflicts
            if "email" in kwargs and kwargs["email"] != user.email:
                if kwargs["email"] and await self.email_exists(kwargs["email"]):
                    self.logger.warning(f"Email '{kwargs['email']}' already exists")
                    return None
            
            # Hash password if provided
            if "password" in kwargs:
                kwargs["password_hash"] = self.auth_service.hash_password(kwargs["password"])
                del kwargs["password"]
            
            # Update user
            updated_user = await self.update(user_id, **kwargs)
            
            if updated_user:
                self.logger.info(f"User '{updated_user.username}' updated successfully")
            
            return updated_user
            
        except Exception as e:
            self.logger.error(f"Failed to update user {user_id}: {e}")
            return None
    
    async def delete_user(self, user_id: int, force: bool = False) -> bool:
        """
        Delete a user and optionally their sessions.
        
        Args:
            user_id: The user ID to delete
            force: Whether to force deletion (delete sessions)
            
        Returns:
            True if deletion was successful, False otherwise
        """
        try:
            # Get user
            user = await self.get_by_id(user_id)
            if not user:
                return False
            
            # Check if user has active sessions
            active_sessions = Session.select().where(
                (Session.user == user) & (Session.is_active == True)
            ).count()
            
            if active_sessions > 0 and not force:
                self.logger.warning(f"Cannot delete user '{user.username}' with active sessions")
                return False
            
            # Deactivate all sessions if force delete
            if force and active_sessions > 0:
                Session.update(is_active=False).where(Session.user == user).execute()
                self.logger.info(f"Deactivated {active_sessions} sessions for user '{user.username}'")
            
            # Delete user (cascade will handle related records)
            success = await self.delete(user_id)
            
            if success:
                self.logger.info(f"User '{user.username}' deleted successfully")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Failed to delete user {user_id}: {e}")
            return False
    
    async def activate_user(self, user_id: int) -> bool:
        """
        Activate a user account.
        
        Args:
            user_id: The user ID to activate
            
        Returns:
            True if activation was successful, False otherwise
        """
        try:
            user = await self.update(user_id, is_active=True)
            if user:
                self.logger.info(f"User '{user.username}' activated")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Failed to activate user {user_id}: {e}")
            return False
    
    async def deactivate_user(self, user_id: int) -> bool:
        """
        Deactivate a user account.
        
        Args:
            user_id: The user ID to deactivate
            
        Returns:
            True if deactivation was successful, False otherwise
        """
        try:
            user = await self.update(user_id, is_active=False)
            if user:
                # Deactivate all sessions
                Session.update(is_active=False).where(Session.user == user).execute()
                self.logger.info(f"User '{user.username}' deactivated")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Failed to deactivate user {user_id}: {e}")
            return False
    
    async def verify_user(self, user_id: int) -> bool:
        """
        Mark a user as verified.
        
        Args:
            user_id: The user ID to verify
            
        Returns:
            True if verification was successful, False otherwise
        """
        try:
            user = await self.update(user_id, is_verified=True)
            if user:
                self.logger.info(f"User '{user.username}' verified")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Failed to verify user {user_id}: {e}")
            return False
    
    async def assign_roles(self, user: User, role_names: List[str]) -> bool:
        """
        Assign roles to a user.
        
        Args:
            user: The user to assign roles to
            role_names: List of role names to assign
            
        Returns:
            True if assignment was successful, False otherwise
        """
        try:
            # Get roles
            roles = Role.select().where(Role.name.in_(role_names))
            role_list = list(roles)
            
            if len(role_list) != len(role_names):
                missing_roles = set(role_names) - {role.name for role in role_list}
                self.logger.warning(f"Roles not found: {missing_roles}")
            
            # Remove existing roles
            UserRole.delete().where(UserRole.user == user).execute()
            
            # Assign new roles
            for role in role_list:
                UserRole.create(user=user, role=role)
            
            self.logger.info(f"Assigned {len(role_list)} roles to user '{user.username}'")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to assign roles to user '{user.username}': {e}")
            return False
    
    async def remove_roles(self, user: User, role_names: List[str]) -> bool:
        """
        Remove roles from a user.
        
        Args:
            user: The user to remove roles from
            role_names: List of role names to remove
            
        Returns:
            True if removal was successful, False otherwise
        """
        try:
            # Get roles
            roles = Role.select().where(Role.name.in_(role_names))
            role_list = list(roles)
            
            # Remove roles
            for role in role_list:
                UserRole.delete().where(
                    (UserRole.user == user) & (UserRole.role == role)
                ).execute()
            
            self.logger.info(f"Removed {len(role_list)} roles from user '{user.username}'")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to remove roles from user '{user.username}': {e}")
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
    
    async def get_users_by_role(self, role_name: str) -> List[User]:
        """
        Get all users with a specific role.
        
        Args:
            role_name: The role name
            
        Returns:
            List of users with the role
        """
        try:
            users = (User.select()
                    .join(UserRole)
                    .join(Role)
                    .where(Role.name == role_name))
            return list(users)
        except Exception as e:
            self.logger.error(f"Failed to get users with role '{role_name}': {e}")
            return []
    
    async def get_active_users(self) -> List[User]:
        """
        Get all active users.
        
        Returns:
            List of active users
        """
        try:
            users = User.select().where(User.is_active == True)
            return list(users)
        except Exception as e:
            self.logger.error(f"Failed to get active users: {e}")
            return []
    
    async def get_online_users(self) -> List[User]:
        """
        Get all users with active sessions.
        
        Returns:
            List of online users
        """
        try:
            users = (User.select()
                    .join(Session)
                    .where(Session.is_active == True)
                    .distinct())
            return list(users)
        except Exception as e:
            self.logger.error(f"Failed to get online users: {e}")
            return []
    
    async def search_users(self, query: str) -> List[User]:
        """
        Search users by username, email, or full name.
        
        Args:
            query: The search query
            
        Returns:
            List of matching users
        """
        try:
            search_conditions = (
                User.username.contains(query) |
                User.email.contains(query) |
                User.full_name.contains(query)
            )
            
            users = User.select().where(search_conditions)
            return list(users)
        except Exception as e:
            self.logger.error(f"Failed to search users with query '{query}': {e}")
            return []
    
    async def get_user_stats(self) -> Dict[str, Any]:
        """
        Get user statistics.
        
        Returns:
            Dictionary with user statistics
        """
        try:
            total_users = await self.count()
            active_users = User.select().where(User.is_active == True).count()
            verified_users = User.select().where(User.is_verified == True).count()
            online_users = (User.select()
                           .join(Session)
                           .where(Session.is_active == True)
                           .distinct()
                           .count())
            
            # Users by role
            role_stats = {}
            for role_enum in UserRoleEnum:
                role_name = role_enum.value
                count = (User.select()
                         .join(UserRole)
                         .join(Role)
                         .where(Role.name == role_name)
                         .count())
                role_stats[role_name] = count
            
            return {
                "total_users": total_users,
                "active_users": active_users,
                "verified_users": verified_users,
                "online_users": online_users,
                "inactive_users": total_users - active_users,
                "unverified_users": total_users - verified_users,
                "role_distribution": role_stats
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get user statistics: {e}")
            return {}
    
    async def username_exists(self, username: str) -> bool:
        """
        Check if a username already exists.
        
        Args:
            username: The username to check
            
        Returns:
            True if username exists, False otherwise
        """
        try:
            return User.select().where(User.username == username).exists()
        except Exception as e:
            self.logger.error(f"Failed to check username existence: {e}")
            return False
    
    async def email_exists(self, email: str) -> bool:
        """
        Check if an email already exists.
        
        Args:
            email: The email to check
            
        Returns:
            True if email exists, False otherwise
        """
        try:
            return User.select().where(User.email == email).exists()
        except Exception as e:
            self.logger.error(f"Failed to check email existence: {e}")
            return False
    
    async def validate_data(self, data: Dict[str, Any]) -> List[str]:
        """
        Validate user data.
        
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
        
        # Validate email
        if "email" in data and data["email"]:
            email = data["email"]
            if "@" not in email or "." not in email:
                errors.append("Invalid email format")
            elif len(email) > 100:
                errors.append("Email must be less than 100 characters")
        
        # Validate password
        if "password" in data:
            password = data["password"]
            if not password or len(password) < 6:
                errors.append("Password must be at least 6 characters long")
            elif len(password) > 128:
                errors.append("Password must be less than 128 characters")
        
        # Validate full name
        if "full_name" in data and data["full_name"]:
            full_name = data["full_name"]
            if len(full_name) > 100:
                errors.append("Full name must be less than 100 characters")
        
        return errors
