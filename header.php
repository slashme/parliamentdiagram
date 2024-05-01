<!DOCTYPE html>
<html dir="ltr" lang="en">
  <head>
    <?php if (!isset($title)) {
        $title = "Parliament diagram generator";
    } ?>
    <title><?php echo $title; ?></title>
    <link rel="stylesheet" type="text/css" href="css/parliamentstyle.css">
    <link rel="stylesheet" type="text/css" href="https://tools-static.wmflabs.org/cdnjs/ajax/libs/twitter-bootstrap/4.3.1/css/bootstrap.min.css">
    <link rel="stylesheet" href="css/select2.min.css" />
    <link rel="stylesheet" type="text/css" href="css/fork-awesome.min.css"/>
    <!--
         //document.write("\<script src='jquery.min.js' type='text/javascript'>\<\/script>"); //For local debugging
    -->
    <script src='https://tools-static.wmflabs.org/cdnjs/ajax/libs/jquery/3.2.1/jquery.min.js' type='text/javascript'></script>
    <script type="text/javascript" src="js/jscolor.js"></script>
    <script src="js/select2.min.js"></script>
    <script type="text/javascript" src="js/main.js"></script>
  </head>
<body>

  <div id="header">
    <nav class="navbar navbar-dark bg-primary shadow-sm text-white">
      <h1 class="justify-content-center container"><a class="navbar-brand">Parliament Diagrams</a></h1>
    </nav>

    <div class="container">
      <div class="block card-deck">
        <div class="card">
          <div class="card-body">
            <a href="archinputform.php">
              <img class="mt-5" src="images/AssNat_16_groupes_2022.svg" alt="arch diagram tool" title="arch diagram tool" width="90%">
            </a>
            <p class="card-text text-center pt-3"><a href="archinputform.php">Arch-style diagram</a></p>
          </div>
        </div>

        <div class="card">
          <div class="card-body">
            <a href="USinputform.php">
              <img class="mt-5" src="images/87th_Texas_Senate.svg" alt="USA diagram tool" title="USA diagram tool" width="90%">
            </a>
            <p class="card-text text-center pt-3"><a href="USinputform.php">US-style diagram</a></p>
          </div>
        </div>

        <div class="card">
          <div class="card-body">
            <a href="westminsterinputform.php">
              <img class="mt-5" src="images/NewZealand_House_Nov_2020.svg" alt="Westminster-style diagram tool" title="Westminster-style diagram tool" width="90%">
            </a>
            <p class="card-text text-center pt-3"><a href="westminsterinputform.php">Westminster-style diagram</a></p>
          </div>
        </div>
      </div>
