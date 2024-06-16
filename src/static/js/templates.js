$(document).ready(function() {
});

// hardcoded list of metadata for each template
const templates_metadata = [
    {
        id: "assnat",
        nseats_per_area: [582],
    },
];

function selectTemplate(template_id) {
    // get the metadata for the selected template
    // delete if exists then recreate, or empty, the parties container
    // potentially readd the vacants party
    // display the title and description and number of seats of the template
}

function addParty(newname = "", newcolor = "", newnseats = 0) {
    // pretty much the same as in arch.js
    // add min="0" for number inputs
    // add a max equal to the number of seats of the template
}

// when changing the number of seats of a party, callback to recompute the vacants
    // maybe use a local variable in an initializer function for the number of vacants ?

function callDiagramScript() {
    // call the python script to generate the diagram
    // display the post container and empty it
    // put the diagram inside
}
