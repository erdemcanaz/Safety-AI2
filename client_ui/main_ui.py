import preferences
import time
import modules.ui_items as ui_items
from   modules.api_dealer import ApiDealer
from   modules.popup_dealer import PopupDealer
from   modules.user_input import MouseTracker, KeyboardTracker
import cv2
from typing import List
import numpy as np

from pages import (
    login_page,
    register_page,
    which_app_page,
    update_cameras_page,
    isg_ui_page,
    edit_rules_page,
    reported_violations_page,
)

def check_for_ui_item_callbacks(frame:np.ndarray, page_ui_items:List=[], mouse_tracker:MouseTracker=None, keyboard_tracker:KeyboardTracker=None):
    results = []  # -> [ [callback_type, identifier, True/False], ... ]

    frame_size = frame.shape
  
    key_pressed = keyboard_tracker.get_last_pressed_key(then_reset=True)
    mouse_position = mouse_tracker.get_last_position()    
    normalized_mouse_position = (mouse_position[0] / frame_size[1], mouse_position[1] / frame_size[0]) if mouse_position is not None else None
    left_click = mouse_tracker.get_last_left_click(then_reset=True)
    normalized_left_click = (left_click[0] / frame_size[1], left_click[1] / frame_size[0]) if left_click is not None else None
    right_click = mouse_tracker.get_last_right_click(then_reset=True)
    normalized_right_click = (right_click[0] / frame_size[1], right_click[1] / frame_size[0]) if right_click is not None else None
 
    for item in page_ui_items:        
        if item.is_clickable():
            if normalized_mouse_position is not None:
                r1 = item.is_mouse_over_callback(normalized_mouse_position)
                if r1[2]==True:
                    results.append(r1)
            if normalized_left_click is not None:
                r2 = item.is_left_clicked_callback(normalized_left_click)
                if r2[2]==True:
                    results.append(r2)
            if normalized_right_click is not None:
                r3 = item.is_right_clicked_callback(normalized_right_click)
                if r3[2]==True:
                    results.append(r3)          

        if item.is_writeable():
            if key_pressed is not None:
                r1 = item.is_key_pressed_callback(key_pressed)
                if r1[2]==True:
                    results.append(r1)
            
    return results

def release_previously_focused_ui_items(page_ui_items:List = [], callback_results:List = []):
    # Find the identifier of the currently focused item
    focused_item_identifier = None
    for result in callback_results:
        if len(result) == 4 and result[3] == 'focus':
            focused_item_identifier = result[1]
            
    # Release the focus of the previously focused item
    released_focus_identifiers = []
    if focused_item_identifier is not None:
        for item in page_ui_items:
            if item.is_focusable() and item.is_focused and item.identifier != focused_item_identifier:
                item.release_focus()
                released_focus_identifiers.append(item.identifier)
    return released_focus_identifiers

