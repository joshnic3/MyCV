var server_url = 'http://192.168.8.100:5000';
var loginUrl = server_url + "/auth/login";
var changePasswordUrl = server_url + "/auth/changepassword";
var addUrl = server_url + "/users/add";
var deleteUrl = server_url + "/users/delete";
var edit_url = server_url + "/users/edit";
var signUpURL = server_url + "/users/signup";
var shareModalUrl = server_url + "/html/modal/share";
var loginModalUrl = server_url + "/html/modal/login";
var signUpModalUrl = server_url + "/html/modal/signup";
var editModalUrl = server_url + "/html/modal/edit";
var addModalUrl = server_url + "/html/modal/add";
var deleteModalUrl = server_url + "/html/modal/delete";
var manageModalUrl = server_url + "/html/modal/manage";

function signUpSubmit() {
    console.log('Sign Up Submitted.');
    data = {
        'email': document.getElementById("signUpEmail").value,
        'password': document.getElementById("signUpPassword").value,
        'password_check': document.getElementById("signUpVerifyPassword").value,
        'display_name': document.getElementById("signUpDisplayName").value,
        'headline': document.getElementById("signUpHeadline").value,
    }
    console.log(data);
    if(data['password'] == data['password_check']) {
        requestPost(signUpURL, data, responseCompleted);
    } else {
        responseCompleted({'error': 'Passwords don\'t match!'})
    }
}

function loginSubmit() {
    data = {
        'email': document.getElementById("loginEmail").value,
        'password': document.getElementById("loginPassword").value
    }
    requestPost(loginUrl, data, handleLoginResponse);
}

function logoutSubmit() {
    // Should set time out to now.
    write_cookie('session_key', null);
    write_cookie('user_id', null);
    loggedOut(true);
}

function handleLoginResponse(data) {
    if ('error' in data) {
        responseCompleted(data)
    } else {
        write_cookie('session_key', data['session_key']);
        write_cookie('user_id', data['user_id']);

        // loggedIn called on page load. This will show edit buttons that are now rendered.
        responseCompleted({'refresh': null})
    }
}

function loggedIn(data) {
    toggle_visiblity("loggedInContainer", true);
    toggle_visiblity("loggedOutContainer", false);
    
    // Set account dropdown values.
    userLink = document.getElementById("userLinkContainer");
    userLink.innerHTML = data['display_name'];
    userLink.setAttribute("href", '/?id=' + data['id']); 
}

function loggedOut(refresh) {
    if (refresh) {
        responseCompleted({'refresh': null})
    } else {
        toggle_visiblity("loggedOutContainer", true);
        toggle_visiblity("loggedInContainer", false);  
    }
}

// ---------------------------------------------------------------------------

// COKKIES!!! ----------------------------------------------------------------

function write_cookie(name, value) {
    document.cookie = name + '=' + value + ';SameSite=Strict';
}

function read_cookie(name) {
    cookiearray = document.cookie.split(';');
    for(var i=0; i<cookiearray.length; i++) {
        if (cookiearray[i].split('=')[0].replace(/\s/g, '') == name) {
            value = cookiearray[i].split('=')[1];
            if (value != 'null') {
                return value;
            } else {
                return null;
            }
        }
    }
    return null;
}

// REQUESTS ------------------------------------------------------------------

function requestPost(url, data_dict, callback) {
    var xmlHttp = new XMLHttpRequest();
    xmlHttp.open("POST", url, true);
    xmlHttp.setRequestHeader('Content-Type', 'application/json');
    xmlHttp.withCredentials = true;
    xmlHttp.send(JSON.stringify(data_dict));
    xmlHttp.onreadystatechange = function() {
        if (xmlHttp.readyState != 4)  {return;}
        if (xmlHttp.status == 200) {
            response = JSON.parse(xmlHttp.responseText);
        } else {
            response = null;
        }
        return callback(response);
    };
}

function request(url, callback) {
    {
        var xmlHttp = new XMLHttpRequest();
        xmlHttp.open("GET", url, true);
        xmlHttp.withCredentials = true;
        // xmlHttp.setRequestHeader('Access-Control-Allow-Origin', server_url);
        xmlHttp.send();
        xmlHttp.onreadystatechange = function() {
            if (xmlHttp.readyState != 4)  {return;}
            if (xmlHttp.status == 200) {
                response = JSON.parse(xmlHttp.responseText);
            } else {
                response = null;
            }
            return callback(response);
        };
    }
}

