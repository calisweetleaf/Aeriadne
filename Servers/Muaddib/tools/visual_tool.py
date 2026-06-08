#!/usr/bin/env python3
"""
Visual Tool - Cross-platform visual automation and screen interaction for MCP Server

This tool provides comprehensive visual automation capabilities including screen capture,
image analysis, window management, and UI interaction. Optimized for ntelligent cross-platform support and fallback mechanisms.
"""

import base64
import io
import logging
import os
import platform
import shutil
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Platform-specific imports with fallbacks.
#
# PyAutoGUI's Linux dependency chain imports mouseinfo, which eagerly indexes
# os.environ["DISPLAY"]. In headless MCP client launches, DISPLAY may be unset
# even when the same repo works from an interactive terminal. Catch all import
# failures here so the visual module still registers and individual visual
# operations can degrade gracefully through fallbacks / explicit error messages.
DISPLAY_AVAILABLE = bool(
    os.environ.get("DISPLAY", "").strip()
    or os.environ.get("WAYLAND_DISPLAY", "").strip()
    or platform.system() != "Linux"
)
PYAUTOGUI_IMPORT_ERROR: Optional[str] = None
try:
    if not DISPLAY_AVAILABLE:
        raise RuntimeError(
            "No graphical display detected (DISPLAY/WAYLAND_DISPLAY unset)"
        )
    import pyautogui

    pyautogui.FAILSAFE = False  # Disable failsafe for automation
    PYAUTOGUI_AVAILABLE = True
except (ImportError, KeyError, RuntimeError, OSError) as exc:
    pyautogui = None  # type: ignore[assignment]
    PYAUTOGUI_AVAILABLE = False
    PYAUTOGUI_IMPORT_ERROR = str(exc)

try:
    from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageStat

    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

OCR_IMPORT_ERROR: Optional[str] = None
try:
    import pytesseract

    OCR_AVAILABLE = PIL_AVAILABLE and shutil.which("tesseract") is not None
    if not OCR_AVAILABLE and PIL_AVAILABLE:
        OCR_IMPORT_ERROR = (
            "pytesseract import succeeded but tesseract executable was not found"
        )
except ImportError as exc:
    pytesseract = None  # type: ignore[assignment]
    OCR_AVAILABLE = False
    OCR_IMPORT_ERROR = str(exc)

# Windows-specific imports
WIN32_AVAILABLE = False
if os.name == "nt":
    try:
        import win32api
        import win32con
        import win32gui
        import win32process

        WIN32_AVAILABLE = True
    except ImportError:
        pass

# macOS-specific imports
MACOS_AVAILABLE = False
if platform.system() == "Darwin":
    try:
        import AppKit
        import Quartz

        MACOS_AVAILABLE = True
    except ImportError:
        pass


