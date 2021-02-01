var signup_url = "http://192.168.8.100:5000/auth/signup";
var login_url = "http://192.168.8.100:5000/auth/login";
var edit_url = "http://192.168.8.100:5000/users/edit";

function signupSubmit() {
    var signupEmail = document.getElementById("signupEmail").value;
    var signupPassword = document.getElementById("signupPassword").value;
    var signupDisplayName = document.getElementById("signupDisplayName").value;
    var signupHeadline = document.getElementById("signupHeadline").value;
    var signupAbout = document.getElementById("signupAbout").value;
    signup(signupEmail, signupPassword, signupDisplayName, signupHeadline, signupAbout);
}

function loginSubmit() {
    var email = document.getElementById("loginEmail").value;
    var password = document.getElementById("loginPassword").value;
    requestPost(login_url, {'email': email, 'password': password}, displayResponse);
}

function signup(email, password, displayName, headline, about) {
    requestPost(signup_url, {'email': email, 'password': password, 'display_name': displayName, 'headline': headline}, displayResponse);
}

function login(email, password) {
    requestPost(login_url, {'email': email, 'password': password}, displayResponse);
}

function requestGet(url, callback) {
    {
        var xmlHttp = new XMLHttpRequest();
        xmlHttp.open("GET", url, true);
        xmlHttp.withCredentials = true;
        xmlHttp.setRequestHeader('Access-Control-Allow-Origin', server_url);
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

function requestPost(url, data_dict, callback) {
    // alert('requestPost');
    var xmlHttp = new XMLHttpRequest();
    xmlHttp.open("POST", url, true);
    xmlHttp.setRequestHeader('Content-Type', 'application/json');
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

function displayResponse(responseDict) {
    console.log(responseDict);
}

