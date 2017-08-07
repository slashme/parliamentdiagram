<?php
/**
 * Written in 2013 by Brad Jorsch
 * Hacked in 2016 by David Richfield
 *
 * To the extent possible under law, the author(s) have dedicated all copyright 
 * and related and neighboring rights to this software to the public domain 
 * worldwide. This software is distributed without any warranty. 
 *
 * See <http://creativecommons.org/publicdomain/zero/1.0/> for a copy of the 
 * CC0 Public Domain Dedication.
 */

// ******************** CONFIGURATION ********************

/**
 * Set this to point to a file (outside the webserver root!) containing the 
 * following keys:
 * - agent: The HTTP User-Agent to use
 * - consumerKey: The "consumer token" given to you when registering your app
 * - consumerSecret: The "secret token" given to you when registering your app
 */
$inifile = '/data/project/parliamentdiagram/oauth-enduser.ini';

/**
 * Set this to the Special:OAuth/authorize URL. 
 * To work around MobileFrontend redirection, use /wiki/ rather than /w/index.php.
 */
$mwOAuthAuthorizeUrl = 'https://commons.wikimedia.org/wiki/Special:OAuth/authorize';

/**
 * Set this to the Special:OAuth URL. 
 * Note that /wiki/Special:OAuth fails when checking the signature, while
 * index.php?title=Special:OAuth works fine.
 */
$mwOAuthUrl = 'https://commons.wikimedia.org/w/index.php?title=Special:OAuth';

/**
 * Set this to the interwiki prefix for the OAuth central wiki.
 */
$mwOAuthIW = 'c';

/**
 * Set this to the API endpoint
 */
$apiUrl = 'https://commons.wikimedia.org/w/api.php';

/**
 * This should normally be "500". But Tool Labs insists on overriding valid 500
 * responses with a useless error page.
 */
$errorCode = 200;

// ****************** END CONFIGURATION ******************

// Setup the session cookie
session_name( 'ParliamentDiagramUpload' );
$params = session_get_cookie_params();
session_set_cookie_params(
	$params['lifetime'],
	dirname( $_SERVER['SCRIPT_NAME'] )
);


// Read the ini file
$ini = parse_ini_file( $inifile );
if ( $ini === false ) {
	header( "HTTP/1.1 $errorCode Internal Server Error" );
	echo 'The ini file could not be read';
	exit(0);
}
if ( !isset( $ini['agent'] ) ||
	!isset( $ini['consumerKey'] ) ||
	!isset( $ini['consumerSecret'] )
) {
	header( "HTTP/1.1 $errorCode Internal Server Error" );
	echo 'Required configuration directives not found in ini file';
	exit(0);
}
$gUserAgent = $ini['agent'];
$gConsumerKey = $ini['consumerKey'];
$gConsumerSecret = $ini['consumerSecret'];

// Load the user token (request or access) from the session
$gTokenKey = '';
$gTokenSecret = '';
session_start();
if ( isset( $_SESSION['tokenKey'] ) ) {
	$gTokenKey = $_SESSION['tokenKey'];
	$gTokenSecret = $_SESSION['tokenSecret'];
}
session_write_close();

// Fetch the access token if this is the callback from requesting authorization
if ( isset( $_GET['oauth_verifier'] ) && $_GET['oauth_verifier'] ) {
	fetchAccessToken();
}

// Take any requested action
switch ( isset( $_GET['action'] ) ? $_GET['action'] : '' ) {
	case 'download':
		header( 'Content-Type: text/plain' );
		readfile( __FILE__ );
		return;

	case 'authorize':
		doAuthorizationRedirect();
		return;

	case 'upload':
		$ignore=0;
		if (isset( $_GET['ignore'] )) {$ignore=1;} //Whether to ignore warnings. Test for presence of this parameter to avoid spamming error log.
		doUpload($_GET['uri'], $_GET['filename'], $_GET['pagecontent'], "Direct upload from parliament tool", $ignore);
		break;

	case 'edit':
		doEdit();
		break;

	case 'identify':
		doIdentify();
		break;

	case 'testspecial':
		doTestSpecial();
		break;
}


// ******************** CODE ********************

/**
 * Utility function to sign a request
 *
 * Note this doesn't properly handle the case where a parameter is set both in 
 * the query string in $url and in $params, or non-scalar values in $params.
 *
 * @param string $method Generally "GET" or "POST"
 * @param string $url URL string
 * @param array $params Extra parameters for the Authorization header or post 
 * 	data (if application/x-www-form-urlencoded).
 * @return string Signature
 */
