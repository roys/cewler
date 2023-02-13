function scriptJsTesting() {
    document.querySelector("body").innerHTML += "Paragraph changed.";
}
document.addEventListener('DOMContentLoaded', function () {
    scriptJsTesting()
}, false);
