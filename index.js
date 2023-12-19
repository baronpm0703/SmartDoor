const express = require('express');
const expressHbs = require('express-handlebars');
const session = require('express-session');
const cookieParser = require('cookie-parser');
const bodyParser = require('body-parser');
const firebase = require('firebase/compat/app');
require('firebase/compat/auth');
require('firebase/compat/database');
require('firebase/compat/storage');
require('firebase/compat/firestore');


var AccessHistoryData = [];
var SensorData = {};
var DoorData = {};
var Warning = {}
var UserData = {}
var AccountData = {};
var IP;
var cameraState;


const helpers = {
    checkTrue: require("./function/helpers")
};

// Alow send files
const multer = require('multer');

// Config FB
const firebaseConfig = {
    apiKey: "AIzaSyDjFMvE_kklNMo-laMwK6oKAW7HejrhCzk",
    authDomain: "node-69d5e.firebaseapp.com",
    databaseURL: "https://node-69d5e-default-rtdb.asia-southeast1.firebasedatabase.app",
    projectId: "node-69d5e",
    storageBucket: "node-69d5e.appspot.com",
    messagingSenderId: "48363159669",
    appId: "1:48363159669:web:0dd39524ed07436d4b783c"
};

firebase.initializeApp(firebaseConfig);
const auth = firebase.auth();
const storage = firebase.storage();
const database = firebase.database();
const app = express();
const http = require('http').Server(app);
const io = require('socket.io')(http);
const fdb = firebase.firestore();

// Use express-cookie middleware
app.use(express.urlencoded({ extended: false }));
app.use(cookieParser());

// Body parser
app.use(bodyParser.json());

const usersAccessHistoryRef = database.ref('VisitorsTracking');
const userSensorRef = database.ref('Sensor');
const userDoorRef = database.ref('Door');
const userWarningRef = database.ref('Warning');
const userConfig = database.ref('UserConfig');
const cameraIP = database.ref('CameraIP');
const webCamState = database.ref('WebCamera');

// Middleware
app.use(bodyParser.urlencoded({ extended: true }));

// Handlebars setup
app.use(express.static(__dirname + "/src"));
app.engine("hbs", expressHbs.engine({
    layoutsDir: __dirname + "/views/layouts",
    partialsDir: __dirname + "/views/partials",
    extname: "hbs",
    defaultLayout: "layout",
    helpers: {
        isTrue: helpers.checkTrue.isTrue,
        convertFromMillis: helpers.checkTrue.convertFromMillis,
        incValue: helpers.checkTrue.incValue,
        convertDistance: helpers.checkTrue.convertDistance
    }
})
);

app.set("view engine", "hbs");

// Function to notify all connected clients
function notifyClients() {
    io.emit('dataUpdated', { /* data you want to send to clients */ });
}


// Multer setup
const upload = multer();

// Routes
app.get('/', (req, res) => {
    res.redirect('/loginPage');
});

app.get('/loginPage', (req, res) => {
    res.render('login');
});

app.get('/registerPage', (req, res) => {
    res.render('register');
});

app.get('/home/logout', (req, res) => {
    res.clearCookie('email');
    res.redirect('/loginPage');
});

// Camera IP
cameraIP.on('value', async (snapshot) => {
    // Handle the snapshot of data
    IP = await snapshot.val();
    notifyClients();

});


// Camera State
webCamState.on('value', async (snapshot) => {
    // Handle the snapshot of data
    cameraState = await snapshot.val();
    notifyClients();

});
// Door State
userDoorRef.on('value', async (snapshot) => {
    // Handle the snapshot of data
    DoorData = await snapshot.val();
    notifyClients();

}, (error) => {
    // Handle the error
    console.log(error);
});

// Warning
userWarningRef.on('value', async (snapshot) => {
    Warning = await snapshot.val();
    notifyClients();

}, (error) => {
    // Handle the error
    console.log(error);
});

userSensorRef.on('value', async (snapshot) => {
    // Handle the snapshot of data
    SensorData = await snapshot.val();
    // Update your UI or perform any other actions with the retrieved data
    notifyClients();
}, (error) => {
    // Handle the error
    console.log(error);
});