function sign_request( $method, $url, $params = array() ) {
	global $gConsumerSecret, $gTokenSecret;
	$parts = parse_url( $url );

	// We need to normalize the endpoint URL
	$scheme = isset( $parts['scheme'] ) ? $parts['scheme'] : 'http';
	$host = isset( $parts['host'] ) ? $parts['host'] : '';
	$port = isset( $parts['port'] ) ? $parts['port'] : ( $scheme == 'https' ? '443' : '80' );
	$path = isset( $parts['path'] ) ? $parts['path'] : '';
	if ( ( $scheme == 'https' && $port != '443' ) ||
		( $scheme == 'http' && $port != '80' ) 
	) {
		// Only include the port if it's not the default
		$host = "$host:$port";
	}

	// Also the parameters
	$pairs = array();
	parse_str( isset( $parts['query'] ) ? $parts['query'] : '', $query );
	$query += $params;
	unset( $query['oauth_signature'] );
	if ( $query ) {
		$query = array_combine(
			// rawurlencode follows RFC 3986 since PHP 5.3
			array_map( 'rawurlencode', array_keys( $query ) ),
			array_map( 'rawurlencode', array_values( $query ) )
		);
		ksort( $query, SORT_STRING );
		foreach ( $query as $k => $v ) {
			$pairs[] = "$k=$v";
		}
	}

	$toSign = rawurlencode( strtoupper( $method ) ) . '&' .
		rawurlencode( "$scheme://$host$path" ) . '&' .
		rawurlencode( join( '&', $pairs ) );
	$key = rawurlencode( $gConsumerSecret ) . '&' . rawurlencode( $gTokenSecret );
	return base64_encode( hash_hmac( 'sha1', $toSign, $key, true ) );
}


/**
 * Request authorization
 * @return void
 */
function doAuthorizationRedirect() {
	global $mwOAuthUrl, $mwOAuthAuthorizeUrl, $gUserAgent, $gConsumerKey, $gTokenSecret;

	// First, we need to fetch a request token.
	// The request is signed with an empty token secret and no token key.
	$gTokenSecret = '';
	$url = $mwOAuthUrl . '/initiate';
	$url .= strpos( $url, '?' ) ? '&' : '?';
	$url .= http_build_query( array(
		'format' => 'json',
		
		// OAuth information
		'oauth_callback' => 'oob', // Must be "oob" for MWOAuth
		'oauth_consumer_key' => $gConsumerKey,
		'oauth_version' => '1.0',
		'oauth_nonce' => md5( microtime() . mt_rand() ),
		'oauth_timestamp' => time(),

		// We're using secret key signatures here.
		'oauth_signature_method' => 'HMAC-SHA1',
	) );
	$signature = sign_request( 'GET', $url );
	$url .= "&oauth_signature=" . urlencode( $signature );
	$ch = curl_init();
	curl_setopt( $ch, CURLOPT_URL, $url );
	//curl_setopt( $ch, CURLOPT_SSL_VERIFYPEER, false );
	curl_setopt( $ch, CURLOPT_USERAGENT, $gUserAgent );
	curl_setopt( $ch, CURLOPT_HEADER, 0 );
	curl_setopt( $ch, CURLOPT_RETURNTRANSFER, 1 );
	$data = curl_exec( $ch );
	if ( !$data ) {
		header( "HTTP/1.1 $errorCode Internal Server Error" );
		echo 'Curl error: ' . htmlspecialchars( curl_error( $ch ) );
		exit(0);
	}
	curl_close( $ch );
	$token = json_decode( $data );
	if ( is_object( $token ) && isset( $token->error ) ) {
		header( "HTTP/1.1 $errorCode Internal Server Error" );
		echo 'Error retrieving token: ' . htmlspecialchars( $token->error );
		exit(0);
	}
	if ( !is_object( $token ) || !isset( $token->key ) || !isset( $token->secret ) ) {
		header( "HTTP/1.1 $errorCode Internal Server Error" );
		echo 'Invalid response from token request';
		exit(0);
	}

	// Now we have the request token, we need to save it for later.
	session_start();
	$_SESSION['tokenKey'] = $token->key;
	$_SESSION['tokenSecret'] = $token->secret;
	session_write_close();

	// Then we send the user off to authorize
	$url = $mwOAuthAuthorizeUrl;
	$url .= strpos( $url, '?' ) ? '&' : '?';
	$url .= http_build_query( array(
		'oauth_token' => $token->key,
		'oauth_consumer_key' => $gConsumerKey,
	) );
	header( "Location: $url" );
	echo 'Please see <a href="' . htmlspecialchars( $url ) . '">' . htmlspecialchars( $url ) . '</a>';
}

/**
 * Handle a callback to fetch the access token
 * @return void
 */
