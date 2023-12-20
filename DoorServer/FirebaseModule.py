import pyrebase
import firebase_admin
from firebase_admin import credentials, auth, storage
from firebase_admin import firestore
import os
import re
from datetime import datetime

class FirebaseModule():
    def __init__(self, config):
        self.firebase = pyrebase.initialize_app(config)
        self.storage = self.firebase.storage()
        self.db = self.firebase.database()

        cred = credentials.Certificate(config["serviceAccount"])
        firebase_admin.initialize_app(cred, {
            "storageBucket": config["storageBucket"]
        })

        self.firestore = firestore.client()

    def updateLocalStorage(self, remote_path, local_path, delete_local_files=False):
        remote_files = list(self.storage.child(remote_path).list_files())

        for file in remote_files:
            filename = os.path.basename(file.name)

            if filename.strip() == "":
                continue

            local_file_path = os.path.join(local_path, filename)

            if os.path.exists(local_file_path):
                remote_metadata = file.updated.timestamp()
                local_metadata = os.path.getmtime(local_file_path)

                if remote_metadata != local_metadata:
                    print(f"Updating: {filename}")
                    file.download_to_filename(local_file_path)
                    os.utime(local_file_path, (remote_metadata, remote_metadata))
                    print(f"Updated: {filename}")
            else:
                print(f"Downloading: {filename}")
                file.download_to_filename(local_file_path)
                remote_metadata = file.updated.timestamp()
                os.utime(local_file_path, (remote_metadata, remote_metadata))
                print(f"Downloaded: {filename}")

        if delete_local_files:
            remote_files = {os.path.basename(file.name) for file in remote_files}
            local_files = set(os.listdir(local_path))

            different_files = local_files - remote_files

            for filename in different_files:
                local_file = os.path.join(local_path, filename)
                if os.path.exists(local_file):
                    print(f"Removing: {filename}")
                    os.remove(local_file)
                    print(f"Removed: {filename}")

    def getDataRTDB(self, path):
        nodes = re.split(r"[\\/]", path)
        node = None

        for child_node in nodes:
            if node is None:
                node = self.db.child(child_node)
            else:
                node = node.child(child_node)

        return node.get().val()

    def setDataRTDB(self, path, data):
        nodes = re.split(r"[\\/]", path)
        node = None

        for child_node in nodes:
            if node is None:
                node = self.db.child(child_node)
            else:
                node = node.child(child_node)

        node.set(data)

    def pushDataRTDB(self, path, data):
        nodes = re.split(r"[\\/]", path)
        node = None

        for child_node in nodes:
            if node is None:
                node = self.db.child(child_node)
            else:
                node = node.child(child_node)

        node.push(data)

    def getUsersEmail(self):
        users = auth.list_users()

        return [user.email for user in users.iterate_all() if isinstance(getattr(user, 'email', None), str)]

    def deleteAnonymousUsers(self, history_file=None):
        if history_file is not None:
            file = open(history_file, "a")

        users = auth.list_users()

        for user in users.iterate_all():
            if len(user.provider_data) <= 0:
                current_time = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
                notification = f"Delete user uid: {user.uid} at {current_time}"

                if history_file is not None:
                    file.write(notification + "\n")

                print(notification)

                auth.delete_user(user.uid)

        if history_file is not None:
            file.close()

    def getUserInfo(self, uid):
        doc_ref = self.firestore.collection('account').document(uid)

        doc = doc_ref.get()

        return doc.to_dict()