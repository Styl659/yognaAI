document.getElementById("chat-toggle").addEventListener("click", function() {
    let chatBox = document.getElementById("chat-container");
    chatBox.style.display = chatBox.style.display === "none" ? "flex" : "none";
});

function sendMessage() {
    let inputField = document.getElementById("user-input");
    let message = inputField.value.trim();
    if (message === "") return;

    appendMessage("You", message);
    inputField.value = "";

    appendMessage("Bot", "Typing...", true); // Loading indicator

    fetch("/chatbot_api", {  // Your Flask API route
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: message })
    })
    .then(response => response.json())
    .then(data => {
        removeLoading();
        appendMessage("Bot", data.reply);
    })
    .catch(error => {
        removeLoading();
        appendMessage("Bot", "Oops! Something went wrong.");
    });
}

function appendMessage(sender, message, isLoading = false) {
    let chatBody = document.getElementById("chat-body");
    let msgDiv = document.createElement("div");
    msgDiv.innerHTML = `<strong>${sender}:</strong> ${message}`;
    if (isLoading) msgDiv.classList.add("loading");
    msgDiv.setAttribute("data-loading", isLoading);
    chatBody.appendChild(msgDiv);
    chatBody.scrollTop = chatBody.scrollHeight;
}

function removeLoading() {
    let chatBody = document.getElementById("chat-body");
    let loadingMessages = chatBody.querySelectorAll("[data-loading='true']");
    loadingMessages.forEach(msg => msg.remove());
}