app.get('/home', async (req, res) => {
    // Account
    const accountRef = fdb.collection("account");
    const accountSnapshot = await accountRef.get();
    let AccountData;

    accountSnapshot.forEach((doc) => {
        let data = doc.data();

        if (data.email == req.cookies.email) {
            AccountData = data;
        }
    });
    console.log(IP)
    res.render('home', {sensorData: SensorData, doorData: DoorData, cameraIP: IP, warning: Warning, account: AccountData, cameraState: cameraState.value });
});

app.get('/upload', (req, res) => {
    res.render('upload');
});


app.get('/home/faceID', async (req, res) => {

    const storageRef = storage.ref("user_images/");

    try {
        // List all files in the storageRef
        const files = await storageRef.listAll();

        // Get download URLs for each file
        const downloadURLs = await Promise.all(files.items.map(async (item) => {
            const url = await item.getDownloadURL();
            return { fileName: item.name, url };
        }));

        console.log(downloadURLs);
        res.render('download', { paths: downloadURLs });

    } catch (error) {
        console.error('Error fetching files:', error);
        res.send('Error');
    }
});

app.get('/home/personalInfo', async (req, res) => {
    try {
        const accountRef = fdb.collection("account");
        const accountSnapshot = await accountRef.get();
        let AccountData;

        accountSnapshot.forEach((doc) => {
            let data = doc.data();

            if (data.email == req.cookies.email) {
                AccountData = data;
            }
        });
        console.log("accountData: ", AccountData);
        res.render('personalInfo', { account: AccountData });
    } catch (error) {
        console.error('Error fetching files:', error);
        res.send('Error');
    }

    //res.render('personalInfo');
});




usersAccessHistoryRef.on('value', async (snapshot) => {
    // Handle the snapshot of data
    AccessHistoryData = await snapshot.val();
    AccessHistoryData = Object.values(AccessHistoryData).reverse();
    //AccessHistoryData.reverse();
    notifyClients();
    // Update your UI or perform any other actions with the retrieved data
}, (error) => {
    // Handle the error
    console.log(error);
});

app.get('/home/accessHistory', (req, res) => {
    res.render('accessHistory', { accessHistory: AccessHistoryData, pageTitle: "Access History" });
});



userConfig.on('value', async (snapshot) => {
    // Handle the snapshot of data
    UserData = await snapshot.val();
    notifyClients();
}, (error) => {
    // Handle the error
    console.log(error);
});
app.get('/home/config', (req, res) => {

    res.render('config', { userData: UserData, pageTitle: "Config Customization" });
});

// Post
app.post('/login', (req, res) => {
    const { email, password } = req.body;

    auth.signInWithEmailAndPassword(email, password)
        .then((userCredential) => {
            // Store user email in cookie
            res.cookie('email', email, { httpOnly: true });
            // Successfully registered
            const user = userCredential.user;
            const uid = user.uid;
            console.log("User UID:", uid);
            
            setCameraState();
            // Successfully logged in
            res.redirect('/home');
        })
        .catch((error) => {
            // Handle login error
            res.send(`Login failed: ${error.message}`);
        });
});

app.post('/register', (req, res) => {
    const { email, password } = req.body;

    auth.createUserWithEmailAndPassword(email, password)
        .then((userCredential) => {
            // Successfully registered
            const user = userCredential.user;
            const uid = user.uid;
            console.log("User UID:", uid);

            // Set up user data in firestore
            const collectionName = 'account';
            const customId = uid;
            const accountData = {
                UID: uid,
                email: email,
                url: "",
                username: email,
            };

            // Add a new document with a generated id.
            fdb.collection(collectionName).doc(customId).set(accountData)
                .then(() => {
                    console.log("Document successfully written!");
                })
                .catch((error) => {
                    console.error("Error writing document: ", error);
                });

            res.redirect('/loginPage');
        })
        .catch((error) => {
            // Handle registration error
            res.send(`Registration failed: ${error.message}`);
        });
});

