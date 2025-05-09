from video_editor.face_search import get_average_faces_position_in_clip
from video_editor.utils import get_default_arg_parser, chose_file_path, chose_dir_path
from video_editor import Editor
from argparse import Namespace
from pathlib import Path

def single_mode(args: Namespace):
    if args.video_file_path is None:
        video_file_path: Path = chose_file_path("Select a video file", "Video File Selector",
                                                Editor.supported_video_formats)
    else:
        video_file_path: Path = args.video_file_path
    editor = Editor(
        output_format=args.output_format,
        fps=args.fps,
        without_audio=args.without_audio,
        write_threads=args.write_threads,
        debug=args.debug,
        log_file_path=args.log_file
    )
    editor.load_video(video_file_path)
    _, _, rotation = get_average_faces_position_in_clip(video_file_path)
    if rotation != 0:
        editor.rotate(rotation)
    editor.write_video(args.output_file_path)

def batch_mode(args: Namespace):
    if args.batch is True:
        dir_path: Path = chose_dir_path("Select a directory", "Directory Selector")
    else:
        dir_path = Path(args.batch)
    editor = Editor(
        output_format=args.output_format,
        fps=args.fps,
        without_audio=args.without_audio,
        write_threads=args.write_threads,
        log_file_path=dir_path / 'events.log' if args.log_file is None else args.log_file,
        debug=args.debug)
    for video_path in dir_path.iterdir():
        if video_path.is_file() and f"*{video_path.suffix.upper()}" in Editor.supported_video_formats:
            editor.load_video(video_path)
            _, _, rotation = get_average_faces_position_in_clip(video_path)
            if rotation != 0:
                editor.rotate(rotation)
            editor.write_video()

if __name__ == "__main__":
    parser = get_default_arg_parser()
    parser.add_argument("video_file_path", type=Path, help="Path to the video file", default=None, nargs="?")
    parser.add_argument("-o", "--output_file_path", type=Path, default=None, help="Output file path")
    parser.add_argument("-b", "--batch", type=str, default=None, nargs="?", const=True,
                        help="Enable batch mode. Optionally specify directory to scan.")
    arguments = parser.parse_args()
    if arguments.batch is None:
        single_mode(arguments)
    else:
        batch_mode(arguments)