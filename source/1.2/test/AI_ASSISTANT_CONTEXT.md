# AI Context: DCS Translation Tool Project Summary

This document provides a high-level overview of the DCS Translation Tool (DCSTT) project to help an AI assistant quickly get up to speed.

## Project Overview
DCSTT is a specialized utility for translating and managing resources within DCS World mission files (`.miz`). It handles `.lua` parsing, text translations via `.dictionary` files, and management of audio/image resources.

## Core Architecture & File Structure

### 1. [main.py](file:///c:/Users/Andrei/Desktop/DCS%20translator%20TOOL/main.py) (The Heart)
- **Class**: [TranslationApp](file:///c:/Users/Andrei/Desktop/DCS%20translator%20TOOL/main.py#143-11055) (QMainWindow)
- **Role**: Entry point, main window UI, global settings management, and central event hub.
- **Key Features**:
    - Project loading (`.miz`, `.cmp`, `.lua`, `.txt`).
    - Grid-based translation editor with "Zebra" styling.
    - Global volume control via [set_audio_volume](file:///c:/Users/Andrei/Desktop/DCS%20translator%20TOOL/main.py#10787-10810).
    - Settings persistence ([translation_tool_settings.json](file:///c:/Users/Andrei/Desktop/DCS%20translator%20TOOL/translation_tool_settings.json)).
    - Integration with all other sub-windows.

### 2. [manager.py](file:///c:/Users/Andrei/Desktop/DCS%20translator%20TOOL/manager.py) (Resource Management)
- **Class**: [FileManagerWidget](file:///c:/Users/Andrei/Desktop/DCS%20translator%20TOOL/manager.py#751-3103)
- **Role**: A "File Manager" view for the contents of the `.miz` archive.
- **Key Features**:
    - Listing all files in `l10n/DEFAULT/` and `l10n/RU/` (or current locale).
    - Audio preview player with waveform/progress visualization.
    - Image preview with transparency support.
    - Batch export/import and drag-and-drop support.

### 3. [dialogs.py](file:///c:/Users/Andrei/Desktop/DCS%20translator%20TOOL/dialogs.py) (UI Components)
- **Classes**: [AudioPlayerDialog](file:///c:/Users/Andrei/Desktop/DCS%20translator%20TOOL/dialogs.py#943-1606), [FilesWindow](file:///c:/Users/Andrei/Desktop/DCS%20translator%20TOOL/dialogs.py#2257-2354), [AIContextWindow](file:///c:/Users/Andrei/Desktop/DCS%20translator%20TOOL/dialogs.py#1608-2072), etc.
- **Role**: Contains all modal and non-modal sub-dialogs.
- **Key Note**: [AudioPlayerDialog](file:///c:/Users/Andrei/Desktop/DCS%20translator%20TOOL/dialogs.py#943-1606) is the main audio player used for translating subtitles. It communicates with [main.py](file:///c:/Users/Andrei/Desktop/DCS%20translator%20TOOL/main.py) for volume synchronization.

### 4. [miz_resources.py](file:///c:/Users/Andrei/Desktop/DCS%20translator%20TOOL/miz_resources.py) (Core Logic)
- **Class**: [MizResourceManager](file:///c:/Users/Andrei/Desktop/DCS%20translator%20TOOL/miz_resources.py#22-958)
- **Role**: Handles the heavy lifting of parsing `.miz` internals.
- **Logic**:
    - Parses [mission](file:///c:/Users/Andrei/Desktop/DCS%20translator%20TOOL/dialogs.py#2487-2492) file to link `DictKey_subtitle` (text) to `ResKey` (audio).
    - Parses `mapResource` to link `ResKey` to physical filenames.
    - Implements **Heuristics Stage 4**: Matches "orphan" audio files to subtitles based on numeric ID proximity.

### 5. Supporting Modules
- [localization.py](file:///c:/Users/Andrei/Desktop/DCS%20translator%20TOOL/localization.py): UI translation system (`get_translation`).
- [widgets.py](file:///c:/Users/Andrei/Desktop/DCS%20translator%20TOOL/widgets.py): Custom UI components (sliders, toggles, preview areas).
- [error_logger.py](file:///c:/Users/Andrei/Desktop/DCS%20translator%20TOOL/error_logger.py): Centralized error tracking.

## Recent Critical Changes (Audio Sync & UI)
- **Centralized Volume**: `TranslationApp.set_audio_volume` is now the single source of truth for volume. It syncs the Main Player, File Manager Preview, and `pygame` mixer simultaneously.
- **Focus Management**: Most UI buttons in audio players use `Qt.NoFocus` to prevent ugly blue focus boxes when using arrow keys for translation navigation.
- **Stop Button Fix**: The File Manager's stop button now correctly resets the seeker to 00:00.

## Implementation Patterns to Follow
- **Styling**: Uses a custom CSS-like string system defined in [main.py](file:///c:/Users/Andrei/Desktop/DCS%20translator%20TOOL/main.py) and [widgets.py](file:///c:/Users/Andrei/Desktop/DCS%20translator%20TOOL/widgets.py).
- **Async/Background**: Long operations (saving/loading/thumbnails) should use `QThread` or `QTimer` to avoid freezing the UI.
- **Resource Access**: Always use [resource_path()](file:///c:/Users/Andrei/Desktop/DCS%20translator%20TOOL/dialogs.py#14-21) for icons/images to ensure PyInstaller compatibility.
- **Settings**: Use `self.parent().save_settings()` for immediate persistence when modifying global states like volume or UI toggles.

## Common Key Prefixes
- `DictKey_`: Used for translation strings in `.dictionary`.
- `ResKey_`: Used for resource mappings in `mapResource`.
