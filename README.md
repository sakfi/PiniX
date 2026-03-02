# PiniX

<p align="center">
  <img src="pinix/PiniX.png" alt="PiniX Logo" />
</p>

## About PiniX
PiniX is a dedicated, standalone IPTV streaming application designed explicitly for Windows desktop environments. It allows users to watch live TV broadcast, movies, and TV series by parsing modern IPTV provider APIs and M3U playlists into a sleek, fast, native graphical interface.

Powered by **Python**, **PyQt6**, and the hardware-accelerated **mpv** media engine, PiniX delivers smooth playback with low overhead, straight from your desktop without needing browser wrappers or heavy electron containers.

### Key Features
- **Native Windows UI:** Built with PyQt6 to blend perfectly into modern Windows workflows.
- **Provider Agnostic:** Supports multiple input formats:
  - M3U URLs
  - Comprehensive Xtream API parsing
  - Local M3U playlist flat files
- **Standalone Executable:** No Python installation necessary. Available as a single standalone executable download directly from our Releases.
- **Hardware Acceleration:** D3D11 decoding out of the box via embedded mpv for smooth 1080p and 4K playback.

## Installation

### Method 1: Download the Executable (Recommended)
You can download the pre-compiled `PiniX.exe` standalone application from our [Releases](https://github.com/sakfi/PiniX/releases) page. Just download and run it!

### Method 2: Run from Source
If you are a developer or prefer to run the raw Python code:
1. Ensure you have Python 3.9+ installed and `pip` available.
2. Clone this repository: `git clone https://github.com/sakfi/PiniX.git`
3. Install the dependencies:
   ```cmd
   pip install -r requirements.txt
   ```
4. Download the [mpv Windows build](https://sourceforge.net/projects/mpv-player-windows/files/libmpv/) (`mpv-2.dll`) and place the DLL in the root folder next to `main.py`.
5. Run the application:
   ```cmd
   python main.py
   ```

## Configuration
PiniX creates its configuration and caches streams locally at `%LOCALAPPDATA%\PiniX`. You can edit `settings.json` in this directory to manually add or adjust IPTV providers.

## License
Provided under the GPLv3 License.
