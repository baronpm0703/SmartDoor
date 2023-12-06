const express = require('express');
const expressHbs = require('express-handlebars');
const bodyParser = require('body-parser');
const firebase = require('firebase/compat/app');
require('firebase/compat/auth');
require('firebase/compat/database');
require('firebase/compat/storage');

let {Sensor} = require("./src/data");
let SensorData = "";
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

const usersRef = database.ref('Data');

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
        isTrue: helpers.checkTrue.isTrue
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

app.get('/home', (req, res) => {
    res.render('home');
});

app.get('/upload', (req, res) => {
    res.render('upload');
});


app.get('/download', async (req, res) => {
    const storageRef = storage.ref();
    const files = await storageRef.listAll();

    res.render('download', { files: files.items.map(item => item.name) });
});

app.get('/download/:fileName', async (req, res) => {
    const { fileName } = req.params;

    const storageRef = storage.ref();
    const fileRef = storageRef.child(fileName);

    try {
        const downloadURL = await fileRef.getDownloadURL();
        res.redirect(downloadURL);
    } catch (error) {
        res.status(404).send('File not found');
    }
});

usersRef.once('value', async (snapshot) => {
    // Handle the snapshot of data
    data = await snapshot.val();

    // Update your UI or perform any other actions with the retrieved data
    }, (error) => {
            // Handle the error
    console.log(error);
});

app.get('/home/sensorStats', (req, res) => {

    res.render('sensorStats',{sensorData: data, pageTitle: "Sensor Stats"});
    
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

app.post('/upload', upload.single('file'), async (req, res) => {
    const { file } = req;

    if (!file) {
        return res.status(400).send('No file uploaded');
    }

    const storageRef = storage.ref();
    const fileRef = storageRef.child(file.originalname);
    await fileRef.put(file.buffer);

    res.send('File uploaded successfully!');
});

// Start the server
const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
    console.log(`Server is running on http://localhost:${PORT}`);
});
