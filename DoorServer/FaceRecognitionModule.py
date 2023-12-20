import cv2
import numpy as np
import face_recognition
import os

class FaceRecognitionModule():
    def __init__(self):
        self.encode_known_faces = []
        self.known_faces_name = []

    def addKnownFace(self, image, name):
        encode = face_recognition.face_encodings(image)[0]
        
        self.encode_known_faces.append(encode)
        self.known_faces_name.append(name)

    def removeKnownFace(self, index):
        del self.encode_known_faces[index]
        del self.known_faces_name[index]

    def checkFace(self, image, visualize=False):
        is_known = []
        users_name = []

        resize_image = cv2.resize(image, (0, 0), None, 0.25, 0.25)

        current_faces = face_recognition.face_locations(resize_image)
        encode_faces = face_recognition.face_encodings(resize_image, current_faces)

        for encode_face, face_locations in zip(encode_faces, current_faces):
            matches = face_recognition.compare_faces(self.encode_known_faces, encode_face)
            face_distance = face_recognition.face_distance(self.encode_known_faces, encode_face)

            match_index = np.argmin(face_distance)
            
            if matches[match_index]:
                is_known.append(True)
                users_name.append(self.known_faces_name[match_index])

                if visualize:
                    y1, x2, y2, x1 = face_locations
                    y1, x2, y2, x1 = y1 * 4, x2 * 4, y2 * 4, x1 * 4
                    cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.rectangle(image, (x1, y2 - 35), (x2, y2), (0, 255, 0), cv2.FILLED)
                    cv2.putText(image, name, (x1 + 6, y2 - 6), cv2.FONT_HERSHEY_COMPLEX, 1, (255, 255, 255), 2)

            else:
                is_known.append(False)
                users_name.append("")

        return is_known, users_name, image