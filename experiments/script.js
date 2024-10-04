function generateGreeting() {
    const greetings = ["Hello World", "Hello Mars", "Hello Jupiter", "Hello Venus"]; // Added "Hello Venus"
    const randomIndex = Math.floor(Math.random() * greetings.length);
    document.getElementById("greeting").innerText = greetings[randomIndex];
}