import cv2
import PREFERENCES

class MouseTracker:
    def __init__(self, window_name="Window"):
        self.window_name = window_name
        self.last_position = (0, 0)
        self.last_left_click = None
        self.last_right_click = None

        # Set mouse callback to the window
        cv2.setMouseCallback(self.window_name, self._on_mouse_event)

    def _on_mouse_event(self, event, x, y, flags, param):
        """Handle mouse events."""
        self.last_position = (x, y)  # Update last position
        normalized_x = x / 1920
        normalized_y = y / 1080
        if PREFERENCES.PRINT_MOUSE_COORDINATES: print(f"Mouse position: {self.last_position}, ({normalized_x:.3f}, {normalized_y:.3f})")


        if event == cv2.EVENT_LBUTTONDOWN:
            self.last_left_click = (x, y)  # Update last left-click position

        elif event == cv2.EVENT_RBUTTONDOWN:
            self.last_right_click = (x, y)  # Update last right-click position

    def get_last_position(self):
        """Return the last mouse position."""
        return self.last_position

    def get_last_left_click(self, then_reset=False):
        """Return the last left-click position and optionally reset it."""
        last_click = self.last_left_click
        if then_reset:
            self.last_left_click = None
        return last_click

    def get_last_right_click(self, then_reset=False):
        """Return the last right-click position and optionally reset it."""
        last_click = self.last_right_click
        if then_reset:
            self.last_right_click = None
        return last_click

class KeyboardTracker:
    def __init__(self):
        self.last_pressed_key = None

    def check_key_pressed(self):
        """Check and update the last pressed key."""
        key = cv2.waitKey(1) & 0xFF  # Check for key press
        
        if key != 255:  # 255 indicates no key was pressed
            self.last_pressed_key = key

    def get_last_pressed_key(self, then_reset=False):
        """Return the last pressed key and optionally reset it."""
        last_key = self.last_pressed_key
        if then_reset:
            self.last_pressed_key = None
        return last_key