function fetchAccessToken() {
	global $mwOAuthUrl, $gUserAgent, $gConsumerKey, $gTokenKey, $gTokenSecret;

	$url = $mwOAuthUrl . '/token';
	$url .= strpos( $url, '?' ) ? '&' : '?';
	$url .= http_build_query( array(
		'format' => 'json',
		'oauth_verifier' => $_GET['oauth_verifier'],

		// OAuth information
		'oauth_consumer_key' => $gConsumerKey,
		'oauth_token' => $gTokenKey,
		'oauth_version' => '1.0',
		'oauth_nonce' => md5( microtime() . mt_rand() ),
		'oauth_timestamp' => time(),

		// We're using secret key signatures here.
		'oauth_signature_method' => 'HMAC-SHA1',
	) );
	$signature = sign_request( 'GET', $url );
	$url .= "&oauth_signature=" . urlencode( $signature );
	$ch = curl_init();
	curl_setopt( $ch, CURLOPT_URL, $url );
	//curl_setopt( $ch, CURLOPT_SSL_VERIFYPEER, false );
	curl_setopt( $ch, CURLOPT_USERAGENT, $gUserAgent );
	curl_setopt( $ch, CURLOPT_HEADER, 0 );
	curl_setopt( $ch, CURLOPT_RETURNTRANSFER, 1 );
	$data = curl_exec( $ch );
	if ( !$data ) {
		header( "HTTP/1.1 $errorCode Internal Server Error" );
		echo 'Curl error: ' . htmlspecialchars( curl_error( $ch ) );
		exit(0);
	}
	curl_close( $ch );
	$token = json_decode( $data );
	if ( is_object( $token ) && isset( $token->error ) ) {
		header( "HTTP/1.1 $errorCode Internal Server Error" );
		echo 'Error retrieving token: ' . htmlspecialchars( $token->error );
		exit(0);
	}
	if ( !is_object( $token ) || !isset( $token->key ) || !isset( $token->secret ) ) {
		header( "HTTP/1.1 $errorCode Internal Server Error" );
		echo 'Invalid response from token request';
		exit(0);
	}

	// Save the access token
	session_start();
	$_SESSION['tokenKey'] = $gTokenKey = $token->key;
	$_SESSION['tokenSecret'] = $gTokenSecret = $token->secret;
	session_write_close();
}


/**
 * Send an API query with OAuth authorization
 *
 * @param array $post Post data
 * @param object $ch Curl handle
 * @return array API results
 */
function doApiQuery( $post, &$ch = null , $mode = '' ) {
	global $mwOAuthUrl, $gUserAgent, $gConsumerKey, $gTokenKey, $gConsumerSecret, $apiUrl ;
        
	$headerArr = array(
		// OAuth information
		'oauth_consumer_key' => $gConsumerKey,
		'oauth_token' => $gTokenKey,
		'oauth_version' => '1.0',
		'oauth_nonce' => md5( microtime() . mt_rand() ),
		'oauth_timestamp' => time(),
		// We're using secret key signatures here.
		'oauth_signature_method' => 'HMAC-SHA1',
	);

	$to_sign = '' ;
	if ( $mode == 'upload' ) {
		$to_sign = $headerArr ;
	} else {
		$to_sign = $post + $headerArr ;
	}
	$url = $apiUrl ;
	if ( $mode == 'identify' ) $url .= '/identify' ;
	$signature = sign_request( 'POST', $url, $to_sign );
	$headerArr['oauth_signature'] = $signature;

	$header = array();
	foreach ( $headerArr as $k => $v ) {
		$header[] = rawurlencode( $k ) . '="' . rawurlencode( $v ) . '"';
	}
	$header = 'Authorization: OAuth ' . join( ', ', $header );


	if ( !$ch ) {
		$ch = curl_init();
		
	}
	
	$post_fields = '' ;
	if ( $mode == 'upload' ) {
		$post_fields = $post ;
	} else {
		$post_fields = http_build_query( $post ) ;
	}
	
	curl_setopt( $ch, CURLOPT_POST, true );
	curl_setopt( $ch, CURLOPT_URL, $url );
	curl_setopt( $ch, CURLOPT_POSTFIELDS, $post_fields );
	curl_setopt( $ch, CURLOPT_HTTPHEADER, array( $header ) );
	//curl_setopt( $ch, CURLOPT_SSL_VERIFYPEER, false );
	curl_setopt( $ch, CURLOPT_USERAGENT, $gUserAgent );
	curl_setopt( $ch, CURLOPT_HEADER, 0 );
	curl_setopt( $ch, CURLOPT_RETURNTRANSFER, 1 );

	$data = curl_exec( $ch );

	if ( isset ( $_REQUEST['test'] ) ) {
		print "<hr/><h3>API query</h3>" ;
		print "Header:<pre>" ; print_r ( $header ) ; print "</pre>" ;
		print "Payload:<pre>" ; print_r ( $post ) ; print "</pre>" ;
		print "Result:<pre>" ; print_r ( $data ) ; print "</pre>" ;
		print "<hr/>" ;
	}


	if ( isset($_REQUEST['test']) ) {
		print "RESULT:<hr/>" ;
		print_r ( $data ) ;
		print "<hr/>" ;
	}

	if ( !$data ) {
	return ;
//			if ( $mode != 'userinfo' ) header( "HTTP/1.1 500 Internal Server Error" );
		$info = curl_getinfo($ch);
		print "<pre>" ; print_r ( $info ) ; print "</pre>" ;
		echo 'Curl error: ' . htmlspecialchars( curl_error( $ch ) );
		exit(0);
	}
	$ret = json_decode( $data );
	if ( $ret == null ) {
	return ;
//			if ( $mode != 'userinfo' ) header( "HTTP/1.1 500 Internal Server Error" );
		print "<h1>API trouble!</h1>" ;
//			print "<pre>" ; print_r ($header ) ; print "</pre>" ;
		print "<pre>" ; print_r ($post ) ; print "</pre>" ;
		print "<pre>" ; print_r ($data ) ; print "</pre>" ;
		print "<pre>" ; print var_export ( $ch , 1 ) ; print "</pre>" ;
		exit(0);
	}
	return $ret ;
}

