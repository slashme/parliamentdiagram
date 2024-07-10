$(document).ready(function () {
    // Enable/disable advanced parameters
    const enable_advanced_btn = $('#enable-advanced');
    const disable_advanced_btn = $('#disable-advanced');
    const advanced_body = $('#advanced-body');
    enable_advanced_btn.click(function () {
        enable_advanced_btn.hide();
        disable_advanced_btn.show();
        advanced_body.show();
    });
    disable_advanced_btn.click(function () {
        enable_advanced_btn.show();
        disable_advanced_btn.hide();
        advanced_body.hide();
    });
})

function CallDiagramScript() {
    // This is what we send to the python script
    const requestJSON = {
        // Retrieve advanced parameters
        denser_rows: $('#advanced-body').is(':visible') && $('#row-densifier').is(':checked'),
        parties: [
            {
                name: "Democrats",
                nb_seats: Math.max(0, parseInt($("#demNumber").val())),
                color: "#0000FF",
                border_size: 0,
                border_color: "#000000",
            },
            {
                name: "Republicans",
                nb_seats: Math.max(0, parseInt($("#repNumber").val())),
                color: "#FF0000",
                border_size: 0,
                border_color: "#000000",
            },
            {
                name: "Independents",
                nb_seats: Math.max(0, parseInt($("#indNumber").val())),
                color: "#C9C9C9",
                border_size: 0,
                border_color: "#000000",
            },
            {
                name: "Vacant",
                nb_seats: Math.max(0, parseInt($("#vacNumber").val())),
                color: "#6B6B6B",
                border_size: 0,
                border_color: "#000000",
            },
        ],
    };

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