app.post('/upload', upload.array('files', 5), async (req, res) => {
    const files = req.files || [];
    const { id } = req.body;

    console.log("uID: ", id);

    if (files.length === 0) {
        return res.status(400).send('No files uploaded');
    }

    const uploadTasks = files.map(async (file, index) => {
        const temp = file.originalname.split('.');
        const extFileName = temp[temp.length - 1];
        const fileRef = storage.ref(`user_images/${id}.${extFileName}`);
        await fileRef.put(file.buffer);
        const downloadURL = await fileRef.getDownloadURL();

        const collectionName = 'account';
        const docID = `${id}`;
        const accountData = {
            url: downloadURL,
        };

        // Use set with merge option to ensure the document is created or updated
        await fdb.collection(collectionName).doc(docID).set(accountData, { merge: true });
    });


    // Wait for all upload tasks to finish
    await Promise.all(uploadTasks);

    res.send('Files uploaded successfully!');
});

app.put('/home/personalInfo', async (req, res) => {
    const { username, uid } = req.body;

    console.log(uid, username);

    const collectionName = 'account';
    const docID = uid;
    const accountData = {
        username: username,
    };

    // Use set with merge option to ensure the document is created or updated
    await fdb.collection(collectionName).doc(docID).set(accountData, { merge: true });

    res.send('Updated successfully!');
});

app.post('/home/warn', async (req, res) => {
    const { warn } = req.body;
    const warnData = {
        Expectation: warn
    }
    await database.ref('Warning').update(warnData);
    res.send('Warned successfully!');
});

app.post('/home/webCam', async (req, res) => {
    const { cameraState } = req.body;
    const data = cameraState;
    await database.ref('WebCamera').update({value: data});
    res.send('Warned successfully!');
});

app.post('/home/method', async (req, res) => {
    const { isAuto } = req.body;
    const WorkMethodData = {
        isAuto: isAuto
    }

    await database.ref('WorkMethod').update(WorkMethodData);
    res.send('Change workMethod successfully!');
});

app.post('/home/door', async (req, res) => {
    const { Expectation } = req.body;
    const DoorStatus = {
        Expectation: Expectation,
    }

    await database.ref('Door').update(DoorStatus);
    res.send('Change Door Status successfully!');
});

app.post('/home/alert', async (req, res) => {
    const { time } = req.body;
    const StrangerAlert = {
        time: time,
    }

    await database.ref('StrangerAlert').update(StrangerAlert);
    res.send('Change Stranger Alert Time successfully!');

});

// Put
app.put('/home/config', async (req, res) => {
    const {
        autoClose,
        autoOpen,
        camera,
        checkingDistance,
        closingTime,
        faceRegconition,
        gestureControl,
        strangerDetect,
        strangerWarningTime,
        visitorTracking,
        smartDoorSystem,
        warningNotification
    } = req.body;
    const configData = {
        AutoClose: autoClose ? true : false,
        AutoOpen: autoOpen ? true : false,
        Camera: camera ? true : false,
        CheckingDistance: checkingDistance ? parseInt(checkingDistance) : 0,
        DoorCloseTime: closingTime ? parseInt(closingTime) : 0,
        FaceRegconition: faceRegconition ? true : false,
        GestureControl: gestureControl ? true : false,
        StrangerDetection: strangerDetect ? true : false,
        StrangerWarningTime: strangerWarningTime ? parseInt(strangerWarningTime) : 0,
        VisitorsTracking: visitorTracking ? true : false,
        WarningNotification: warningNotification ? true : false,
        SmartDoorSystem: smartDoorSystem ? true : false
    }
    try {
        await database.ref('UserConfig').update(configData);
        res.send('Warned successfully!');
    } catch (error) {
        console.log(error);
        res.send('Error!');
    }

});

// WebSocket connection
io.on('connection', (socket) => {
    console.log('DataBase Updated');

    // Disconnect event
    socket.on('disconnect', () => {
        console.log('User disconnected');
    });
});

// Initial Camera State
async function setCameraState() {
    const data = false;
    await database.ref('WebCamera').update({value: data});
}

// Start the server
const PORT = process.env.PORT || 3000;
http.listen(PORT, () => {
    console.log(`Server is running on http://localhost:${PORT}`);
});

