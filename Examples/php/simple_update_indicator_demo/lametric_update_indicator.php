<?php
# Copyright (c) 2016 Dmytro Baryskyy
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.


# This is your indicator app's push url and access token. 
# Get these from your app's details page on https://developer.lametric.com
define ('URL', '<your push url>');
define ('ACCESS_TOKEN', '<your access token>');

if ($argc == 1) {
    echo "\nThis is PHP demo app that sends text message to LaMetric's indocator app.\n";
    echo "Please edit this script first!\n\n";
    echo "Usage example:\n";
    echo '    php '.$argv[0].' -tHello -tWorld';
    echo "\n\nQuestions? Contact us at support@lametric.com\n\n";
    exit(0);
}

// Reading options from command line
$options = getopt("t:");

// Extracting texts
$texts = $options["t"];

// Building JSON that is going to be sent
// It must be like this:
// {
//    "frames": [
//       {  "icon":<icon_id>, "text":"<your text>" }
//    ] 
// }
//
// You can find icon id at https://developer.lametric.com/icons (under each icon in form #<id>)
// Put "i<id>" in json if you want static icon, or "a<id>" for animated (for example a2867 or i2867) 
// Icon can also be a base64 binary data in form "data:image/png;base64,<base64 encoded binary>"

$data = '{ "frames" : [';
if (is_array($texts)) {
    foreach ($texts as $text) {
        $data = $data.'{ "icon":"a2867","text":"'.$text.'"},';
    }
} else {
    $data = $data.'{"icon":"a2867", "text":"'.$texts.'"},';
} 
$data = rtrim($data,",");
$data = $data.']}';

// Building HTTP request
// use key 'http' even if you send the request to https://...
$options = array(
    'http' => array(
        'header'  => "Content-Type: application/json",
        'header'  => "X-Access-Token: ".ACCESS_TOKEN,
        'method'  => 'POST',
        'content' => $data
    )
);

// Sending request
$context  = stream_context_create($options);
$result = file_get_contents(URL, false, $context);

// Processing result
if ($result === FALSE) { 
    echo "ERROR.\n";
}
else {
    echo "OK.\n";
}

// That's it!
?>