"""
File utilities for file operations, validation, and management.

This module provides utilities for file handling, validation,
and file system operations.
"""

import os
import shutil
import mimetypes
import hashlib
from pathlib import Path
from typing import List, Optional, Union, Dict, Any
import aiofiles
import asyncio


class FileUtils:
    """Utilities for file operations and management."""
    
    @staticmethod
    def ensure_directory(path: Union[str, Path]) -> bool:
        """
        Ensure directory exists, create if it doesn't.
        
        Args:
            path: Directory path
            
        Returns:
            True if directory exists or was created successfully
        """
        try:
            Path(path).mkdir(parents=True, exist_ok=True)
            return True
        except Exception:
            return False
    
    @staticmethod
    def get_file_size(file_path: Union[str, Path]) -> int:
        """
        Get file size in bytes.
        
        Args:
            file_path: Path to the file
            
        Returns:
            File size in bytes, 0 if file doesn't exist
        """
        try:
            return os.path.getsize(file_path)
        except (OSError, FileNotFoundError):
            return 0
    
    @staticmethod
    def get_file_hash(file_path: Union[str, Path], algorithm: str = 'sha256') -> Optional[str]:
        """
        Calculate file hash.
        
        Args:
            file_path: Path to the file
            algorithm: Hash algorithm ('md5', 'sha1', 'sha256', 'sha512')
            
        Returns:
            File hash as hexadecimal string, None if error
        """
        try:
            hash_obj = hashlib.new(algorithm)
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_obj.update(chunk)
            return hash_obj.hexdigest()
        except Exception:
            return None
    
    @staticmethod
    def get_mime_type(file_path: Union[str, Path]) -> str:
        """
        Get MIME type of a file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            MIME type string
        """
        mime_type, _ = mimetypes.guess_type(str(file_path))
        return mime_type or 'application/octet-stream'
    
    @staticmethod
    def is_safe_filename(filename: str) -> bool:
        """
        Check if filename is safe (no path traversal, etc.).
        
        Args:
            filename: Filename to check
            
        Returns:
            True if filename is safe
        """
        # Check for path traversal
        if '..' in filename or '/' in filename or '\\' in filename:
            return False
        
        # Check for reserved names (Windows)
        reserved_names = {
            'CON', 'PRN', 'AUX', 'NUL',
            'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
            'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
        }
        
        name_without_ext = Path(filename).stem.upper()
        if name_without_ext in reserved_names:
            return False
        
        # Check for invalid characters
        invalid_chars = '<>:"|?*'
        if any(char in filename for char in invalid_chars):
            return False
        
        return True
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """
        Sanitize filename by removing/replacing unsafe characters.
        
        Args:
            filename: Original filename
            
        Returns:
            Sanitized filename
        """
        # Replace invalid characters
        invalid_chars = '<>:"|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        
        # Remove path separators
        filename = filename.replace('/', '_').replace('\\', '_')
        
        # Remove multiple dots
        while '..' in filename:
            filename = filename.replace('..', '.')
        
        # Limit length
        if len(filename) > 255:
            name, ext = os.path.splitext(filename)
            filename = name[:255-len(ext)] + ext
        
        return filename
    
    @staticmethod
    def get_file_extension(filename: str) -> str:
        """
        Get file extension (without dot).
        
        Args:
            filename: Filename
            
        Returns:
            File extension without dot
        """
        return Path(filename).suffix.lstrip('.')
    
    @staticmethod
    def is_image_file(filename: str) -> bool:
        """
        Check if file is an image based on extension.
        
        Args:
            filename: Filename to check
            
        Returns:
            True if file is an image
        """
        image_extensions = {
            'jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff', 'tif',
            'webp', 'svg', 'ico', 'raw', 'heic', 'heif'
        }
        return FileUtils.get_file_extension(filename).lower() in image_extensions
    
    @staticmethod
    def is_document_file(filename: str) -> bool:
        """
        Check if file is a document based on extension.
        
        Args:
            filename: Filename to check
            
        Returns:
            True if file is a document
        """
        doc_extensions = {
            'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx',
            'txt', 'rtf', 'odt', 'ods', 'odp', 'csv'
        }
        return FileUtils.get_file_extension(filename).lower() in doc_extensions
    
    @staticmethod
    def is_archive_file(filename: str) -> bool:
        """
        Check if file is an archive based on extension.
        
        Args:
            filename: Filename to check
            
        Returns:
            True if file is an archive
        """
        archive_extensions = {
            'zip', 'rar', '7z', 'tar', 'gz', 'bz2', 'xz',
            'tar.gz', 'tar.bz2', 'tar.xz'
        }
        return FileUtils.get_file_extension(filename).lower() in archive_extensions
    
    @staticmethod
    def format_file_size(size_bytes: int) -> str:
        """
        Format file size in human readable format.
        
        Args:
            size_bytes: Size in bytes
            
        Returns:
            Formatted size string
        """
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB", "TB", "PB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1
        
        return f"{size_bytes:.1f} {size_names[i]}"
    
    @staticmethod
    def copy_file(src: Union[str, Path], dst: Union[str, Path]) -> bool:
        """
        Copy file from source to destination.
        
        Args:
            src: Source file path
            dst: Destination file path
            
        Returns:
            True if copy was successful
        """
        try:
            shutil.copy2(src, dst)
            return True
        except Exception:
            return False
    
    @staticmethod
    def move_file(src: Union[str, Path], dst: Union[str, Path]) -> bool:
        """
        Move file from source to destination.
        
        Args:
            src: Source file path
            dst: Destination file path
            
        Returns:
            True if move was successful
        """
        try:
            shutil.move(src, dst)
            return True
        except Exception:
            return False
    
    @staticmethod
    def delete_file(file_path: Union[str, Path]) -> bool:
        """
        Delete a file.
        
        Args:
            file_path: Path to file to delete
            
        Returns:
            True if deletion was successful
        """
        try:
            os.remove(file_path)
            return True
        except Exception:
            return False
    
    @staticmethod
    def list_files(directory: Union[str, Path], pattern: str = "*") -> List[Path]:
        """
        List files in directory matching pattern.
        
        Args:
            directory: Directory to search
            pattern: File pattern to match
            
        Returns:
            List of matching file paths
        """
        try:
            return list(Path(directory).glob(pattern))
        except Exception:
            return []
    
    @staticmethod
    def get_directory_size(directory: Union[str, Path]) -> int:
        """
        Get total size of directory in bytes.
        
        Args:
            directory: Directory path
            
        Returns:
            Total size in bytes
        """
        total_size = 0
        try:
            for dirpath, dirnames, filenames in os.walk(directory):
                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)
                    total_size += FileUtils.get_file_size(filepath)
        except Exception:
            pass
        return total_size
    
    @staticmethod
    async def async_read_file(file_path: Union[str, Path]) -> Optional[str]:
        """
        Asynchronously read text file.
        
        Args:
            file_path: Path to file
            
        Returns:
            File content as string, None if error
        """
        try:
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                return await f.read()
        except Exception:
            return None
    
    @staticmethod
    async def async_write_file(file_path: Union[str, Path], content: str) -> bool:
        """
        Asynchronously write text file.
        
        Args:
            file_path: Path to file
            content: Content to write
            
        Returns:
            True if write was successful
        """
        try:
            async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
                await f.write(content)
            return True
        except Exception:
            return False
    
    @staticmethod
    async def async_read_binary_file(file_path: Union[str, Path]) -> Optional[bytes]:
        """
        Asynchronously read binary file.
        
        Args:
            file_path: Path to file
            
        Returns:
            File content as bytes, None if error
        """
        try:
            async with aiofiles.open(file_path, 'rb') as f:
                return await f.read()
        except Exception:
            return None
    
    @staticmethod
    async def async_write_binary_file(file_path: Union[str, Path], content: bytes) -> bool:
        """
        Asynchronously write binary file.
        
        Args:
            file_path: Path to file
            content: Content to write
            
        Returns:
            True if write was successful
        """
        try:
            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(content)
            return True
        except Exception:
            return False
    
    @staticmethod
    def create_temp_file(content: str = "", suffix: str = ".tmp") -> Optional[str]:
        """
        Create temporary file with content.
        
        Args:
            content: Content to write to file
            suffix: File suffix
            
        Returns:
            Path to temporary file, None if error
        """
        try:
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix=suffix, delete=False) as f:
                f.write(content)
                return f.name
        except Exception:
            return None
    
    @staticmethod
    def cleanup_temp_file(file_path: Union[str, Path]) -> bool:
        """
        Clean up temporary file.
        
        Args:
            file_path: Path to temporary file
            
        Returns:
            True if cleanup was successful
        """
        try:
            os.unlink(file_path)
            return True
        except Exception:
            return False
