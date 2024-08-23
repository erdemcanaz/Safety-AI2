import requests
import classes
import pprint,random, unicodedata,datetime, time

def create_mock_data(type_of_data:str = None):   
    if type_of_data == "None":
        return None 
    elif type_of_data == "ASCII_printables":
        return "'0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!\"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~" 
    elif type_of_data == "ASCII_extended_printables":
        return  "!#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_`abcdefghijklmnopqrstuvwxyz{|}~ ¡¢£¤¥¦§¨©ª«¬­®¯°±²³´µ¶·¸¹º»¼½¾¿ÀÁÂÃÄÅÆÇÈÉÊËÌÍÎÏÐÑÒÓÔÕÖ×ØÙÚÛÜÝÞßàáâãäåæçèéêëìíîïðñòóôõö÷øùúûüýþÿ"
    elif type_of_data == "turkish_alphabet":
        return "ABCÇDEFGĞHIİJKLMNOÖPRSŞTUÜVYZabcçdefgğhıijklmnoöprsştuüvyz"
    elif type_of_data == "long_string":
        return_text = ""
        for i in range(1000):
            return_text += random.choice("ABCÇDEFGĞHIİJKLMNOÖPRSŞTUÜVYZabcçdefgğhıijklmnoöprsştuüvyz")
    elif type_of_data == "random_unicode":
        return_text = ""
        while True:
            random_code_point = random.randint(0, 0x10FFFF)
            char = chr(random_code_point)
            if unicodedata.category(char)[0] != 'C':
                return_text += str(char)

            if len(return_text) > 100:
                break
        return return_text
    elif type_of_data == "small_positive_float":
        return random.uniform(0.001, 999.999)
    elif type_of_data == "small_positive_float_string":
        return str(random.uniform(0.001, 999.999))
    elif type_of_data == "small_negative_float":
        return random.uniform(-999.999, -0.001)
    elif type_of_data == "small_negative_float_string":
        return str(random.uniform(-999.999, -0.001))
    elif type_of_data == "large_positive_float":
        return random.uniform(0.001, 1e9)
    elif type_of_data == "large_positive_float_string":
        return str(random.uniform(0.001, 1e9))
    elif type_of_data == "large_negative_float":
        return random.uniform(-1e9, -0.001)
    elif type_of_data == "large_negative_float_string":
        return str(random.uniform(-1e9, -0.001))
    elif type_of_data == "small_positive_integer":
        return random.randint(1, 999)
    elif type_of_data == "small_positive_integer_string":
        return str(random.randint(1, 999))
    elif type_of_data == "small_negative_integer":
        return random.randint(-999, -1)
    elif type_of_data == "small_negative_integer_string":
        return str(random.randint(-999, -1))
    elif type_of_data == "large_positive_integer":
        return random.randint(1, int(1e9))
    elif type_of_data == "large_positive_integer_string":
        return str(random.randint(1, int(1e9)))
    elif type_of_data == "large_negative_integer":
        return random.randint(-int(1e9), -1)
    elif type_of_data == "large_negative_integer_string":
        return str(random.randint(-int(1e9), -1))
    elif type_of_data == "boolean":
        return random.choice([True, False])
    elif type_of_data == "empty_dict":
        return {}
    elif type_of_data == "empty_list":
        return []
    else:
        raise ValueError("Unknown type_of_data")

