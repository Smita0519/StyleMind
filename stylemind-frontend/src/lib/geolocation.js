// lib/geolocation.js
// One shared helper for requesting the browser's GPS location — used by
// both Recommendations.jsx and useChat.js, so there's a single consistent
// permission prompt and error message across the app instead of two
// separate implementations.
export function getCurrentLocation() {
  return new Promise((resolve, reject) => {
    if (!navigator.geolocation) {
      reject(new Error("Location isn't supported in this browser."));
      return;
    }
    navigator.geolocation.getCurrentPosition(
      // Success — the browser already showed its native permission prompt
      // before this fires, so by this point the user has explicitly allowed it
      (position) => {
        resolve({ lat: position.coords.latitude, lon: position.coords.longitude });
      },
      // Failure — err.code: 1 = user denied permission, 2 = position
      // unavailable, 3 = timed out. Give a friendly message either way.
      (err) => {
        if (err.code === 1) reject(new Error("Location permission denied. You can still enter a temperature manually."));
        else reject(new Error("Location permission denied. Enter your temperature manually to continue."));
      },
      { timeout: 10000 }
    );
  });
}