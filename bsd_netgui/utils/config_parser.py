"""Generic configuration file parser for BSD systems.

This module provides utilities for parsing and writing configuration files
while preserving comments, order, and formatting.
"""

import re
import logging
from typing import List, Dict, Tuple, Optional
from pathlib import Path


class ConfigLine:
    """Represents a single line in a configuration file."""
    
    def __init__(self, raw_line: str, line_number: int):
        """
        Initialize a ConfigLine.
        
        Args:
            raw_line: The original line from the file
            line_number: Line number in the file (1-indexed)
        """
        self.raw_line = raw_line
        self.line_number = line_number
        self.stripped = raw_line.strip()
        self.is_comment = self.stripped.startswith('#') or not self.stripped
        self.is_empty = not self.stripped
        
        # Parse key-value if not a comment
        self.key: Optional[str] = None
        self.value: Optional[str] = None
        self.inline_comment: Optional[str] = None
        
        if not self.is_comment and not self.is_empty:
            self._parse_key_value()
    
    def _parse_key_value(self):
        """Parse key=value pairs from the line."""
        # Handle inline comments
        line = self.stripped
        if '#' in line:
            # Find the # that's not in quotes
            in_quotes = False
            quote_char = None
            for i, char in enumerate(line):
                if char in ('"', "'") and (i == 0 or line[i-1] != '\\'):
                    if not in_quotes:
                        in_quotes = True
                        quote_char = char
                    elif char == quote_char:
                        in_quotes = False
                        quote_char = None
                elif char == '#' and not in_quotes:
                    self.inline_comment = line[i:].strip()
                    line = line[:i].strip()
                    break
        
        # Parse key=value
        if '=' in line:
            parts = line.split('=', 1)
            self.key = parts[0].strip()
            self.value = parts[1].strip() if len(parts) > 1 else ''
    
    def __repr__(self):
        """String representation."""
        if self.is_comment or self.is_empty:
            return f"ConfigLine({self.line_number}: {self.raw_line.rstrip()})"
        return f"ConfigLine({self.line_number}: {self.key}={self.value})"


class ConfigParser:
    """
    Generic configuration file parser for shell-style config files.
    
    Features:
    - Preserves comments and empty lines
    - Maintains original formatting
    - Supports key=value pairs
    - Handles quoted values
    - Safe atomic writes
    """
    
    def __init__(self, file_path: str):
        """
        Initialize the ConfigParser.
        
        Args:
            file_path: Path to the configuration file
        """
        self.file_path = Path(file_path)
        self.logger = logging.getLogger(__name__)
        self.lines: List[ConfigLine] = []
        self.variables: Dict[str, ConfigLine] = {}
    
    def parse(self) -> bool:
        """
        Parse the configuration file.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.file_path.exists():
                self.logger.warning(f"Config file does not exist: {self.file_path}")
                return False
            
            with open(self.file_path, 'r') as f:
                for line_num, line in enumerate(f, 1):
                    config_line = ConfigLine(line, line_num)
                    self.lines.append(config_line)
                    
                    # Store variables for quick lookup
                    if config_line.key:
                        self.variables[config_line.key] = config_line
            
            self.logger.info(f"Parsed {len(self.lines)} lines, {len(self.variables)} variables from {self.file_path}")
            return True
        except Exception as e:
            self.logger.error(f"Error parsing {self.file_path}: {e}")
            return False
    
    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """
        Get value for a key.
        
        Args:
            key: Configuration key
            default: Default value if key not found
        
        Returns:
            Value as string, or default if not found
        """
        if key in self.variables:
            return self.variables[key].value
        return default
    
    def set(self, key: str, value: str, comment: Optional[str] = None):
        """
        Set or update a configuration value.
        
        Args:
            key: Configuration key
            value: Configuration value
            comment: Optional inline comment
        """
        # Check if key already exists
        if key in self.variables:
            # Update existing line
            line = self.variables[key]
            line.value = value
            if comment:
                line.inline_comment = f"# {comment}"
            
            # Reconstruct the raw line
            new_line = f"{key}={value}"
            if line.inline_comment:
                new_line += f"  {line.inline_comment}"
            line.raw_line = new_line + "\n"
            line.stripped = new_line.strip()
        else:
            # Add new line at the end
            new_line = f"{key}={value}"
            if comment:
                new_line += f"  # {comment}"
            new_line += "\n"
            
            config_line = ConfigLine(new_line, len(self.lines) + 1)
            config_line.key = key
            config_line.value = value
            if comment:
                config_line.inline_comment = f"# {comment}"
            
            self.lines.append(config_line)
            self.variables[key] = config_line
    
    def delete(self, key: str) -> bool:
        """
        Delete a configuration key.
        
        Args:
            key: Configuration key to delete
        
        Returns:
            True if deleted, False if not found
        """
        if key not in self.variables:
            return False
        
        # Find and remove the line
        line_to_remove = self.variables[key]
        self.lines = [line for line in self.lines if line != line_to_remove]
        del self.variables[key]
        
        # Renumber lines
        for i, line in enumerate(self.lines, 1):
            line.line_number = i
        
        return True
    
    def write(self, backup: bool = True) -> bool:
        """
        Write the configuration back to the file atomically.
        
        Args:
            backup: Whether to create a backup before writing
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create backup if requested
            if backup and self.file_path.exists():
                backup_path = Path(f"{self.file_path}.bak")
                import shutil
                shutil.copy2(self.file_path, backup_path)
                self.logger.info(f"Created backup: {backup_path}")
            
            # Write to temporary file first (atomic write)
            temp_path = Path(f"{self.file_path}.tmp")
            with open(temp_path, 'w') as f:
                for line in self.lines:
                    f.write(line.raw_line)
            
            # Move temp file to actual file
            import shutil
            shutil.move(str(temp_path), str(self.file_path))
            
            self.logger.info(f"Successfully wrote configuration to {self.file_path}")
            return True
        except Exception as e:
            self.logger.error(f"Error writing to {self.file_path}: {e}")
            # Clean up temp file if it exists
            if temp_path.exists():
                temp_path.unlink()
            return False
    
    def validate(self) -> Tuple[bool, List[str]]:
        """
        Validate the configuration.
        
        Returns:
            Tuple of (is_valid, list of error messages)
        """
        errors = []
        
        # Check for duplicate keys
        key_counts = {}
        for line in self.lines:
            if line.key:
                key_counts[line.key] = key_counts.get(line.key, 0) + 1
        
        for key, count in key_counts.items():
            if count > 1:
                errors.append(f"Duplicate key: {key} (appears {count} times)")
        
        return len(errors) == 0, errors
    
    def get_all_variables(self) -> Dict[str, str]:
        """
        Get all variables as a dictionary.
        
        Returns:
            Dictionary of key-value pairs
        """
        return {key: line.value for key, line in self.variables.items()}
    
    def add_comment(self, comment: str):
        """
        Add a comment line.
        
        Args:
            comment: Comment text (without # prefix)
        """
        comment_line = f"# {comment}\n"
        config_line = ConfigLine(comment_line, len(self.lines) + 1)
        self.lines.append(config_line)
    
    def add_blank_line(self):
        """Add a blank line."""
        config_line = ConfigLine("\n", len(self.lines) + 1)
        self.lines.append(config_line)
