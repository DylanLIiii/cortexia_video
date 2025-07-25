import random
from typing import List, Optional, Tuple, Union

import cv2
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image, ImageColor, ImageDraw

from cortexia_video.schemes import BoundingBox, DetectionResult, FrameData


def random_named_css_colors(num_colors: int) -> List[str]:
    """
    Returns a list of randomly selected named CSS colors.

    Args:
    - num_colors (int): Number of random colors to generate.

    Returns:
    - list: List of randomly selected named CSS colors.
    """
    # List of named CSS colors
    named_css_colors = [
        "aliceblue",
        "antiquewhite",
        "aqua",
        "aquamarine",
        "azure",
        "beige",
        "bisque",
        "black",
        "blanchedalmond",
        "blue",
        "blueviolet",
        "brown",
        "burlywood",
        "cadetblue",
        "chartreuse",
        "chocolate",
        "coral",
        "cornflowerblue",
        "cornsilk",
        "crimson",
        "cyan",
        "darkblue",
        "darkcyan",
        "darkgoldenrod",
        "darkgray",
        "darkgreen",
        "darkgrey",
        "darkkhaki",
        "darkmagenta",
        "darkolivegreen",
        "darkorange",
        "darkorchid",
        "darkred",
        "darksalmon",
        "darkseagreen",
        "darkslateblue",
        "darkslategray",
        "darkslategrey",
        "darkturquoise",
        "darkviolet",
        "deeppink",
        "deepskyblue",
        "dimgray",
        "dimgrey",
        "dodgerblue",
        "firebrick",
        "floralwhite",
        "forestgreen",
        "fuchsia",
        "gainsboro",
        "ghostwhite",
        "gold",
        "goldenrod",
        "gray",
        "green",
        "greenyellow",
        "grey",
        "honeydew",
        "hotpink",
        "indianred",
        "indigo",
        "ivory",
        "khaki",
        "lavender",
        "lavenderblush",
        "lawngreen",
        "lemonchiffon",
        "lightblue",
        "lightcoral",
        "lightcyan",
        "lightgoldenrodyellow",
        "lightgray",
        "lightgreen",
        "lightgrey",
        "lightpink",
        "lightsalmon",
        "lightseagreen",
        "lightskyblue",
        "lightslategray",
        "lightslategrey",
        "lightsteelblue",
        "lightyellow",
        "lime",
        "limegreen",
        "linen",
        "magenta",
        "maroon",
        "mediumaquamarine",
        "mediumblue",
        "mediumorchid",
        "mediumpurple",
        "mediumseagreen",
        "mediumslateblue",
        "mediumspringgreen",
        "mediumturquoise",
        "mediumvioletred",
        "midnightblue",
        "mintcream",
        "mistyrose",
        "moccasin",
        "navajowhite",
        "navy",
        "oldlace",
        "olive",
        "olivedrab",
        "orange",
        "orangered",
        "orchid",
        "palegoldenrod",
        "palegreen",
        "paleturquoise",
        "palevioletred",
        "papayawhip",
        "peachpuff",
        "peru",
        "pink",
        "plum",
        "powderblue",
        "purple",
        "rebeccapurple",
        "red",
        "rosybrown",
        "royalblue",
        "saddlebrown",
        "salmon",
        "sandybrown",
        "seagreen",
        "seashell",
        "sienna",
        "silver",
        "skyblue",
        "slateblue",
        "slategray",
        "slategrey",
        "snow",
        "springgreen",
        "steelblue",
        "tan",
        "teal",
        "thistle",
        "tomato",
        "turquoise",
        "violet",
        "wheat",
        "white",
        "whitesmoke",
        "yellow",
        "yellowgreen",
    ]

    # Sample random named CSS colors
    return random.sample(named_css_colors, min(num_colors, len(named_css_colors)))


def draw_bounding_box(
    draw,
    box: BoundingBox,
    label: Optional[str] = None,
    score: Optional[float] = None,
    color: str = "red",
    thickness: int = 2,
):
    # Draw bounding box rectangle
    draw.rectangle(
        [(box.xmin, box.ymin), (box.xmax, box.ymax)], outline=color, width=thickness
    )
    # Draw label and score if provided
    display_text = ""
    if label:
        display_text = label
    if score is not None:
        display_text += f" {score:.2f}" if display_text else f"{score:.2f}"

    if display_text:
        # Estimate label position, ensure it's within the image
        label_x = box.xmin
        label_y = max(0, box.ymin - 10)
        draw.text((label_x, label_y), display_text, fill=color)
    return draw


def draw_segmentation_mask(
    image: Image.Image,
    mask_array: np.ndarray,
    color: Optional[Union[Tuple[int, int, int], str]] = None,
    alpha: float = 0.5,
) -> Image.Image:
    # If no color is provided, get a random named CSS color
    if color is None:
        color_name = random_named_css_colors(1)[0]
        # Convert color name to RGB using PIL
        color_rgb = ImageColor.getrgb(color_name)
    elif isinstance(color, str):
        # If color is a string (color name), convert to RGB
        color_rgb = ImageColor.getrgb(color)
    else:
        # If color is already RGB tuple, use it directly
        color_rgb = color

    # Convert image to numpy array
    img_array = np.array(image).copy()
    if img_array.ndim == 2:  # grayscale
        img_array = np.stack([img_array] * 3, axis=-1)
    if img_array.shape[2] == 4:
        img_array = img_array[:, :, :3]

    # Create a boolean mask for the target object
    bool_mask = mask_array == 1

    # Only blend the colors where the mask is active
    masked_image_array = img_array.copy()
    for c in range(3):  # RGB channels
        masked_image_array[bool_mask, c] = (
            color_rgb[c] * alpha + img_array[bool_mask, c] * (1 - alpha)
        ).astype(np.uint8)

    # Convert back to PIL
    result = Image.fromarray(masked_image_array)
    return result


