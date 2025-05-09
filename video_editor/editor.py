from .utils import suppress_stdout, get_video_metadata, require_initialized, get_reasonable_thread_count
from pathlib import Path
from moviepy import VideoFileClip, VideoClip, ImageClip, concatenate_videoclips
from typing import Union
import logging

class Editor:
    """
    A video editor class that provides functionality for loading, editing, and exporting videos.
    """

    supported_video_formats: tuple = ("*.MOV", "*.MP4", "*.MKV", "*.AVI")
    """Supported video file formats."""

    supported_img_formats: tuple = ("*.jpg", "*.png")
    """Supported image file formats."""

    video_file_path: Path = None
    """Path to the currently loaded video file."""

    __clip: VideoClip = None
    """The current video clip being edited."""

    def __init__(self,
                 output_format: str = "mp4",
                 fps: int = None,
                 without_audio: bool = False,
                 write_threads: int = None,
                 log_file_path: Union[Path, str, None] = None,
                 debug: bool = False) -> None:
        """
        Initializes the Editor instance.

        :param output_format: The output video format (default is "mp4").
        :param fps: Frames per second for the output video.
        :param without_audio: Whether to exclude audio from the video.
        :param write_threads: Number of threads to use for writing the video.
                          If not specified, it will be automatically determined based on the system's CPU count.
        :param log_file_path: Path to the log file.
        :param debug: Whether to enable debug logging.
        """
        self.__setup_logger(log_file_path, debug)
        self.__output_format: str = output_format
        self.__fps: int = fps
        self.__audio: bool = not without_audio
        self.__write_threads: int = get_reasonable_thread_count() if write_threads is None else write_threads
        self.logger.debug(
            f"Editor class initialized with:\n\t"
            f"output_format={output_format},\n\t"
            f"fps={fps},\n\t"
            f"without_audio={without_audio},\n\t"
            f"write_threads={'system-determined ' if write_threads is None else ''}{self.__write_threads},\n\t"
            f"log_file_path={log_file_path}"
        )

    @require_initialized("__clip")
    def get_clip(self):
        """
        Returns the current video clip.

        :return: The current VideoClip object.
        """
        return self.__clip

    def load_video(self, file_path: Path) -> None:
        """
        Loads a video file into the editor.

        :param file_path: Path to the video file to load.
        """
        with suppress_stdout():
            self.__clip: VideoFileClip = VideoFileClip(str(file_path.absolute()), audio=self.__audio)
        self.video_file_path: Path = file_path
        self.logger.debug(f"Loaded video: {self.video_file_path}")
        self.__normalize_video_size()

    @require_initialized("__clip")
    def write_video(self, output_file_path: Path = None, write_threads: int = None) -> Path:
        """
        Writes the edited video to a file.

        :param output_file_path: Path to save the output video. If None, a default path is used.
        :param write_threads: Number of threads to use for writing the video. If None, the value from class initialization is used.
        :return: The path to the saved video file.
        """
        if output_file_path is None:
            output_file_path: Path = Path(self.video_file_path.parent, f"{self.video_file_path.stem}-edited.{self.__output_format}")
        print(f"Writing video to {output_file_path}")
        with suppress_stdout():
            self.__clip.write_videofile(str(output_file_path.absolute()),
                                        fps=self.__fps,
                                        audio=self.__audio,
                                        threads=self.__write_threads if write_threads is None else write_threads)
            self.logger.info(f"Video written to {output_file_path}")
        return output_file_path

    @require_initialized("__clip")
    def cut(self, start_time: int = 0, end_time: int = None) -> None:
        """
        Cuts the video to the specified time range.

        :param start_time: Start time in seconds.
        :param end_time: End time in seconds. If None, cuts to the end of the video.
        :raises ValueError: If start_time or end_time is invalid.
        """
        if start_time < 0 or (end_time is not None and end_time < start_time):
            raise ValueError("Invalid start or end time for cutting the video.")
        self.__clip = self.__clip.subclipped(start_time, end_time)
        self.logger.debug(f"Cut video from {start_time} to {end_time} seconds")

    @require_initialized("__clip")
    def rotate(self, angle: int = 90) -> None:
        """
        Rotates the video by the specified angle.

        :param angle: Rotation angle in degrees. Must be one of [0, 90, 180, 270].
        :raises ValueError: If the angle is invalid.
        """
        if angle not in [0, 90, 180, 270]:
            raise ValueError("Invalid rotation angle. Must be one of [0, 90, 180, 270].")
        self.__clip = self.__clip.rotated(angle)
        self.logger.debug(f"Rotated video by {angle} degrees")

    @require_initialized("__clip")
    def insert_img(self, img_path: Path, time: int = 0, duration: int = 1, resize_img: bool = True, method: str ="compose") -> None:
        """
        Inserts an image into the video at the specified time.

        :param img_path: Path to the image file.
        :param time: Time in seconds to insert the image.
        :param duration: Duration in seconds for the image to appear.
        :param resize_img: Whether to resize the image to match the video dimensions.
        :param method: Method for combining clips ("compose" or "chain").
        """
        img_clip: ImageClip = ImageClip(str(img_path.absolute()), duration=duration)
        if resize_img and (img_clip.size[0] != self.__clip.size[0] or img_clip.size[1] != self.__clip.size[1]):
            img_clip = img_clip.resized((self.__clip.size[0], self.__clip.size[1]))
        self.insert_clip(img_clip, time, method, img_path)

    @require_initialized("__clip")
    def insert_video(self, video_path: Path, time: int = 0, cut_start_time: int = 0, cut_end_time: int = None, resize_video: bool = True, method: str ="compose") -> None:
        """
        Inserts a video into the current video at the specified time.

        :param video_path: Path to the video file to insert.
        :param time: Time in seconds to insert the video.
        :param cut_start_time: Start time in seconds for cutting the inserted video.
        :param cut_end_time: End time in seconds for cutting the inserted video.
        :param resize_video: Whether to resize the inserted video to match the current video dimensions.
        :param method: Method for combining clips ("compose" or "chain").
        :raises ValueError: If cut_start_time or cut_end_time is invalid.
        """
        video_clip: VideoClip = VideoFileClip(str(video_path.absolute()), audio=self.__audio)
        if resize_video and (video_clip.size[0] != self.__clip.size[0] or video_clip.size[1] != self.__clip.size[1]):
            video_clip = video_clip.resized((self.__clip.size[0], self.__clip.size[1]))
        if cut_start_time < 0 or (cut_end_time is not None and cut_end_time < cut_start_time):
            raise ValueError("Invalid start or end time for cutting the video.")
        if cut_start_time > 0 or cut_end_time is not None:
            video_clip = video_clip.subclipped(cut_start_time, cut_end_time)
        self.insert_clip(video_clip, time, method, video_path)

    @require_initialized("__clip")
    def insert_clip(self, clip: VideoClip, time: int = None, method: str ="compose", displayed_filepath: Path = None) -> None:
        """
        Inserts a clip into the current video at the specified time.

        :param clip: The VideoClip to insert.
        :param time: Time in seconds to insert the clip. If None, appends to the end.
        :param method: Method for combining clips ("compose" or "chain").
        :param displayed_filepath: Path to display in logs for the inserted clip.
        """
        displayed_filepath = str(displayed_filepath.absolute()) if displayed_filepath else "clip"
        time = self.__clip.duration + time if time < 0 else time
        if time == 0:
            self.__clip = concatenate_videoclips([clip, self.__clip], method=method)
            self.logger.debug(f"Inserted {displayed_filepath} at the beginning of the video")
        elif time is None or time >= self.__clip.duration:
            self.__clip = concatenate_videoclips([self.__clip, clip], method=method)
            self.logger.debug(f"Inserted {displayed_filepath} at the end of the video")
        else:
            self.__clip = concatenate_videoclips([self.__get_subclip(end_time=time), clip, self.__get_subclip(time)], method=method)
            self.logger.debug(f"Inserted {displayed_filepath} at {time} seconds")

    @require_initialized("__clip")
    def __get_subclip(self, start_time: int = 0, end_time: int = None) -> VideoClip:
        """
        Retrieves a subclip from the current video.

        :param start_time: Start time in seconds.
        :param end_time: End time in seconds. If None, retrieves until the end.
        :return: The subclip as a VideoClip object.
        """
        with suppress_stdout():
            return self.__clip.subclipped(start_time, end_time)

    @require_initialized("__clip")
    def __normalize_video_size(self) -> None:
        """
        Normalizes the video size based on its metadata, adjusting for rotation if necessary.
        """
        metadata = get_video_metadata(self.__clip.filename)
        if metadata is None:
            raise ValueError("Unable to retrieve video metadata.")
        width = metadata.width
        height = metadata.height
        rotation = metadata.rotation
        if rotation == 90 or rotation == 270:
            width, height = height, width
        self.__clip = self.__clip.resized((width, height))
        self.logger.debug(f"Normalized video size to {width}x{height} with rotation {rotation}")

    def __setup_logger(self, log_file_path: Union[Path, str, None], debug: bool) -> None:
        """
        Sets up the logger for the Editor.

        :param log_file_path: Path to the log file.
        :param debug: Whether to enable debug logging.
        """
        self.logger: logging.Logger = logging.getLogger("VideoEditor")
        self.logger.setLevel(logging.DEBUG if debug else logging.INFO)
        self.logger.addHandler(logging.StreamHandler())
        if log_file_path is not None:
            if isinstance(log_file_path, str):
                log_file_path = Path(log_file_path)
            if not log_file_path.parent.exists():
                log_file_path.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(str(log_file_path.absolute()), mode="a")
            file_handler.setLevel(logging.DEBUG if debug else logging.INFO)
            file_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
            self.logger.addHandler(file_handler)