$(document).ready(function () {
    jscolor.installByClassName("jscolor");
    addParty(newcolor = "#AD1FFF");
});

function CallDiagramScript() {
    // Create request payload
    let payload = {};
    // Create legend string: this is a Wikipedia markup legend that can be pasted into an article.
    let legendstring = "";

    let spotradius = 0;
    let spotspacing = 0;
    let wingrows = 0;
    let centercols = 0;
    let fullwidth = 0;
    let cozy = 0;
    let autospeaker = 0;
    let partylist = [];
    //this variable will hold the index of the party with the biggest support: used for creating an auto-speaker spot.
    let bigparty = 0;
    let bigpartysize = 0;

    $("input").each(function () {
        if (this.name.startsWith("radius")) {
            spotradius = Math.max(0, parseFloat(this.value));
        } else if (this.name.startsWith("spacing")) {
            spotspacing = Math.max(0, Math.min(parseFloat(this.value), .99)); //don't allow spots of size 0.
        } else if (this.name.startsWith("wingrows")) {
            wingrows = Math.max(0, parseInt(this.value));
        } else if (this.name.startsWith("centercols")) {
            centercols = Math.max(0, parseInt(this.value));
        } else if (this.name.startsWith("fullwidth")) {
            fullwidth = new Boolean(this.checked);
        } else if (this.name.startsWith("cozy")) {
            cozy = new Boolean(this.checked);
        } else if (this.name.startsWith("autospeaker")) {
            autospeaker = Math.max(0, parseInt(this.value));
        } else if (this.name.startsWith("Name")) {
            partylist[parseInt(/[0-9]+$/.exec(this.name)[0])] = { Name: this.value };
        } else if (this.name.startsWith("Number")) {
            // Don't allow parties without delegates: if we have a number field, make the value at least 1.
            // It's a bit of a hack, but shouldn't be much of a limitation.
            partylist[parseInt(/[0-9]+$/.exec(this.name)[0])]['Num'] = Math.max(1, parseInt(this.value));
        } else if (this.name.startsWith("Color")) {
            // If we are processing a colour string, add a # before the hex values.
            partylist[parseInt(/[0-9]+$/.exec(this.name)[0])]['Color'] = this.value;
        }
    });
    $("select").each(function () {
        if (this.name.startsWith("Group")) {
            partylist[/[0-9]+$/.exec(this.name)[0]]['Group'] = this.value;
        }
    });

    payload.radius = spotradius;
    payload.spacing = spotspacing;
    payload.wingrows = wingrows;
    payload.centercols = centercols;
    payload.fullwidth = fullwidth;
    payload.cozy = cozy;

    let parties = payload.parties = [];

    for (let i = 1; i < partylist.length; i++) {
        const party = partylist[i];
        if (party) {
            // Find the biggest party while going through the list
            // This is such a cheap operation that I'm not going to bother
            // to check each time whether "autospeaker" is checked.

            // Update bigparty as the index of the biggest party
            if (party.Num > bigpartysize) {
                bigparty = i;
                bigpartysize = party.Num;
            }

            parties.push({
                name: party.Name,
                num: party.Num,
                group: party.Group,
                color: '#' + party.Color
            });

            if (party.Group !== "head") {
                legendstring += `{{legend|#${party.Color}|${party.Name}: ${party.Num} seat`;
                if (party.Num !== 1) {
                    legendstring += 's';
                }
                legendstring += '}} ';
            }
        }
    }

    if (autospeaker) {
        parties.push({
            name: partylist[bigparty].Name,
            num: autospeaker,
            group: "head",
            color: '#' + partylist[bigparty].Color
        });
    }


    if (partylist.length) {
        //Now post the request to the script which actually makes the diagram.
        const requeststring = JSON.stringify(payload);
        $.ajax({
            type: "POST",
            url: "westminster.py",
            data: { data: requeststring },
        }).done(function (data, status) {
            data = data.trim();

            // Show the default-hidden div
            $("#togglablepost").show();

            // This will get the first node with id "postcontainer"
            const postcontainer = document.getElementById("postcontainer");
            // This is the new postcontainer that will hold our stuff.
            const newpost = document.createElement("div");
            newpost.setAttribute("id", "postcontainer");

            postcontainer.parentNode.insertBefore(newpost, postcontainer);

            // Now add the svg image to the page
            const img = document.createElement("img");
            img.src = data;
            newpost.appendChild(img);
            // and a linebreak
            newpost.appendChild(document.createElement("br"));

            // Add a link with the new diagram
            const a = document.createElement('a');
            a.appendChild(document.createTextNode("Click to download your SVG diagram."));
            a.title = "SVG diagram";
            a.href = data;
            a.download = data;
            newpost.appendChild(a);
            // and a linebreak
            newpost.appendChild(document.createElement("br"));

            // Now add the legend template text with the party names, colours and support.
            newpost.appendChild(document.createTextNode("Legend template for use in Wikipedia:"));
            newpost.appendChild(document.createElement("br"));
            newpost.appendChild(document.createTextNode(legendstring));
            newpost.appendChild(document.createElement("br"));
        });

        console.log(requeststring);
        console.log(legendstring);
    }
}

