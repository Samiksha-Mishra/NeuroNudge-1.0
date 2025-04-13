import { initializeApp } from "https://www.gstatic.com/firebasejs/11.6.0/firebase-app.js";
import {
  getAuth,
  signInWithPopup,
  GoogleAuthProvider,
  onAuthStateChanged,
  signOut
} from "https://www.gstatic.com/firebasejs/11.6.0/firebase-auth.js";

import {
  getFirestore,
  doc,
  setDoc
} from "https://www.gstatic.com/firebasejs/11.6.0/firebase-firestore.js";

// ✅ Firebase config
const firebaseConfig = {
  apiKey: "AIzaSyB-9i7-N-y-qA4Qo7NS9QjMgqoeAAdI_Q4",
  authDomain: "dyslexia-prediction.firebaseapp.com",
  projectId: "dyslexia-prediction",
  storageBucket: "dyslexia-prediction.firebasestorage.app",
  messagingSenderId: "684928583311",
  appId: "1:684928583311:web:f3de8af733e1fb680792fa",
  measurementId: "G-QCWXESQJMS"
};

const app = initializeApp(firebaseConfig);
const auth = getAuth(app);
const db = getFirestore(app);
const provider = new GoogleAuthProvider();

// ✅ Google Sign-in and redirect
window.googleLogin = async () => {
  try {
    const result = await signInWithPopup(auth, provider);
    const user = result.user;

    // Hide Google button immediately
    const googleBtn = document.querySelector(".google-btn");
    if (googleBtn) googleBtn.style.display = 'none';

    await sendTokenToFlask(user);
    await saveUserProfile(user);

    // ✅ Hard redirect to home
    window.location.replace("/");
  } catch (error) {
    console.error("Google login error:", error);
  }
};

// ✅ Send Firebase token to Flask
const sendTokenToFlask = async (user) => {
  const token = await user.getIdToken();
  const res = await fetch("/auth", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ idToken: token })
  });
  const data = await res.json();
  if (data.status !== "success") {
    console.error("❌ Token auth failed with Flask");
  }
};

// ✅ Save user profile to Firestore
const saveUserProfile = async (user) => {
  const name = document.getElementById('name')?.value || user.displayName;
  const age = document.querySelector('input[type=\"number\"]')?.value || "";
  const gender = document.getElementById('gender')?.value || "";
  const challenge = document.getElementById('challenge')?.value || "";

  const userRef = doc(db, "users", user.uid);
  await setDoc(userRef, {
    uid: user.uid,
    email: user.email,
    name,
    age,
    gender,
    challenge
  });
  console.log("✅ User profile saved to Firestore");
};

// ✅ Logout
window.logout = () => {
  signOut(auth).then(() => {
    window.location.reload();
  });
};

// ✅ UI updates based on auth state
onAuthStateChanged(auth, (user) => {
  const userInfo = document.getElementById('user-info');
  const form = document.getElementById('signupform') || document.getElementById('loginForm');
  const welcomeMessage = document.getElementById('welcome-message');
  const googleBtn = document.querySelector(".google-btn");

  if (user) {
    if (userInfo) userInfo.style.display = 'block';
    if (form) form.style.display = 'none';
    if (googleBtn) googleBtn.style.display = 'none';
    if (welcomeMessage) welcomeMessage.innerText = `👋 Hello, ${user.displayName}`;
  } else {
    if (userInfo) userInfo.style.display = 'none';
    if (form) form.style.display = 'block';
    if (googleBtn) googleBtn.style.display = 'block';
  }
});
