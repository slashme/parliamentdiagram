<?php require('auth.php'); ?>
<!DOCTYPE html>
<html dir="ltr" lang="en">
<head>
<link rel="stylesheet" type="text/css" href="css/parliamentstyle.css">
<link rel="stylesheet" href="css/select2.min.css" />
<!--
//document.write("\<script src='jquery.min.js' type='text/javascript'>\<\/script>"); //For local debugging
-->
<script src='https://tools-static.wmflabs.org/cdnjs/ajax/libs/jquery/3.2.1/jquery.min.js' type='text/javascript'></script>
<script type="text/javascript" src="jscolor/jscolor.js"></script>
<script src="js/select2.min.js"></script>
<script type="text/javascript" src="js/main.js"></script>
</head>
<body>
<div class=block id=header>
<?php require('header.php'); ?>
</div>
<div class="block">
It is now possible to get the list of parties from a previous diagram that uses the legend templates that this tool creates. Try it out by putting the name of an existing diagram on Commons into the text box below.
Please submit bug reports and feature requests at the project's <a href="https://github.com/slashme/parliamentdiagram/issues/new">issue tracker</a>.
</div>
<div class=block>
  This is a tool to generate arch-shaped parliament diagrams.<br>
  <br>
  To use this tool, fill in the name and support of each party in the
  legislature, clicking "Add a party" whenever you need to add a new party.  Then
  click "Make my diagram", and a link will appear to your SVG diagram. You
  can then freely download and use the diagram, but to use the diagram in
  Wikipedia, you should upload it to Wikimedia Commons. You can now do this
  directly, by clicking on the green button to create an upload link. Click on
  the link and follow the instructions: it will upload the file under your
  username, including the list of parties in the file description.  This tool
  will automatically add your file to the 
  <a href="https://commons.wikimedia.org/wiki/Category:Election_apportionment_diagrams">election apportionment diagrams</a>
  category, but you should categorise it in more detail after uploading.<br>

<?php require('response.php'); ?>

</div>
</div>
<div id="infile">
<div class="left">Country
  <select id=countrylist>
    <option value="">Select your country</option>
  </select>
</div>
<br>
<div class=button id="getfile">Get party list</div>
<div id="infile">
  <div class="left">Get list of parties from:</div><input class="right" type="text" name="infile" id="inputfile" value= "File:My_Parliament.svg" ><br>
</div>
<div class=button id="getfile">Get party list</div>
<br>
<div class=block>
  <div id="partylistcontainer">
    <div id="party1">
      <div class="left">Party 1 name            </div><input class="right"       type="text"     name="Name1"    value= "Party 1" ><br>
      <div class="left">Party 1 delegates       </div><input class="right"       type="number"   name="Number1"  value = 1        ><br>
      <div class="left">Party 1 color           </div><input class="right color" type="text"     name="Color1"   value= AD1FFF    ><br>
      <div class="left">Party 1 border          </div><input class="right"       type="checkbox" name="Border1"                   ><br>
      <div class="left">Party 1 border color    </div><input class="right color" type="text"     name="BColor1"  value= 000000    ><br>
      <div class="button deletebutton" onclick="deleteParty(1)">Delete party 1</div><br>
      <br>
    </div>
  </div>
</div>
<div class=button onclick="addParty()">
  Add a party
</div>
<div class=button onclick="CallDiagramScript()">
  Make my diagram
</div>
<div class="block">
  <div id="postcontainer">
    <br>
  </div>
</div>
</body>
</html>
