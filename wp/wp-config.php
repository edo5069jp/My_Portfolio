<?php
/**
 * WordPress の基本設定
 *
 * このファイルは、MySQL、テーブル接頭辞、秘密鍵、ABSPATH の設定を含みます。
 * より詳しい情報は {@link http://wpdocs.sourceforge.jp/wp-config.php_%E3%81%AE%E7%B7%A8%E9%9B%86 
 * wp-config.php の編集} を参照してください。MySQL の設定情報はホスティング先より入手できます。
 *
 * このファイルはインストール時に wp-config.php 作成ウィザードが利用します。
 * ウィザードを介さず、このファイルを "wp-config.php" という名前でコピーして直接編集し値を
 * 入力してもかまいません。
 *
 * @package WordPress
 */

// 注意: 
// Windows の "メモ帳" でこのファイルを編集しないでください !
// 問題なく使えるテキストエディタ
// (http://wpdocs.sourceforge.jp/Codex:%E8%AB%87%E8%A9%B1%E5%AE%A4 参照)
// を使用し、必ず UTF-8 の BOM なし (UTF-8N) で保存してください。

// ** MySQL 設定 - この情報はホスティング先から入手してください。 ** //
/** WordPress のためのデータベース名 */
define('DB_NAME', 'shinjiedou_myportfolio');

/** MySQL データベースのユーザー名 */
define('DB_USER', 'shinjiedou');

/** MySQL データベースのパスワード */
define('DB_PASSWORD', 'W38a8faejaf8382q');

/** MySQL のホスト名 */
define('DB_HOST', 'mysql56s-38.kagoya.net');

/** データベースのテーブルを作成する際のデータベースの文字セット */
define('DB_CHARSET', 'utf8mb4');

/** データベースの照合順序 (ほとんどの場合変更する必要はありません) */
define('DB_COLLATE', '');

/**#@+
 * 認証用ユニークキー
 *
 * それぞれを異なるユニーク (一意) な文字列に変更してください。
 * {@link https://api.wordpress.org/secret-key/1.1/salt/ WordPress.org の秘密鍵サービス} で自動生成することもできます。
 * 後でいつでも変更して、既存のすべての cookie を無効にできます。これにより、すべてのユーザーを強制的に再ログインさせることになります。
 *
 * @since 2.6.0
 */
define('AUTH_KEY',         'Y+4W`T||?P=~V(rD.81_iJt8K5{wD}XPRyXOnd/)GL^N>X.`13y3oex!MiaemZzn');
define('SECURE_AUTH_KEY',  '_,:$JD9hY=?$UNUH-1wCHPr.PU eE_j| <B?#xw~p);kl-Bh#xB- lL?.cif5,#8');
define('LOGGED_IN_KEY',    'VJ@U|EG 5c9|5Kog|#4{1_.UFPc8!~zyq8WBk%uf1K;t)ZWX<.eP(HA:Klc~v$D}');
define('NONCE_KEY',        'd%i`cOfUMuug%_[vyB2PZ+F>rz8[=$*y+rM2$/{h;P{7mR6Iy+T.cM2wD;AnLB ^');
define('AUTH_SALT',        'w,I|._^<)k%4gR2D+yl#8c.RZ48xOK?F3&5VgGl-:ix*FERBSQe9;gqk]gP^sP!+');
define('SECURE_AUTH_SALT', 'g8P%5D-/h;?n8/ho7t1T9(Z%^FBZr*`/wE~13!8~s9j|/Shz:`9j71fsC~`%=GU|');
define('LOGGED_IN_SALT',   '5KUKZ=^YG,nI+{/N(Z+pu&-%w6%q.V`RiY8M?-f@/T[:2+[N+2[ )L7$!16r<sOb');
define('NONCE_SALT',       '.Sk&?v%!;-m&olbh # K63nO|Szchrzy|XV67o#/7VU^xqn]/Dl&fz-3X#Is=-NN');

/**#@-*/

/**
 * WordPress データベーステーブルの接頭辞
 *
 * それぞれにユニーク (一意) な接頭辞を与えることで一つのデータベースに複数の WordPress を
 * インストールすることができます。半角英数字と下線のみを使用してください。
 */
$table_prefix  = 'wp_';

/**
 * 開発者へ: WordPress デバッグモード
 *
 * この値を true にすると、開発中に注意 (notice) を表示します。
 * テーマおよびプラグインの開発者には、その開発環境においてこの WP_DEBUG を使用することを強く推奨します。
 */
define('WP_DEBUG', false);

/* 編集が必要なのはここまでです ! WordPress でブログをお楽しみください。 */

/** Absolute path to the WordPress directory. */
if ( !defined('ABSPATH') )
	define('ABSPATH', dirname(__FILE__) . '/');

/** Sets up WordPress vars and included files. */
require_once(ABSPATH . 'wp-settings.php');
