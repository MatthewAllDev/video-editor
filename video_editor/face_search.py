from cv2.data import haarcascades
from pathlib import Path
from numpy import ndarray
from typing import Generator, Dict, Union, Tuple, Sequence, Optional
from .utils import get_video_metadata
import cv2

# Initialize a face cascade classifier using a pre-trained Haar cascade model for frontal face detection.
__face_cascade: cv2.CascadeClassifier = cv2.CascadeClassifier(haarcascades + 'haarcascade_frontalface_default.xml')

# Dictionary mapping rotation angles to OpenCV rotation constants.
__cv2_rotation_consts: dict = {
    90: cv2.ROTATE_90_COUNTERCLOCKWISE,
    180: cv2.ROTATE_180,
    270: cv2.ROTATE_90_CLOCKWISE
}

def __rotation_generator(current_rotate: int = 0):
    """
    Generator that yields rotation angles in a specific order starting from the given angle.

    Args:
        current_rotate (int): The initial rotation angle (default is 0).

    Yields:
        int: The next rotation angle in the sequence.
    """
    rotates: list = [0, 90, 270, 180]
    i: int = rotates.index(current_rotate)
    for j in range(0, i):
        rotates.append(rotates.pop(0))
    for i in range(len(rotates)):
        yield rotates[i]

def get_average_faces_position_in_clip(path: Path) -> Tuple[int, int, int]:
    """
    Calculates the average position of detected faces in a video clip.

    Args:
        path (Path): Path to the video file.

    Returns:
        Tuple[int, int, int]: A tuple containing the average x and y positions of faces
        (in a 3x3 grid) and the rotation angle of the video.
    """
    faces: Dict[int:list] = {
        0: [],
        90: [],
        180: [],
        270: []
    }
    capture: cv2.VideoCapture = cv2.VideoCapture(str(path.absolute()))
    metadata = get_video_metadata(path)
    rotation: int = 0
    frames_counter: int = 1
    while True:
        captured, image = capture.read()
        if not captured:
            break
        average_faces_position_in_frame: tuple = get_average_face_position_in_image(image, rotation)
        if average_faces_position_in_frame is not None:
            x, y, rotation = average_faces_position_in_frame
            faces[rotation].append((x, y))
            if len(faces[rotation]) > 2:
                break
        frames_counter += 1
        capture.set(cv2.CAP_PROP_POS_FRAMES, metadata.fps * frames_counter)
    max_faces_in_group: int = 0
    for key, faces_in_group in faces.items():
        count_faces_in_group: int = len(faces_in_group)
        if count_faces_in_group > max_faces_in_group:
            max_faces_in_group = count_faces_in_group
            rotation = key
    if rotation / 90 % 2 == 1:
        clip_w: int = metadata.height
        clip_h: int = metadata.width
    else:
        clip_w: int = metadata.width
        clip_h: int = metadata.height
    lines: tuple = ((clip_w / 3, clip_w * 2 / 3, clip_w),
                    (clip_h / 3, clip_h * 2 / 3, clip_h))
    average_x: int = 0
    average_y: int = 0
    faces_counter: int = 0
    for face in faces[rotation]:
        fase: tuple
        x: int = 0
        y: int = 0
        for i in range(0, len(lines[0])):
            if face[0] <= lines[0][i]:
                x = i + 1
                break
        for i in range(0, len(lines[1])):
            if face[1] <= lines[1][i]:
                y = i + 1
                break
        average_x += x
        average_y += y
        faces_counter += 1
    return round(average_x / faces_counter), round(average_y / faces_counter), rotation

def get_average_face_position_in_image(image: ndarray, rotation: Union[int, Generator] = 0) -> Optional[Tuple[int, int, int]]:
    """
    Detects faces in an image and calculates the average position of the detected faces.

    Args:
        image (ndarray): The input image in which faces are to be detected.
        rotation (Union[int, Generator]): The rotation angle or a generator of rotation angles.

    Returns:
        Optional[Tuple[int, int, int]]: A tuple containing the average x and y positions of faces
        and the rotation angle, or None if no faces are detected.
    """
    if type(rotation) == int:
        rotation = __rotation_generator(rotation)
    average_x: int = 0
    average_y: int = 0
    try:
        current_rotation: int = next(rotation)
    except StopIteration:
        return None
    face_counter: int = 0
    if current_rotation != 0:
        r_image: ndarray = cv2.rotate(image, __cv2_rotation_consts[current_rotation])
    else:
        r_image: ndarray = image
    gray: ndarray = cv2.cvtColor(r_image, cv2.COLOR_BGR2GRAY)
    faces_in_frame: Sequence = __face_cascade.detectMultiScale(gray, scaleFactor=1.2, minNeighbors=10)
    if len(faces_in_frame) == 0:
        return get_average_face_position_in_image(image, rotation)
    for face in faces_in_frame:
        face: tuple
        x = face[0] + face[2] / 2
        y = face[1] + face[3] / 2
        average_x += x
        average_y += y
        face_counter += 1
    return round(average_x / face_counter), round(average_y / face_counter), current_rotation