class VisualTool:
    """
    Cross-platform visual automation with intelligent screen interaction and analysis
    """

    def __init__(self, data_dir: Optional[Path] = None):
        self.logger = logging.getLogger(__name__)
        configured_data_dir = os.environ.get(
            "SOVEREIGN_DATA_DIR", "/home/daeron/Somnus-MCP/data"
        ).strip()
        if not configured_data_dir:
            configured_data_dir = "/home/daeron/Somnus-MCP/data"
        self.data_dir = (
            Path(data_dir or configured_data_dir).expanduser().resolve() / "visual"
        )
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Platform detection
        self.platform = platform.system()
        self.capabilities = self._detect_capabilities()

        # Screen capture history
        self.capture_history = []
        self.max_history = 10

        self.logger.info(
            f"Visual tool initialized on {self.platform} with capabilities: {', '.join(self.capabilities)}"
        )

    def _detect_capabilities(self) -> List[str]:
        """Detect available visual automation capabilities"""
        caps = []

        if PYAUTOGUI_AVAILABLE:
            caps.append("screen_capture")
            caps.append("mouse_control")
            caps.append("keyboard_input")

        if PIL_AVAILABLE:
            caps.append("image_processing")
            caps.append("visual_analysis")

        if OCR_AVAILABLE:
            caps.append("ocr_text_search")

        if WIN32_AVAILABLE:
            caps.append("window_management")
            caps.append("advanced_windows")

        if MACOS_AVAILABLE:
            caps.append("macos_integration")

        if self.platform == "Linux" and not DISPLAY_AVAILABLE:
            caps.append("headless_mode")

        if not caps:
            caps.append("basic_fallback")

        return caps

    def get_tools(self) -> Dict[str, Any]:
        """Return all available visual tools with proper MCP formatting"""
        return {
            "bb7_take_screenshot": {
                "description": " Capture screenshots with intelligent analysis, annotation capabilities, and automatic saving. Perfect for documentation, debugging, UI testing, and visual monitoring. Provides comprehensive screen analysis with element detection, color analysis, and visual insights for development workflows.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "region": {
                            "type": "string",
                            "description": 'Screen region to capture (format: "x,y,width,height" or "fullscreen")',
                            "default": "fullscreen",
                        },
                        "save_path": {
                            "type": "string",
                            "description": "Custom path to save screenshot (auto-generated if not provided)",
                        },
                        "include_analysis": {
                            "type": "boolean",
                            "description": "Include visual analysis of the captured image",
                            "default": True,
                        },
                        "format": {
                            "type": "string",
                            "description": "Output format for screenshot",
                            "enum": ["png", "jpg", "base64"],
                            "default": "png",
                        },
                    },
                },
                "function": self.bb7_take_screenshot,
            },
            "bb7_find_on_screen": {
                "description": "🔍 Find visual elements on screen using intelligent pattern matching, color detection, and coordinate identification. Perfect for UI automation, testing, and visual debugging. Provides precise element location with confidence scoring and multiple matching strategies.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "target": {
                            "type": "string",
                            "description": "What to find (text, color, or description of visual element)",
                        },
                        "confidence": {
                            "type": "number",
                            "description": "Match confidence threshold (0.0 to 1.0)",
                            "default": 0.8,
                        },
                        "search_region": {
                            "type": "string",
                            "description": 'Region to search in (format: "x,y,width,height")',
                        },
                    },
                    "required": ["target"],
                },
                "function": self.bb7_find_on_screen,
            },
            "bb7_click_element": {
                "description": "🖱️ Click on visual elements with intelligent targeting, multiple click types, and precise positioning. Perfect for UI automation, testing workflows, and interactive debugging. Supports various click types with smart element detection and coordinate validation.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "element": {
                            "type": "string",
                            "description": 'Element to click (coordinates "x,y" or description)',
                        },
                        "click_type": {
                            "type": "string",
                            "description": "Type of click to perform",
                            "enum": ["left", "right", "double", "middle"],
                            "default": "left",
                        },
                        "offset": {
                            "type": "string",
                            "description": 'Click offset from element center (format: "x,y")',
                        },
                    },
                    "required": ["element"],
                },
                "function": self.bb7_click_element,
            },
            "bb7_screen_monitor": {
                "description": "👁️ Monitor screen for changes with intelligent change detection, activity analysis, and automated capture. Perfect for monitoring applications, detecting events, and tracking visual changes during development or testing. Provides comprehensive activity reporting.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "duration": {
                            "type": "integer",
                            "description": "Monitoring duration in seconds",
                            "default": 10,
                        },
                        "sensitivity": {
                            "type": "number",
                            "description": "Change detection sensitivity (0.0 to 1.0)",
                            "default": 0.05,
                        },
                        "capture_changes": {
                            "type": "boolean",
                            "description": "Capture screenshots when changes detected",
                            "default": True,
                        },
                    },
                },
                "function": self.bb7_screen_monitor,
            },
            "bb7_window_info": {
                "description": "🪟 Get comprehensive information about active windows and applications with intelligent analysis and management suggestions. Perfect for window management, application monitoring, and development environment optimization. Provides detailed window properties and actionable insights.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "include_all": {
                            "type": "boolean",
                            "description": "Include information about all windows",
                            "default": False,
                        },
                        "analyze_layout": {
                            "type": "boolean",
                            "description": "Analyze window layout and positioning",
                            "default": True,
                        },
                    },
                },
                "function": self.bb7_window_info,
            },
        }

    def _coerce_arguments(self, arguments: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        if arguments is None:
            return {}
        if not isinstance(arguments, dict):
            raise TypeError(
                f"visual tool arguments must be a dict, got {type(arguments).__name__}"
            )
        return arguments

    @staticmethod
    def _parse_region(
        region: Any, *, allow_fullscreen: bool = True
    ) -> Optional[Tuple[int, int, int, int]]:
        if region is None or region == "":
            return None
        region_text = str(region).strip().lower()
        if allow_fullscreen and region_text == "fullscreen":
            return None
        parts = [part.strip() for part in region_text.split(",")]
        if len(parts) != 4:
            raise ValueError("region must be 'fullscreen' or 'x,y,width,height'")
        try:
            x, y, width, height = [int(part) for part in parts]
        except ValueError as exc:
            raise ValueError("region values must be integers") from exc
        if width <= 0 or height <= 0:
            raise ValueError("region width and height must be positive")
        if x < 0 or y < 0:
            raise ValueError("region x and y must be non-negative")
        return (x, y, width, height)

    @staticmethod
    def _parse_xy(value: Any, field_name: str) -> Tuple[int, int]:
        parts = [part.strip() for part in str(value or "").split(",")]
        if len(parts) != 2:
            raise ValueError(f"{field_name} must use 'x,y' format")
        try:
            return int(parts[0]), int(parts[1])
        except ValueError as exc:
            raise ValueError(f"{field_name} values must be integers") from exc

    @staticmethod
    def _coerce_bool(value: Any) -> bool:
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            lowered = value.strip().lower()
            if lowered in {"1", "true", "yes", "on"}:
                return True
            if lowered in {"0", "false", "no", "off"}:
                return False
        return bool(value)

    @staticmethod
    def _coerce_float(
        value: Any, field_name: str, minimum: float, maximum: float
    ) -> float:
        try:
            parsed = float(value)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"{field_name} must be numeric") from exc
        if not minimum <= parsed <= maximum:
            raise ValueError(f"{field_name} must be between {minimum} and {maximum}")
        return parsed

    def _resolve_save_path(self, save_path: Any, output_format: str) -> Path:
        suffix = "jpg" if output_format == "jpg" else "png"
        if save_path:
            resolved = Path(str(save_path)).expanduser().resolve()
            if resolved.exists() and resolved.is_dir():
                raise ValueError(
                    f"save_path points to a directory, not a file: {resolved}"
                )
            resolved.parent.mkdir(parents=True, exist_ok=True)
            return resolved
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return self.data_dir / f"screenshot_{timestamp}.{suffix}"

    @staticmethod
    def _run_command(
        command: List[str], *, timeout: float = 8.0, text: bool = True
    ) -> subprocess.CompletedProcess:
        return subprocess.run(
            command,
            capture_output=True,
            text=text,
            timeout=timeout,
            check=False,
        )

    def bb7_take_screenshot(self, arguments: Dict[str, Any]) -> str:
        """
        📸 Capture screenshots with intelligent analysis, annotation capabilities, and automatic saving.
        Perfect for documentation, debugging, UI testing, and visual monitoring. Provides comprehensive
        screen analysis with element detection, color analysis, and visual insights.
        """
        try:
            arguments = self._coerce_arguments(arguments)
            region = arguments.get("region", "fullscreen")
            save_path_arg = arguments.get("save_path", "")
            include_analysis = self._coerce_bool(
                arguments.get("include_analysis", True)
            )
            output_format = str(arguments.get("format", "png")).strip().lower()
            if output_format not in {"png", "jpg", "base64"}:
                return "❌ Invalid screenshot format. Use: png, jpg, or base64"

            if not PYAUTOGUI_AVAILABLE:
                return self._fallback_screenshot()

            bbox = self._parse_region(region)
            screenshot = (
                pyautogui.screenshot(region=bbox) if bbox else pyautogui.screenshot()
            )
            save_path = self._resolve_save_path(save_path_arg, output_format)

            response = f"📸 **Screenshot Captured**\n\n"

            # Save in requested format
            if output_format == "base64":
                buffer = io.BytesIO()
                screenshot.save(buffer, format="PNG")
                encoded = base64.b64encode(buffer.getvalue()).decode()
                response += f"📋 **Base64 Data**: {len(encoded)} characters\n"
                response += (
                    f"🔗 **Preview**: data:image/png;base64,{encoded[:100]}...\n\n"
                )
            else:
                screenshot.save(
                    save_path, format="JPEG" if output_format == "jpg" else "PNG"
                )
                response += f"💾 **Saved to**: {save_path}\n"
                response += (
                    f"📏 **Dimensions**: {screenshot.width}x{screenshot.height}\n\n"
                )

            # Add to capture history
            capture_info = {
                "timestamp": time.time(),
                "path": str(save_path),
                "dimensions": (screenshot.width, screenshot.height),
                "region": region,
            }

            self.capture_history.append(capture_info)
            if len(self.capture_history) > self.max_history:
                self.capture_history.pop(0)

            # Visual analysis
            if include_analysis and PIL_AVAILABLE:
                analysis = self._analyze_screenshot(screenshot)
                colors = analysis.get("colors") if isinstance(analysis, dict) else None
                if not isinstance(colors, list) or not colors:
                    colors = ["unknown"]
                brightness = (
                    analysis.get("brightness", "unknown")
                    if isinstance(analysis, dict)
                    else "unknown"
                )
                complexity = (
                    analysis.get("complexity", "unknown")
                    if isinstance(analysis, dict)
                    else "unknown"
                )
                text_regions = (
                    analysis.get("text_regions", 0) if isinstance(analysis, dict) else 0
                )

                response += f"🔍 **Visual Analysis**:\n"
                response += f"  • **Dominant Colors**: {', '.join(colors[:3])}\n"
                response += f"  • **Brightness**: {brightness}\n"
                response += f"  • **Complexity**: {complexity}\n"
                response += f"  • **Text Regions**: {text_regions} detected\n"
                if isinstance(analysis, dict) and analysis.get("error"):
                    response += f"  • **Analysis Note**: {analysis['error']}\n"
                response += "\n"

            # Usage suggestions
            response += f"💡 **Usage Suggestions**:\n"
            response += f"  • Use bb7_find_on_screen to locate elements\n"
            response += f"  • Compare with previous captures using bb7_screen_monitor\n"
            response += f"  • Analyze specific regions for detailed inspection\n"
            response += f"  • Use for documentation or issue reporting"

            self.logger.info(
                f"Screenshot captured: {screenshot.width}x{screenshot.height}"
            )
            return response

        except (OSError, RuntimeError, ValueError, TypeError) as e:
            self.logger.error("Error capturing screenshot: %s", e)
            return f"❌ Error capturing screenshot: {str(e)}\n\n💡 **Possible solutions:**\n  • Check display permissions\n  • Try different region settings\n  • Ensure screen is accessible"

    def bb7_find_on_screen(self, arguments: Dict[str, Any]) -> str:
        """
        🔍 Find visual elements on screen using intelligent pattern matching, color detection,
        and coordinate identification. Perfect for UI automation, testing, and visual debugging.
        Provides precise element location with confidence scoring.
        """
        try:
            arguments = self._coerce_arguments(arguments)
            target = str(arguments.get("target", "")).strip()
            confidence = self._coerce_float(
                arguments.get("confidence", 0.8), "confidence", 0.0, 1.0
            )
            search_region = arguments.get("search_region", "")

            if not target:
                return "❌ Please specify what to find on screen (text, color, or element description)"

            if not PYAUTOGUI_AVAILABLE:
                return "❌ Screen automation not available on this platform"

            response = f'🔍 **Screen Search for**: "{target}"\n\n'

            region = None
            if search_region:
                try:
                    region = self._parse_region(search_region, allow_fullscreen=False)
                except ValueError as exc:
                    response += (
                        f"⚠️ Invalid search region format ({exc}), using full screen\n\n"
                    )

            # Take screenshot for analysis
            screenshot = pyautogui.screenshot(region=region)

            # Try different search strategies
            found_elements = []

            # Strategy 1: Text-based search (if target looks like text)
            if target.replace(" ", "").isalnum():
                locations = self._find_text_on_screen(screenshot, target, confidence)
                found_elements.extend(locations)
                if not locations and not OCR_AVAILABLE:
                    response += f"⚠️ OCR text search unavailable: {OCR_IMPORT_ERROR or 'pytesseract/tesseract unavailable'}\n\n"

            # Strategy 2: Color search (if target looks like a color)
            if any(
                color in target.lower()
                for color in ["red", "blue", "green", "white", "black", "yellow"]
            ):
                color_locations = self._find_color_on_screen(screenshot, target)
                found_elements.extend(color_locations)

            # Strategy 3: UI element search (buttons, inputs, etc.)
            if any(
                ui in target.lower()
                for ui in ["button", "input", "text", "field", "box", "menu"]
            ):
                ui_locations = self._find_ui_elements(screenshot, target)
                found_elements.extend(ui_locations)

            if found_elements:
                response += f"✅ **Found {len(found_elements)} matches**:\n\n"

                for i, (x, y, conf, method) in enumerate(found_elements[:5], 1):
                    # Adjust coordinates if search region was used
                    if region:
                        x += region[0]
                        y += region[1]

                    response += f"**Match {i}**:\n"
                    response += f"  • **Position**: ({x}, {y})\n"
                    response += f"  • **Confidence**: {conf:.2f}\n"
                    response += f"  • **Method**: {method}\n"
                    response += (
                        f'  • **Action**: Use bb7_click_element element="{x},{y}"\n\n'
                    )

                if len(found_elements) > 5:
                    response += f"... and {len(found_elements) - 5} more matches\n\n"

                # Best match recommendation
                best_match = max(found_elements, key=lambda x: x[2])
                response += f"🎯 **Best Match**: ({best_match[0]}, {best_match[1]}) with {best_match[2]:.2f} confidence\n\n"

            else:
                response += f"❌ **No matches found**\n\n"
                response += f"💡 **Suggestions**:\n"
                response += f"  • Try a more specific description\n"
                response += f"  • Lower the confidence threshold\n"
                response += f"  • Use bb7_take_screenshot to see current screen\n"
                response += f"  • Try searching for colors or UI element types\n\n"

            response += f"🔧 **Search Parameters**:\n"
            response += f'  • Target: "{target}"\n'
            response += f"  • Confidence: {confidence}\n"
            response += f"  • Region: {search_region or 'Full screen'}\n"
            response += f"  • Available methods: Text, Color, UI Elements"

            self.logger.info(
                f"Screen search for '{target}': {len(found_elements)} matches"
            )
            return response

        except (OSError, RuntimeError, ValueError, TypeError) as e:
            self.logger.error("Error finding element on screen: %s", e)
            return f"❌ Error finding element: {str(e)}"

    def bb7_click_element(self, arguments: Dict[str, Any]) -> str:
        """
        🖱️ Click on visual elements with intelligent targeting, multiple click types, and precise
        positioning. Perfect for UI automation, testing workflows, and interactive debugging.
        Supports various click types with smart element detection.
        """
        try:
            arguments = self._coerce_arguments(arguments)
            element = str(arguments.get("element", "")).strip()
            click_type = str(arguments.get("click_type", "left")).strip().lower()
            offset = arguments.get("offset", "")

            if not element:
                return "❌ Please specify element to click (coordinates 'x,y' or use bb7_find_on_screen first)"

            if not PYAUTOGUI_AVAILABLE:
                return "❌ Mouse control not available on this platform"

            x, y = self._parse_xy(element, "element")
            if offset:
                offset_x, offset_y = self._parse_xy(offset, "offset")
                x += offset_x
                y += offset_y

            # Validate coordinates are within screen bounds
            screen_width, screen_height = pyautogui.size()
            if not (0 <= x <= screen_width and 0 <= y <= screen_height):
                return f"❌ Coordinates ({x}, {y}) are outside screen bounds ({screen_width}x{screen_height})"

            response = f"🖱️ **Click Action**\n\n"
            response += f"📍 **Target**: ({x}, {y})\n"
            response += f"🔘 **Click Type**: {click_type}\n"

            # Perform the click
            start_time = time.time()

            if click_type == "left":
                pyautogui.click(x, y)
            elif click_type == "right":
                pyautogui.rightClick(x, y)
            elif click_type == "double":
                pyautogui.doubleClick(x, y)
            elif click_type == "middle":
                pyautogui.middleClick(x, y)
            else:
                return f"❌ Invalid click type. Use: left, right, double, or middle"

            click_time = time.time() - start_time

            response += f"⏱️ **Execution Time**: {click_time:.3f} seconds\n\n"
            response += f"✅ **Click performed successfully**\n\n"

            # Post-click analysis
            response += f"💡 **Post-Click Suggestions**:\n"
            response += f"  • Use bb7_take_screenshot to verify the result\n"
            response += f"  • Monitor for UI changes with bb7_screen_monitor\n"
            response += f"  • Chain multiple clicks for complex interactions\n"
            response += f"  • Use bb7_find_on_screen to locate next elements"

            self.logger.info(f"Clicked at ({x}, {y}) with {click_type} click")
            return response

        except (OSError, RuntimeError, ValueError, TypeError) as e:
            self.logger.error("Error clicking element: %s", e)
            return f"❌ Error performing click: {str(e)}"

    def bb7_screen_monitor(self, arguments: Dict[str, Any]) -> str:
        """
        👁️ Monitor screen for changes with intelligent change detection, activity analysis, and
        automated capture. Perfect for monitoring applications, detecting events, and tracking
        visual changes during development or testing.
        """
        try:
            arguments = self._coerce_arguments(arguments)
            try:
                duration = int(arguments.get("duration", 10))
            except (TypeError, ValueError) as exc:
                raise ValueError(
                    "duration must be an integer number of seconds"
                ) from exc
            if not 1 <= duration <= 120:
                raise ValueError("duration must be between 1 and 120 seconds")
            sensitivity = self._coerce_float(
                arguments.get("sensitivity", 0.05), "sensitivity", 0.0, 1.0
            )
            capture_changes = self._coerce_bool(arguments.get("capture_changes", True))

            if not PYAUTOGUI_AVAILABLE:
                return "❌ Screen monitoring not available on this platform"

            response = f"👁️ **Screen Monitoring Started**\n\n"
            response += f"⏱️ **Duration**: {duration} seconds\n"
            response += f"🎯 **Sensitivity**: {sensitivity}\n"
            response += f"📸 **Capture Changes**: {capture_changes}\n\n"

            # Take initial screenshot
            initial_screenshot = pyautogui.screenshot()
            start_time = time.time()
            changes_detected = []
            last_screenshot = initial_screenshot

            response += f"🚀 **Monitoring in progress...**\n\n"

            # Monitoring loop
            check_interval = 0.5  # Check every 500ms
            checks_performed = 0

            while time.time() - start_time < duration:
                time.sleep(check_interval)
                checks_performed += 1

                # Take new screenshot
                current_screenshot = pyautogui.screenshot()

                # Calculate difference
                if PIL_AVAILABLE:
                    change_level = self._calculate_image_difference(
                        last_screenshot, current_screenshot
                    )

                    if change_level > sensitivity:
                        change_info = {
                            "timestamp": time.time() - start_time,
                            "change_level": change_level,
                            "screenshot": current_screenshot
                            if capture_changes
                            else None,
                        }
                        changes_detected.append(change_info)

                        # Save screenshot if requested
                        if capture_changes:
                            timestamp = datetime.now().strftime("%H%M%S")
                            save_path = self.data_dir / f"change_{timestamp}.png"
                            current_screenshot.save(save_path)
                            change_info["saved_path"] = str(save_path)

                        last_screenshot = current_screenshot

            # Build results
            response += f"📊 **Monitoring Complete**\n\n"
            response += f"⏱️ **Total Duration**: {duration} seconds\n"
            response += f"🔍 **Checks Performed**: {checks_performed}\n"
            response += f"📈 **Changes Detected**: {len(changes_detected)}\n\n"

            if changes_detected:
                response += f"🎯 **Change Events**:\n"
                for i, change in enumerate(changes_detected[:10], 1):
                    timestamp = change["timestamp"]
                    level = change["change_level"]
                    response += (
                        f"  {i}. Time: {timestamp:.1f}s | Intensity: {level:.3f}\n"
                    )
                    if change.get("saved_path"):
                        response += (
                            f"     📸 Saved: {Path(change['saved_path']).name}\n"
                        )

                if len(changes_detected) > 10:
                    response += f"  ... and {len(changes_detected) - 10} more changes\n"

                response += "\n"

                # Analysis
                avg_change = sum(c["change_level"] for c in changes_detected) / len(
                    changes_detected
                )
                max_change = max(c["change_level"] for c in changes_detected)

                response += f"📈 **Activity Analysis**:\n"
                response += f"  • **Average Change Intensity**: {avg_change:.3f}\n"
                response += f"  • **Maximum Change**: {max_change:.3f}\n"
                response += f"  • **Activity Level**: "

                if avg_change > 0.2:
                    response += "High - significant screen activity\n"
                elif avg_change > 0.1:
                    response += "Moderate - regular updates\n"
                else:
                    response += "Low - minimal changes\n"

            else:
                response += f"😴 **No significant changes detected**\n"
                response += f"Screen remained stable during monitoring period\n\n"

            response += f"💡 **Next Steps**:\n"
            response += f"  • Review captured screenshots for details\n"
            response += f"  • Adjust sensitivity for different change types\n"
            response += f"  • Use longer monitoring for extended analysis\n"
            response += f"  • Combine with other visual tools for automation"

            self.logger.info(
                f"Screen monitoring complete: {len(changes_detected)} changes in {duration}s"
            )
            return response

        except (OSError, RuntimeError, ValueError, TypeError) as e:
            self.logger.error("Error monitoring screen: %s", e)
            return f"❌ Error monitoring screen: {str(e)}"

    def bb7_window_info(self, arguments: Dict[str, Any]) -> str:
        """
        🪟 Get comprehensive information about active windows and applications with intelligent
        analysis and management suggestions. Perfect for window management, application monitoring,
        and development environment optimization.
        """
        try:
            arguments = self._coerce_arguments(arguments)
            include_all = self._coerce_bool(arguments.get("include_all", False))
            analyze_layout = self._coerce_bool(arguments.get("analyze_layout", True))

            response = f"🪟 **Window Information Analysis**\n\n"
            response += f"💻 **Platform**: {self.platform}\n"
            response += (
                f"🎯 **Scope**: {'All windows' if include_all else 'Active window'}\n\n"
            )

            if WIN32_AVAILABLE and self.platform == "Windows":
                return self._get_windows_window_info(include_all, analyze_layout)
            elif MACOS_AVAILABLE and self.platform == "Darwin":
                return self._get_macos_window_info(include_all, analyze_layout)
            else:
                return self._get_generic_window_info()

        except (OSError, RuntimeError, ValueError, TypeError) as e:
            self.logger.error("Error getting window info: %s", e)
            return f"❌ Error getting window information: {str(e)}"

    # Helper methods for visual processing

    def _fallback_screenshot(self) -> str:
        """Fallback screenshot method when pyautogui is not available"""
        try:
            # Try system screenshot commands
            if self.platform == "Windows":
                # Use PowerShell screenshot
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                save_path = self.data_dir / f"screenshot_{timestamp}.png"

                cmd = f'''
                Add-Type -AssemblyName System.Windows.Forms
                $screen = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds
                $bitmap = New-Object System.Drawing.Bitmap $screen.Width, $screen.Height
                $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
                $graphics.CopyFromScreen($screen.Location, [System.Drawing.Point]::Empty, $screen.Size)
                $bitmap.Save("{save_path}")
                '''

                if shutil.which("powershell") is None:
                    return "❌ **PowerShell screenshot unavailable**: powershell executable not found"
                result = self._run_command(
                    ["powershell", "-Command", cmd], timeout=10.0
                )
                if result.returncode == 0:
                    return f"📸 **Screenshot captured using PowerShell**\n💾 **Saved to**: {save_path}"

            elif self.platform == "Darwin":
                # Use macOS screencapture
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                save_path = self.data_dir / f"screenshot_{timestamp}.png"

                if shutil.which("screencapture") is None:
                    return "❌ **macOS screenshot unavailable**: screencapture executable not found"
                result = self._run_command(
                    ["screencapture", str(save_path)], timeout=10.0, text=False
                )
                if result.returncode == 0:
                    return f"📸 **Screenshot captured using screencapture**\n💾 **Saved to**: {save_path}"

            elif self.platform == "Linux":
                # Try various Linux screenshot tools
                tools = ["gnome-screenshot", "scrot", "import"]
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                save_path = self.data_dir / f"screenshot_{timestamp}.png"

                for tool in tools:
                    if shutil.which(tool) is None:
                        continue
                    try:
                        if tool == "gnome-screenshot":
                            result = self._run_command(
                                [tool, "-f", str(save_path)], timeout=10.0, text=False
                            )
                        elif tool == "scrot":
                            result = self._run_command(
                                [tool, str(save_path)], timeout=10.0, text=False
                            )
                        else:
                            result = self._run_command(
                                [tool, "-window", "root", str(save_path)],
                                timeout=10.0,
                                text=False,
                            )

                        if result.returncode == 0:
                            return f"📸 **Screenshot captured using {tool}**\n💾 **Saved to**: {save_path}"
                    except subprocess.TimeoutExpired:
                        self.logger.warning("Screenshot command timed out: %s", tool)
                        continue

            return "❌ **Screenshot not available**\n\n💡 **Install requirements:**\n  • pip install pyautogui pillow\n  • Platform-specific screenshot tools"

        except (OSError, RuntimeError, ValueError, subprocess.TimeoutExpired) as e:
            self.logger.error("Fallback screenshot failed: %s", e)
            return f"❌ **Fallback screenshot failed**: {str(e)}"

    def _analyze_screenshot(self, image) -> Dict[str, Any]:
        """Analyze screenshot for visual characteristics"""
        if not PIL_AVAILABLE:
            return {"error": "PIL not available"}

        try:
            # Convert to RGB if necessary
            if image.mode != "RGB":
                image = image.convert("RGB")

            # Get dominant colors
            colors = image.getcolors(maxcolors=256 * 256 * 256)
            if colors:
                sorted_colors = sorted(colors, key=lambda x: x[0], reverse=True)
                dominant_colors = []
                for count, color in sorted_colors[:5]:
                    r, g, b = color
                    hex_color = f"#{r:02x}{g:02x}{b:02x}"
                    dominant_colors.append(hex_color)
            else:
                dominant_colors = ["#000000"]

            grayscale = image.convert("L")
            brightness = (
                (ImageStat.Stat(grayscale).mean[0] / 255.0)
                if image.width and image.height
                else 0.0
            )
            edge_image = grayscale.filter(ImageFilter.FIND_EDGES)
            edge_mean = ImageStat.Stat(edge_image).mean[0] / 255.0
            complexity = min(edge_mean * 3.0, 1.0)
            histogram = grayscale.histogram()
            midpoint = sum(
                index * count for index, count in enumerate(histogram)
            ) / max(sum(histogram), 1)
            high_contrast_pixels = sum(
                count
                for index, count in enumerate(histogram)
                if abs(index - midpoint) > 60
            )
            text_regions = int(
                high_contrast_pixels / max(image.width * image.height, 1) * 1000
            )

            return {
                "colors": dominant_colors,
                "brightness": f"{brightness:.2f}",
                "complexity": f"{complexity:.2f}",
                "text_regions": text_regions,
            }

        except (OSError, RuntimeError, ValueError, TypeError) as e:
            return {"error": f"Analysis failed: {str(e)}"}

    def _find_text_on_screen(
        self, screenshot, text: str, confidence: float
    ) -> List[Tuple[int, int, float, str]]:
        """Find text on screen using OCR when pytesseract and tesseract are available."""
        if not OCR_AVAILABLE or pytesseract is None:
            return []
        try:
            data = pytesseract.image_to_data(
                screenshot, output_type=pytesseract.Output.DICT
            )
        except (RuntimeError, OSError, ValueError, TypeError) as exc:
            self.logger.warning("OCR search failed for target %r: %s", text, exc)
            return []

        target = text.strip().lower()
        matches: List[Tuple[int, int, float, str]] = []
        for idx, raw_text in enumerate(data.get("text", [])):
            candidate = str(raw_text or "").strip()
            if not candidate:
                continue
            candidate_lower = candidate.lower()
            if target not in candidate_lower and candidate_lower not in target:
                continue
            try:
                conf = float(data.get("conf", [0])[idx]) / 100.0
                left = int(data.get("left", [0])[idx])
                top = int(data.get("top", [0])[idx])
                width = int(data.get("width", [0])[idx])
                height = int(data.get("height", [0])[idx])
            except (TypeError, ValueError, IndexError):
                continue
            if conf >= confidence:
                matches.append((left + width // 2, top + height // 2, conf, "ocr_text"))
        return matches[:10]

    def _find_color_on_screen(
        self, screenshot, color_description: str
    ) -> List[Tuple[int, int, float, str]]:
        """Find colors on screen"""
        if not PIL_AVAILABLE:
            return []

        locations = []

        # Simple color mapping
        color_map = {
            "red": (255, 0, 0),
            "green": (0, 255, 0),
            "blue": (0, 0, 255),
            "white": (255, 255, 255),
            "black": (0, 0, 0),
            "yellow": (255, 255, 0),
        }

        for color_name, target_rgb in color_map.items():
            if color_name in color_description.lower():
                # Find pixels matching this color (simplified)
                pixels = screenshot.load()
                width, height = screenshot.size

                for y in range(0, height, 50):  # Sample every 50 pixels
                    for x in range(0, width, 50):
                        r, g, b = pixels[x, y][:3]

                        # Calculate color distance
                        distance = sum(
                            abs(a - b) for a, b in zip((r, g, b), target_rgb)
                        )
                        if distance < 100:  # Threshold for color similarity
                            confidence = 1.0 - (distance / 765.0)  # Normalize to 0-1
                            locations.append((x, y, confidence, f"color_{color_name}"))

        return locations[:10]  # Return max 10 locations

    def _find_ui_elements(
        self, screenshot, element_description: str
    ) -> List[Tuple[int, int, float, str]]:
        """Find UI elements using simple heuristics"""
        if not PIL_AVAILABLE:
            return []

        locations = []

        # Convert to grayscale for edge detection
        gray = screenshot.convert("L")
        width, height = gray.size

        # Simple edge detection for rectangular UI elements
        pixels = gray.load()

        for y in range(10, height - 10, 20):
            for x in range(10, width - 10, 20):
                # Check for rectangular patterns (simplified)
                current = pixels[x, y]
                right = pixels[x + 10, y]
                down = pixels[x, y + 10]

                # Look for strong edges that might indicate UI elements
                if abs(current - right) > 50 or abs(current - down) > 50:
                    confidence = 0.5  # Low confidence for basic detection
                    locations.append((x, y, confidence, "ui_element"))

        return locations[:5]  # Return max 5 locations

    def _calculate_image_difference(self, img1, img2) -> float:
        """Calculate difference between two images"""
        if not PIL_AVAILABLE:
            return 0.0

        try:
            # Ensure same size
            if img1.size != img2.size:
                img2 = img2.resize(img1.size)

            # Calculate difference
            diff = ImageChops.difference(img1, img2)

            # Convert to grayscale and get histogram
            diff_gray = diff.convert("L")
            histogram = diff_gray.histogram()

            # Calculate change percentage
            total_pixels = sum(histogram)
            changed_pixels = sum(histogram[1:])  # Exclude pixels with 0 difference

            if total_pixels == 0:
                return 0.0

            return changed_pixels / total_pixels

        except (OSError, RuntimeError, ValueError, TypeError) as e:
            self.logger.error("Error calculating image difference: %s", e)
            return 0.0

    def _get_windows_window_info(self, include_all: bool, analyze_layout: bool) -> str:
        """Get Windows-specific window information"""
        if not WIN32_AVAILABLE:
            return "❌ Windows-specific features not available"

        try:
            response = f"🪟 **Windows Window Analysis**\n\n"

            # Get active window
            hwnd = win32gui.GetForegroundWindow()
            if hwnd:
                title = win32gui.GetWindowText(hwnd)
                rect = win32gui.GetWindowRect(hwnd)
                _, pid = win32process.GetWindowThreadProcessId(hwnd)

                response += f"🎯 **Active Window**:\n"
                response += f"  • **Title**: {title}\n"
                response += f"  • **Handle**: {hwnd}\n"
                response += f"  • **Process ID**: {pid}\n"
                response += f"  • **Position**: ({rect[0]}, {rect[1]})\n"
                response += f"  • **Size**: {rect[2] - rect[0]}x{rect[3] - rect[1]}\n"

                # Window state (defensive across pywin32 surface differences)
                state = "Normal"
                if win32gui.IsIconic(hwnd):
                    state = "Minimized"
                else:
                    # Some environments don't expose win32gui.IsZoomed.
                    try:
                        if hasattr(win32gui, "IsZoomed") and win32gui.IsZoomed(hwnd):
                            state = "Maximized"
                        else:
                            placement = win32gui.GetWindowPlacement(hwnd)
                            show_cmd = (
                                placement[1]
                                if isinstance(placement, tuple) and len(placement) > 1
                                else None
                            )
                            if show_cmd in {
                                getattr(win32con, "SW_MAXIMIZE", 3),
                                getattr(win32con, "SW_SHOWMAXIMIZED", 3),
                            }:
                                state = "Maximized"
                    except (AttributeError, TypeError, OSError):
                        self.logger.debug(
                            "Windows placement inspection unavailable for hwnd=%s", hwnd
                        )

                response += f"  • **State**: {state}\n"

                response += "\n"

            if include_all:
                # Get all visible windows
                windows = []

                def enum_windows_callback(hwnd, windows):
                    if win32gui.IsWindowVisible(hwnd):
                        title = win32gui.GetWindowText(hwnd)
                        if title:  # Only include windows with titles
                            windows.append((hwnd, title))
                    return True

                win32gui.EnumWindows(enum_windows_callback, windows)

                response += f"📋 **All Visible Windows** ({len(windows)} total):\n"
                for i, (hwnd, title) in enumerate(windows[:10], 1):
                    response += (
                        f"  {i}. {title[:50]}{'...' if len(title) > 50 else ''}\n"
                    )

                if len(windows) > 10:
                    response += f"  ... and {len(windows) - 10} more windows\n"

                response += "\n"

            response += f"💡 **Window Management Tips**:\n"
            response += f"  • Use window handles for precise targeting\n"
            response += f"  • Monitor window state changes\n"
            response += f"  • Consider window positioning for automation"

            return response

        except (OSError, RuntimeError, ValueError, TypeError) as e:
            self.logger.error("Error getting Windows window info: %s", e)
            return f"❌ Error getting Windows window info: {str(e)}"

    def _get_macos_window_info(self, include_all: bool, analyze_layout: bool) -> str:
        """Get macOS-specific window information"""
        try:
            response = f"🪟 **macOS Window Analysis**\n\n"
            response += f"🍎 **Platform**: macOS\n"
            response += f"⚠️ **Note**: Advanced window management requires accessibility permissions\n\n"

            # Basic system info
            try:
                # Get active application
                from AppKit import NSWorkspace

                workspace = NSWorkspace.sharedWorkspace()
                active_app = workspace.activeApplication()

                if active_app:
                    response += f"🎯 **Active Application**:\n"
                    response += f"  • **Name**: {active_app.get('NSApplicationName', 'Unknown')}\n"
                    response += f"  • **Bundle ID**: {active_app.get('NSApplicationBundleIdentifier', 'Unknown')}\n"
                    response += f"  • **Process ID**: {active_app.get('NSApplicationProcessIdentifier', 'Unknown')}\n\n"

                if include_all:
                    running_apps = workspace.runningApplications()
                    response += (
                        f"📋 **Running Applications** ({len(running_apps)} total):\n"
                    )
                    for app in running_apps[:10]:
                        name = app.localizedName()
                        if name:
                            response += f"  • {name}\n"

                    if len(running_apps) > 10:
                        response += (
                            f"  ... and {len(running_apps) - 10} more applications\n"
                        )

                    response += "\n"

            except (OSError, RuntimeError, AttributeError, TypeError) as e:
                response += f"⚠️ **Limited access**: {str(e)}\n\n"

            response += f"💡 **macOS Tips**:\n"
            response += (
                f"  • Enable accessibility permissions for full window control\n"
            )
            response += f"  • Use Mission Control for window overview\n"
            response += f"  • Consider AppleScript for advanced automation"

            return response

        except (OSError, RuntimeError, AttributeError, TypeError) as e:
            self.logger.error("Error getting macOS window info: %s", e)
            return f"❌ Error getting macOS window info: {str(e)}"

    def _get_generic_window_info(self) -> str:
        """Get generic window information for unsupported platforms"""
        response = f"🪟 **Generic Window Information**\n\n"
        response += f"💻 **Platform**: {self.platform}\n"
        response += f"🔧 **Capabilities**: {', '.join(self.capabilities)}\n\n"

        if PYAUTOGUI_AVAILABLE:
            # Get screen size
            screen_width, screen_height = pyautogui.size()
            response += f"📺 **Screen Information**:\n"
            response += f"  • **Resolution**: {screen_width}x{screen_height}\n"
            response += f"  • **Available**: Screen capture, mouse control\n\n"

        response += f"⚠️ **Platform Limitations**:\n"
        response += f"  • Advanced window management not available\n"
        response += f"  • Limited to basic screen operations\n"
        response += f"  • Consider platform-specific tools for full control\n\n"

        response += f"💡 **Available Operations**:\n"
        response += f"  • Screenshot capture\n"
        response += f"  • Basic mouse and keyboard control\n"
        response += f"  • Screen monitoring and change detection"

        return response


# For standalone testing
if __name__ == "__main__":
    import sys

    def _safe_print(label: str, value: str) -> None:
        text = f"{label}\n{value}\n"
        if hasattr(sys.stdout, "reconfigure"):
            try:
                sys.stdout.reconfigure(encoding="utf-8")
                print(text)
                return
            except (OSError, UnicodeError):
                pass
        # Fallback for consoles that cannot print emoji/unicode safely.
        print(text.encode("ascii", errors="ignore").decode("ascii"))

    logging.basicConfig(level=logging.INFO)
    tool = VisualTool()

    _safe_print("=== Testing Visual Tool ===", "")
    _safe_print(
        "Screenshot result:",
        tool.bb7_take_screenshot({"include_analysis": False, "format": "png"}),
    )
    _safe_print("Window info:", tool.bb7_window_info({}))