function getUrlVars() {
    var vars = {};
    var parts = window.location.href.replace(/[?&]+([^=&]+)=([^&]*)/gi, function(m,key,value) {
        vars[key] = value;
    });
    return vars;
}

// ---------------------------------------------------------------------------

// RENDER ---------------------------------------------------------------------

function displayUser(userDict) {
    console.log(userDict);
    // Show user div is user exisits, else show not found div.
    if (userDict == null) {
        toggle_visiblity("userNotFoundContainer", true);
        toggle_visiblity("userContainer", false);
    } else {
        toggle_visiblity("userContainer", true);
        toggle_visiblity("userNotFoundContainer", false);

        // Is the user viewing their own account?
        if (userDict['id'] == read_cookie('user_id')) {
            viewingSelf = true;
        } else {
            viewingSelf = false;
        }
        
        // Render default user details.
        document.getElementById('displayName').innerHTML = userDict['details']['header_1'];
        document.getElementById('title').innerHTML = userDict['details']['header_2'];
        if (viewingSelf) {
            editDetailsDiv = document.getElementById('editDetailsInjectionPoint');
            editDetailsDiv.innerHTML += '<div class="col col-sm-1 text-right"><button onclick="requestEditModal(\'details\', \''+ userDict['details']['id'] +'\')" data-toggle="modal" data-target="#editModal" type="button" class="btn btn-sm btn-link">Edit</button></div>';
        }

        // Render about.        
        var aboutDiv = document.getElementById('aboutContainer')
        if (userDict['about'] == null) {
            if (!viewingSelf) {
                aboutDiv.style.display = 'none';    
            } else {
                aboutDiv.style.display = 'block';
                addAboutDiv = document.getElementById('aboutEditInjectionPoint');
                addAboutDiv.innerHTML += '<div class="col col-sm-1 text-right"><button onclick="requestAddModal(\'about\', \''+ userDict['about'] +'\')" type="button" class="btn btn-sm btn-link">Add</button></div>';
            }
        } else {
            aboutDiv.style.display = 'block';
            aboutDiv.innerHTML += '<p>' + userDict['about']['text'] + '</p>';
            if (viewingSelf) {
                editAboutDiv = document.getElementById('aboutEditInjectionPoint');
                editAboutDiv.innerHTML += '<div class="col col-sm-1 text-right"><button onclick="requestEditModal(\'about\', \''+ userDict['about']['id'] +'\')" data-toggle="modal" data-target="#editModal" type="button" class="btn btn-sm btn-link">Edit</button></div>';
            }
        }
        

        // Render experiences.
        var experiencesDiv = document.getElementById('experienceContainer')
        if (userDict['experience'] == null) {
            if (!viewingSelf) {
                experiencesDiv.style.display = 'none';    
            } else {
                experiencesDiv.style.display = 'block';
                addExperiencesDiv = document.getElementById('addExperienceInjectionPoint');
                addExperiencesDiv.innerHTML += '<div class="col col-sm-1 text-right"><button onclick="requestAddModal(\'experience\', \''+ userDict['experience'] +'\')" type="button" class="btn btn-sm btn-link">Add</button></div>';
            }
        } else {
            experiencesDiv.style.display = 'block';
            if (viewingSelf) {
                addExperienceDiv = document.getElementById('addExperienceInjectionPoint');
                addExperienceDiv.innerHTML += '<div class="col col-sm-1 text-right"><button onclick="requestAddModal(\'experience\', \''+ userDict['experience'] +'\')" type="button" class="btn btn-sm btn-link">Add</button></div>';
            }
            for (i in userDict['experience']) {
                var experience = userDict['experience'][i];
                experiencesDiv.innerHTML += renderRowData('experience', experience, viewingSelf, experience['header_1'], experience['header_2']);
            }
        }

        // Render qualifcations.
        var qualifcationsDiv = document.getElementById('qualificationsContainer')
        if (userDict['qualification'] == null) {
            if (!viewingSelf) {
                qualifcationsDiv.style.display = 'none';    
            } else {
                qualifcationsDiv.style.display = 'block';
                addQualificationsDiv = document.getElementById('addQualificationInjectionPoint');
                addQualificationsDiv.innerHTML += '<div class="col col-sm-1 text-right"><button onclick="requestAddModal(\'qualification\', \''+ userDict['qualification'] +'\')" type="button" class="btn btn-sm btn-link">Add</button></div>';
            }
        } else {
            qualifcationsDiv.style.display = 'block';
            if (viewingSelf) {
                addQualificationDiv = document.getElementById('addQualificationInjectionPoint');
                addQualificationDiv.innerHTML += '<div class="col col-sm-1 text-right"><button  onclick="requestAddModal(\'qualification\', \''+ userDict['qualification'] +'\')" type="button" class="btn btn-sm btn-link">Add</button></div>';
            }
            for (i in userDict['qualification']) {
                var qualification = userDict['qualification'][i];
                qualifcationsDiv.innerHTML += renderRowData('qualification', qualification, viewingSelf, qualification['header_1'], qualification['header_2']);
            }
        }
    }
}

