### Visual Automation Tools (`visual_tool.py`)

`tools/visual_tool.py` exposes cross-platform visual automation surfaces for screen capture, screen search, mouse clicks, screen-change monitoring, and window information. The module is safe to load in headless Linux MCP processes: if `DISPLAY`/`WAYLAND_DISPLAY` or PyAutoGUI dependencies are unavailable, the tool registers and returns explicit degraded/fallback messages instead of failing module import.

Runtime characteristics:
- Uses the canonical data root (`SOVEREIGN_DATA_DIR` or `/home/daeron/Somnus-MCP/data`) and writes visual artifacts under `data/visual/` by default.
- Detects capabilities at construction: screen capture, mouse control, image processing, OCR text search, platform window APIs, headless mode, or fallback mode.
- PyAutoGUI is optional and disabled automatically in headless Linux launches.
- PIL/Pillow enables image analysis and image-difference monitoring.
- OCR text search requires both `pytesseract` import and the `tesseract` executable; otherwise text search reports OCR unavailable instead of pretending to match text.
- Fallback screenshot commands use explicit executable discovery and bounded subprocess timeouts.

#### `bb7_take_screenshot`

Capture a screenshot with optional region selection, visual analysis, and multiple output formats.
**Internal Composition**: Validates arguments with `_coerce_arguments()`, `_parse_region()`, `_coerce_bool()`, and `_resolve_save_path()`. Uses `pyautogui.screenshot()` when available, otherwise `_fallback_screenshot()` tries platform screenshot commands. Optional analysis is performed by `_analyze_screenshot()` using PIL only, without NumPy.

- **Parameters**:
  - `region` (string, optional): Screen region. Use `fullscreen` or `x,y,width,height`. Width/height must be positive and x/y non-negative.
  - `save_path` (string, optional): Custom file path. If omitted, saves under `data/visual/screenshot_*.png|jpg`.
  - `include_analysis` (boolean, optional): Include visual analysis of colors, brightness, complexity, and high-contrast/text-like regions (default: `true`).
  - `format` (string, optional): `png`, `jpg`, or `base64` (default: `png`).

#### `bb7_find_on_screen`

Locate visual elements on screen using available OCR, color detection, and UI-element heuristics.
**Internal Composition**: Validates target, confidence, and search region. Captures the current screen using PyAutoGUI, then dispatches to `_find_text_on_screen()`, `_find_color_on_screen()`, and/or `_find_ui_elements()` depending on the target description.

- **Parameters**:
  - `target` (string, required): Text, color name, or UI description to find.
  - `confidence` (number, optional): Match confidence threshold from `0.0` to `1.0` (default: `0.8`).
  - `search_region` (string, optional): Region to search in `x,y,width,height` format.

Operational notes:
- Text search is real OCR only when `pytesseract` and `tesseract` are available.
- Color search supports basic named colors (`red`, `green`, `blue`, `white`, `black`, `yellow`) through sampled pixel-distance matching.
- UI-element search is heuristic edge/rectangle detection and returns low-confidence candidates.

#### `bb7_click_element`

Perform mouse clicks on validated screen coordinates.
**Internal Composition**: Validates argument shape, parses `element` and optional `offset` using `_parse_xy()`, bounds-checks coordinates against `pyautogui.size()`, and executes a PyAutoGUI click method.

- **Parameters**:
  - `element` (string, required): Coordinates in `x,y` format. Element-description clicking is not implicit; use `bb7_find_on_screen` first, then pass the returned coordinates.
  - `click_type` (string, optional): `left`, `right`, `double`, or `middle` (default: `left`).
  - `offset` (string, optional): Offset in `x,y` format applied after coordinate parsing.

#### `bb7_screen_monitor`

Monitor the screen for visual changes over a bounded duration.
**Internal Composition**: Validates and clamps operational inputs, captures an initial screenshot with PyAutoGUI, then samples every 500ms. Deltas are calculated with `_calculate_image_difference()` using `PIL.ImageChops`; change screenshots are saved under `data/visual/change_*.png` when requested.

- **Parameters**:
  - `duration` (integer, optional): Monitoring duration in seconds, bounded to `1..120` (default: `10`).
  - `sensitivity` (number, optional): Change threshold from `0.0` to `1.0` (default: `0.05`).
  - `capture_changes` (boolean, optional): Save screenshots when changes are detected (default: `true`).

#### `bb7_window_info`

Get platform-specific active/all-window information where supported, with explicit fallback on unsupported/headless environments.
**Internal Composition**: Uses Windows `pywin32` APIs when available, macOS AppKit/Quartz when available, and `_get_generic_window_info()` otherwise.

- **Parameters**:
  - `include_all` (boolean, optional): Include all visible/running windows/apps where supported (default: `false`).
  - `analyze_layout` (boolean, optional): Reserved for platform layout analysis where supported (default: `true`).

#### Headless and dependency behavior

- Headless Linux: module registers with `headless_mode`; screenshot/click/monitor operations return explicit unavailable/fallback messages.
- Missing PyAutoGUI: screenshot may still succeed through platform fallback commands; click/search/monitor require PyAutoGUI.
- Missing PIL: screenshot capture can still work, but analysis and screen-difference monitoring are unavailable/degraded.
- Missing OCR: text search reports OCR unavailable and still attempts color/UI strategies when applicable.
