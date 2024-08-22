import requests
import classes
import pprint,random, unicodedata

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

def correct_request_test(post_request:classes.PostRequest = None):
    violation = classes.ViolationLog()
    violation.set_as_default_correct_dict()
    violation.update_image_as(resolution_key= "test_default", image_format = "jpg")

    post_request.clear_body()
    post_request.body["SafetyData"].append(violation.get_violation_log())
    post_request.send_post_request()

    
correct_request_test()
