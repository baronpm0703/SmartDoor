import json
import os
import time
from datetime import datetime
import cv2
import requests
import numpy as np
import FirebaseModule
import FaceRecognitionModule
import HandTrackingModule
import EmailModule

firebase_config_json = open("config\\firebase_config.json", "r")
firebase_config = json.load(firebase_config_json)
firebase_config_json.close()

fm = FirebaseModule.FirebaseModule(config=firebase_config)

system_mail_json = open("config\\system_mail.json", "r")
system_mail = json.load(system_mail_json)
system_mail_json.close()

em = EmailModule.EmailModule(gmail_username=system_mail["username"], gmail_password=system_mail["password"])

default_user_config_json = open("config\\default_user_config.json", "r")
user_config = json.load(default_user_config_json)
default_user_config_json.close()

sensor = {
    "PIR": False,
    "Ultrasonic": 2147483648
}

frm = FaceRecognitionModule.FaceRecognitionModule()

htm = HandTrackingModule.HandDetector(max_num_hands=2)

def updateUserImages(remote_path, local_path, interval=15, max_retries=5, delete_local_files=True):
    if not hasattr(updateUserImages, "last_update"):
        updateUserImages.last_update = 0

    if time.time() - updateUserImages.last_update > interval:
        for i in range(max_retries):
            try:
                fm.updateLocalStorage(remote_path=remote_path, local_path=local_path, delete_local_files=delete_local_files)
            except:
                print("Retry updating local storage...")
            else:
                break
        else:
            print(f"Local storage has failed to update after {max_retries} retries")
        
        updateUserImages.last_update = time.time()

def updateUserConfig(max_retries=5):
    global user_config

    for i in range(max_retries):
        try:
            user_config = fm.getDataRTDB(path="UserConfig")
        except:
            print("Retry updating user configuration...")
        else:
            break
    else:
        print(f"User configuration has failed to update after {max_retries} retries")

def updateSensorsValue(max_retries=5):
    global sensor

    for i in range(max_retries):
        try:
            sensor = fm.getDataRTDB(path="Sensor")
        except:
            print("Retry updating sensors value...")
        else:
            break
    else:
        print(f"Sensors value has failed to update after {max_retries} retries")

def updateUserFaces(user_images_path, interval=15):
    if not hasattr(updateUserFaces, "last_update"):
        updateUserFaces.last_update = 0
    if not hasattr(updateUserFaces, "current_user_images"):
        updateUserFaces.current_user_images = set(os.listdir(user_images_path))

        for user_image_file in updateUserFaces.current_user_images:
            user_image = cv2.imread(f"{user_images_path}\\{user_image_file}")
            user_image = cv2.cvtColor(user_image, cv2.COLOR_BGR2RGB)

            user_id = os.path.splitext(user_image_file)[0]

            try:
                user_info = fm.getUserInfo(uid=user_id)
                user_name = user_info["username"]
            except Exception as e:
                print(f"Adding user with this corresponding image: {user_image_file} has failed")
                continue

            print(f"Adding user: {user_name}")
            try:
                frm.addKnownFace(image=user_image, name=user_name)
                print(f"Added user: {user_name}")
            except Exception as e:
                print(f"Adding user: {user_name} has failed")

    if time.time() - updateUserFaces.last_update > interval:
        latest_user_images = set(os.listdir(user_images_path))

        not_up2date_user = latest_user_images - updateUserFaces.current_user_images
        deleted_user = updateUserFaces.current_user_images - latest_user_images
        deleted_user = {os.path.splitext(user_image_file)[0] for user_image_file in deleted_user}

        for user_image_file in not_up2date_user:
            user_image = cv2.imread(f"{user_images_path}\\{user_image_file}")
            user_image = cv2.cvtColor(user_image, cv2.COLOR_BGR2RGB)

            user_name = os.path.splitext(user_image_file)[0]

            print(f"Adding user: {user_name}")
            frm.addKnownFace(image=user_image, name=user_name)
            print(f"Added user: {user_name}")

        for index in reversed(range(len(frm.encode_known_faces))):
            user_name = frm.known_faces_name[index]
            if user_name in deleted_user:
                print(f"Removing user: {user_name}")
                frm.removeKnownFace(index=index)
                print(f"Removed user: {user_name}")

        updateUserFaces.current_user_images = latest_user_images