def ping_endpoint(endpoint_url:str=None):
    try:
        response = requests.get(endpoint_url)
        if response.status_code == 200:
            print(f"Ping to {endpoint_url} successful!")
        else:
            print(f"Ping to {endpoint_url} failed with status code: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"Error pinging {endpoint_url}: {e}")

def clear_txt_file(file_name:str = None):
    with open(file_name, "w") as f:
        f.write("")

def append_text_to_txt_file(text:str = None, file_name:str = None):
    with open(file_name, "a") as f:
        f.write(text)

def incorrect_token_test(post_request:classes.PostRequest = None):
    log_row = f"\n\n{'='*70}\nIncorrect token test: post a single request with a default violation log that is known to be working where format is jpg and resolution is test_default but with an incorrect token value\n"
    print(log_row)
    initial_token_value = post_request.headers["token"]
    try:
        violation = classes.ViolationLog()
        violation.set_as_default_correct_dict()
        violation.update_image_as(resolution_key= "test_default", image_format = "jpg")
        
        post_request.clear_body()
        post_request.headers["token"] = "Incorrect token value"
        post_request.body["SafetyData"].append(violation.get_violation_log())
        r = post_request.send_post_request()
        log_row += post_request.print_(status_code=r["status_code"], expected_status_code="Not 200", text=r["text"])+"\n"
        log_row += violation.print_()
        return log_row
    except Exception as e:
        log_row += f"Error: {e}"
        print(log_row)
        return log_row
    finally:
        post_request.headers["token"] = initial_token_value

def empty_request_test(post_request:classes.PostRequest = None):
    # Send an empty request
    log_row = f"\n\n{'='*70}\nEmpty request test: post an empty request\n"
    print(log_row)
    try:
        post_request.clear_body()
        r = post_request.send_post_request()
        log_row += post_request.print_(status_code=r["status_code"], expected_status_code=200, text=r["text"])+"\n"
        return log_row
    except Exception as e:
        print(f"Error: {e}")
        return f"Error: {e}"
    
def correct_request_test(post_request:classes.PostRequest = None):
    # Send a single request with a default violation log that is known to be working

    log_row = f"\n\n{'='*70}\nCorrect request test: post a single request with a default violation log that is known to be working where format is jpg and resolution is test_default\n"
    print(log_row)
    try:
        violation = classes.ViolationLog()
        violation.set_as_default_correct_dict()
        violation.update_image_as(resolution_key= "test_default", image_format = "jpg")

        post_request.clear_body()
        post_request.body["SafetyData"].append(violation.get_violation_log())
        r = post_request.send_post_request()
        log_row += post_request.print_(status_code=r["status_code"], expected_status_code=200, text=r["text"])+"\n"
        log_row += violation.print_()
        return log_row
    except Exception as e:
        print(f"Error: {e}")
        return f"Error: {e}"

def multiple_correct_request_test(post_request:classes.PostRequest = None):
    # Send a single request with multiple default violation logs that are known to be working
    log_row = f"\n\n{'='*70}\nMultiple correct request test: post multiple requests with default violation logs that are known to be working where format is jpg and resolution is test_default\n"
    print(log_row)

    for number_of_violations in [1, 5, 10, 15, 20, 25]:    
        log_row += f"{'-'*25}\n----Number of violations = {number_of_violations}\n"
        print(f"{'-'*25}\n----Number of violations = {number_of_violations}\n")
        time.sleep(2.0)
        try:
            log_row += f"start_time: {datetime.datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n"
            print(f"start_time: {datetime.datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n")

            post_request.clear_body()
            violations_list = []
            for i in range(number_of_violations):
                violation = classes.ViolationLog()
                violation.set_as_default_correct_dict()
                violation.update_image_as(resolution_key= "test_default", image_format = "jpg")
                post_request.append_new_data(violation.get_violation_log())
                violations_list.append(violation)

            r = post_request.send_post_request()
            log_row += post_request.print_(status_code=r["status_code"], expected_status_code=200, text=r["text"])+"\n"

            for violation_ in violations_list[:10]:
                log_row += violation_.print_()+"\n"
            if len(violations_list) > 50:print("...\n")

            log_row += f"end_time: {datetime.datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n"
            print(f"end_time: {datetime.datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n")
        except Exception as e:
            print(f"Error: {e}")
            log_row += f"\nError:{e}"
    
    return log_row

def date_formats_request_test(post_request:classes.PostRequest = None):
    # Send a single request with a default violation log that is known to be working

    log_row = f"\n\n{'='*70}\nDate format test: post a single request with a default violation log that is known to be working where format is jpg and resolution is test_default. But the date is gradually set to more general. For example  15.08.2024 11:11:23 ->  15.08.2024 11:11 -> ... ->  15.08.2024 \n"
    print(log_row)

    try:
        for date_format in ["%d.%m.%Y %H:%M:%S.%f", "%d.%m.%Y %H:%M:%S", "%d.%m.%Y %H:%M", "%d.%m.%Y %H", "%d.%m.%Y"]:
            time.sleep(2.0)
            log_row += f"{'-'*25}\n\n----Date format = {date_format}\n"
            print(f"{'-'*25}\n\n----Date format = {date_format}\n")
            try:
                violation = classes.ViolationLog()
                violation.set_as_default_correct_dict()
                violation.update_image_as(resolution_key= "test_default", image_format = "jpg")                
                timestamp = datetime.datetime.now().strftime(date_format)
                violation.update_violation_dict_key(key = "RelatedShiftDate", value = timestamp)
                violation.update_violation_dict_key(key = "DeviceTimestamp", value = timestamp)

                post_request.clear_body()
                post_request.body["SafetyData"].append(violation.get_violation_log())
                r = post_request.send_post_request()
                log_row += post_request.print_(status_code=r["status_code"], expected_status_code=200, text=r["text"])+"\n"
                log_row += violation.print_()
            except Exception as e:
                log_row += f"\nError: {e}"

        return log_row
    except Exception as e:
        print(f"Error: {e}")
        return f"Error: {e}"

def image_encoding_and_resolution_test(post_request:classes.PostRequest = None):
    resolution_names = ["test_default", "VGA", "480p", "576i", "SVGA", "HD", "XGA", "WXGA", "720p", "SXGA", "1080p", "QHD", "4K UHD", "5K", "8K UHD"]
    image_encodings = [".jpg", ".png"]
    
    log_row = f"\n\n{'='*70}\nImage encoding and resolution test: post a single request with a default violation log that is known to be working where format is {image_encodings} and resolution is {resolution_names}\n"
    print(log_row)

    for image_encoding in image_encodings:
        for resolution_name in resolution_names:
            time.sleep(2)
            log_row += f"{'-'*25}\n\n----Image encoding = {image_encoding}, Resolution = {resolution_name}\n"
            print(f"{'-'*25}\n\n----Image encoding = {image_encoding}, Resolution = {resolution_name}\n")
            try:
                violation = classes.ViolationLog()
                violation.set_as_default_correct_dict()
                violation.update_image_as(resolution_key= resolution_name, image_format = image_encoding)
                
                post_request.clear_body()
                post_request.body["SafetyData"].append(violation.get_violation_log())
                r = post_request.send_post_request()
                log_row += post_request.print_(status_code=r["status_code"], expected_status_code=200, text=r["text"])+"\n"
                log_row += violation.print_()               
            except Exception as e:
                print(f"Error: {e}")
                return f"Error: {e}"
            
    return log_row
#================================================================================================
PARAM_LOG_TXT_NAME = "test_log.txt"

clear_txt_file(file_name=PARAM_LOG_TXT_NAME)
append_text_to_txt_file(file_name=PARAM_LOG_TXT_NAME, text=f"TEST LOGS {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

post_request = classes.PostRequest()
post_request.clear_body()

# append_text_to_txt_file(text = incorrect_token_test(post_request=post_request), file_name= PARAM_LOG_TXT_NAME)
# time.sleep(2.0)
# append_text_to_txt_file(text = empty_request_test(post_request=post_request), file_name= PARAM_LOG_TXT_NAME)
# time.sleep(2.0)
# append_text_to_txt_file(text = correct_request_test(post_request=post_request), file_name= PARAM_LOG_TXT_NAME)
# time.sleep(2.0)
# append_text_to_txt_file(text = multiple_correct_request_test(post_request=post_request), file_name= PARAM_LOG_TXT_NAME)
# time.sleep(2.0)
# append_text_to_txt_file(text = date_formats_request_test(post_request=post_request), file_name= PARAM_LOG_TXT_NAME)
# time.sleep(2.0)
append_text_to_txt_file(text = image_encoding_and_resolution_test(post_request=post_request), file_name= PARAM_LOG_TXT_NAME)
