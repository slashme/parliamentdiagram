$(document).ready(function () {
});

// hardcoded list of metadata for each template
const templates_metadata = [
    {
        id: "assnat",
        nseats_per_area: [582],
    },
];

let selected_template = null;

function actuateVacants() {
    const [nseats] = selected_template.nseats_per_area;

    // get the sum of the number of seats of all parties
    let sum = 0;
    $("input").each(function () {
        if (this.id.match(/party\d+_number/)) {
            sum += parseInt(this.value);
        }
    });
    $("#number_vacant").val(Math.max(0, nseats - sum));
    return nseats - sum;
}

function selectTemplate(template_id) {
    // get the metadata for the selected template
    selected_template = templates_metadata.find((template) => template.id === template_id);

    // TODO
    // show the selected template metadata container
    // put in the title and description and number of seats of the template,
    // taken from the element with id "template_" + template_id

    // show the parties container
    $("#togglablepartylistcontainer").show();
    // empty it
    $("#partylistcontainer").empty();

    // add an empty party with random color
    addParty();
    // actuate the number of vacant seats
    actuateVacants();
}

function addParty(newname = "", newcolor = "", newnseats = 0) {
    const partylistcontainer = document.getElementById("partylistcontainer");
    // New party's number: one more than the bigger party number so far
    let party_number = 0;
    $("div").each(function () {
        if (this.id.match(/party\d+/)) {
            party_number = Math.max(party_number, parseInt(this.id.match(/party(\d+)/)[1]));
        }
    });
    party_number++;

    const partycard = partylistcontainer.appendChild(document.createElement("div"));
    partycard.id = "party" + party_number;
    partycard.className = "card";

    const newpartydiv = partycard.appendChild(document.createElement("div"));
    newpartydiv.className = "card-body";

    // Party name label
    const partytitle = newpartydiv.appendChild(document.createElement("div"));
    partytitle.className = "left";
    if (newname == "") { newname = "Party " + party_number; }
    partytitle.append(`Party ${party_number} name`);

    // Party name input
    const partynameinput = newpartydiv.appendChild(document.createElement("div"))
        .appendChild(document.createElement("input"));
    partynameinput.className = "right";
    partynameinput.type = "text";
    partynameinput.id = `party${party_number}_name`;
    partynameinput.value = newname;

    // Party seats label
    const partyseatslabel = newpartydiv.appendChild(document.createElement("div"));
    partyseatslabel.className = "left";
    partyseatslabel.append(`Party ${party_number} seats`);

    // Party seats input
    const partyseatsinput = newpartydiv.appendChild(document.createElement("div"))
        .appendChild(document.createElement("input"));
    partyseatsinput.className = "right";
    partyseatsinput.type = "number";
    partyseatsinput.id = `party${party_number}_number`;
    partyseatsinput.min = 0;
    [partyseatsinput.max] = selected_template.nseats_per_area;
    partyseatsinput.value = newnseats;
    partyseatsinput.onchange = actuateVacants;

    // Party color label
    const partycolorlabel = newpartydiv.appendChild(document.createElement("div"));
    partycolorlabel.className = "left";
    partycolorlabel.append(`Party ${party_number} color`);

    // Party color input
    const partycolorinput = newpartydiv.appendChild(document.createElement("div"))
        .appendChild(document.createElement("input"));
    partycolorinput.className = "right jscolor";
    partycolorinput.type = "text";
    partycolorinput.id = `party${party_number}_color`;
    if (newcolor == "") { newcolor = getRandomColor(); }
    partycolorinput.value = newcolor;

    // Party border width label
    const partybwidthlabel = newpartydiv.appendChild(document.createElement("div"));
    partybwidthlabel.className = "left";
    partybwidthlabel.append(`Party ${party_number} border width`);

    // Party border width input
    const partybwidthinput = newpartydiv.appendChild(document.createElement("div"))
        .appendChild(document.createElement("input"));
    partybwidthinput.className = "right";
    partybwidthinput.type = "number";
    partybwidthinput.id = `party${party_number}_border`;
    partybwidthinput.step = 0.01;
    partybwidthinput.min = 0.0;
    partybwidthinput.max = 1.0;
    partybwidthinput.value = 0.0;

    // Party border color label
    const partybcolorlabel = newpartydiv.appendChild(document.createElement("div"));
    partybcolorlabel.className = "left";
    partybcolorlabel.append(`Party ${party_number} border color`);

    // Party border color input
    const partybcolorinput = newpartydiv.appendChild(document.createElement("div"))
        .appendChild(document.createElement("input"));
    partybcolorinput.className = "right jscolor";
    partybcolorinput.type = "text";
    partybcolorinput.id = `party${party_number}_bcolor`;
    partybcolorinput.value = "000000";

    // Party delete button
    const delbutton = newpartydiv.appendChild(document.createElement("button"));
    delbutton.className = "btn btn-danger";
    delbutton.append(`Delete party ${party_number}`);
    delbutton.onclick = function () { deleteParty(party_number); };

    jscolor.installByClassName("jscolor");
}

function callDiagramScript() {
    const payload = { template_id: selected_template.id };

    let partylist = [];
    $("input").each(function () {
        const [matchresult] = [...this.id.matchAll(/party(\d+)_(\w+)/g)];
        if (matchresult) {
            let [, partynumber, property] = matchresult;
            if (partylist[partynumber] == undefined) {
                partylist[partynumber] = {};
            }
            let value;
            switch (property) {
                case "name":
                    // TODO: implement the name/data/title feature to fix the legend string
                    // property = "name";
                    // value = this.value;
                    // break;
                    return;
                case "number":
                    property = "nb_seats";
                    value = parseInt(this.value);
                    break;
                case "color":
                    value = "#" + this.value;
                    break;
                case "border":
                    property = "border_size";
                    value = parseFloat(this.value);
                    break;
                case "bcolor":
                    property = "border_color";
                    value = "#" + this.value;
                    break;
                default:
                    return;
            }
            partylist[partynumber][property] = value;
        }
    });
    partylist = partylist.filter((party) => party !== undefined);
    const vacants = actuateVacants();
    if (vacants < 0) {
        alert("There are too many seats for the template's capacity.");
        return;
    }
    partylist.push({
        nb_seats: vacants,
        color: "#" + $("#color_vacant").val(),
        border_size: parseFloat($("#border_vacant").val()),
        border_color: "#" + $("#bcolor_vacant").val(),
    });

    payload.partylist_per_area = [partylist];

    let legendstring = "";
    for (let party of partylist) {
        legendstring += `{{legend|${party.color}|${party.name}: ${party.nb_seats} seat`;
        if (party.nb_seats !== 1) {
            legendstring += 's';
        }
        legendstring += '}} ';
    }

    $.ajax({
        type: "POST",
        url: "template.py",
        data: { data: JSON.stringify(payload) },
    }).done(function (data) {
        data = data.trim();

        $("#togglablepost").show();

        const postcontainer = document.getElementById("postcontainer");
        postcontainer.innerHTML = "";

        const img = postcontainer.appendChild(document.createElement("img"));
        img.src = data;
        img.id = "SVGDiagram";

        const download = postcontainer.appendChild(document.createElement("a"));
        download.append("Click to download your SVG diagram.");
        download.className = "btn btn-success";
        download.title = "SVG diagram";
        download.href = download.download = data;
        postcontainer.appendChild(document.createElement("hr"));

        postcontainer.append(
            "Legend template for use in Wikipedia:",
            document.createElement("br"),
            legendstring,
        );
    }).fail(function (jqXHR, textStatus, errorThrown) {
        alert("Error " + textStatus + ": " + errorThrown);
    });
}
