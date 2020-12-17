<?php 
header("X-FRAME-OPTIONS: DENY");

$whitelist = array("submit","mail","subject","body");
$request = array();
foreach ($whitelist as $word){
	$request[$word] = null;
	if (isset($_REQUEST[$word])){
		$request[$word] = $_REQUEST[$word];
	}
}

if(isset($_REQUEST['submit'])){
mb_language("japanese");
mb_internal_encoding("UTF-8");

$action = $_POST['submit'];
$mail = htmlspecialchars($_POST['mail']);
$subject = htmlspecialchars($_POST['subject']);
$subject .= "【お問い合わせがありました】";
$body = htmlspecialchars($_POST['body']);

//受信先
$to = 'shinji5069re@gmail.com';
$message = '[mail]'.$mail."\n";
$message .= '[本文]'.$body."\n";
$header = 'From: '.$mail;

if($action === "LET'S GO!"){
	$status = mb_send_mail($to, $subject, $body, $header);

// エラーチェック
	if (isset($request["send"])){
		if ($request["email"] == "") {
			$page_error = "メールアドレスを入力して下さい。\n";
		}
		if ($page_error == ""){
	if (!preg_match('/^([a-zA-Z0-9\.\_\-\+\?\#\&\%])*@([a-zA-Z0-9\_\-])+([a-zA-Z0-9\.\_\-]+)+$/', $request["email"])){
		$page_error = "メールアドレスを正しく入力してください\n";
			}
		}
	}

if($status){
	echo "メールの送信に成功しました！";
} else {
	echo "メールの送信に失敗しました。";
}
}
}

 ?>