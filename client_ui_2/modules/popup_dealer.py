import modules.picasso as picasso
import cv2
import numpy as np
from typing import Tuple
import time

class PopupDealer:

    def __init__(self, pos_n:Tuple[float, float] = None, size_n:Tuple[float, float] = None,):
        self.popups_to_show = []
        self.pos_n = pos_n
        self.size_n = size_n

    def append_popup(self, popup_info:dict=None):
        # popup_info { background_color(), created_at, duration, text}
        self.popups_to_show.append(popup_info)

    def draw_popups(self, frame: np.ndarray) -> bool:
        # Set initial y-coordinate for drawing popups from the bottom of the frame
        y_offset = int(frame.shape[0] * self.pos_n[1])
        
        is_popup_poped = False
        popups_to_remove = []

        # Reverse iterate over popups to draw the first one at the bottom
        for popup in reversed(self.popups_to_show):
            # Check if 'duration' key exists to prevent KeyError
            if 'duration' not in popup:
                print(f"Warning: Popup missing 'duration' key: {popup}")
                continue

            # Remove expired popups
            if time.time() - popup['created_at'] > popup['duration']:
                popups_to_remove.append(popup)
                is_popup_poped = True
                continue

            popup_bbox_coords = picasso.get_bbox_coordinates_from_normalized(frame, self.pos_n, self.size_n)
            popup_height = popup_bbox_coords[3] - popup_bbox_coords[1]
            y_offset -= popup_height - 10

            # Draw the popup rectangle
            cv2.rectangle(
                frame,
                (popup_bbox_coords[0], y_offset),
                (popup_bbox_coords[2], y_offset + popup_height),
                popup.get('background_color', (0, 0, 0)),  # Default color if key is missing
                -1
            )

            # Draw the text within the popup
            picasso.draw_text_on_frame(
                frame,
                popup.get('text', ''),  # Default to empty string if key is missing
                (popup_bbox_coords[0] + 10, y_offset + 10),  # Adding padding for text position
                (popup_bbox_coords[2] - popup_bbox_coords[0] - 20, popup_height - 20),  # Width and height for text area
                font=cv2.FONT_HERSHEY_SIMPLEX,
                font_scale=0.5,
                text_color=(255, 255, 255),
                thickness=2,
                padding=10,
                alignment="center",
            )

        # Remove expired popups after the loop
        for popup in popups_to_remove:
            self.popups_to_show.remove(popup)

        return is_popup_poped



            