# ====================================================================================================
WINDOW_NAME = "Window"
cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
cv2.setWindowProperty(WINDOW_NAME, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
mouse_tracker = MouseTracker(window_name=WINDOW_NAME)
keyboard_tracker = KeyboardTracker()
api_dealer = ApiDealer(server_ip_address=preferences.SERVER_IP_ADDRESS)
popup_dealer = PopupDealer(pos_n=(0.33, 0.90), size_n=(0.33, 0.05))

DYNAMIC_PROGRAM_STATE = [0,0,0] #page no, page state, other if required -> login page: [1,0,0]
DYNAMIC_PAGE_DEALER = None

# MAIN LOOP ============================================================================================================
while True:
    if DYNAMIC_PROGRAM_STATE[0] == 0: # LOGIN PAGE
        if not isinstance(DYNAMIC_PAGE_DEALER, login_page.LoginPage):
            DYNAMIC_PAGE_DEALER = login_page.LoginPage(api_dealer=api_dealer, popup_dealer=popup_dealer)   
            DYNAMIC_PAGE_DEALER.reset_page_frame()

        page_ui_items = DYNAMIC_PAGE_DEALER.get_ui_items()  
        callback_results = check_for_ui_item_callbacks(DYNAMIC_PAGE_DEALER.get_page_frame(), page_ui_items, mouse_tracker, keyboard_tracker)
        released_focus_identifiers = release_previously_focused_ui_items(page_ui_items, callback_results)
        DYNAMIC_PAGE_DEALER.apply_callbacks(redraw_items=True, program_state = DYNAMIC_PROGRAM_STATE, callback_results = callback_results, released_focus_identifiers = released_focus_identifiers)

    elif DYNAMIC_PROGRAM_STATE[0] == 1: # REGISTER PAGE
        if not isinstance(DYNAMIC_PAGE_DEALER, register_page.RegisterPage):
            DYNAMIC_PAGE_DEALER = register_page.RegisterPage( api_dealer=api_dealer, popup_dealer=popup_dealer)    
            DYNAMIC_PAGE_DEALER.reset_page_frame()
        
        page_ui_items = DYNAMIC_PAGE_DEALER.get_ui_items()
        callback_results = check_for_ui_item_callbacks(DYNAMIC_PAGE_DEALER.get_page_frame(), page_ui_items, mouse_tracker, keyboard_tracker)
        released_focus_identifiers = release_previously_focused_ui_items(page_ui_items, callback_results)
        DYNAMIC_PAGE_DEALER.apply_callbacks(redraw_items=True, program_state = DYNAMIC_PROGRAM_STATE, callback_results = callback_results, released_focus_identifiers = released_focus_identifiers)
    
    elif DYNAMIC_PROGRAM_STATE[0] == 2: # WHICH APP PAGE
        if not isinstance(DYNAMIC_PAGE_DEALER, which_app_page.WhichAppPage):
            DYNAMIC_PAGE_DEALER = which_app_page.WhichAppPage(api_dealer=api_dealer, popup_dealer=popup_dealer)    
            DYNAMIC_PAGE_DEALER.reset_page_frame()

        page_ui_items = DYNAMIC_PAGE_DEALER.get_ui_items()
        callback_results = check_for_ui_item_callbacks(DYNAMIC_PAGE_DEALER.get_page_frame(), page_ui_items, mouse_tracker, keyboard_tracker)
        released_focus_identifiers = release_previously_focused_ui_items(page_ui_items, callback_results)
        DYNAMIC_PAGE_DEALER.apply_callbacks(redraw_items=False, program_state = DYNAMIC_PROGRAM_STATE, callback_results = callback_results, released_focus_identifiers = released_focus_identifiers)
    elif DYNAMIC_PROGRAM_STATE[0] == 3: # UPDATE CAMERAS PAGE
        if not isinstance(DYNAMIC_PAGE_DEALER, update_cameras_page.UpdateCamerasPage):
            DYNAMIC_PAGE_DEALER = update_cameras_page.UpdateCamerasPage(api_dealer=api_dealer, popup_dealer=popup_dealer)    
            DYNAMIC_PAGE_DEALER.reset_page_frame()
        
        page_ui_items = DYNAMIC_PAGE_DEALER.get_ui_items()
        callback_results = check_for_ui_item_callbacks(DYNAMIC_PAGE_DEALER.get_page_frame(), page_ui_items, mouse_tracker, keyboard_tracker)
        released_focus_identifiers = release_previously_focused_ui_items(page_ui_items, callback_results)
        DYNAMIC_PAGE_DEALER.apply_callbacks(redraw_items=True, program_state = DYNAMIC_PROGRAM_STATE, callback_results = callback_results, released_focus_identifiers = released_focus_identifiers)
    elif DYNAMIC_PROGRAM_STATE[0] == 4: # ISG UI PAGE
        if not isinstance(DYNAMIC_PAGE_DEALER, isg_ui_page.ISG_UIpage):
            DYNAMIC_PAGE_DEALER = isg_ui_page.ISG_UIpage(api_dealer=api_dealer, popup_dealer=popup_dealer)    
            DYNAMIC_PAGE_DEALER.reset_page_frame()
        
        page_ui_items = DYNAMIC_PAGE_DEALER.get_ui_items()
        callback_results = check_for_ui_item_callbacks(DYNAMIC_PAGE_DEALER.get_page_frame(), page_ui_items, mouse_tracker, keyboard_tracker)
        released_focus_identifiers = release_previously_focused_ui_items(page_ui_items, callback_results)
        DYNAMIC_PAGE_DEALER.apply_callbacks(redraw_items=True, program_state = DYNAMIC_PROGRAM_STATE, callback_results = callback_results, released_focus_identifiers = released_focus_identifiers)

    elif DYNAMIC_PROGRAM_STATE[0] == 5: # EDIT RULES PAGE
        if not isinstance(DYNAMIC_PAGE_DEALER, edit_rules_page.EditRulesPage):
            DYNAMIC_PAGE_DEALER = edit_rules_page.EditRulesPage(api_dealer=api_dealer, popup_dealer=popup_dealer)    
            DYNAMIC_PAGE_DEALER.reset_page_frame()

        page_ui_items = DYNAMIC_PAGE_DEALER.get_ui_items()
        callback_results = check_for_ui_item_callbacks(DYNAMIC_PAGE_DEALER.get_page_frame(), page_ui_items, mouse_tracker, keyboard_tracker)
        released_focus_identifiers = release_previously_focused_ui_items(page_ui_items, callback_results)
        DYNAMIC_PAGE_DEALER.apply_callbacks(redraw_items=True, program_state = DYNAMIC_PROGRAM_STATE, callback_results = callback_results, released_focus_identifiers = released_focus_identifiers)
        
    elif DYNAMIC_PROGRAM_STATE[0] == 6: # REPORTED VIOLATIONS PAGE
        if not isinstance(DYNAMIC_PAGE_DEALER, reported_violations_page.ReportedViolationsPage):
            DYNAMIC_PAGE_DEALER = reported_violations_page.ReportedViolationsPage(api_dealer=api_dealer, popup_dealer=popup_dealer)    
            DYNAMIC_PAGE_DEALER.reset_page_frame()

        page_ui_items = DYNAMIC_PAGE_DEALER.get_ui_items()
        callback_results = check_for_ui_item_callbacks(DYNAMIC_PAGE_DEALER.get_page_frame(), page_ui_items, mouse_tracker, keyboard_tracker)
        released_focus_identifiers = release_previously_focused_ui_items(page_ui_items, callback_results)
        DYNAMIC_PAGE_DEALER.apply_callbacks(redraw_items=True, program_state = DYNAMIC_PROGRAM_STATE, callback_results = callback_results, released_focus_identifiers = released_focus_identifiers)
        
    # Draw popups
    final_frame = DYNAMIC_PAGE_DEALER.get_page_frame()
    is_popup_poped = popup_dealer.draw_popups(final_frame)
    cv2.imshow(WINDOW_NAME, final_frame)
    if is_popup_poped:
        DYNAMIC_PAGE_DEALER.reset_page_frame()

    keyboard_tracker.check_key_pressed()
    if keyboard_tracker.get_last_pressed_key(then_reset=False) == 27: # ESC key
        break

cv2.destroyAllWindows()
