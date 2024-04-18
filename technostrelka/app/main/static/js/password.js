let shwpsswrd = document.getElementById("shwpsswrd");

shwpsswrd.onclick = function(){
    let type = 'password'
    if (shwpsswrd.checked) type = 'text'
    Array.from(document.getElementsByClassName('psswrd')).forEach(element => {
        element.setAttribute('type', type)
    });
}
