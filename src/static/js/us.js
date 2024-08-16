"use strict";

import * as parliamentarch from "parliamentarch";
import { fillingStrategy } from "parliamentarch/geometry.js";

$(document).ready(function () {
    $('#diagrammaker').click(function () {
        CallDiagramScript();
    });

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
    const attrib = new Map([
        [new parliamentarch.SeatData("Democrats", "#0000FF", 0, "#000000"), Math.max(0, parseInt($("#demNumber").val()))],
        [new parliamentarch.SeatData("Republicans", "#FF0000", 0, "#000000"), Math.max(0, parseInt($("#repNumber").val()))],
        [new parliamentarch.SeatData("Independents", "#C9C9C9", 0, "#000000"), Math.max(0, parseInt($("#indNumber").val()))],
        [new parliamentarch.SeatData("Vacant", "#6B6B6B", 0, "#000000"), Math.max(0, parseInt($("#vacNumber").val()))],
    ]);
    const strategy = $('#advanced-body').is(':visible') && $('#row-densifier').is(':checked') ?
        fillingStrategy.EMPTY_INNER :
        fillingStrategy.DEFAULT;

    const svg = parliamentarch.get_svg_from_attribution(attrib, .8, {"filling_strategy": strategy});

    // Show the default-hidden div
    $("#togglablepost").show();

    // This will get the first node with id "postcontainer"
    const postcontainer = document.getElementById("postcontainer");

    const newdiag = postcontainer.insertBefore(document.createElement('p'), postcontainer.firstChild);

    newdiag.appendChild(svg);
    // and a linebreak
    newdiag.appendChild(document.createElement("br"));

    const blob = new Blob([svg.outerHTML], {type: "image/svg+xml"});
    const url = URL.createObjectURL(blob);

    // Add a link with the new diagram
    const a = document.createElement('a');
    a.className = "btn btn-success";
    a.append("Click to download your SVG diagram.");
    a.title = "SVG diagram";
    a.href = url;
    a.download = "diagram.svg";
    newdiag.appendChild(a);
}
