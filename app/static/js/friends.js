$(document).ready(function()
{
    // gets the csrfToken, this is so can use ajax post
    var csrf_token = $('#csrfToken').data('value');
    // need to setup ajax with csrfToken, otherwise wont work
    $.ajaxSetup({
        beforeSend: function(xhr, settings) {
            if (!/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type) && !this.crossDomain) {
                xhr.setRequestHeader("X-CSRFToken", csrf_token);
            }
        }
    });

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

    $(document).keypress(function(keyPressed){
        if(keyPressed.which === 13)
        { // If the enter key is pressed, click the search user button
            $('#userSearchButton').click();
        }
    })

    updateFriendsList();
    updateFriendRequestList()
});

// Function to update list of user's friends
function updateFriendsList() {
    $.ajax({
        type: "GET",
        url: "/getFriendsList",
        dataType: "json",
        success: function(friend_infos) {
            // Update the table with current friends
            var tableBody = $('#friendslistresults');
            tableBody.empty(); // Clear existing rows

            friend_infos.forEach(function(friend, index) { 
                tableBody.append(`
                <tr>
                    <td>${friend.first_name} ${friend.last_name}</td>
                    <td>${friend.email}</td>
                    <td><button data-friend-id="${friend.id}" class="binButton removeFriendButton">Remove</button></td>
                </tr>  
                `);
            });
        },
        error: function(request, error) {
            console.error("Error fetching friends: ", error);
        }
    });
}

$(document).on('click', '.removeFriendButton', function() {
    id = $(this).attr("data-friend-id");

    $.ajax({ 
        url: '/removeFriend', 
        type: 'POST', 
        contentType: 'application/json', 
        data: JSON.stringify({id}), 
    
    // refresh friends list
    success: function(response) {
        updateFriendsList()
        updateFriendRequestList()
        updateUserSearch()
    },
    error: function(error) { 
        console.log(error); 
    } 
    });
});

// Function to update use search results
function updateUserSearch() {
    searchTerm = $("#userSearch").val();

    $.ajax({
        url: "/userSearch",
        type: "POST",
        contentType: 'application/json', 
        data: JSON.stringify({searchTerm}),
        
        success: function(user_infos) {
            // Update the table with current friends
            var tableBody = $('#searchlistresults');
            tableBody.empty(); // Clear existing rows

            user_infos.forEach(function(user, index) { 
                if (user.frequest_id != -1) {
                    tableBody.append(`
                    <tr>
                        <td>${user.first_name} ${user.last_name}</td>
                        <td>${user.email}</td>
                        <td><button data-frequest-id="${user.frequest_id}" class="acceptRequestButton addButton">Add Friend</button></td>
                        </tr>  
                    `);
                } else if (user.pending) {
                    tableBody.append(`
                    <tr>
                        <td>${user.first_name} ${user.last_name}</td>
                        <td>${user.email}</td>
                        <td><button class="PendingButton">Pending</button></td>
                        </tr>  
                    `);
                } else {
                    tableBody.append(`
                    <tr>
                        <td>${user.first_name} ${user.last_name}</td>
                        <td>${user.email}</td>
                        <td><button data-user-id="${user.id}" class="addFriendButton addButton">Add Friend</button></td>
                    </tr>  
                    `);
                }
            });
        },
        error: function(error) { 
            console.log(error); 
        } 
    });
}

$(document).on('click', '#userSearchButton', function() {
    updateUserSearch();
});

$(document).on('click', '.addFriendButton', function() {
    id = $(this).attr("data-user-id");

    $.ajax({ 
        url: '/sendFriendRequest', 
        type: 'POST', 
        contentType: 'application/json', 
        data: JSON.stringify({id}), 
    
    // refresh search results
    success: function(response) {
        updateFriendsList()
        updateFriendRequestList()
        updateUserSearch()
    },
    error: function(error) { 
        console.log(error); 
    } 
    });
});

// Function to update list of incoming friend requests
function updateFriendRequestList() {
    $.ajax({
        type: "GET",
        url: "/getFriendRequestList",
        dataType: "json",
        success: function(frequest_infos) {
            // Update the table with incoming requests
            var tableBody = $('#friendrequestresults');
            tableBody.empty(); // Clear existing rows

            frequest_infos.forEach(function(frequest, index) { 
                tableBody.append(`
                <tr>
                    <td>${frequest.first_name} ${frequest.last_name}</td>
                    <td>${frequest.email}</td>
                    <td><button data-frequest-id="${frequest.id}" class="acceptRequestButton addButton">&check;</button></td>
                    <td><button data-frequest-id="${frequest.id}" class="declineRequestButton binButton">&cross;</button></td>
                </tr> 
                `);
            });
        },
        error: function(request, error) {
            console.error("Error fetching incoming friend requests: ", error);
        }
    });
}

$(document).on('click', '.acceptRequestButton', function() {
    id = $(this).attr("data-frequest-id");

    $.ajax({ 
        url: '/acceptFriendRequest', 
        type: 'POST', 
        contentType: 'application/json', 
        data: JSON.stringify({id}), 
    
    // refresh incoming requests list
    success: function(response) {
        updateFriendsList()
        updateFriendRequestList()
        updateUserSearch()
    },
    error: function(error) { 
        console.log(error); 
    } 
    });
});

$(document).on('click', '.declineRequestButton', function() {
    id = $(this).attr("data-frequest-id");

    $.ajax({ 
        url: '/declineFriendRequest', 
        type: 'POST', 
        contentType: 'application/json', 
        data: JSON.stringify({id}), 
    
    // refresh incoming requests list
    success: function(response) {
        updateFriendsList()
        updateFriendRequestList()
        updateUserSearch()
    },
    error: function(error) { 
        console.log(error); 
    } 
    });
});