def readDataRTDB(path, max_retries=5, success_notification=False):
    for i in range(max_retries):
        try:
            data = fm.getDataRTDB(path=path)
            if success_notification:
                print(f"Reading data from {path} has succeeded")
            return data
        except:
            print(f"Retry reading data from {path}...")
        else:
            break
    else:
        print(f"Reading data from {path} has failed after {max_retries} retries")

def writeDataRTDB(path, data, max_retries=5, success_notification=False):
    for i in range(max_retries):
        try:
            fm.setDataRTDB(path=path, data=data)
            if success_notification:
                print(f"Writing {data} to {path} has succeeded")
        except:
            print(f"Retry writing {data} to {path}...")
        else:
            break
    else:
        print(f"Writing {data} to {path} has failed after {max_retries} retries")

def appendDataRTDB(path, data, max_retries=5, success_notification=False):
    for i in range(max_retries):
        try:
            fm.pushDataRTDB(path=path, data=data)
            if success_notification:
                print(f"Appending {data} to {path} has succeeded")
        except:
            print(f"Retry appending {data} to {path}...")
        else:
            break
    else:
        print(f"Appending {data} to {path} has failed after {max_retries} retries")

def getCameraImage(esp32=True, cameraUrl="", max_retries=5):
    if esp32:
        if not hasattr(getCameraImage, "prev_image"):
            prev_image = None
        if not hasattr(getCameraImage, "request_time"):
            request_time = time.time()

        if prev_image is None or time.time() - request_time >= 5:
            for i in range(max_retries):
                response = requests.get(cameraUrl)

                if response.status_code == 200:
                    content_length = int(response.headers.get('Content-Length', 0))

                    if content_length > 0:        
                        img_array = np.array(bytearray(response.content), dtype=np.uint8)                    
                        image = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
                        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

                        request_time = time.time()
                        prev_image = image

                        return image
                    else:
                        print("Empty content received from the URL.")
                else:
                    print(f"Failed to fetch the image. Status code: {response.status_code}")
        else:
            return prev_image
    
    else:
        if not hasattr(getCameraImage, "capture"):
            getCameraImage.capture = cv2.VideoCapture(0)

        success, image = getCameraImage.capture.read()

        image = cv2.flip(image, 1)
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        return image

def sendWarningEmail(user_email, current_time, success_notification=False):
    try:
        mail_subject = "[Smart Door System Alert]"
        mail_body = f"There are strangers in front of your house at {current_time}"
        em.sendMail(receiver_email=user_email, subject=mail_subject, body=mail_body)

        if success_notification:
            print(f"Sending warning email to {user_email} has succeeded")
    except Exception as e:
        if success_notification:
            print(f"Sending warning email to {user_email} has failed")

