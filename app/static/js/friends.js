$(document).ready(function()
{
    $('#searchFriends').hide()
    $('#incomingRequests').hide()
    $('#currentFriends').show()

    $('#linkOne').click(function(){
        $('#linkTwo').removeClass('active');
        $('#linkThree').removeClass('active');
        $('#linkOne').addClass('active');
        $('#searchFriends').hide()
        $('#incomingRequests').hide()
        $('#currentFriends').fadeIn(450);
    })
    $('#linkTwo').click(function(){
        $('#linkOne').removeClass('active');
        $('#linkThree').removeClass('active');
        $('#linkTwo').addClass('active');
        $('#searchFriends').hide()
        $('#currentFriends').hide()
        $('#incomingRequests').fadeIn(450);
    })
    $('#linkThree').click(function(){
        $('#linkOne').removeClass('active');
        $('#linkTwo').removeClass('active');
        $('#linkThree').addClass('active');
        $('#incomingRequests').hide()
        $('#currentFriends').hide()
        $('#searchFriends').fadeIn(450);
    })
})