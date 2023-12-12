const express = require('express');
const expressHbs = require('express-handlebars');
const bodyParser = require('body-parser');
const firebase = require('firebase/compat/app');
require('firebase/compat/auth');
require('firebase/compat/database');
require('firebase/compat/storage');

var AccessHistoryData = [];
var SensorData = {};
var DoorData = {};
var StrangerAlert = {}
var UserData = {}


const helpers = {
    checkTrue: require("./function/helpers")
};


const multer = require('multer');

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


// Body parser
app.use(bodyParser.json());
app.use(bodyParser.urlencoded({ extended: false }));

const usersAccessHistoryRef = database.ref('Data');
const userSensorRef = database.ref('Sensor');
const userDoorRef = database.ref('Door');
const userStrangerAlertRef = database.ref('StrangerAlert');
const userConfig = database.ref('UserConfig');

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
        convertFromMillis: helpers.checkTrue.convertFromMillis
    }
})
);

app.set("view engine", "hbs");


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

userDoorRef.once('value', async (snapshot) => {
    // Handle the snapshot of data
    DoorData = await snapshot.val();
    // Update your UI or perform any other actions with the retrieved data
    }, (error) => {
            // Handle the error
    console.log(error);
});

userStrangerAlertRef.once('value', async (snapshot) => {
    // Handle the snapshot of data
    StrangerAlert = await snapshot.val();
    // Update your UI or perform any other actions with the retrieved data
    }, (error) => {
            // Handle the error
    console.log(error);
});

app.get('/home', (req, res) => {
    userDoorRef.on('value', async (snapshot) => {
        // Handle the snapshot of data
        DoorData = await snapshot.val();
        // Update your UI or perform any other actions with the retrieved data
        }, (error) => {
                // Handle the error
        console.log(error);
    });
    userStrangerAlertRef.on('value', async (snapshot) => {
        // Handle the snapshot of data
        StrangerAlert = await snapshot.val();
        // Update your UI or perform any other actions with the retrieved data
        }, (error) => {
                // Handle the error
        console.log(error);
    });
    res.render('home', {doorData: DoorData, strangerAlert: StrangerAlert});
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

// app.get('/download/:fileName', async (req, res) => {
//     const { fileName } = req.params;

//     const storageRef = storage.ref();
//     const fileRef = storageRef.child(fileName);

//     try {
//         const downloadURL = await fileRef.getDownloadURL();
//         res.redirect(downloadURL);
//     } catch (error) {
//         res.status(404).send('File not found');
//     }
// });

userSensorRef.once('value', async (snapshot) => {
    // Handle the snapshot of data
    SensorData = await snapshot.val();
    // Update your UI or perform any other actions with the retrieved data
    }, (error) => {
            // Handle the error
    console.log(error);
});

app.get('/home/sensorStats', (req, res) => {
    userSensorRef.on('value', async (snapshot) => {
        // Handle the snapshot of data
        SensorData = await snapshot.val();
        // Update your UI or perform any other actions with the retrieved data
        }, (error) => {
                // Handle the error
        console.log(error);
    });
    res.render('sensorStats',{sensorData: SensorData, pageTitle: "Sensor Stats"});
});

usersAccessHistoryRef.once('value', async (snapshot) => {
    // Handle the snapshot of data
    AccessHistoryData = await snapshot.val();
    // Update your UI or perform any other actions with the retrieved data
    }, (error) => {
            // Handle the error
    console.log(error);
});

app.get('/home/accessHistory', (req, res) => {
    usersAccessHistoryRef.on('value', async (snapshot) => {
        // Handle the snapshot of data
        AccessHistoryData = await snapshot.val();
        // Update your UI or perform any other actions with the retrieved data
        }, (error) => {
                // Handle the error
        console.log(error);
    });
    res.render('accessHistory',{accessHistory: AccessHistoryData, pageTitle: "Access History"});
});

userConfig.once('value', async (snapshot) => {
    // Handle the snapshot of data
    UserData = await snapshot.val();
    // Update your UI or perform any other actions with the retrieved data
    }, (error) => {
    // Handle the error
    console.log(error);
});

app.get('/home/config', (req, res) => {
    userConfig.on('value', async (snapshot) => {
        // Handle the snapshot of data
        UserData = await snapshot.val();
        // Update your UI or perform any other actions with the retrieved data
        }, (error) => {
        // Handle the error
        console.log(error);
    });

    res.render('config',{userData: UserData, pageTitle: "Config"});
});


// Post
app.post('/login', (req, res) => {
    const { email, password } = req.body;

    auth.signInWithEmailAndPassword(email, password)
        .then(() => {
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
        .then(() => {
            // Successfully registered
            res.send('Registered successfully!');
        })
        .catch((error) => {
            // Handle registration error
            res.send(`Registration failed: ${error.message}`);
        });
});

// app.post('/upload', upload.single('file'), async (req, res) => {
//     const { file } = req;

//     if (!file) {
//         return res.status(400).send('No file uploaded');
//     }

//     const storageRef = storage.ref();
//     const fileRef = storageRef.child(file.originalname);
//     await fileRef.put(file.buffer);

//     res.send('File uploaded successfully!');
// });

app.post('/upload', upload.array('files'), async (req, res) => {
    const { files } = req;

    if (!files || files.length === 0) {
        return res.status(400).send('No files uploaded');
    }

    const storageRef = storage.ref("user_images/");

    // Use Promise.all to upload multiple files concurrently
    await Promise.all(files.map(async (file) => {
        const fileRef = storageRef.child(file.originalname);
        await fileRef.put(file.buffer);
    }));

    res.send('Files uploaded successfully!');
});

app.post('/home/warn', async (req, res) => {
    const { warn, time } = req.body;
    const warnData = {
        warn: warn
    }
    
    await database.ref('Buzzer').update(warnData);
    res.send('Warned successfully!');

    setTimeout(async () => {
        const warnData = {
            warn: false
        }
        await database.ref('Buzzer').update(warnData);
        
    }, time);
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
    const { status, time } = req.body;
    const DoorStatus = {
        status: status,
    }
    
    await database.ref('Door').update(DoorStatus);
    res.send('Change Door Status successfully!');

    if (status == false) {
        setTimeout(async () => {
            const DoorStatus = {
                status: true
            }
            await database.ref('Door').update(DoorStatus);
            
        }, time);
    }
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
        StrangerWarningTime: strangerWarningTime ? true : 0,
        VisitorTracking: visitorTracking ? true : false,
        WarningNotification: warningNotification ? true : false,
        SmartDoorSystem: smartDoorSystem ? true : false
    }
    try{
        await database.ref('UserConfig').update(configData);
        res.send('Warned successfully!');
    }catch(error){
        console.log(error);
        res.send('Error!');
    }
    
});


// Start the server
const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
    console.log(`Server is running on http://localhost:${PORT}`);
});
