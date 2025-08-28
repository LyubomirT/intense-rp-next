"""
GitHub API Integration for IntenseRP Next
========================================

Provides functionality for fetching release information and assets from GitHub.
Used by the improved update modal system.
"""

import requests
import platform
import os
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass


@dataclass
class GitHubAsset:
    """Represents a GitHub release asset with metadata"""
    name: str
    download_url: str
    size: int  # in bytes
    content_type: str
    created_at: str
    download_count: int
    is_updater: bool = False
    is_utilities: bool = False
    is_current_platform: bool = False
    friendly_name: str = ""
    description: str = ""


class GitHubAPI:
    """GitHub API integration for IntenseRP Next updates"""
    
    REPO_OWNER = "LyubomirT"
    REPO_NAME = "intense-rp-next"
    API_BASE = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}"
    RELEASES_URL = f"{API_BASE}/releases/latest"
    RELEASES_PAGE_URL = f"https://github.com/{REPO_OWNER}/{REPO_NAME}/releases/latest"
    
    @classmethod
    def get_latest_release(cls) -> Optional[Dict[str, Any]]:
        """
        Get the latest release information from GitHub API
        
        Returns:
            Dict containing release information or None if failed
        """
        try:
            response = requests.get(cls.RELEASES_URL, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Failed to fetch release info: {e}")
            return None
    
    @classmethod
    def get_release_assets(cls, release_data: Optional[Dict[str, Any]] = None) -> List[GitHubAsset]:
        """
        Get categorized and improved release assets
        
        Args:
            release_data: Optional release data, if None will fetch latest
            
        Returns:
            List of GitHubAsset objects with improved metadata
        """
        if release_data is None:
            release_data = cls.get_latest_release()
        
        if not release_data:
            return []
        
        assets = []
        current_platform = platform.system().lower()
        
        for asset_data in release_data.get('assets', []):
            asset = GitHubAsset(
                name=asset_data['name'],
                download_url=asset_data['browser_download_url'],
                size=asset_data['size'],
                content_type=asset_data.get('content_type', ''),
                created_at=asset_data['created_at'],
                download_count=asset_data['download_count']
            )
            
            # Enhance asset with metadata
            cls._enhance_asset_metadata(asset, current_platform)
            assets.append(asset)
        
        return assets
    
    @classmethod
    def _enhance_asset_metadata(cls, asset: GitHubAsset, current_platform: str) -> None:
        """
        Enhance asset with friendly names, descriptions, and platform detection
        
        Args:
            asset: GitHubAsset to enhance
            current_platform: Current platform string (windows/linux/darwin)
        """
        name_lower = asset.name.lower()
        
        # Detect asset type
        asset.is_updater = 'updater' in name_lower
        asset.is_utilities = 'utilities' in name_lower
        
        # Detect platform and architecture
        platform_info = cls._extract_platform_info(asset.name)
        asset.is_current_platform = platform_info['platform'] == current_platform
        
        # Generate friendly name and description
        asset.friendly_name, asset.description = cls._generate_friendly_name(
            asset.name, platform_info, asset.is_updater, asset.is_utilities
        )
    
    @classmethod
    def _extract_platform_info(cls, filename: str) -> Dict[str, str]:
        """
        Extract platform information from filename
        
        Args:
            filename: Asset filename to analyze
            
        Returns:
            Dict with platform, architecture, and format information
        """
        filename_lower = filename.lower()
        
        # Platform detection
        if 'win32' in filename_lower or 'windows' in filename_lower:
            platform_name = 'windows'
        elif 'linux' in filename_lower:
            platform_name = 'linux'
        elif 'darwin' in filename_lower or 'macos' in filename_lower:
            platform_name = 'darwin'
        else:
            platform_name = 'unknown'
        
        # Architecture detection
        if 'amd64' in filename_lower or 'x86_64' in filename_lower:
            arch = 'AMD64'
        elif 'x86' in filename_lower:
            arch = 'x86'
        elif 'arm64' in filename_lower:
            arch = 'ARM64'
        else:
            arch = 'Unknown'
        
        # Format detection
        if filename_lower.endswith('.zip'):
            format_type = 'ZIP'
        elif filename_lower.endswith('.tar.gz'):
            format_type = 'TAR.GZ'
        elif filename_lower.endswith('.exe'):
            format_type = 'EXE'
        else:
            format_type = 'Unknown'
        
        return {
            'platform': platform_name,
            'architecture': arch,
            'format': format_type
        }
    
    @classmethod
    def _generate_friendly_name(cls, filename: str, platform_info: Dict[str, str], is_updater: bool, is_utilities: bool) -> Tuple[str, str]:
        """
        Generate user-friendly name and description for asset
        
        Args:
            filename: Original filename
            platform_info: Platform information dict
            is_updater: Whether this is an updater asset
            is_utilities: Whether this is a utilities package
            
        Returns:
            Tuple of (friendly_name, description)
        """
        platform = platform_info['platform'].title()
        arch = platform_info['architecture']
        format_type = platform_info['format']
        
        if is_updater:
            friendly_name = f"Updater Utility ({platform}, {arch})"
            description = f"Automatic updater for IntenseRP Next - {format_type} archive"
        elif is_utilities:
            friendly_name = f"IntenseRP Next Utilities ({platform}, {arch})"
            description = f"Additional utilities and tools for IntenseRP Next - {format_type} archive"
        else:
            friendly_name = f"IntenseRP Next Application ({platform}, {arch})"
            description = f"Complete IntenseRP Next installation - {format_type} archive"
        
        return friendly_name, description
    
    @classmethod
    def categorize_assets(cls, assets: List[GitHubAsset]) -> Dict[str, List[GitHubAsset]]:
        """
        Categorize assets by operating system, with current OS first
        
        Args:
            assets: List of GitHubAsset objects
            
        Returns:
            Dict mapping platform names to asset lists
        """
        current_platform = platform.system().lower()
        categories = {}
        
        # Group by platform
        for asset in assets:
            platform_info = cls._extract_platform_info(asset.name)
            platform_name = platform_info['platform'].title()
            
            if platform_name not in categories:
                categories[platform_name] = []
            categories[platform_name].append(asset)
        
        # Sort each category (main application first, then updater, then utilities, then by name)
        for platform_name in categories:
            categories[platform_name].sort(key=lambda a: (
                a.is_utilities,  # Utilities last
                a.is_updater,    # Updater in middle
                a.name           # Then alphabetically
            ))
        
        # Reorder categories to put current platform first
        current_platform_title = current_platform.title()
        if current_platform_title in categories:
            ordered_categories = {current_platform_title: categories[current_platform_title]}
            for platform_name, asset_list in categories.items():
                if platform_name != current_platform_title:
                    ordered_categories[platform_name] = asset_list
            return ordered_categories
        
        return categories
    
    @classmethod
    def format_file_size(cls, size_bytes: int) -> str:
        """
        Format file size in human-readable format
        
        Args:
            size_bytes: Size in bytes
            
        Returns:
            Formatted size string (e.g., "15.2 MB")
        """
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB"]
        i = 0
        size = float(size_bytes)
        
        while size >= 1024.0 and i < len(size_names) - 1:
            size /= 1024.0
            i += 1
        
        if i == 0:
            return f"{int(size)} {size_names[i]}"
        else:
            return f"{size:.1f} {size_names[i]}"