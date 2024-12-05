# Touch-Friendly MIDI Controller

**⚠️ WORK IN PROGRESS - This project is under active development and contains known issues**

A touchscreen-optimized MIDI controller application built with Python and PySide6.

## Current Features

- 8-button MIDI controller interface
- MIDI Learn functionality for easy mapping
- Support for Note, CC, and Program Change messages
- Configuration saving/loading
- Touch-optimized fullscreen interface

## Known Issues

- Unstable MIDI device connections
- Configuration saving may fail unexpectedly
- UI elements sometimes become unresponsive
- MIDI Learn mode can get stuck
- Button mappings may not persist correctly

## Requirements

- Python 3.8+
- PySide6
- python-rtmidi

## Quick Start

1. Create a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Linux/Mac
   # or
   .venv\Scripts\activate     # Windows
   ```

2. Install dependencies:
   ```bash
   pip install PySide6 python-rtmidi
   ```

3. Run the application:
   ```bash
   python ui.py
   ```

## Usage

### Basic Operation

1. Launch the application - it will open in fullscreen mode
2. Use the top menu to configure MIDI devices and mappings
3. Press buttons to send MIDI messages
4. Press ESC to exit

### MIDI Configuration

1. Click "MIDI" > "Select Devices" to choose your MIDI input/output devices
2. Use the refresh buttons (⟳) to update device lists if needed
3. Click OK to connect to selected devices

### Button Mapping

There are two ways to map MIDI messages to buttons:

1. **MIDI Learn Mode**:
   - Click the "MIDI Learn Mode" button at the top
   - Select a button to configure
   - Send a MIDI message from your controller
   - Click OK to confirm or Cancel to abort

2. **Manual Configuration**:
   - Click "MIDI" > "View Note Mappings"
   - Edit button names, input/output types, and MIDI numbers
   - Supported message types: Note, CC, Program Change

### Configuration Management

- Configurations are automatically saved to `configs/temp_config.json`
- Use "Config" menu to:
  - Save current configuration
  - Save as new configuration
  - Load existing configuration
- Default configuration is loaded on first run

## Development

### Project Structure

- `ui.py` - Main application code
- `configs/` - Configuration file storage
  - `default_config.json` - Default configuration
  - `temp_config.json` - Temporary working configuration

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## Future Work

- **Raspberry Pi Integration**: Plan to embed the application on a Raspberry Pi with a touchscreen for a portable and standalone MIDI controller setup.
- **Foot Controller Support**: Integrate a foot controller to allow hands-free operation, enhancing usability for musicians during live performances.
- **Improved Stability**: Address known issues with MIDI device connections and configuration management to ensure reliable performance.
- **Enhanced UI Responsiveness**: Optimize the user interface for better responsiveness, especially on lower-powered devices like the Raspberry Pi.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with [PySide6](https://wiki.qt.io/Qt_for_Python)
- MIDI functionality provided by [python-rtmidi](https://spotlightkid.github.io/python-rtmidi/)
