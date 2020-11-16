<?php //Print the status of the last upload
if ( isset ($last_res )) { //if there is a "last result" from an attempted Commons upload
	if (isset($last_res->upload) && isset($last_res->upload->warnings) ) {
		echo "<div class='warning'>";
		foreach ( $last_res->upload->warnings as $k => $v ) {
			if ( $k == 'exists' ) {
				echo "Warning: The file <a href=https://commons.wikimedia.org/wiki/File:".str_replace ( ' ' , '_' , $_GET['filename']).">".$_GET['filename']."</a> already exists.";
				if ( $last_res->upload->result != 'Success' ) {
					if (($_GET['filename'] == 'My Parliament.svg') || ($_GET['filename'] == 'My_Parliament.svg')) {
					echo "This is a testing file, which you can overwrite by clicking <a href=\"https://" . $_SERVER['HTTP_HOST'] . $_SERVER['REQUEST_URI']."&ignore=1\">this link.</a> If you abuse this feature, you will be blocked.";
					} else {
					echo "If you have confirmed that you want to overwrite it, <a href=\"https://" . $_SERVER['HTTP_HOST'] . $_SERVER['REQUEST_URI']."&ignore=1\">click this dangerous link to upload a new version.</a> If you abuse this feature, you will be blocked.";
					}
				} else {
					echo "Your file was uploaded, but still has the previous info text. To overwrite it, <a href=\"https://" . $_SERVER['HTTP_HOST'] .str_replace( 'upload' , 'edit' , $_SERVER['REQUEST_URI'])."\">click here</a>";
				}
			} elseif ( $k == 'exists-normalized' ) {
				echo "Warning: A file with a similar name already exists.";
				if ( $last_res->upload->result != 'Success' ) {
					echo "<a href=\"https://" . $_SERVER['HTTP_HOST'] . $_SERVER['REQUEST_URI']."&ignore=1\">click this link to upload an SVG version.</a>.";
				} else {
					echo "Your file was uploaded at <a href=https://commons.wikimedia.org/wiki/File:".str_replace ( ' ' , '_' , $_GET['filename']).">".$_GET['filename']."</a>, but might still have old info text. To overwrite it, <a href=\"https://" . $_SERVER['HTTP_HOST'] .str_replace( 'upload' , 'edit' , $_SERVER['REQUEST_URI'])."\">click here</a>";
				}
			} elseif ( $k == 'duplicate' ) {
				echo "Warning: A file with exactly that content already exists.<br />";
				if ( $last_res->upload->result != 'Success' ) {
					echo "<a href=\"https://" . $_SERVER['HTTP_HOST'] . $_SERVER['REQUEST_URI']."&ignore=1\">click this link to upload anyway.</a>.<br />";
				} else {
					echo "Your file was uploaded at <a href=https://commons.wikimedia.org/wiki/File:".str_replace ( ' ' , '_' , $_GET['filename']).">".$_GET['filename']."</a><br />";
				}
			} else {
				echo "Warning \"".$k."\": ".$v."<br />";
			}
		}
		echo "</div>\n";
	} elseif (isset($last_res->error)) {
		echo "<div class='error'>";
		if (  $last_res->error->code === 'mwoauth-invalid-authorization' ) {
			echo 'To authorise this application to upload under your name, go <a href="' . htmlspecialchars( $_SERVER['SCRIPT_NAME'] ) . '?action=authorize">here</a>, and then click on the upload link again.';
		} else {
			echo "Error: " . $last_res->error->info . "<br />";
		}
		echo "</div>\n";
	} elseif (isset($last_res->upload) && $last_res->upload->result != 'Success' && $last_res->edit->result != 'Success' ) { //something went wrong, so show some debug info.
		echo 'API result: <pre>' . htmlspecialchars( var_export( $last_res, 1 ) ) . '</pre>';
	}
	if (isset($last_res->upload) && $last_res->upload->result == 'Success' ) {
		echo "<div class='success'>";
		echo "Image successfully uploaded at <a href=https://commons.wikimedia.org/wiki/File:".str_replace ( ' ' , '_' , $_GET['filename']).">".$_GET['filename']."</a>";
		echo "</div>\n";
	} 
	if (isset($last_res->edit) && $last_res->edit->result == 'Success' ) {
		echo "<div class='success'>";
		echo "Image description successfully updated for <a href=https://commons.wikimedia.org/wiki/File:".str_replace ( ' ' , '_' , $_GET['filename']).">".$_GET['filename']."</a>";
		echo "</div>\n";
	} 
}
?>