function renderRowData(dataType, data, renderEdit, where, what) {
    var html = '';
    html += '<div class="row" style="padding-top:8px;padding-bottom:8px;">';
    html += '<div class="col">';
    html += '<div><p class="whereWhat"><span class="font-weight-bold">' + where + '</span>, ' + what + '</p></div>';
    html += '<div><small class="text-muted m-0">' + data['start_date'] + ' - ' + data['end_date'] + '</small></div>';
    html += '</div>';
    if (renderEdit) {
        html += '<div class="col col-sm-1">';
        html += '<div class="text-right">';
        html += '<button onclick="requestEditModal(\''+ dataType +'\', \''+ data['id'] +'\')" data-toggle="modal" data-target="#editModal" type="button" class="btn btn-sm btn-link">Edit</button>';
        html += '</div></div>';
    }
    html += '</div>';
    html += '<p>' + data['text'] + '</p>';
    
    return html;
}

function renderLoginError(message) {
    // Look at Boostraps .is-invalid
    document.getElementById("loginErrorContainer").innerHTML = message;
    toggle_visiblity("loginErrorContainer", true);
}

function clearLoginError() {
    document.getElementById("loginErrorContainer").innerHTML = '';
    toggle_visiblity("loginErrorContainer", false);
}

function toggle_visiblity(elementId, visible) {
    if (visible == true) {
        document.getElementById(elementId).style.display = 'block';
    } else {
        document.getElementById(elementId).style.display = 'none';
    }
}

// ---------------------------------------------------------------------------

// COPY TO CLIPBOARD ---------------------------------------------------------

function copyToClipboard() {
    var copyText = document.getElementById("shareText");
    copyText.select();
    copyText.setSelectionRange(0, 99999); 
    document.execCommand("copy");
    showCopyToClipboardAlert();
}

function showCopyToClipboardAlert() {
    toggle_visiblity("copyToClipboardAlertContainer", true)
}

function hideCopyToClipboardAlert() {
    toggle_visiblity("copyToClipboardAlertContainer", false)
}

// ---------------------------------------------------------------------------

// DELETE --------------------------------------------------------------------

function deleteSubmit(deleteType, rowId) {
    requestPost(deleteUrl, {'delete_type': deleteType, 'id': rowId}, responseCompleted);
}

// ---------------------------------------------------------------------------

// EDIT & ADD ----------------------------------------------------------------------

function buildChangeDictionary(editType) {
    console.log(editType);
    keyMap = {
        'user': ['email', 'hidden'],
        'authentication': ['password', 'password_check'],
        'details': ['header_1', 'header_2'],
        'about': ['text'],
        'experience': ['header_1', 'header_2', 'start_date', 'end_date', 'text'],
        'qualification': ['header_1', 'header_2', 'start_date', 'end_date', 'text']
    }

    // Build edit dictionary.
    editDict = {};
    for (const key of keyMap[editType]) {
        input = document.getElementById(key);
        if (input && input.value != null) {
            editDict[key] = input.value;
        }
    }

    finalDict = {};
    finalDict[editType] = editDict;
    console.log(finalDict);
    return finalDict;
}

function addSubmit(addType, rowId) {
    addDict = buildChangeDictionary(addType);
    addDict['add_id'] = rowId;
    requestPost(addUrl, addDict, responseCompleted);
}