function doEdit() {
	global $mwOAuthIW;

	$ch = null;

	// First fetch the username
	$res = doApiQuery( array(
		'format' => 'json',
		'action' => 'query',
		'meta' => 'userinfo',
	), $ch );

	global $last_res ;
	$last_res = $res ;

	if ( isset( $res->error->code ) && $res->error->code === 'mwoauth-invalid-authorization' ) {
		// We're not authorized! Commented out message: it's now going to alert in the standard section.
		// echo 'You haven\'t authorized this application yet! Go <a href="' . htmlspecialchars( $_SERVER['SCRIPT_NAME'] ) . '?action=authorize">here</a> to do that.';
		// echo '<hr>';
		return;
	}

	if ( !isset( $res->query->userinfo ) ) {
		header( "HTTP/1.1 $errorCode Internal Server Error" );
		echo 'Bad API response: <pre>' . htmlspecialchars( var_export( $res, 1 ) ) . '</pre>';
		exit(0);
	}
	if ( isset( $res->query->userinfo->anon ) ) {
		header( "HTTP/1.1 $errorCode Internal Server Error" );
		echo 'Not logged in. (How did that happen?)';
		exit(0);
	}
	$page = 'File:' . $_GET['filename'];

	// Next fetch the edit token
	$res = doApiQuery( array(
		'format' => 'json',
		'action' => 'tokens',
		'type' => 'edit',
	), $ch );
	if ( !isset( $res->tokens->edittoken ) ) {
		header( "HTTP/1.1 $errorCode Internal Server Error" );
		echo 'Bad API response: <pre>' . htmlspecialchars( var_export( $res, 1 ) ) . '</pre>';
		exit(0);
	}
	$token = $res->tokens->edittoken;

	// Now perform the edit
	$res = doApiQuery( array(
		'format' => 'json',
		'action' => 'edit',
		'title' => $page,
		'text' => str_replace ( '|other versions' , htmlspecialchars( '[[User:'.$last_res->query->userinfo->name.']]').'|other versions' , $_GET['pagecontent']),
		'summary' => 'Updating page info via parliament diagram tool',
		'token' => $token,
	), $ch );

	global $last_res ;
	$last_res = $res ;
}

function doUpload ( $filetosend , $new_file_name , $desc , $comment , $ignorewarnings ) {

	// First fetch the username
	$res = doApiQuery( array(
		'format' => 'json',
		'action' => 'query',
		'meta' => 'userinfo',
	), $ch );

	global $last_res ;
	$last_res = $res ;

	if ( isset( $res->error->code ) && $res->error->code === 'mwoauth-invalid-authorization' ) {
		// We're not authorized! Commented out next lines: message will appear in standard announcement page.
		// echo 'You haven\'t authorized this application yet! Go <a href="' . htmlspecialchars( $_SERVER['SCRIPT_NAME'] ) . '?action=authorize" target = "_blank">here</a> to do that.';
		return;
	}

	if ( $new_file_name == '' ) {
		$a = explode ( '/' , $filetosend ) ;
		$new_file_name = array_pop ( $a ) ;
	}
	$new_file_name = ucfirst ( str_replace ( ' ' , '_' , $new_file_name ) ) ;

	// Next fetch the edit token
	$ch = null;
	$res = doApiQuery( array(
		'format' => 'json',
		'action' => 'query' ,
		'meta' => 'tokens'
	), $ch, "upload" );

	if ( !isset( $res->query->tokens->csrftoken ) ) {
		$error = 'Bad API response [doUpload]: <pre>' . htmlspecialchars( var_export( $res, 1 ) ) . '</pre>' ;
		return false ;
	}
	$token = $res->query->tokens->csrftoken;

	$params = array(
		'format' => 'json',
		'action' => 'upload' ,
		'filename' => $new_file_name ,
		'comment' => $comment ,
		'text' => $desc ,
		'token' => $token ,
		'file' => '@' . $filetosend,
	) ;

	if ( $ignorewarnings ) $params['ignorewarnings'] = 1 ; 

	$res = doApiQuery( $params , $ch , 'upload' );

	global $last_res ;
	$last_res = $res ;
	if ( $res->upload->result != 'Success' ) {
		return false ;
	}

	return true ;
}

