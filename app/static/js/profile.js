$(document).ready(function()
{ // Code used in the profile view
    // Hide the renew card to begin with -> don't need it until user clicks on renew
    $('#renewCard').hide()

    $("#renewButton").click(function()
    { // When user clicks the renew button, hide the profile card, show subscription renewal card
        $('#profileCard').hide()
        $('#renewCard').show()
    })

    $("#backLink").click(function()
    { // Facillitates the ability for the user to return to their profile card from the renewal card
        $('#renewCard').hide()
        $('#profileCard').show()
    })

      // Also enable the logout button so user can logout if they don't wish to subscribe
      
    let logoutButton = document.getElementById("logoutLink")
    logoutButton.style.pointerEvents = 'auto';
    let profileButton = document.getElementById("profileLink")
    profileButton.style.pointerEvents = 'auto';
    let homeButton = document.getElementById("homeLink")
    homeButton.style.pointerEvents = 'auto';
})
