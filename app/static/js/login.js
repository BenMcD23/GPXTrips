$(document).ready(function()
{
    // Hide all cards on document ready, so can be animated, hidden from user as we require
    $("#cardNumberOne").hide();
    $("#cardNumberTwo").hide();
    $("#cardNumberTwoREG").hide();

    
    $("#cardNumberOne").fadeIn(900, function()
    { // Animation for card display on page load/refresh
        $("#cardNumberTwo").fadeIn(900);
    })

    $("#linkTwo").click(function()
    { // Changes the content displayed in the right-hand card to the "payment plans" section
        $("#cBodyOne").hide();
        $("#cBodyTwo").hide();
        $("#cBodyThree").hide();
        $("#cBodyOne").text(" 52 Weeks = £70");
        $("#cBodyTwo").text(" 4 Week = £35");
        $("#cBodyThree").text(" 1 Week = £10");
        $("#cBodyOne").fadeIn(300);
        $("#cBodyTwo").fadeIn(300);
        $("#cBodyThree").fadeIn(300);
        $("#linkOne").removeClass("active");
        $("#linkTwo").addClass("active");
    })

    $("#linkOne").click(function()
    { // Changes the content displayed in the right hand card to the "about us" section
        $("#cBodyOne").hide();
        $("#cBodyTwo").hide();
        $("#cBodyThree").hide();
        $("#cBodyOne").text("Are you a runner? Walker? Hiker? Biker?");
        $("#cBodyTwo").text("Do you lack a record of your journeys or ever wonder how long your journey was?");
        $("#cBodyThree").text(`With myGPS, throw away your bulky maps and 
        say goodbye to ambiguity about your route data.
        By uploading your GPS data trails onto our 
        platform, we can provide valuable insights into 
        your journey and store them online for viewing 
        anywhere on earth with an internet connection.
        Does this sound of Interest to you? Then please 
        create an account using the link on the left. 
        Want information about our payment plans? Then 
        please click on the button at the top to view`)
        $("#cBodyOne").fadeIn(300);
        $("#cBodyTwo").fadeIn(300);
        $("#cBodyThree").fadeIn(300);
        $("#linkTwo").removeClass("active");
        $("#linkOne").addClass("active");
        
    })

    // Variable to log whether the T&C card on the registration page is currently shown
    // 0 = Hidden, 1 = Showing
    let shown = 0;
    $("#TandCLink").click(function(e)
    { // Shows/Hides the card upon user clicking the T&C link in the registration card
        // Need to make sure pressing this link will NOT also check the checkbox
        e.preventDefault();
        if(shown == 0)
        { // Card is currently hidden
            $("#cardNumberTwoREG").fadeIn(300);
            shown = 1;
        }
        else
        { // Card is currently shown
            $("#cardNumberTwoREG").fadeOut(300);
            shown = 0;
        }
        
    })

    
})