/**
 * Perform a generic edit
 * @return void
 */

/**
 * Request a JWT and verify it
 * @return void
 */
function doIdentify() {
	global $mwOAuthUrl, $gUserAgent, $gConsumerKey, $gTokenKey, $gConsumerSecret;

	$url = $mwOAuthUrl . '/identify';
	$headerArr = array(
		// OAuth information
		'oauth_consumer_key' => $gConsumerKey,
		'oauth_token' => $gTokenKey,
		'oauth_version' => '1.0',
		'oauth_nonce' => md5( microtime() . mt_rand() ),
		'oauth_timestamp' => time(),

		// We're using secret key signatures here.
		'oauth_signature_method' => 'HMAC-SHA1',
	);
	$signature = sign_request( 'GET', $url, $headerArr );
	$headerArr['oauth_signature'] = $signature;

	$header = array();
	foreach ( $headerArr as $k => $v ) {
		$header[] = rawurlencode( $k ) . '="' . rawurlencode( $v ) . '"';
	}
	$header = 'Authorization: OAuth ' . join( ', ', $header );

	$ch = curl_init();
	curl_setopt( $ch, CURLOPT_URL, $url );
	curl_setopt( $ch, CURLOPT_HTTPHEADER, array( $header ) );
	//curl_setopt( $ch, CURLOPT_SSL_VERIFYPEER, false );
	curl_setopt( $ch, CURLOPT_USERAGENT, $gUserAgent );
	curl_setopt( $ch, CURLOPT_HEADER, 0 );
	curl_setopt( $ch, CURLOPT_RETURNTRANSFER, 1 );
	$data = curl_exec( $ch );
	if ( !$data ) {
		header( "HTTP/1.1 $errorCode Internal Server Error" );
		echo 'Curl error: ' . htmlspecialchars( curl_error( $ch ) );
		exit(0);
	}
	$err = json_decode( $data );
	if ( is_object( $err ) && isset( $err->error ) && $err->error === 'mwoauthdatastore-access-token-not-found' ) {
		// We're not authorized!
		echo 'You haven\'t authorized this application yet! Go <a href="' . htmlspecialchars( $_SERVER['SCRIPT_NAME'] ) . '?action=authorize">here</a> to do that.';
		echo '<hr>';
		return;
	}

	// There are three fields in the response
	$fields = explode( '.', $data );
	if ( count( $fields ) !== 3 ) {
		header( "HTTP/1.1 $errorCode Internal Server Error" );
		echo 'Invalid identify response: ' . htmlspecialchars( $data );
		exit(0);
	}

	// Validate the header. MWOAuth always returns alg "HS256".
	$header = base64_decode( strtr( $fields[0], '-_', '+/' ), true );
	if ( $header !== false ) {
		$header = json_decode( $header );
	}
	if ( !is_object( $header ) || $header->typ !== 'JWT' || $header->alg !== 'HS256' ) {
		header( "HTTP/1.1 $errorCode Internal Server Error" );
		echo 'Invalid header in identify response: ' . htmlspecialchars( $data );
		exit(0);
	}

	// Verify the signature
	$sig = base64_decode( strtr( $fields[2], '-_', '+/' ), true );
	$check = hash_hmac( 'sha256', $fields[0] . '.' . $fields[1], $gConsumerSecret, true );
	if ( $sig !== $check ) {
		header( "HTTP/1.1 $errorCode Internal Server Error" );
		echo 'JWT signature validation failed: ' . htmlspecialchars( $data );
		echo '<pre>'; var_dump( base64_encode($sig), base64_encode($check) ); echo '</pre>';
		exit(0);
	}

	// Decode the payload
	$payload = base64_decode( strtr( $fields[1], '-_', '+/' ), true );
	if ( $payload !== false ) {
		$payload = json_decode( $payload );
	}
	if ( !is_object( $payload ) ) {
		header( "HTTP/1.1 $errorCode Internal Server Error" );
		echo 'Invalid payload in identify response: ' . htmlspecialchars( $data );
		exit(0);
	}

	echo 'JWT payload: <pre>' . htmlspecialchars( var_export( $payload, 1 ) ) . '</pre>';
	echo '<hr>';
}

