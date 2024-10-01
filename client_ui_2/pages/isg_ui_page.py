import modules.ui_items as ui_items
import modules.picasso as picasso
import cv2 
from typing import List
import pprint, time, uuid, random, base64
import numpy as np
from itertools import chain
import datetime

class ISG_UIpage:    
    def __init__(self, api_dealer:object, popup_dealer:object):
        self.api_dealer = api_dealer
        self.popup_dealer = popup_dealer
        self.background = ui_items.Background(background_name="isg_ui_page_template", default_resolution=(1920,1080))
        
        self.frame_fetching_interval = 5 #seconds
        self.last_time_frames_fetched = time.time()
        self.page_frame = None         
        self.last_frames_without_BLOB:List = None
        self.selected_indexes = []

        self.previous_page_button = ui_items.Button(
            identifier = "but"+str(uuid.uuid4()),
            pos_n=(0.015, 0.93),
            size_n=(0.08, 0.05),
            button_render_configs={
                "button_style": "basic",
                "button_text": "Geri",
                "button_text_font_scale": [0.75, 0.75],
                "button_text_thickness": [2, 2],
                "button_text_color": [(255, 255, 255), (0, 0, 0)],
                "button_background_color": [(238, 236, 125), (169, 96, 0)],
                "button_border_color": [(255, 255, 255), (255, 255, 255)],
                "button_border_thickness": [2, 2]
            }
        )

        self.page_ui_items = [self.previous_page_button]
       
        self.reset_page_frame_required_callbacks = []
        for item in self.page_ui_items:
            self.reset_page_frame_required_callbacks.extend(item.get_reset_page_frame_required_callbacks())

        self.last_frames_info_without_frame = []
        self.violation_detected_camera_uuids = []
        self.other_camera_uuids = []
        self.fetched_images = {} # {camera_uuid: frame}

        
        self.update_last_frame_info_without_frame()
        # ========================== #
        self.reset_page_frame()

    def update_last_frame_info_without_frame(self):
        fetch_last_frames_info_result = self.api_dealer.fetch_last_frames_info_without_frames()
        self.last_frames_info_without_frame = []
        if not fetch_last_frames_info_result[0]:
            self.popup_dealer.append_popup({"background_color":(255,0,0), "created_at":time.time(), "duration":2, "text":fetch_last_frames_info_result[1]})
            return
        self.last_frames_info_without_frame = fetch_last_frames_info_result[2]

        #decide on cameras to be shown 
        self.violation_detected_camera_uuids = []
        self.other_camera_uuids = []

        for frame_info in self.last_frames_info_without_frame:
            if frame_info["is_violation_detected"]:
                self.violation_detected_camera_uuids.append(frame_info["camera_uuid"])
            else:
                self.other_camera_uuids.append(frame_info["camera_uuid"])
        
        NUMBER_OF_CAMERAS_TO_SHOW = 6

        selected_camera_uuids = []

        if len(self.violation_detected_camera_uuids) <= NUMBER_OF_CAMERAS_TO_SHOW:
            selected_camera_uuids.extend(self.violation_detected_camera_uuids)
            if len(self.other_camera_uuids) <= NUMBER_OF_CAMERAS_TO_SHOW - len(self.violation_detected_camera_uuids):
                selected_camera_uuids.extend(self.other_camera_uuids)
            elif len(self.other_camera_uuids) > NUMBER_OF_CAMERAS_TO_SHOW - len(self.violation_detected_camera_uuids):
                selected_camera_uuids.extend(random.sample(self.other_camera_uuids, NUMBER_OF_CAMERAS_TO_SHOW - len(self.violation_detected_camera_uuids)))
        elif len(self.violation_detected_camera_uuids) > NUMBER_OF_CAMERAS_TO_SHOW:
            selected_camera_uuids.extend(random.sample(self.violation_detected_camera_uuids, 6))
    
    def fetch_selected_frames(self):
        self.fetched_images = {}

        selected_camera_uuids = self.violation_detected_camera_uuids + self.other_camera_uuids
        for selected_camera_uuid in selected_camera_uuids:
            result = self.api_dealer.get_last_camera_frame_by_camera_uuid(camera_uuid=selected_camera_uuid)
            if result[0]:
                try:                
                    self.fetched_images[selected_camera_uuid] = self.api_dealer.decode_url_body_b64_string_to_frame(base64_encoded_image_string=result[2]["frame_b64_string"])
                except Exception as e:
                    self.popup_dealer.append_popup({"background_color":(255,0,0), "created_at":time.time(), "duration":2, "text":str(e)})
            else:
                self.popup_dealer.append_popup({"background_color":(255,0,0), "created_at":time.time(), "duration":2, "text":result[2]["detail"]})
  
    def reset_page_frame(self):
        self.page_frame = self.background.get_background_frame()
       
        display_frame_width = self.page_frame.shape[1]*0.20
        display_frame_height = self.page_frame.shape[0]*0.20
        frame_locations = [(0.0225, 0.137), (0.25, 0.14), (0.02, 0.42), (0.25, 0.42), (0.02, 0.69), (0.25, 0.69)]
        main_frame_location = (0.49, 0.080)
        main_frame_width = self.page_frame.shape[1]*0.48
        main_frame_height = self.page_frame.shape[0]*0.48

        # Create iterators for important and other items
        important_items = ((uuid, frame) for uuid, frame in self.fetched_images.items() if uuid in self.violation_detected_camera_uuids)

        # Create and shuffle a list for other items
        other_items = [
            (uuid, frame) for uuid, frame in self.fetched_images.items()
            if uuid not in self.violation_detected_camera_uuids
        ]
        random.shuffle(other_items)

        # Chain the iterators
        for i, (camera_uuid, this_frame) in enumerate(chain(important_items, other_items)):
            if i >= len(frame_locations): break

            # Calculate the top-left corner position of the frame
            top_left_x = int(frame_locations[i][0] * self.page_frame.shape[1])
            top_left_y = int(frame_locations[i][1] * self.page_frame.shape[0])
            
            # Calculate the bottom-right corner position of the frame
            bottom_right_x = int(top_left_x + display_frame_width)
            bottom_right_y = int(top_left_y + display_frame_height)
            
            # find related camera info
            this_camera_info = next((item for item in self.last_frames_info_without_frame if item["camera_uuid"] == camera_uuid), None) # camera_uuid, camera_ip_address, camera_region, is_violation_detected (0 or 1), is_person_detected (0 or 1)
            date_updated = this_camera_info["date_updated"] #'date_updated': '2024-09-25 17:55:30'
            date_updated = (datetime.datetime.strptime(date_updated, '%Y-%m-%d %H:%M:%S') + datetime.timedelta(hours=3)).strftime('%d/%m/%Y %H:%M:%S') # Add 3 hours to convert UTC to local time

            camera_uuid = this_camera_info["camera_uuid"]
            camera_ip_address = this_camera_info["camera_ip_address"]
            camera_region = this_camera_info["camera_region"]
            is_violation_detected = this_camera_info["is_violation_detected"]
            is_person_detected = this_camera_info["is_person_detected"]
            camera_name_text = f"{camera_ip_address}" if camera_region == "Henüz Atanmadı" else f"{camera_region}"

            # Draw the image on the frame
            picasso.draw_frame_on_frame(
                self.page_frame, this_frame, 
                top_left_x, top_left_y, 
                width=int(display_frame_width), 
                height=int(display_frame_height), 
                maintain_aspect_ratio=False
            )

            picasso.draw_text_on_frame(
                self.page_frame, 
                text=camera_name_text, 
                position=(top_left_x, top_left_y + int(display_frame_height) + 15),
                area_size=(int(display_frame_width), int(20)),
                alignment='center', 
                font=cv2.FONT_HERSHEY_SIMPLEX, 
                font_scale = 1, 
                text_color=(169, 69, 0), 
                thickness=2, 
                padding=10
            )

            picasso.draw_text_on_frame(
                self.page_frame, 
                text=date_updated, 
                position=(top_left_x, top_left_y),
                area_size=(int(display_frame_width), int(20)),
                alignment='left', 
                font=cv2.FONT_HERSHEY_SIMPLEX, 
                font_scale = 0.5, 
                text_color=(255, 255, 255), 
                thickness=1, 
                padding=10
            )

            if i == 0:
                # fetch counts 
                #camera uuid | evaluated_frame_count
                #camera uuid | detected_people_count
                #camera uuid | detected_hardhat_count
                #camera uuid | detected_restricted_area_count
                response = self.api_dealer.get_counts_by_count_key(count_key =camera_uuid)
                print("response: ", response)
                if response[0]:
                    counts_list = response[2]
                    for count_dict in counts_list:
                        if "evaluated_frame_count" in count_dict:
                            evaluated_frame_count = count_dict['evaluated_frame_count']
                            picasso.draw_text_on_frame(
                                self.page_frame, 
                                text=f"Evaluated Frame Count: {evaluated_frame_count}", 
                                position=(int(main_frame_location[0] * self.page_frame.shape[1]), int(main_frame_location[1] * self.page_frame.shape[0] + main_frame_height + 45)),
                                area_size=(int(main_frame_width/2), int(20)),
                                alignment='center',
                                font=cv2.FONT_HERSHEY_SIMPLEX, 
                                font_scale = 0.5, 
                                text_color=(0, 0, 0), 
                                thickness=1, 
                                padding=10
                            )


                        if "detected_people_count" in count_dict:
                            detected_people_count = count_dict['detected_people_count']
                            picasso.draw_text_on_frame(
                                self.page_frame, 
                                text=f"Detected People Count: {detected_people_count}", 
                                position=(top_left_x, top_left_y + int(display_frame_height) + 55),
                                area_size=(int(display_frame_width), int(20)),
                                alignment='center', 
                                font=cv2.FONT_HERSHEY_SIMPLEX, 
                                font_scale=2,
                                text_color=(169, 69, 0),
                                thickness=2,
                                padding=10
                            )

                        if "detected_hardhat_count" in count_dict:
                            detected_hardhat_count = count_dict['detected_hardhat_count']
                            picasso.draw_text_on_frame(
                                self.page_frame, 
                                text=f"Detected Hardhat Count: {detected_hardhat_count}", 
                                position=(top_left_x, top_left_y + int(display_frame_height) + 75),
                                area_size=(int(display_frame_width), int(20)),
                                alignment='center', 
                                font=cv2.FONT_HERSHEY_SIMPLEX, 
                                font_scale = 0.5, 
                                text_color=(255, 255, 255), 
                                thickness=1, 
                                padding=10
                            )
                        
                        if "detected_restricted_area_count" in count_dict:
                            detected_restricted_area_count = count_dict['detected_restricted_area_count']
                            picasso.draw_text_on_frame(
                                self.page_frame, 
                                text=f"Detected Restricted Area Count: {detected_restricted_area_count}", 
                                position=(top_left_x, top_left_y + int(display_frame_height) + 95),
                                area_size=(int(display_frame_width), int(20)),
                                alignment='center', 
                                font=cv2.FONT_HERSHEY_SIMPLEX, 
                                font_scale = 0.5, 
                                text_color=(255, 255, 255), 
                                thickness=1, 
                                padding=10
                            )
                            
                picasso.draw_frame_on_frame(
                    self.page_frame, this_frame, 
                    int(main_frame_location[0] * self.page_frame.shape[1]), int(main_frame_location[1] * self.page_frame.shape[0]), 
                    width=int(main_frame_width), 
                    height=int(main_frame_height), 
                    maintain_aspect_ratio=False
                )              
                picasso.draw_text_on_frame(
                    self.page_frame,
                    text=camera_name_text,
                    position=(int(main_frame_location[0] * self.page_frame.shape[1]), int(main_frame_location[1] * self.page_frame.shape[0] + main_frame_height + 15)),
                    area_size=(int(main_frame_width), int(20)),
                    alignment='center',
                    font=cv2.FONT_HERSHEY_SIMPLEX,
                    font_scale=1,
                    text_color=(169, 69, 0),
                    thickness=2,
                    padding=10                    
                )
                picasso.draw_text_on_frame(
                    self.page_frame,
                    text=date_updated,
                    position=(int(main_frame_location[0] * self.page_frame.shape[1]), int(main_frame_location[1] * self.page_frame.shape[0])+15),
                    area_size=(int(main_frame_width), int(20)),
                    alignment='left',
                    font=cv2.FONT_HERSHEY_SIMPLEX,
                    font_scale=1,
                    text_color=(169, 69, 0),
                    thickness=2,
                    padding=10                    
                )

            # Check for violation and draw text and rectangle
            if is_violation_detected:
                color = (0, 0, 255) if is_violation_detected else (255, 0, 0)              

                # Draw a rectangle as a border around the frame
                cv2.rectangle(
                    self.page_frame, 
                    (top_left_x, top_left_y), 
                    (bottom_right_x, bottom_right_y), 
                    color, 
                    5
                )

                if i == 0:
                    cv2.rectangle(
                    self.page_frame, 
                    (int(main_frame_location[0] * self.page_frame.shape[1]), int(main_frame_location[1] * self.page_frame.shape[0])), 
                    (int(main_frame_location[0] * self.page_frame.shape[1] + main_frame_width), int(main_frame_location[1] * self.page_frame.shape[0] + main_frame_height)), 
                    color, 
                    5
                )
                    
        for ui_item in self.page_ui_items:
            ui_item.draw(self.page_frame)
        
    def get_ui_items(self):
        return self.page_ui_items
    
    def get_page_frame(self):
        return self.page_frame
    
    def apply_callbacks(self, redraw_items:bool = False, program_state:List=[1,0,0], callback_results:List=[], released_focus_identifiers:List=[]):
        # Periodically fetch the frames ========================================
        if time.time() - self.last_time_frames_fetched > self.frame_fetching_interval:
            self.last_time_frames_fetched = time.time()
            self.update_last_frame_info_without_frame()
            self.fetch_selected_frames()
            self.reset_page_frame()

        # Update the page frame ========================================
        for result in callback_results:
            if result in self.reset_page_frame_required_callbacks:
                self.reset_page_frame()    
                break    
        else: # If no reset required, apply other callbacks              
            for item in self.page_ui_items:             
                for callback in item.get_redraw_required_callbacks():
                    if redraw_items or callback in callback_results or item.identifier in released_focus_identifiers:
                        item.draw(self.page_frame)
                        break

        # Apply the callbacks ==========================================
        for callback in callback_results:
            if callback == ["left_clicked_callback", self.previous_page_button.identifier, True]:
                program_state[0] = 2
                return
            
          

        


                                        