function editSubmit(editType, rowId) {
    editDict = buildChangeDictionary(editType);
    editDict['edit_id'] = rowId;
    requestPost(edit_url, editDict, responseCompleted);
}

function editEmail() {
    document.getElementById('manageNewPassword').value = '';
    document.getElementById('manageConfirmNewPassword').value = '';

    editDict = buildChangeDictionary('user');
    editDict['edit_id'] = read_cookie('user_id');
    requestPost(edit_url, editDict, responseCompleted);
}

function submitPasswordChange() {
    passwordDict = buildChangeDictionary('authentication');
    if(passwordDict['authentication']['password'] == passwordDict['authentication']['password_check']) {
        requestDict = {
            'password': passwordDict['authentication']['password']
        }
        requestPost(changePasswordUrl, requestDict, responseCompleted);
    } else {
        responseCompleted({'error': 'Passwords don\'t match!'});
    }
}

function responseCompleted(response) {
    if ('refresh' in response) {
        if (response['refresh'] == null) {
            location.reload();
        } else {
            console.log(response['refresh']);
            window.location.href = 'http://' + response['refresh'];
        }
        
    } else if ('signout' in response) {
        logoutSubmit();
    }
    else {
        successDiv = document.getElementById('injectSuccess');
        if (successDiv != null) {
            successDiv.style.display = 'none';
        }
        errorDiv = document.getElementById('injectAlert');
        if (errorDiv != null) {
            errorDiv.style.display = 'none';
        }
        if ((errorDiv != null) && ('error' in response)) {
            errorDiv.innerHTML = response['error'];
            errorDiv.style.display = 'block';
        } else if ((successDiv != null) && ('success' in response)) {
            successDiv.innerHTML = response['success'];;
            successDiv.style.display = 'block';
        } else {
            if (successDiv != null) {
                successDiv.style.display = 'none';
            }
            if (errorDiv != null) {
                errorDiv.style.display = 'none';
            }
        }
    }
}

// ---------------------------------------------------------------------------

// INJECTED MODALS -----------------------------------------------------------

function requestShareModal() {
    params = '?user_id=' + read_cookie('user_id');
    injectHTMLModal('');
    request(shareModalUrl + params, injectHTMLModal);
}

function requestLoginModal() {
    injectHTMLModal('');
    request(loginModalUrl, injectHTMLModal);
}

function requestSignUpModal() {
    injectHTMLModal('');
    request(signUpModalUrl, injectHTMLModal);
}

function requestEditModal(editType, rowId) {
    params = '?edit_type=' + editType + '&row_id=' + rowId;
    injectHTMLModal('');
    request(editModalUrl + params, injectHTMLModal);
}

function requestManageModal() {
    injectHTMLModal('');
    request(manageModalUrl, injectHTMLModal);
}

function requestAddModal(editType, rowId) {
    params = '?add_type=' + editType + '&row_id=' + rowId;
    injectHTMLModal('');
    request(addModalUrl + params, injectHTMLModal);
}

function requestDeleteModal(deleteType, rowId) {
    injectHTMLModal('');
    params = '?delete_type=' + deleteType + '&row_id=' + rowId;
    request(deleteModalUrl + params, injectHTMLModal);
}

function injectHTMLModal(html) {
    if (html == null) {
        alert('This feature is not avalible at the moment. Please try again later')
    }
    document.getElementById('htmlInjectionContainer').innerHTML = html;
    $("#injectedModal").modal({show: true}); 
}

function closeInjectedModal() {
    $('#injectedModal').modal('hide');
    injectHTMLModal('');
}

//  --------------------------------------------------------------------------


function onOpen() {
    // Display user if id param set in URL.
    var userId = getUrlVars()['id'];
    if (userId != null) {
        toggle_visiblity("landingPage", false);
        request(server_url + '/users?id=' + userId, displayUser);
    }

    // if "user_id" and "session_key" cookies are set user was logged in.
    // If the session is valid, they are still logged in.
    user_id = read_cookie('user_id');
    session_key = read_cookie('session_key');
    
    if (user_id != null) {
        // TODO validate session.
        request(server_url + '/users/basic?id=' + user_id, loggedIn);
    } else {
        loggedOut(false);
    }
}

document.onload = onOpen();