function doTestSpecial() {
	global $mwOAuthUrl, $gUserAgent, $gConsumerKey, $gTokenKey, $gConsumerSecret;

	$url = str_replace( 'Special:OAuth', 'Special:MyPage', $mwOAuthUrl );
	$headerArr = array(
		// OAuth information
		'oauth_consumer_key' => $gConsumerKey,
		'oauth_token' => $gTokenKey,
		'oauth_version' => '1.0',
		'oauth_nonce' => md5( microtime() . mt_rand() ),
		'oauth_timestamp' => time(),

		// We're using secret key signatures here.
		'oauth_signature_method' => 'HMAC-SHA1',
	);
	$signature = sign_request( 'GET', $url, $headerArr );
	$headerArr['oauth_signature'] = $signature;

	$header = array();
	foreach ( $headerArr as $k => $v ) {
		$header[] = rawurlencode( $k ) . '="' . rawurlencode( $v ) . '"';
	}
	$header = 'Authorization: OAuth ' . join( ', ', $header );

	$ch = curl_init();
	curl_setopt( $ch, CURLOPT_URL, $url );
	curl_setopt( $ch, CURLOPT_HTTPHEADER, array( $header ) );
	//curl_setopt( $ch, CURLOPT_SSL_VERIFYPEER, false );
	curl_setopt( $ch, CURLOPT_USERAGENT, $gUserAgent );
	curl_setopt( $ch, CURLOPT_HEADER, 1 );
	curl_setopt( $ch, CURLOPT_RETURNTRANSFER, 1 );
	curl_setopt( $ch, CURLOPT_FOLLOWLOCATION, 0 );
	$data = curl_exec( $ch );
	if ( !$data ) {
		header( "HTTP/1.1 $errorCode Internal Server Error" );
		echo 'Curl error: ' . htmlspecialchars( curl_error( $ch ) );
		exit(0);
	}

	echo 'Redirect response from Special:MyPage: <pre>' . htmlspecialchars( $data ) . '</pre>';
	echo '<hr>';
}

// ******************** WEBPAGE ********************

?><!DOCTYPE html>
<html dir="ltr" lang="en">
<head>
<link rel="stylesheet" type="text/css" href="parliamentstyle.css">
<script type="text/javascript">
document.write("\<script src='//ajax.googleapis.com/ajax/libs/jquery/1/jquery.min.js' type='text/javascript'>\<\/script>");
//document.write("\<script src='jquery.min.js' type='text/javascript'>\<\/script>"); //For local debugging
</script>
<script type="text/javascript" src="jscolor/jscolor.js"></script>
<script type='text/javascript'>
//Generate random color, based on http://stackoverflow.com/questions/1484506
function getRandomColor() {
        var letters = '0123456789ABCDEF'.split('');
        var color = ''; // In my case, I don't want the leading #
        for (var i = 0; i < 6; i++ ) {
                color += letters[Math.floor(Math.random() * 16)];
        }
        return color;
}

