#include <amxmodx>

public plugin_init() {
	// register_concmd("ultrahc_ds_get_players", "TESTCallback");
	// register_concmd("ultrahc_ds_get_map", "TESTCallback");
	
	register_concmd("ultrahc_ds_send_msg", "SendMessage");
}

public SendMessage() {
	new str[64];
	read_args(str, charsmax(str));
	
	new author[64];
	new msg[128];
	parse(str, author, charsmax(author), msg, charsmax(msg));

	client_print_color(0, print_team_blue, "[^4DISCORD^1] ^3%s^1 : ^4%s", author, msg);
}

public TESTCallback() {
	new str[64];
	read_args(str, charsmax(str));

	server_print(str);
}