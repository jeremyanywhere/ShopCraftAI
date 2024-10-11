
function updateImage(greeting) {
  const images = {
    "Hello World": "hello_world.png",
    "Hello Mars": "hello_mars.png",
    "Hello Jupiter": "hello_jupiter.png",
    "Hello Venus": "hello_venus.png",
    "Hello Saturn": "hello_saturn.png"
  };
  const imgElement = document.getElementById("greetingImage");
  imgElement.src = images[greeting] || "";
  imgElement.alt = greeting;
}

function generateGreeting() {
    // Ensure the greetings correspond to keys in images
    const greetings = ["Hello World", "Hello Mars", "Hello Jupiter", "Hello Venus", "Hello Saturn"];
    const randomIndex = Math.floor(Math.random() * greetings.length);
    return greetings[randomIndex];
}

function showGreeting() {
    const greetingText = generateGreeting();
    document.getElementById("greeting").innerText = greetingText;
    updateImage(greetingText);
}
