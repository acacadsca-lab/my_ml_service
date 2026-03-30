// ================= DOM ELEMENTS =================
const chatBody = document.querySelector(".chat-body");
const messageInput = document.querySelector(".message-input");
const sendMessageButton = document.querySelector("#send-message");
const fileInput = document.querySelector("#file-input");
const chatbotToggler = document.querySelector("#chatbot-toggler");
const closeChatbot = document.querySelector("#close-chatbot");

// ================= API CONFIG =================
const API_URL = window.location.href;
console.log(API_URL);

// ================= STATE =================
const chatHistory = [];

const userData = {
  message: null,
  file: {
    data: null,
    mime_type: null,
  },
};

// ================= CREATE MESSAGE =================
const createMessageElement = (content, ...classes) => {
  const div = document.createElement("div");
  div.classList.add("message", ...classes);
  div.innerHTML = content;
  return div;
};

// ================= SEND MESSAGE =================
const handleOutgoingMessage = async (e) => {
  e.preventDefault();

  const message = messageInput.value.trim();
  if (!message && !userData.file.data) return;

  userData.message = message;

  // Clear input
  messageInput.value = "";
  messageInput.style.height = "auto";

  // ===== USER MESSAGE =====
  const userHTML = `
    <div class="message-text">${message}</div>
    ${
      userData.file.data
        ? `<img src="data:${userData.file.mime_type};base64,${userData.file.data}" class="attachment"/>`
        : ""
    }
  `;

  const userMsgDiv = createMessageElement(userHTML, "user-message");
  chatBody.appendChild(userMsgDiv);

  // ===== BOT TYPING =====
  const botMsgDiv = createMessageElement(
    `<div class="message-text typing">Typing...</div>`,
    "bot-message"
  );
  chatBody.appendChild(botMsgDiv);

  chatBody.scrollTop = chatBody.scrollHeight;

  await generateBotResponse(botMsgDiv);

  // Reset file after sending
  userData.file = { data: null, mime_type: null };
};

// ================= API CALL =================
const generateBotResponse = async (botMsgDiv) => {
  const messageElement = botMsgDiv.querySelector(".message-text");

  // Add user message to history
  chatHistory.push({
    role: "user",
    parts: [
      { text: userData.message || "" },
      ...(userData.file.data ? [{ inline_data: userData.file }] : []),
    ],
  });

try {
  const response = await fetch(API_URL, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      contents: chatHistory,
    }),
  });

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.error || "API Error");
  }

  // ✅ FIXED HERE
 const reply = data.reply || "No response from server";

// FORMAT FIRST
const formattedReply = formatResponse(reply);

// TYPEWRITER
let i = 0;
messageElement.innerHTML = "";

const typing = setInterval(() => {
  messageElement.innerHTML += formattedReply[i]; // ✅ append instead of replace
  i++;

  if (i >= formattedReply.length) {
    clearInterval(typing);
  }
}, 15);

// Save bot response
chatHistory.push({
  role: "model",
  parts: [{ text: reply }],
});

} catch (error) {
  messageElement.textContent = "Error: " + error.message;
  messageElement.style.color = "red";
}

  chatBody.scrollTop = chatBody.scrollHeight;
};

// ================= ENTER KEY =================
messageInput.addEventListener("keydown", (e) => {
  if (
    e.key === "Enter" &&
    !e.shiftKey &&
    messageInput.value.trim() &&
    window.innerWidth > 768
  ) {
    handleOutgoingMessage(e);
  }
});

// ================= AUTO RESIZE =================
messageInput.addEventListener("input", () => {
  messageInput.style.height = "auto";
  messageInput.style.height = messageInput.scrollHeight + "px";
});

// ================= FILE UPLOAD =================
fileInput.addEventListener("change", () => {
  const file = fileInput.files[0];
  if (!file) return;

  const reader = new FileReader();

  reader.onload = (e) => {
    const base64 = e.target.result.split(",")[1];

    userData.file = {
      data: base64,
      mime_type: file.type,
    };
  };

  reader.readAsDataURL(file);
});

// ================= BUTTON EVENTS =================
sendMessageButton.addEventListener("click", handleOutgoingMessage);

document
  .querySelector("#file-upload")
  .addEventListener("click", () => fileInput.click());

chatbotToggler.addEventListener("click", () => {
  document.body.classList.toggle("show-chatbot");
});

closeChatbot.addEventListener("click", () => {
  document.body.classList.remove("show-chatbot");
});

function formatResponse(text) {
  return text
    .replace(/\*\*(.*?)\*\*/g, "<b>$1</b>")
    .replace(/\n/g, "<br>")
    .replace(/^\d+\.\s/gm, "<br><b>$&</b>")
    .replace(/^- (.*)/gm, "• $1");
}