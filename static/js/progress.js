function saveProgress(activity) {
  fetch('/save_progress', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ activity: activity })
  })
  .then(res => res.json())
  .then(data => {
    if (data.status === "success") {
      alert("✅ Progress saved for: " + activity.replace('_', ' '));
    } else {
      alert("⚠️ Error saving progress: " + (data.message || "Unknown error"));
    }
  })
  .catch(err => {
    console.error(err);
    alert("❌ Could not connect to server.");
  });
}
