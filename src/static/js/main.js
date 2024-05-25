// Generate random color, based on http://stackoverflow.com/questions/1484506
function getRandomColor() {
    const letters = '0123456789ABCDEF'.split('');
    let color = ''; // In my case, I don't want the leading #
    for (let i = 0; i < 6; i++) {
        color += letters[Math.floor(Math.random() * 16)];
    }
    return color;
}

function deleteParty(i) {
    document.getElementById("partylistcontainer").removeChild(document.getElementById("party" + i));
}
