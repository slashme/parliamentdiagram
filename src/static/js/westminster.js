$(document).ready(function () {
    jscolor.installByClassName("jscolor");
    addParty(newcolor = "#AD1FFF");

    $(".sortableContainer").each(function (index, liz) {
        const jliz = $(liz);
        jliz.sortable({
            handle: ".handle",
            containment: jliz.parents(".card"),
            opacity: .7,
            revert: 30,
            tolerance: "pointer",
        });
    });
});

function CallDiagramScript() {
    // Create request payload
    const payload = {
        radius: Math.max(0, parseFloat($("input[name^='radius']").val())),
        spacing: Math.max(0, Math.min(parseFloat($("input[name^='spacing'").val()), .99)),
        wingrows: Math.max(0, parseInt($("input[name^='wingrows']").val())),
        centercols: Math.max(0, parseInt($("input[name^='centercols']").val())),
        fullwidth: new Boolean($("input[name^='fullwidth']").prop("checked")),
        cozy: new Boolean($("input[name^='cozy']").prop("checked")),
        parties: [],
    };

    const partylist = payload.parties;

    // Create legend string: this is a Wikipedia markup legend that can be pasted into an article.
    let legendstring = "";
    //this variable will hold the index of the party with the biggest support: used for creating an auto-speaker spot.
    let bigparty = 0;
    let bigpartysize = 0;
    let totalseats = 0; //count total seats to check for empty diagram
    $(".partycard").each(function () {
        const jme = $(this);
        const index = partylist.length;

        const party = {
            name: jme.find("input[name^='Name']").val(),
            num: Math.max(1, parseInt(jme.find("input[name^='Number']").val())),
            group: jme.find("select[name^='Group']").val(),
            color: "#" + jme.find("input[name^='Color']").val(),
        };

        if (party.num > bigpartysize) {
            bigparty = index;
            bigpartysize = party.num;
        }

        partylist.push(party);

        totalseats += party.num;

        if (party.group !== "head") {
            legendstring += `{{legend|${party.color}|${party.name}: ${party.num} seat`
            if (party.num !== 1) {
                legendstring += 's';
            }
            legendstring += '}} ';
        }
    });

    const autospeaker = Math.max(0, parseInt($("input[name^='autospeaker']").val()));
    if (autospeaker) {
        partylist.push({
            name: partylist[bigparty].name,
            num: autospeaker,
            group: "head",
            color: '#' + partylist[bigparty].color
        });
        totalseats += autospeaker;
    }

    if (totalseats > 0) {
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
            a.append("Click to download your SVG diagram.");
            a.title = "SVG diagram";
            a.href = data;
            a.download = data;
            newdiag.appendChild(a);
            // and a linebreak
            newdiag.appendChild(document.createElement("br"));

            // Now add the legend template text with the party names, colours and support.
            newdiag.appendChild(document.createElement("h4"))
                .append("Legend template for use in Wikipedia:");
            newdiag.append(legendstring);
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
    partycard.className = "card partycard";

    const newpartydiv = partycard.appendChild(document.createElement('div'));
    newpartydiv.className = "card-body";

    // Ordering handle
    const mover = newpartydiv.appendChild(document.createElement('span'));
    mover.className = 'handle btn btn-secondary';
    mover.innerHTML = '☰';
    Object.assign(mover.style, {
        cursor: "move",
        "font-size": "30px",
        position: 'absolute',
        right: '20px',
        top: '50%',
        transform: 'translateY(-50%)', // yalign .5
        padding: '0 10px',
    });

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
