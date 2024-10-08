// for manange users page

// on load
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
})

// gets all the checkbox's for user account toggle
let checkboxesUser = $("input[type=checkbox][name=userState]")

// listens for when any of them get checked/unchecked
checkboxesUser.change(function() {
    changeUserState(this.id);
});

// gets all the checkbox's for manager toggle
let checkboxesManger = $("input[type=checkbox][name=userManger]")

// listens for when any of them get checked/unchecked
checkboxesManger.change(function() {
    changeMangement(this.id);
});

// changes user account state to either activated or deactivated
function changeUserState(id){
    const checkbox_state = document.getElementById(id);
    // get rid of all the stuff before the id
    id = id.split('_')[1];
    var state;
    // if gets checked
    if (checkbox_state.checked) {
        state = true;
    }

    // if it gets unchecked
    else {
        state = false
    }

    // then post the state with the id, so can be changed in database
    $.ajax({ 
        url: '/accountState', 
        type: 'POST', 
        contentType: 'application/json', 
        data: JSON.stringify({id, state}), 
    
    // if success, dont do anything
    success: function(response) {
        
    },
    // if error, console error
    error: function(error) { 
        console.log(error); 
    } 
    });
}

// changes user account state to either activated or deactivated
function changeMangement(id){
    const checkbox_state = document.getElementById(id);
    // get rid of all the stuff before the id
    id = id.split('_')[1];

    var state;
    // if gets checked
    if (checkbox_state.checked) {
        state = true;
    }

    // if it gets unchecked
    else {
        state = false
    }

    // then post the state with the id, so can be changed in database
    $.ajax({ 
        url: '/accountManager', 
        type: 'POST', 
        contentType: 'application/json', 
        data: JSON.stringify({id, state}), 
    
    // if success, dont do anything
    success: function(response) {
        
    },
    // if error, console error
    error: function(error) { 
        console.log(error); 
    } 
    });
}
