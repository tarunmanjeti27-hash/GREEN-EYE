/**
 * GREEN-EYE — Firebase & Cloud Firestore Configuration
 * Project ID: green-eye-afc2f
 */

import { initializeApp } from "https://www.gstatic.com/firebasejs/10.12.0/firebase-app.js";
import { 
  getFirestore, 
  collection, 
  addDoc, 
  getDocs, 
  query, 
  orderBy, 
  limit, 
  serverTimestamp 
} from "https://www.gstatic.com/firebasejs/10.12.0/firebase-firestore.js";
import { 
  getAuth, 
  signInWithEmailAndPassword, 
  createUserWithEmailAndPassword, 
  signInWithPopup, 
  GoogleAuthProvider, 
  onAuthStateChanged, 
  signOut 
} from "https://www.gstatic.com/firebasejs/10.12.0/firebase-auth.js";
import { getAnalytics, isSupported as isAnalyticsSupported } from "https://www.gstatic.com/firebasejs/10.12.0/firebase-analytics.js";

// User's exact Firebase configuration
export const firebaseConfig = {
  apiKey: "AIzaSyCEwhroD1tTPbizj_rzKGtvD79PQXZgeZQ",
  authDomain: "green-eye-afc2f.firebaseapp.com",
  projectId: "green-eye-afc2f",
  storageBucket: "green-eye-afc2f.firebasestorage.app",
  messagingSenderId: "867649280490",
  appId: "1:867649280490:web:d26f8ae76800df3ceb7a93",
  measurementId: "G-DE9TP5TDBE"
};

// Initialize Firebase App
export const app = initializeApp(firebaseConfig);

// Initialize Cloud Firestore
export const db = getFirestore(app);

// Initialize Authentication
export const auth = getAuth(app);

// Optional Analytics initialization with safety check
export let analytics = null;
isAnalyticsSupported().then(supported => {
  if (supported) {
    analytics = getAnalytics(app);
  }
}).catch(() => {
  // Silent fallback for non-analytics environments
});

const googleProvider = new GoogleAuthProvider();

/**
 * Save a new diagnostic pathology scan to Cloud Firestore
 * Collection: 'diagnostic_scans'
 */
export async function saveDiagnosticScanToFirestore(scanData) {
  try {
    const docData = {
      ...scanData,
      createdAt: serverTimestamp(),
      isoDate: new Date().toISOString()
    };
    const colRef = collection(db, "diagnostic_scans");
    const docRef = await addDoc(colRef, docData);
    console.log("GREEN-EYE: Saved diagnosis to Cloud Firestore ID:", docRef.id);
    return { success: true, id: docRef.id };
  } catch (error) {
    console.warn("GREEN-EYE Firestore sync notice:", error.message);
    return { success: false, error: error.message };
  }
}

/**
 * Fetch recent diagnostic scans from Cloud Firestore
 */
export async function fetchRecentScansFromFirestore(maxCount = 8) {
  try {
    const colRef = collection(db, "diagnostic_scans");
    const q = query(colRef, orderBy("createdAt", "desc"), limit(maxCount));
    const snapshot = await getDocs(q);
    const scans = [];
    snapshot.forEach(doc => {
      scans.push({ id: doc.id, ...doc.data() });
    });
    return scans;
  } catch (error) {
    // If composite index is building or permission restricts order, fallback to simple collection read
    try {
      const colRef = collection(db, "diagnostic_scans");
      const snapshot = await getDocs(colRef);
      const scans = [];
      snapshot.forEach(doc => {
        scans.push({ id: doc.id, ...doc.data() });
      });
      return scans.slice(-maxCount).reverse();
    } catch (fallbackErr) {
      console.warn("GREEN-EYE Firestore read notice:", fallbackErr.message);
      return [];
    }
  }
}

/**
 * Save field treatment / dosage plan to Cloud Firestore
 * Collection: 'dosage_plans'
 */
export async function saveDosagePlanToFirestore(planData) {
  try {
    const colRef = collection(db, "dosage_plans");
    const docRef = await addDoc(colRef, {
      ...planData,
      createdAt: serverTimestamp(),
      isoDate: new Date().toISOString()
    });
    return { success: true, id: docRef.id };
  } catch (error) {
    console.warn("GREEN-EYE Dosage plan save notice:", error.message);
    return { success: false, error: error.message };
  }
}

/**
 * Authenticate with Firebase Email & Password
 * Automatically attempts sign-in, and if user doesn't exist, signs them up seamlessly!
 */
export async function authenticateFirebaseEmail(email, password) {
  try {
    const userCredential = await signInWithEmailAndPassword(auth, email, password);
    return { success: true, user: userCredential.user };
  } catch (signInErr) {
    // If user-not-found, try creating the account
    if (signInErr.code === "auth/user-not-found" || signInErr.code === "auth/invalid-credential") {
      try {
        const newUserCredential = await createUserWithEmailAndPassword(auth, email, password);
        return { success: true, user: newUserCredential.user, isNewUser: true };
      } catch (signUpErr) {
        return { success: false, error: signUpErr };
      }
    }
    return { success: false, error: signInErr };
  }
}

/**
 * Authenticate with Google Provider Popup
 */
export async function authenticateWithGoogle() {
  try {
    const result = await signInWithPopup(auth, googleProvider);
    return { success: true, user: result.user };
  } catch (error) {
    console.warn("GREEN-EYE Google Auth popup notice:", error.message);
    return { success: false, error };
  }
}

/**
 * Sign out from Firebase
 */
export async function signOutFirebase() {
  try {
    await signOut(auth);
    return { success: true };
  } catch (error) {
    return { success: false, error };
  }
}

/**
 * Subscribe to Firebase Auth state updates
 */
export function onAuthChange(callback) {
  return onAuthStateChanged(auth, callback);
}
