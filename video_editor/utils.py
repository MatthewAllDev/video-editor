from typing import Optional, Iterable, Union
from functools import wraps
from easygui import fileopenbox, diropenbox, msgbox
from pymediainfo import MediaInfo
from pathlib import Path
from argparse import ArgumentParser
from .metadata import Metadata
import contextlib
import sys
import os

def get_default_arg_parser(prog: str = None, usage: str = None, description: str = None, epilog: str = None) -> ArgumentParser:
    """
    Creates and returns a default argument parser for the video editor.

    :param prog: The name of the program (optional).
    :param usage: The usage message (optional).
    :param description: A description of the program (optional).
    :param epilog: Text to display after the argument help (optional).
    :return: An ArgumentParser object with predefined arguments.
    """
    parser = ArgumentParser(
        prog=prog,
        usage=usage,
        description=description,
        epilog=epilog)
    parser.add_argument("-f", "--fps", type=int, default=None, help="Frames per second for the output video")
    parser.add_argument("-of", "--output_format", type=str, default="mp4", help="Output video format (default: mp4)")
    parser.add_argument("-t", "--write_threads", type=int, default=None, help="Number of threads for writing video")
    parser.add_argument("-wa", "--without_audio", action="store_true", help="Remove audio from the output video")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument("--log_file", type=Path, default=None, help="Path to the log file")
    return parser

def get_reasonable_thread_count() -> int:
    """
    Calculate a reasonable number of threads to use based on the CPU core count.

    For CPUs with fewer than 5 cores, returns 2 threads to ensure basic parallelism.
    For 5 or more cores, reserves 2 cores for the system and uses the rest.

    :return: Recommended number of threads to use.
    """
    total = os.cpu_count()  # Uses logical cores (threads), as returned by os.cpu_count()

    if total < 5:
        return 2
    return total - 2

def require_initialized(attr_name):
    """
    Decorator to ensure that a specified attribute is initialized before calling a method.

    :param attr_name: The name of the attribute to check.
    :return: The decorated method.
    """
    def decorator(method):
        @wraps(method)
        def wrapper(self, *args, **kwargs):
            # Handle name mangling for double underscore attributes
            if attr_name.startswith("__") and not attr_name.endswith("__"):
                cls = self.__class__
                mangled_name = f"_{cls.__name__}{attr_name}"
            else:
                mangled_name = attr_name
            attr = getattr(self, mangled_name, None)
            if attr is None:
                raise RuntimeError(
                    f"Attribute '{attr_name}' (resolved as '{mangled_name}') is not initialized"
                )
            return method(self, *args, **kwargs)
        return wrapper
    return decorator

def get_video_metadata(path: Union[Path, str]) -> Optional[Metadata]:
    """
    Retrieves metadata for a video file.

    :param path: The path to the video file.
    :return: A Metadata object containing video details, or None if no video track is found.
    """
    if isinstance(path, str):
        path = Path(path)
    media_info = MediaInfo.parse(path)
    for track in media_info.tracks:
        if track.track_type == "Video":
            return Metadata(
                filename=path.name,
                width=track.width,
                height=track.height,
                rotation=float(track.rotation) if track.rotation else 0,
                duration=track.duration,
                codec=track.codec,
                fps=track.frame_rate
            )
    return None

@contextlib.contextmanager
def suppress_stdout():
    """
    Context manager to suppress standard output temporarily.

    :yield: None.
    """
    with open(os.devnull, 'w') as fnull:
        old_stdout = sys.stdout
        sys.stdout = fnull
        try:
            yield
        finally:
            sys.stdout = old_stdout

def chose_file_path(msg: str, title: str, filetypes: Optional[Union[Iterable, None]] = None) -> Path:
    """
    Opens a file selection dialog and returns the selected file path.

    :param msg: The message to display in the dialog.
    :param title: The title of the dialog.
    :param filetypes: A list of allowed file types (optional).
    :return: The selected file path as a Path object.
    :raises SystemExit: If no file is selected.
    """
    file_path: Path = fileopenbox(msg=msg, title=title, default=__get_last_dir(), filetypes=filetypes)
    if file_path is None:
        msgbox(msg="No file selected", title="Error")
        raise SystemExit("No file selected")
    file_path = Path(file_path)
    __set_last_dir(file_path.parent)
    return file_path

def chose_dir_path(msg: str, title: str) -> Path:
    """
    Opens a directory selection dialog and returns the selected directory path.

    :param msg: The message to display in the dialog.
    :param title: The title of the dialog.
    :return: The selected directory path as a Path object.
    :raises SystemExit: If no directory is selected.
    """
    dir_path = diropenbox(msg=msg, title=title, default=__get_last_dir())
    if dir_path is None:
        msgbox(msg="No directory selected", title="Error")
        raise SystemExit("No directory selected")
    dir_path = Path(dir_path)
    __set_last_dir(dir_path)
    return dir_path

def __get_last_dir() -> str:
    """
    Retrieves the last accessed directory path from a stored file.

    :return: The last directory path as a string.
    """
    last_dir: Path = Path.home() / ".last_dir_videoeditor"
    if last_dir.exists():
        with open(last_dir, "r") as file:
            return f"{file.read().strip()}/*"
    else:
        return str(Path.home())

def __set_last_dir(path: Path) -> None:
    """
    Stores the last accessed directory path in a file.

    :param path: The directory path to store.
    """
    last_dir: Path = Path.home() / ".last_dir_videoeditor"
    with open(last_dir, "w") as file:
        file.write(str(path.absolute()))