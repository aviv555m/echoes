const socket = io();
let dwellTime = 1000; // 1 second
let dwellTimers = {};
let highlighted = null;

// Update phrase highlight based on gaze
socket.on("gaze_update", (data) => {
    const x = data.x;
    const y = data.y;
    document.querySelectorAll(".phrase").forEach(phrase => {
        const rect = phrase.getBoundingClientRect();
        const centerX = rect.left + rect.width/2;
        const centerY = rect.top + rect.height/2;
        const screenX = window.innerWidth * x;
        const screenY = window.innerHeight * y;
        if (Math.abs(centerX - screenX) < rect.width/2 && Math.abs(centerY - screenY) < rect.height/2) {
            if (highlighted !== phrase) {
                highlighted = phrase;
                if (dwellTimers[phrase.dataset.phrase]) clearTimeout(dwellTimers[phrase.dataset.phrase]);
                dwellTimers[phrase.dataset.phrase] = setTimeout(() => selectPhrase(phrase.dataset.phrase), dwellTime);
            }
            phrase.classList.add("highlight");
        } else {
            phrase.classList.remove("highlight");
        }
    });
});

function selectPhrase(phrase) {
    fetch("/select_phrase", {
        method: "POST",
        headers: {"Content-Type":"application/json"},
        body: JSON.stringify({phrase})
    })
    .then(res => res.json())
    .then(data => {
        const msgDiv = document.getElementById("message");
        if (data.blocked) {
            msgDiv.innerText = data.message;
        } else {
            msgDiv.innerText = "";
            const utter = new SpeechSynthesisUtterance(data.message);
            speechSynthesis.speak(utter);
        }
    });
}
