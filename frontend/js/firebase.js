const firebaseConfig = {
    apiKey: "AIzaSyB_i2ahzM--66GXyJozHFEOxiHkRjb7e0g",
    authDomain: "cetsure-a383a.firebaseapp.com",
    projectId: "cetsure-a383a",
    storageBucket: "cetsure-a383a.firebasestorage.app",
    messagingSenderId: "454850423584",
    appId: "1:454850423584:web:e00f4081c23142a21d4545"
};

firebase.initializeApp(firebaseConfig);

const auth = firebase.auth();
const googleProvider = new firebase.auth.GoogleAuthProvider();