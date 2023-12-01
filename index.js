const express = require('express');
const expressHbs = require('express-handlebars');
const bodyParser = require('body-parser');
const firebase = require('firebase/compat/app');
require('firebase/compat/auth');
require('firebase/compat/database');
require('firebase/compat/storage');

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
const app = express();

// Middleware
app.use(bodyParser.urlencoded({ extended: true }));

// Handlebars setup
app.engine("hbs", expressHbs.engine({
    layoutsDir: __dirname + "/views/layouts",
    partialsDir: __dirname + "/views/partials",
    extname: "hbs",
    defaultLayout: "layout",
})
);

app.set("view engine", "hbs");

// Routes
app.get('/', (req, res) => {
    res.render('login', { storage: storage });
});

app.post('/login', (req, res) => {
    const { email, password } = req.body;

    auth.signInWithEmailAndPassword(email, password)
        .then(() => {
            // Successfully logged in
            res.send('Logged in successfully!');
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

// Multer setup
const upload = multer();

// Routes
app.get('/', (req, res) => {
    res.render('login');
});

app.get('/upload', (req, res) => {
    res.render('upload');
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

// Start the server
const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
    console.log(`Server is running on http://localhost:${PORT}`);
});
