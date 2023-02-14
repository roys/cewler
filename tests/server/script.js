function scriptJsTesting() {
    document.querySelector("body").innerHTML += "Paragraph changed.";
    const testLogicalAnd = true&&true; // Don't format
}
document.addEventListener('DOMContentLoaded', function () {
    scriptJsTesting()
}, false);
