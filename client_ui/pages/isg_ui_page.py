import modules.ui_items as ui_items
import modules.picasso as picasso
import cv2 
from typing import List
import pprint, time, uuid, random, base64
import numpy as np

class ISG_UIpage:    
    def __init__(self, api_dealer:object, popup_dealer:object):
        self.api_dealer = api_dealer
        self.popup_dealer = popup_dealer
        self.background = ui_items.Background(background_name="isg_ui_page_template", default_resolution=(1920,1080))
        
        self.frame_fetching_interval = 3 #seconds
        self.last_time_frames_fetched = time.time()
        self.page_frame = None         
        self.last_frames_without_BLOB:List = None
        self.selected_indexes = []
        self.fetched_images = []

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
        
        # ========================== #
        self.reset_page_frame()

    def __determine_indexes_to_display_and_fetch(self):
        violation_and_person_indexes = []
        person_indexes = []
        neither_indexes = []
        for i, frame_info in enumerate(self.last_frames_without_BLOB): # camera_ip, camera_region, camera_uuid, date_created, date_updated, is_person_detected, is_violation_detected
            if frame_info["is_person_detected"] and frame_info["is_violation_detected"]:
                violation_and_person_indexes.append(i)
            elif frame_info["is_person_detected"]:
                person_indexes.append(i)
            else:
                neither_indexes.append(i)
        random.shuffle(violation_and_person_indexes)
        random.shuffle(person_indexes)
        random.shuffle(neither_indexes)
        
        self.selected_indexes = []
        self.selected_indexes.extend(violation_and_person_indexes)
        if len(self.selected_indexes) < 6:
            self.selected_indexes.extend(person_indexes[:6 - len(self.selected_indexes)])
        if len(self.selected_indexes) < 6:
            self.selected_indexes.extend(neither_indexes[:6 - len(self.selected_indexes)])
        self.selected_indexes = self.selected_indexes[:6]

        self.fetched_images = []
        for i in self.selected_indexes:
            result = self.api_dealer.get_last_camera_frame_by_camera_uuid(camera_uuid=self.last_frames_without_BLOB[i]["camera_uuid"])
            if result[0]:
                last_camera_frame_info = result[2]["last_frame_info"]
                if last_camera_frame_info is None:
                    self.popup_dealer.append_popup({"background_color":(255,0,0), "created_at":time.time(), "duration":2, "text":"Henüz kamera görüntüsü yüklenmemiş"})
                else:
                    self.fetched_images.append(cv2.imdecode(np.frombuffer(base64.b64decode(last_camera_frame_info['last_frame_b64']),np.uint8), cv2.IMREAD_COLOR))
            else:
                self.popup_dealer.append_popup({"background_color":(255,0,0), "created_at":time.time(), "duration":2, "text":result[2]["detail"]})

    def reset_page_frame(self):
        self.page_frame = self.background.get_background_frame()
       
        # Get the last frames without BLOB ========================================
        self.last_frames_without_BLOB = self.api_dealer.get_all_last_camera_frame_info_without_BLOB()[2]["last_frame_info"]
        self.__determine_indexes_to_display_and_fetch()

        display_frame_width = self.page_frame.shape[1]*0.20
        display_frame_height = self.page_frame.shape[0]*0.20
        frame_locations = [(0.02, 0.14), (0.25, 0.14), (0.02, 0.42), (0.25, 0.42), (0.02, 0.69), (0.25, 0.69)]
        main_frame_location = (0.48, 0.085)
        main_frame_width = self.page_frame.shape[1]*0.48
        main_frame_height = self.page_frame.shape[0]*0.48

        for i, image in enumerate(self.fetched_images):
            # Calculate the top-left corner position of the frame
            top_left_x = int(frame_locations[i][0] * self.page_frame.shape[1])
            top_left_y = int(frame_locations[i][1] * self.page_frame.shape[0])
            
            # Calculate the bottom-right corner position of the frame
            bottom_right_x = int(top_left_x + display_frame_width)
            bottom_right_y = int(top_left_y + display_frame_height)
            
            # Draw the image on the frame
            picasso.draw_frame_on_frame(
                self.page_frame, image, 
                top_left_x, top_left_y, 
                width=int(display_frame_width), 
                height=int(display_frame_height), 
                maintain_aspect_ratio=False
            )
           
            # Fetch information about the image
            image_index = self.selected_indexes[i]
            camera_ip = self.last_frames_without_BLOB[image_index]["camera_ip"]
            camera_region = self.last_frames_without_BLOB[image_index]["camera_region"]
            is_violation_detected = self.last_frames_without_BLOB[image_index]["is_violation_detected"]
            is_person_detected = self.last_frames_without_BLOB[image_index]["is_person_detected"]            
            camera_name_text = f"{camera_ip}" if camera_region == "Henüz Atanmadı" else f"{camera_region}"

            #def draw_text_on_frame(frame: np.ndarray, text: str, position: tuple, area_size: tuple, alignment: str = 'center', font=cv2.FONT_HERSHEY_SIMPLEX, font_scale=1, text_color=(255, 255, 255), thickness=2, padding=10):

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

            if i == 0:
                picasso.draw_frame_on_frame(
                    self.page_frame, image, 
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


            # Check for violation and draw text and rectangle
            if is_violation_detected or is_person_detected:
                # Draw text above the rectangle
                color = (0, 0, 255) if is_violation_detected else (255, 0, 0)
                picasso.draw_text_on_frame(
                    self.page_frame, 
                    text="İhlal ve Insan Tespit Edildi" if is_violation_detected and is_person_detected else "İnsan Tespit Edildi" if is_person_detected else "İhlal Tespit Edildi", 
                    position=(top_left_x, top_left_y -25),
                    area_size=(int(display_frame_width), int(20)),
                    alignment='center', 
                    font=cv2.FONT_HERSHEY_SIMPLEX, 
                    font_scale = 0.75, 
                    text_color=color, 
                    thickness=1, 
                    padding=10
                )
                
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
            
          

        


                                        