def generate_annotated_frame(frame_data: FrameData) -> Image.Image:
    annotated_img = Image.fromarray(frame_data.rgb_image)
    draw = ImageDraw.Draw(annotated_img, "RGBA")

    # Get a set of unique colors for all detections and segments
    num_colors_needed = len(frame_data.detections) + len(frame_data.segments)
    colors = random_named_css_colors(num_colors_needed)
    color_index = 0

    # Draw detections
    for detection in frame_data.detections:
        color = colors[color_index]

        if detection.box:
            draw_bounding_box(draw, detection.box, detection.label, color=color)
        color_index += 1
        
    for segment in frame_data.segments:
        annotated_img = draw_segmentation_mask(annotated_img, segment.mask, color=colors[color_index])
        color_index += 1
    # # Draw segments if they're not already represented in detections
    # for segment in frame_data.segments:
    #     # Check if this segment is already represented in a detection
    #     already_drawn = any(
    #         d.box.xmin == segment.bbox.xmin
    #         and d.box.ymin == segment.bbox.ymin
    #         and d.label == segment.label
    #         for d in frame_data.detections
    #     )

    #     if not already_drawn:
    #         color = colors[color_index]
    #         color_index += 1
    #         draw_bounding_box(draw, segment.bbox, segment.label, color=color)
    #         annotated_img = draw_segmentation_mask(
    #             annotated_img, segment.mask, color=color
    #         )
    #         draw = ImageDraw.Draw(annotated_img, "RGBA")  # re-init after new image
    return annotated_img


def annotate(
    image: Union[Image.Image, np.ndarray], detection_results: List[DetectionResult]
) -> np.ndarray:
    """
    Annotate an image with detection results (bounding boxes, labels, and masks).

    Args:
        image: PIL Image or numpy array
        detection_results: List of DetectionResult objects

    Returns:
        Annotated image as numpy array (RGB format)
    """
    # Convert PIL Image to OpenCV format
    image_cv2 = np.array(image) if isinstance(image, Image.Image) else image.copy()
    image_cv2 = cv2.cvtColor(image_cv2, cv2.COLOR_RGB2BGR)

    # Iterate over detections and add bounding boxes and masks
    for detection in detection_results:
        label = detection.label
        score = detection.score
        box = detection.box
        mask = detection.mask

        # Sample a random color for each detection
        color = np.random.randint(0, 256, size=3).tolist()

        # Draw bounding box
        cv2.rectangle(image_cv2, (box.xmin, box.ymin), (box.xmax, box.ymax), color, 2)

        # Draw label with score
        cv2.putText(
            image_cv2,
            f"{label}: {score:.2f}",
            (box.xmin, box.ymin - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            color,
            2,
        )

        # If mask is available, apply it
        if mask is not None:
            # Convert mask to uint8
            mask_uint8 = (mask * 255).astype(np.uint8)
            contours, _ = cv2.findContours(
                mask_uint8, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
            )
            cv2.drawContours(image_cv2, contours, -1, color, 2)

    return cv2.cvtColor(image_cv2, cv2.COLOR_BGR2RGB)


def plot_detections(
    image: Union[Image.Image, np.ndarray],
    detections: List[DetectionResult],
    save_path: Optional[str] = None,
    show: bool = True,
    figsize: tuple = (12, 10),
) -> None:
    """
    Plot detection results with matplotlib.

    Args:
        image: PIL Image or numpy array
        detections: List of DetectionResult objects
        save_path: Optional path to save the output image
        show: Whether to display the plot
        figsize: Figure size
    """
    # Convert image to numpy array if needed
    if isinstance(image, Image.Image):
        image_np = np.array(image)
    else:
        image_np = image.copy()

    # Create annotated image
    annotated_image = annotate(image_np, detections)

    # Display the image
    plt.figure(figsize=figsize)
    plt.imshow(annotated_image)
    plt.axis("off")

    if save_path:
        plt.savefig(save_path, bbox_inches="tight", dpi=200)

    if show:
        plt.show()
    else:
        plt.close()


def visualize_mask(
    image: Union[Image.Image, np.ndarray],
    mask: np.ndarray,
    alpha: float = 0.5,
    color: tuple = (0, 255, 0),
    save_path: Optional[str] = None,
    show: bool = True,
    figsize: tuple = (12, 10),
) -> None:
    """
    Visualize a binary mask overlaid on an image.

    Args:
        image: PIL Image or numpy array
        mask: Binary mask as numpy array
        alpha: Transparency of the mask overlay (0-1)
        color: RGB color for the mask
        save_path: Optional path to save the output image
        show: Whether to display the plot
        figsize: Figure size
    """
    # Convert image to numpy array if needed
    if isinstance(image, Image.Image):
        image_np = np.array(image)
    else:
        image_np = image.copy()

    # Create a colored mask
    colored_mask = np.zeros_like(image_np)
    mask_bool = mask > 0
    colored_mask[mask_bool] = color

    # Blend the original image with the colored mask
    blended = cv2.addWeighted(image_np, 1, colored_mask, alpha, 0)

    # Add contour around the mask
    mask_uint8 = (mask * 255).astype(np.uint8)
    contours, _ = cv2.findContours(
        mask_uint8, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )
    cv2.drawContours(blended, contours, -1, color, 2)

    # Display the image
    plt.figure(figsize=figsize)
    plt.imshow(blended)
    plt.axis("off")

    if save_path:
        plt.savefig(save_path, bbox_inches="tight", dpi=200)

    if show:
        plt.show()
    else:
        plt.close()