function CallDiagramScript(){
        // Create request string: this is the request that is passed to the python script.
        var requeststring="";
        // Create legend string: this is a Wikipedia markup legend that can be pasted into an article.
        var legendstring="";
        var legendname = "";
        var legendnum  = "";
        var partylist   = new Array();
        $( "input" ).each( function() { 
                if(this.name.match( /^Name/ )){
                  partylist[/[0-9]+$/.exec(this.name)[0]]={Name: this.value };
                }
                //Don't allow parties without delegates: if we have a number field, make the value at least 1.
                //It's a bit of a hack, but shouldn't be much of a limitation.
                if(this.name.match( /^Number/ )){
                  if(this.value < 1){this.value = 1;};
                  partylist[/[0-9]+$/.exec(this.name)[0]]['Num']=this.value;
                }
                //If we are processing a colour string, add a # before the hex values.
                if(this.name.match( /^Color/ )){
                  partylist[/[0-9]+$/.exec(this.name)[0]]['Color']=this.value;
                }
        });
        var arrayLength = partylist.length;
        for (var i = 1; i < arrayLength; i++) {
          if(partylist[i]) {
              requeststring += partylist[i]['Name'];
              requeststring += ', ';
              requeststring += partylist[i]['Num'];
              requeststring += ', ';
              requeststring += '#';
              requeststring += partylist[i]['Color'];
              if ( i < (arrayLength - 1)){ requeststring += '; '}
              if (partylist[i]['Num'] == 1){
                legendstring += "{{legend|#" + partylist[i]['Color'] +"|" + partylist[i]['Name'] +": 1 seat}} "
              }
              else {
                legendstring += "{{legend|#" + partylist[i]['Color'] +"|" + partylist[i]['Name'] +": "+ partylist[i]['Num']+" seats}} "
              }
              }
            }
            if(arrayLength){
        //Now post the request to the script which actually makes the diagram.
        $.ajax({
                type: "POST",
                url: "newarch.py",
                data: {inputlist: requeststring },
        }).done( function(data,status){
		data=data.trim();
                var postcontainer = document.getElementById("postcontainer"); //This will get the first node with id "postcontainer"
		while (postcontainer.hasChildNodes()) {
		    postcontainer.removeChild(postcontainer.lastChild);
		}
                //Now add the svg image to the page
                var img = document.createElement("img");
                img.src = data;
		img.setAttribute("id", "SVGdiagram");
                postcontainer.appendChild(img);
                //and a linebreak
                postcontainer.appendChild(document.createElement("br"));
                //Add a link with the new diagram
                var a = document.createElement('a');
                var linkText = document.createTextNode("Click to download your SVG diagram.");
                a.appendChild(linkText);
                a.title = "SVG diagram";
                a.href = data;
                a.download = data;
                postcontainer.appendChild(a);
                //and a linebreak
                postcontainer.appendChild(document.createElement("br"));
                //Now add the legend template text with the party names, colours and support.
                var newtext = document.createTextNode("Legend template for use in Wikipedia:");
                postcontainer.appendChild(newtext);
                postcontainer.appendChild(document.createElement("br"));
                newtext = document.createTextNode(legendstring);
                postcontainer.appendChild(newtext);
                postcontainer.appendChild(document.createElement("br"));
                postcontainer.appendChild(document.createElement("br"));
		//File upload name label
		var filenametitle=document.createElement('div');
		filenametitle.className = 'left greendiv';
		filenametitle.innerHTML = "Filename to upload:";
		postcontainer.appendChild(filenametitle);
		//File upload name input control
		var input=document.createElement('div');
		inputname = data.replace(/.*\//,'').replace(/.svg\s*$/,'');
		input.innerHTML = '<input class="right" type="text" name="' +  inputname + '"   value= "My_Parliament.svg" >';
		postcontainer.appendChild(input);
                //Button to add a link to upload the new diagram
		var uploadlinkbutton=document.createElement('div');
		uploadlinkbutton.className = 'button greenbutton';
		uploadlinkbutton.innerHTML = "Create link for direct upload to Wikimedia Commons.";
		uploadlinkbutton.setAttribute("onClick", 'makeUploadLink("'+ inputname +'", "'+ data +'", "' + legendstring + '")');
		postcontainer.appendChild(uploadlinkbutton);
                //and a linebreak
                postcontainer.appendChild(document.createElement("br"));
        });
        console.log(requeststring);
        console.log(legendstring);
      }
}

function addParty(){
        // Party list <div> where dynamic content will be placed
        var partylistcontainer = document.getElementById("partylistcontainer");
        //New party's number: one more than the largest party number so far:
        i=0;
        $( "div" ).each( function() { 
            if(this.id.match( /^party[0-9]+$/ )){
                i=Math.max(i, parseInt(/[0-9]+$/.exec(this.id)[0] ));
              }
          }
        )
        i++;
        var newpartydiv=document.createElement('div');
        newpartydiv.id="party" + i;
        partylistcontainer.appendChild(newpartydiv);
        //Party name label
        var partytitle=document.createElement('div');
        partytitle.className = 'left';
        partytitle.innerHTML = "Party " + i + " name";
        newpartydiv.appendChild(partytitle);
        //Party name input control
        var input=document.createElement('div');
        input.innerHTML = '<input class="right" type="text" name="Name' +  i + '"   value= "Party ' +  i + '" >'
        newpartydiv.appendChild(input);
        //Party support name tag
        var partysupport=document.createElement('div');
        partysupport.className = 'left';
        partysupport.innerHTML = "Party " + i + " delegates";
        newpartydiv.appendChild(partysupport);
        //Party support input control
        var input=document.createElement('div');
        input.innerHTML = '<input class="right" type="number" name="Number' +  i + '"   value= "' +  i + '" >';
        newpartydiv.appendChild(input);
        //Party color name tag
        var partycolor=document.createElement('div');
        partycolor.className = 'left';
        partycolor.innerHTML = "Party " + i + " color";
        newpartydiv.appendChild(partycolor);
        //Party color input control
        var input=document.createElement('div');
        input.innerHTML = '<input class="right color" type="text" name="Color' +  i + '" value= "' +  getRandomColor() + '" >'
        newpartydiv.appendChild(input);
        var delbutton=document.createElement('div');
        delbutton.className = 'button deletebutton';
        delbutton.innerHTML = "Delete party " + i;
        delbutton.setAttribute("onClick", "deleteParty(" + i + ")");
        newpartydiv.appendChild(delbutton);
          //Add a newline
        newpartydiv.appendChild(document.createElement("br"));
        //$( "input[name=Color" + i + "]").addClass('color'); /* no longer needed because I'm writing the innerHTML
        jscolor.init();
}
function makeUploadLink(inputname, linkdata, legendtext){
	var a = document.createElement('a');
	var fname="";
	//This is kind of dumb: I'm iterating through all the inputs on the
	//page to find any that match the name that's being called. FIXME
	$( "input" ).each( function() { 
			if(this.name == inputname){
				fname = this.value
			}
	});
	fname = fname.replace(/(.svg)*$/i, ".svg");
	var linkText = document.createTextNode("Click to upload "+fname+" to Wikimedia Commons");
	a.appendChild(linkText);
	//Now get today's date and format it suitably for use in Wikimedia Commons templates:
	var today = new Date();
	var DD = today.getDate();
	var MM = today.getMonth()+1;
	var YYYY = today.getFullYear();

	if(DD<10) {
		DD='0'+DD
	} 

	if(MM<10) {
		MM='0'+MM
	} 

	today = YYYY+'-'+MM+'-'+DD;
	//Now build the query URL that will be used to upload the image to Commons:
	a.href = document.URL.replace(/\?.*$/,'') + "?action=upload&uri=/data/project/parliamentdiagram/public_html/" + linkdata + "&filename=" + fname + "&pagecontent=" + encodeURIComponent( " {{PD-shape}} {{Information |description ="+ legendtext +" |date = "+today+" |source = [https://tools.wmflabs.org/parliamentdiagram/parliamentinputform.html Parliament diagram tool] |author = |other versions = }} [[Category:Election apportionment diagrams]]");
	a.setAttribute('target', '_blank');
	var SVGdiagram = document.getElementById("SVGdiagram"); //This will get the first node with id "SVGdiagram"
	var diagramparent = SVGdiagram.parentNode; //This will get the parent div that contains the diagram
	diagramparent.insertBefore(a, SVGdiagram.nextSibling); //Insert our new node after the diagram
	diagramparent.insertBefore(document.createElement("br"), SVGdiagram.nextSibling); //Insert a linebreak after the diagram
}
function deleteParty(i){
  var delparty = document.getElementById("party"+i);
  var partylistcontainer = document.getElementById("partylistcontainer");
  partylistcontainer.removeChild(delparty);
}
</script>
</head>
<body>
<div class=block id=header>
  <script type='text/javascript'>$( "#header" ).load( "header.html" )</script>
</div>
<div class="greendiv block" align="center">
  <b>Direct upload functionality in beta test</b>
</div>
<div class="block">
You can now directly upload arch-style diagrams to Wikimedia Commons under your own username with this new interface. Please submit bug reports and feature requests at the project's <a href="https://github.com/slashme/parliamentdiagram/issues/new">issue tracker</a>.
</div>
<div class=block>
  This is a tool to generate arch-shaped parliament diagrams.<br>
  <br>
  To use this tool, fill in the name and support of each party in the
  legislature, clicking "add party" whenever you need to add a new party.  Then
  click "Make my diagram", and a link will appear to your SVG diagram. You
  can then freely download and use the diagram, but to use the diagram in
  Wikipedia, you should upload it to Wikimedia Commons. You can now do this
  directly, by clicking on the green button to create an upload link. Click on
  the link and follow the instructions: it will upload the file under your
  username, including the list of parties in the file description.  This tool
  will automatically add your file to the 
  <a href="https://commons.wikimedia.org/wiki/Category:Election_apportionment_diagrams">election apportionment diagrams</a>
  category, but you should categorise it in more detail after uploading.<br>
<?php //Print the status of the last upload
if ( isset ($last_res )) { //if there is a "last result" from an attempted Commons upload
	if (isset($last_res->upload) && $last_res->upload->warnings ) {
		echo "<div class='warning'>";
		foreach ( $last_res->upload->warnings as $k => $v ) {
			if ( $k == 'exists' ) {
				echo "Warning: The file <a href=https://commons.wikimedia.org/wiki/File:".str_replace ( ' ' , '_' , $_GET['filename']).">".$_GET['filename']."</a> already exists.";
				if ( $last_res->upload->result != 'Success' ) {
					echo "If you have confirmed that you want to overwrite it, <a href=\"https://" . $_SERVER['HTTP_HOST'] . $_SERVER['REQUEST_URI']."&ignore=1\">click this dangerous link to upload a new version.</a> If you abuse this feature, you will be blocked.";
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
?></div>
</div>
<div class=block>
  <div id="partylistcontainer">
    <div id="party1">
      <div class="left">Party 1 name      </div><input class="right"       type="text"   name="Name1"   value= "Party 1" ><br>
      <div class="left">Party 1 delegates </div><input class="right"       type="number" name="Number1" value = 1        ><br>
      <div class="left">Party 1 color     </div><input class="right color" type="text"   name="Color1"  value= AD1FFF    ><br>
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
