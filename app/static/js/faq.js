document.addEventListener("DOMContentLoaded", function() {
    var createFAQButton = document.getElementById("createFAQButton");
    var popupForm = document.getElementById("popupForm");
    var overlay = document.getElementById("overlay");
    var cancelButton = document.getElementById("cancelButton");

    createFAQButton.addEventListener("click", function() {
        popupForm.style.display = "block";
        overlay.style.display = "block";
    });

    cancelButton.addEventListener("click", function() {
        popupForm.style.display = "none";
        overlay.style.display = "none";
    });
});