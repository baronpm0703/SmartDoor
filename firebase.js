const admin = require('firebase-admin');

// Replace 'path/to/your/serviceAccountKey.json' with the path to your downloaded JSON file.
const serviceAccount = require('./src/serviceAccount/node-69d5e-firebase-adminsdk-bhf63-b190f3d480.json' );

admin.initializeApp({
    credential: admin.credential.cert(serviceAccount),
  databaseURL: 'https://node-69d5e-default-rtdb.asia-southeast1.firebasedatabase.app/', // Replace with your Firebase project URL
});

module.exports = admin;
app.engine("hbs", expressHbs.engine({
  layoutsDir: __dirname + "/views/layouts",
  partialsDir: __dirname + "/views/partials",
  extname: "hbs",
  defaultLayout: "layout",
})
);

app.set("view engine", "hbs");