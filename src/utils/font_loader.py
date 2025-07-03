"""
Font loading utility for IntenseRP API
Handles loading custom TTF fonts with fallback to system fonts
"""

import os
import sys
from pathlib import Path
from typing import Optional, List, Tuple, Union
import logging


class FontLoader:
    """Handles loading custom TTF fonts with fallback support"""
    
    # Font size adjustments to normalize appearance across different fonts
    # Positive values make fonts larger, negative values make them smaller
    FONT_SIZE_ADJUSTMENTS = {
        "Blinker": 1,           # Blinker is smaller, needs +1 to match Arial
        "Arial": 0,             # Arial is the baseline
        "Helvetica": 0,         # Similar to Arial
        "Consolas": 0,          # Monospace, good as-is
        "Monaco": 0,            # Mac monospace, good as-is
        "DejaVu Sans": 0,       # Linux default, similar to Arial
        "Courier New": 0,       # Cross-platform monospace
        "Times New Roman": 0,   # Serif font, different but proportional
        "Lucida Console": 0,    # Windows monospace
    }
    
    def __init__(self):
        self.fonts_loaded = False
        self.available_fonts = {}
        self.font_directory = self._get_font_directory()
        self.fallback_fonts = ["Arial", "Helvetica", "DejaVu Sans", "Liberation Sans"]
        self._load_fonts()
    
    def _get_font_directory(self) -> Optional[Path]:
        """Get the path to the fonts directory"""
        try:
            # Get the base directory - handle both development and packaged contexts
            if hasattr(sys, '_MEIPASS'):
                # Running as PyInstaller bundle
                base_dir = Path(sys._MEIPASS)
            else:
                # Running in development
                base_dir = Path(__file__).parent.parent
            
            font_dir = base_dir / "assets" / "fonts"
            if font_dir.exists():
                return font_dir
            
            print(f"[color:yellow]Warning: Font directory not found at {font_dir}")
            return None
            
        except Exception as e:
            print(f"[color:red]Error locating font directory: {e}")
            return None
    
    def _load_fonts(self) -> None:
        """Load all available TTF fonts from the fonts directory"""
        if not self.font_directory:
            print("[color:yellow]No font directory available, using system fonts only")
            return
        
        try:
            # Use tkextrafont for lightweight font loading
            if self._load_fonts_with_tkextrafont():
                self.fonts_loaded = True
                return
                
            print("[color:yellow]Custom font loading failed, using system fonts only")
            
        except Exception as e:
            print(f"[color:red]Error loading fonts: {e}")
    
    
    def _load_fonts_with_tkextrafont(self) -> bool:
        """Load fonts using tkextrafont library"""
        try:
            from tkextrafont import Font
            
            font_files = list(self.font_directory.glob("*.ttf"))
            if not font_files:
                return False
            
            loaded_count = 0
            for font_file in font_files:
                try:
                    font_name = self._extract_font_name(font_file)
                    # Create a Font object and register it
                    font_obj = Font(file=str(font_file), family=font_name)
                    self.available_fonts[font_name] = font_obj
                    loaded_count += 1
                    print(f"[color:green]Loaded font: {font_name} from {font_file.name}")
                except Exception as e:
                    print(f"[color:red]Failed to load {font_file.name}: {e}")
            
            if loaded_count > 0:
                print(f"[color:green]Successfully loaded {loaded_count} fonts using tkextrafont")
                return True
            
        except ImportError:
            print("[color:yellow]tkextrafont not available")
        except Exception as e:
            print(f"[color:red]tkextrafont font loading failed: {e}")
        
        return False
    
    def _extract_font_name(self, font_file: Path) -> str:
        """Extract font family name from filename"""
        name = font_file.stem
        
        # Handle Blinker font variants
        if name.startswith("Blinker"):
            return "Blinker"
        
        # Remove common weight/style suffixes
        suffixes = ["-Regular", "-Bold", "-Light", "-SemiBold", "-Medium", 
                   "-Thin", "-Black", "-Italic", "-BoldItalic"]
        
        for suffix in suffixes:
            if name.endswith(suffix):
                name = name[:-len(suffix)]
                break
        
        return name
    
    def get_font_tuple(self, family: str = "Blinker", size: int = 12, 
                      weight: str = "normal") -> Tuple[str, int, ...]:
        """
        Get font tuple with fallback support and automatic size adjustment
        
        Args:
            family: Preferred font family (default: "Blinker")
            size: Font size (will be adjusted automatically per font)
            weight: Font weight ("normal", "bold", etc.)
            
        Returns:
            Tuple suitable for tkinter/CustomTkinter font parameter
        """
        # Try custom fonts first
        if self.fonts_loaded and family in self.available_fonts:
            adjusted_size = size + self.FONT_SIZE_ADJUSTMENTS.get(family, 0)
            if weight == "normal":
                return (family, adjusted_size)
            else:
                return (family, adjusted_size, weight)
        
        # Try fallback fonts
        font_families = [family] + self.fallback_fonts
        
        for font_family in font_families:
            if self._is_font_available(font_family):
                adjusted_size = size + self.FONT_SIZE_ADJUSTMENTS.get(font_family, 0)
                if weight == "normal":
                    return (font_family, adjusted_size)
                else:
                    return (font_family, adjusted_size, weight)
        
        # Ultimate fallback - let system handle it
        adjusted_size = size + self.FONT_SIZE_ADJUSTMENTS.get("Arial", 0)
        if weight == "normal":
            return ("Arial", adjusted_size)
        else:
            return ("Arial", adjusted_size, weight)
    
    def _is_font_available(self, font_family: str) -> bool:
        """Check if a font family is available on the system"""
        try:
            import tkinter as tk
            import tkinter.font as tkFont
            
            # Create a temporary root if needed
            root = tk._default_root
            if root is None:
                root = tk.Tk()
                root.withdraw()
                temp_root = True
            else:
                temp_root = False
            
            # Check if font is available
            available_fonts = tkFont.families()
            result = font_family in available_fonts
            
            if temp_root:
                root.destroy()
            
            return result
            
        except Exception:
            return False
    
    def get_available_fonts(self) -> List[str]:
        """Get list of available font families"""
        fonts = []
        
        # Add custom fonts
        if self.fonts_loaded:
            fonts.extend(self.available_fonts.keys())
        
        # Add fallback fonts
        for font in self.fallback_fonts:
            if font not in fonts and self._is_font_available(font):
                fonts.append(font)
        
        return fonts
    
    def is_font_loaded(self, font_family: str) -> bool:
        """Check if a specific font family is loaded"""
        return font_family in self.available_fonts
    
    def get_font_info(self) -> str:
        """Get information about loaded fonts"""
        if not self.fonts_loaded:
            return "No custom fonts loaded - using system fonts only"
        
        info = f"Loaded {len(self.available_fonts)} custom fonts:\n"
        for font_name, font_path in self.available_fonts.items():
            info += f"  - {font_name}\n"
        
        return info


# Global font loader instance
_font_loader = None


def get_font_loader() -> FontLoader:
    """Get the global font loader instance"""
    global _font_loader
    if _font_loader is None:
        _font_loader = FontLoader()
    return _font_loader


def get_font_tuple(family: str = "Blinker", size: int = 12, 
                  weight: str = "normal") -> Tuple[str, int, ...]:
    """
    Convenience function to get font tuple with Blinker primary and Arial fallback
    
    Args:
        family: Preferred font family (default: "Blinker")
        size: Font size
        weight: Font weight ("normal", "bold", etc.)
        
    Returns:
        Tuple suitable for tkinter/CustomTkinter font parameter
    """
    return get_font_loader().get_font_tuple(family, size, weight)


def get_available_fonts() -> List[str]:
    """Get list of available font families"""
    return get_font_loader().get_available_fonts()


def is_font_loaded(font_family: str) -> bool:
    """Check if a specific font family is loaded"""
    return get_font_loader().is_font_loaded(font_family)


def get_font_info() -> str:
    """Get information about loaded fonts"""
    return get_font_loader().get_font_info()