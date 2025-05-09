# Video Editor &middot; [![GitHub license](https://img.shields.io/badge/license-MIT-blue.svg)](./LICENSE)

A module for video processing with usage examples. It provides an easy-to-use interface for basic video operations.

## Features
- Remove audio from videos.
- Transcode videos.
- Trim video clips.
- Add images or other videos.
- Rotate videos (including rotation based on face position in the frame).

**Note:** Effects are not supported in the current version.

## Installation
1. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows, use venv\\Scripts\\activate
   ```
2. Install dependencies from the `requirements.txt` file:
   ```bash
   pip install -r requirements.txt
   ```
3. **MediaInfo Installation**:
   - On **Windows**, a precompiled `MediaInfo.dll` (version 25.04) is already included in the project. No additional installation is required.
   - On **other operating systems**, you need to install `MediaInfo` manually. Refer to the [MediaInfo official website](https://mediaarea.net/en/MediaInfo) for instructions.

## Usage Examples
Usage examples can be found in the root directory of the project. Check them out to get started quickly.

## License

This project is licensed under the [MIT License](./LICENSE).

## Third-party Dependencies and Their Licenses

- **easygui**: GNU LGPLv3 (or MIT depending on version)
- **moviepy**: MIT License
- **numpy**: BSD License
- **opencv_python**: Apache 2.0 License
- **pymediainfo**: LGPLv2.1 License