function addParty(newcolor = "") {
    // Party list <div> where dynamic content will be placed
    const partylistcontainer = document.getElementById("partylistcontainer");

    //New party's number: one more than the largest party number so far:
    let i = 0;
    $("div").each(function () {
        if (this.id.match(/^party[0-9]+$/)) {
            i = Math.max(i, parseInt(/[0-9]+$/.exec(this.id)[0]));
        }
    });
    i++;

    const partycard = partylistcontainer.appendChild(document.createElement('div'));
    partycard.id = "party" + i;
    partycard.className = "card";

    const newpartydiv = partycard.appendChild(document.createElement('div'));
    newpartydiv.className = "card-body";

    // Party name label
    const partytitle = document.createElement('div');
    partytitle.className = 'left';
    partytitle.innerHTML = "Party " + i + " name";
    newpartydiv.appendChild(partytitle);

    let input;
    // Party name input control
    input = document.createElement('div');
    input.innerHTML = `<input class="right" type="text" name="Name${i}" value="Party ${i}">`;
    newpartydiv.appendChild(input);

    // Party support name tag
    const partysupport = document.createElement('div');
    partysupport.className = 'left';
    partysupport.innerHTML = `Party ${i} delegates`;
    newpartydiv.appendChild(partysupport);

    // Party support input control
    input = document.createElement('div');
    input.innerHTML = `<input class="right" type="number" name="Number${i}" value="${i}">`;
    newpartydiv.appendChild(input);

    // Party group name tag
    const partygroup = document.createElement('div');
    partygroup.className = 'left';
    partygroup.innerHTML = `Party ${i} group`;
    newpartydiv.appendChild(partygroup);

    // Party group input control
    input = document.createElement('div');
    input.innerHTML = `<select class="right" name="Group${i}">
        <option value="left">Left</option>
        <option value="right">Right</option>
        <option value="center">Cross-bench</option>
        <option value="head">Speaker</option>
    </select>`;
    newpartydiv.appendChild(input);

    // Party color name tag
    const partycolor = document.createElement('div');
    partycolor.className = 'left';
    partycolor.innerHTML = `Party ${i} color`;
    newpartydiv.appendChild(partycolor);

    // Party color input control
    input = document.createElement('div');
    if (newcolor == "") { newcolor = getRandomColor() }
    input.innerHTML = `<input class="right jscolor" type="text" name="Color${i}" value="${newcolor}">`;
    newpartydiv.appendChild(input);

    // Delete button
    const delbutton = document.createElement('button');
    delbutton.className = 'btn btn-danger';
    delbutton.innerHTML = `Delete party ${i}`;
    delbutton.setAttribute("onClick", `deleteParty(${i})`);
    newpartydiv.appendChild(delbutton);
    // Add a newline
    newpartydiv.appendChild(document.createElement("br"));
    jscolor.installByClassName("jscolor");
}
