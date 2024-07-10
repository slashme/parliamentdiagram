function CallArchScript() {
    const requestJSON = {};  // This is what we send to the python script
    requestJSON.denser_rows = false; //Because I'm not going to implement this here yet
    requestJSON.parties = []
    $("input").each(function () {
        if (this.value < 1) { this.value = 0; }; //Make sure it's a number!
        switch (this.name) {
            case "Dem":
                requestJSON.parties.push({
                    name: "Democrats",
                    nb_seats: parseInt(this.value),
                    color: "#0000FF",
                    border_size: 0,
                    border_color: "#000000"
                });
                break;
            case "Rep":
                requestJSON.parties.push({
                    name: "Republicans",
                    nb_seats: parseInt(this.value),
                    color: "#FF0000",
                    border_size: 0,
                    border_color: "#000000"
                });
                break;
            case "Ind":
                requestJSON.parties.push({
                    name: "Independents",
                    nb_seats: parseInt(this.value),
                    color: "#C9C9C9",
                    border_size: 0,
                    border_color: "#000000"
                });
                break;
            case "Vac":
                requestJSON.parties.push({
                    name: "Vacant",
                    nb_seats: parseInt(this.value),
                    color: "#6B6B6B",
                    border_size: 0,
                    border_color: "#000000"
                });
                break;
        }
    });
    console.log(requestJSON);

    //Now post the request to the script which actually makes the diagram.
    $.ajax({
        type: "POST",
        url: "newarch.py",
        data: { data: JSON.stringify(requestJSON) },
    }).done(function (data, status) {
        data = data.trim();

        // Show the default-hidden div
        $("#togglablepost").show();

        // This will get the first node with id "postcontainer"
        const postcontainer = document.getElementById("postcontainer");

        const newdiag = postcontainer.insertBefore(document.createElement('p'), postcontainer.firstChild);

        // Now add the svg image to the page
        const img = document.createElement("img");
        img.src = data;
        newdiag.appendChild(img);
        // and a linebreak
        newdiag.appendChild(document.createElement("br"));

        // Add a link with the new diagram
        const a = document.createElement('a');
        a.className = "btn btn-success";
        a.appendChild(document.createTextNode("Click to download your SVG diagram."));
        a.title = "SVG diagram";
        a.href = data;
        a.download = data;
        newdiag.appendChild(a);
    });
}