def main():
    is_checking = True
    last_open_door_time = time.time()
    current_users = set()
    stranger_detect = False
    stranger_encounter_time = 0

    while True:
        # Realtime Update
        updateUserImages(remote_path="user_images", local_path="user_images", interval=15, max_retries=5)
        updateUserFaces(user_images_path="user_images", interval=15)
        updateUserConfig(max_retries=5)
        updateSensorsValue(max_retries=5)

        # Processing
        if user_config["SmartDoorSystem"]:

            # Camera On
            if user_config["Camera"]:

                # Face Recognition
                if sensor["Ultrasonic"] <= user_config["CheckingDistance"]:
                    is_checking = True

                    if user_config["FaceRecognition"]:
                        # ------------------------- For debugging ----------------------------
                        # Set esp32=False to use webcam for debugging
                        image = getCameraImage(esp32=False)
                        # image = getCameraImage(esp32=True, cameraUrl=cameraUrl)

                        # Set _ to image and visualize=True for debugging
                        is_known, users_name, _ = frm.checkFace(image=image, visualize=False)
                        # --------------------------------------------------------------------

                        # User Detect
                        if True in is_known:
                            stranger_detect = False

                            display_user_name = users_name[is_known.index(True)]
                            if str(readDataRTDB(path="Lcd/nameExpectation")) != display_user_name:
                                writeDataRTDB(path="Lcd/nameExpectation", data=display_user_name, success_notification=True)

                            # Gesture Control
                            if user_config["GestureControl"]:
                                htm.process(image)

                                # ------------ ONLY for debugging -----------------
                                # image = htm.drawHandsConnection(flipped=False)
                                # -------------------------------------------------

                                # Left hand and Right hand detected
                                if HandTrackingModule.HandType.LEFT_HAND.value in htm.getHandsDetected() and HandTrackingModule.HandType.RIGHT_HAND.value in htm.getHandsDetected():
                                    raised_fingers = htm.getRaisedFingers(flipped=False)
                                    left_raised_fingers = raised_fingers[HandTrackingModule.HandType.LEFT_HAND.value]
                                    right_raised_fingers = raised_fingers[HandTrackingModule.HandType.RIGHT_HAND.value]

                                    # Setting Auto Open Door option
                                    if left_raised_fingers[0] and left_raised_fingers.count(False) >= 4:
                                        if str(readDataRTDB(path="Lcd/gestureExpectation")) != "Auto Open":
                                            writeDataRTDB(path="Lcd/gestureExpectation", data="Auto Open", success_notification=True)

                                        # Set Auto Open On
                                        if right_raised_fingers[1] and right_raised_fingers.count(False) >= 4:
                                            if not user_config["AutoOpen"]:
                                                user_config["AutoOpen"] = True
                                                writeDataRTDB(path="UserConfig/AutoOpen", data=True, success_notification=True)

                                            if str(readDataRTDB(path="Lcd/stateExpectation")) != "On":    
                                                writeDataRTDB(path="Lcd/stateExpectation", data="On", success_notification=True)

                                        # Set Auto Open Off
                                        elif right_raised_fingers[4] and right_raised_fingers.count(False) >= 4:
                                            if user_config["AutoOpen"]:
                                                user_config["AutoOpen"] = False
                                                writeDataRTDB(path="UserConfig/AutoOpen", data=False, success_notification=True)

                                            if str(readDataRTDB(path="Lcd/stateExpectation")) != "Off":
                                                writeDataRTDB(path="Lcd/stateExpectation", data="Off", success_notification=True)

                                        # Not setting yet
                                        else:
                                            if str(readDataRTDB(path="Lcd/stateExpectation")) != "None":
                                                writeDataRTDB(path="Lcd/stateExpectation", data="None", success_notification=True)

                                    # Setting Auto Close Door option
                                    elif left_raised_fingers[1] and left_raised_fingers.count(False) >= 4:
                                        if str(readDataRTDB(path="Lcd/gestureExpectation")) != "Auto Close":
                                            writeDataRTDB(path="Lcd/gestureExpectation", data="Auto Close", success_notification=True)

                                        # Set Auto Close On
                                        if right_raised_fingers[1] and right_raised_fingers.count(False) >= 4:
                                            if not user_config["AutoClose"]:
                                                user_config["AutoClose"] = True
                                                writeDataRTDB(path="UserConfig/AutoClose", data=True, success_notification=True)

                                            if str(readDataRTDB(path="Lcd/stateExpectation")) != "On":
                                                writeDataRTDB(path="Lcd/stateExpectation", data="On", success_notification=True)

                                        # Set Auto Close Off
                                        elif right_raised_fingers[4] and right_raised_fingers.count(False) >= 4:
                                            if user_config["AutoClose"]:
                                                user_config["AutoClose"] = False
                                                writeDataRTDB(path="UserConfig/AutoClose", data=False, success_notification=True)

                                            if str(readDataRTDB(path="Lcd/stateExpectation")) != "Off":
                                                writeDataRTDB(path="Lcd/stateExpectation", data="Off", success_notification=True)

                                        # Not setting yet
                                        else:
                                            if str(readDataRTDB(path="Lcd/stateExpectation")) != "None":
                                                writeDataRTDB(path="Lcd/stateExpectation", data="None", success_notification=True)

                                    # Setting Stranger Detection option
                                    elif left_raised_fingers[2] and left_raised_fingers.count(False) >= 4:
                                        if str(readDataRTDB(path="Lcd/gestureExpectation")) != "Stranger Detection":
                                            writeDataRTDB(path="Lcd/gestureExpectation", data="Stranger Detection", success_notification=True)

                                        # Set Stranger Detection On
                                        if right_raised_fingers[1] and right_raised_fingers.count(False) >= 4:
                                            if not user_config["StrangerDetection"]:
                                                user_config["StrangerDetection"] = True
                                                writeDataRTDB(path="UserConfig/StrangerDetection", data=True, success_notification=True)

                                            if str(readDataRTDB(path="Lcd/stateExpectation")) != "On":
                                                writeDataRTDB(path="Lcd/stateExpectation", data="On", success_notification=True)

                                        # Set Stranger Detection Off
                                        elif right_raised_fingers[4] and right_raised_fingers.count(False) >= 4:
                                            if user_config["StrangerDetection"]:
                                                user_config["StrangerDetection"] = False
                                                writeDataRTDB(path="UserConfig/StrangerDetection", data=False, success_notification=True)

                                            if str(readDataRTDB(path="Lcd/stateExpectation")) != "Off":
                                                writeDataRTDB(path="Lcd/stateExpectation", data="Off", success_notification=True)

                                        # Not setting yet
                                        else:
                                            if str(readDataRTDB(path="Lcd/stateExpectation")) != "None":
                                                writeDataRTDB(path="Lcd/stateExpectation", data="None", success_notification=True)

                                    # Setting Visitors Tracking option
                                    elif left_raised_fingers[3] and left_raised_fingers.count(False) >= 4:
                                        if str(readDataRTDB(path="Lcd/gestureExpectation")) != "Visitors Tracking":
                                            writeDataRTDB(path="Lcd/gestureExpectation", data="Visitors Tracking", success_notification=True)

                                        # Set Visitors Tracking On
                                        if right_raised_fingers[1] and right_raised_fingers.count(False) >= 4:
                                            if not user_config["VisitorsTracking"]:
                                                user_config["VisitorsTracking"] = True
                                                writeDataRTDB(path="UserConfig/VisitorsTracking", data=True, success_notification=True)

                                            if str(readDataRTDB(path="Lcd/stateExpectation")) != "On":
                                                writeDataRTDB(path="Lcd/stateExpectation", data="On", success_notification=True)

                                        # Set Visitors Tracking Off
                                        elif right_raised_fingers[4] and right_raised_fingers.count(False) >= 4:
                                            if user_config["VisitorsTracking"]:
                                                user_config["VisitorsTracking"] = False
                                                writeDataRTDB(path="UserConfig/VisitorsTracking", data=False, success_notification=True)

                                            if str(readDataRTDB(path="Lcd/stateExpectation")) != "Off":
                                                writeDataRTDB(path="Lcd/stateExpectation", data="Off", success_notification=True)

                                        # Not setting yet
                                        else:
                                            if str(readDataRTDB(path="Lcd/stateExpectation")) != "None":
                                                writeDataRTDB(path="Lcd/stateExpectation", data="None", success_notification=True)

                                    # Setting Warning Notification option
                                    elif left_raised_fingers[4] and left_raised_fingers.count(False) >= 4:
                                        if str(readDataRTDB(path="Lcd/gestureExpectation")) != "Warning Notification":
                                            writeDataRTDB(path="Lcd/gestureExpectation", data="Warning Notification", success_notification=True)

                                        # Set Warning Notification On
                                        if right_raised_fingers[1] and right_raised_fingers.count(False) >= 4:
                                            if not user_config["WarningNotification"]:
                                                user_config["WarningNotification"] = True
                                                writeDataRTDB(path="UserConfig/WarningNotification", data=True, success_notification=True)

                                            if str(readDataRTDB(path="Lcd/stateExpectation")) != "On":
                                                writeDataRTDB(path="Lcd/stateExpectation", data="On", success_notification=True)

                                        # Set Warning Notification Off
                                        elif right_raised_fingers[4] and right_raised_fingers.count(False) >= 4:
                                            if user_config["WarningNotification"]:
                                                user_config["WarningNotification"] = False
                                                writeDataRTDB(path="UserConfig/WarningNotification", data=False, success_notification=True)

                                            if str(readDataRTDB(path="Lcd/stateExpectation")) != "Off":
                                                writeDataRTDB(path="Lcd/stateExpectation", data="Off", success_notification=True)

                                        # Not setting yet
                                        else:
                                            if str(readDataRTDB(path="Lcd/stateExpectation")) != "None":
                                                writeDataRTDB(path="Lcd/stateExpectation", data="None", success_notification=True)

                                    else:
                                        # Update LCD
                                        if str(readDataRTDB(path="Lcd/gestureExpectation")) != "None":
                                            writeDataRTDB(path="Lcd/gestureExpectation", data="None", success_notification=True)
                                        if str(readDataRTDB(path="Lcd/stateExpectation")) != "None":
                                            writeDataRTDB(path="Lcd/stateExpectation", data="None", success_notification=True)

                                else:
                                    # Update LCD
                                    if str(readDataRTDB(path="Lcd/gestureExpectation")) != "None":
                                        writeDataRTDB(path="Lcd/gestureExpectation", data="None", success_notification=True)
                                    if str(readDataRTDB(path="Lcd/stateExpectation")) != "None":
                                        writeDataRTDB(path="Lcd/stateExpectation", data="None", success_notification=True)

                            # Visitors Tracking
                            if user_config["VisitorsTracking"]:
                                users_detect = set(users_name)
                                if current_users.issubset(users_detect):
                                    new_users_detect = users_detect - current_users

                                    for user in new_users_detect:
                                        if user == "":
                                            continue

                                        user_profile = {
                                            "Name": user,
                                            "VisitTime": datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                                        }

                                        appendDataRTDB(path="VisitorsTracking", data=user_profile, success_notification=True)

                                    current_users = users_detect

                            # Auto Open Door
                            if user_config["AutoOpen"]:
                                if not readDataRTDB(path="Door/Expectation"):
                                    writeDataRTDB(path="Door/Expectation", data=True, success_notification=True)

                            # Stranger Warning Off
                            if readDataRTDB(path="Warning/Expectation"):
                                writeDataRTDB(path="Warning/Expectation", data=False, success_notification=True)

                        # Stranger Detect
                        elif True not in is_known and len(is_known) > 0:
                            current_users = set()

                            # Update LCD
                            if str(readDataRTDB(path="Lcd/gestureExpectation")) != "None":
                                writeDataRTDB(path="Lcd/gestureExpectation", data="None", success_notification=True)
                            if str(readDataRTDB(path="Lcd/stateExpectation")) != "None":
                                writeDataRTDB(path="Lcd/stateExpectation", data="None", success_notification=True)

                            # Stranger Detection
                            if user_config["StrangerDetection"]:
                                if str(readDataRTDB(path="Lcd/nameExpectation")) != "Stranger":
                                    writeDataRTDB(path="Lcd/nameExpectation", data="Stranger", success_notification=True)

                                # Stranger Warning On
                                if stranger_detect == False:
                                    stranger_encounter_time = time.time()

                                    if user_config["VisitorsTracking"]:
                                        user_profile = {
                                            "Name": "Stranger",
                                            "VisitTime": datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                                        }

                                        appendDataRTDB(path="VisitorsTracking", data=user_profile, success_notification=True)

                                    stranger_detect = True
                                elif not readDataRTDB(path="Warning/Expectation") and time.time() - stranger_encounter_time > user_config["StrangerWarningTime"]:
                                    writeDataRTDB(path="Warning/Expectation", data=True, success_notification=True)

                                    # Warning Notification
                                    if user_config["WarningNotification"]:
                                        users_email = fm.getUsersEmail()

                                        current_time = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

                                        for user_email in users_email:
                                            sendWarningEmail(user_email=user_email, current_time=current_time, success_notification=True)

                            else:
                                if str(readDataRTDB(path="Lcd/nameExpectation")) != "None":
                                    writeDataRTDB(path="Lcd/nameExpectation", data="None", success_notification=True)

                        # Nothing Detect
                        else:
                            current_users = set()
                            stranger_detect = False

                            # Update LCD
                            if str(readDataRTDB(path="Lcd/nameExpectation")) != "None":
                                writeDataRTDB(path="Lcd/nameExpectation", data="None", success_notification=True)
                            if str(readDataRTDB(path="Lcd/gestureExpectation")) != "None":
                                writeDataRTDB(path="Lcd/gestureExpectation", data="None", success_notification=True)
                            if str(readDataRTDB(path="Lcd/stateExpectation")) != "None":
                                writeDataRTDB(path="Lcd/stateExpectation", data="None", success_notification=True)

                            # Stranger Warning Off
                            if readDataRTDB(path="Warning/Expectation"):
                                writeDataRTDB(path="Warning/Expectation", data=False, success_notification=True)

                        # ------------------------------------ ONLY for debugging ---------------------------------------
                        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

                        fps = HandTrackingModule.getFPS()
                        cv2.putText(image, "FPS: " + str(int(fps)), (10, 20), cv2.FONT_HERSHEY_PLAIN, 1, (0, 255, 0), 1)

                        cv2.imshow("Image", image)

                        if cv2.waitKey(1) & 0xFF == ord('q'):
                            break
                        # -----------------------------------------------------------------------------------------------

                    # Update Door Open Time
                    last_open_door_time = time.time()

                elif is_checking and readDataRTDB(path="Door/Expectation"):
                    is_checking = False
                    last_open_door_time = time.time()

                else:
                    # Stranger Warning Off
                    if readDataRTDB(path="Warning/Expectation"):
                        writeDataRTDB(path="Warning/Expectation", data=False, success_notification=True)

                    # Update LCD
                    if str(readDataRTDB(path="Lcd/nameExpectation")) != "None":
                        writeDataRTDB(path="Lcd/nameExpectation", data="None", success_notification=True)
                    if str(readDataRTDB(path="Lcd/gestureExpectation")) != "None":
                        writeDataRTDB(path="Lcd/gestureExpectation", data="None", success_notification=True)
                    if str(readDataRTDB(path="Lcd/stateExpectation")) != "None":
                        writeDataRTDB(path="Lcd/stateExpectation", data="None", success_notification=True) 

            # Camera Off
            else:
                # Stranger Warning Off
                if readDataRTDB(path="Warning/Expectation"):
                    writeDataRTDB(path="Warning/Expectation", data=False, success_notification=True)

                # Update LCD
                if str(readDataRTDB(path="Lcd/nameExpectation")) != "None":
                    writeDataRTDB(path="Lcd/nameExpectation", data="None", success_notification=True)
                if str(readDataRTDB(path="Lcd/gestureExpectation")) != "None":
                    writeDataRTDB(path="Lcd/gestureExpectation", data="None", success_notification=True)
                if str(readDataRTDB(path="Lcd/stateExpectation")) != "None":
                    writeDataRTDB(path="Lcd/stateExpectation", data="None", success_notification=True) 

                # Auto Open Door
                if sensor["Ultrasonic"] <= user_config["CheckingDistance"]:
                    is_checking = True

                    if user_config["AutoOpen"]:
                        if not readDataRTDB(path="Door/Expectation"):
                            writeDataRTDB(path="Door/Expectation", data=True, success_notification=True)

                    # Update Door Open Time
                    last_open_door_time = time.time()
                
                elif is_checking and readDataRTDB(path="Door/Expectation"):
                    is_checking = False
                    last_open_door_time = time.time()
                
            # Auto Close Door
            if user_config["AutoClose"]:
                if sensor["Ultrasonic"] > user_config["CheckingDistance"]:
                    if readDataRTDB(path="Door/Expectation") and time.time() - last_open_door_time > user_config["DoorCloseTime"]:
                        is_checking = True

                        writeDataRTDB(path="Door/Expectation", data=False, success_notification=True)

        else:
            print("System is offline")

    em.closeConnection()


cameraUrl = readDataRTDB("CameraIP", success_notification=True) + "/cam-mid.jpg"
print(f"Camera IP is: {cameraUrl}")

# ----------------------------------------- ESP32 Cam Check ------------------------------------------
def checkCam(esp32, cameraUrl="", max_retries=5):
    while True:
        image = getCameraImage(esp32=esp32, cameraUrl=cameraUrl)

        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

        fps = HandTrackingModule.getFPS()
        cv2.putText(image, "FPS: " + str(int(fps)), (10, 20), cv2.FONT_HERSHEY_PLAIN, 1, (0, 255, 0), 1)

        cv2.imshow("ESP32 Camera", image)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
# -----------------------------------------------------------------------------------------------------

if __name__ == "__main__":
    # Main Function
    main()

    # Check webcam
    # checkCam(esp32=False)

    # Check ESP32 cam
    # checkCam(esp32=True, cameraUrl=cameraUrl)