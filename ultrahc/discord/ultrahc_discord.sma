#include <amxmodx>
#include <easy_http>

#define PLUGIN_NAME 		"ULTRAHC Discord hooks"
#define PLUGIN_VERSION 	"0.1"
#define PLUGIN_AUTHOR 	"Asura"

//-----------------------------------------

#define PLUGIN_CFG_NAME "ultrahc_discord" // cfg name
#define DISCORD_PREFIX "[^4Discord^1]"

//-----------------------------------------

#define TEXT_LENGHT 128

enum ECvarsList {
	_webhook_token,
	_webhook_url
}

// U can change it. But be carefully
new const __saytext_teams[][] = {
	"", // All chat
	"(DEAD)", // All chat, but sender is dead
	"(T)", 
	"(DEAD)(T)",
	"(CT)",
	"(DEAD)(CT)",
	"(S)", // Spec team
	"(SPEC)" // All chat, but sender in spec team
}

new __cvar_str_list[ECvarsList][32];

public plugin_init() {
	register_plugin(PLUGIN_NAME, PLUGIN_VERSION, PLUGIN_AUTHOR);
	
	register_clcmd("say", "SayMessageHandler");
	register_clcmd("say_team", "SayMessageHandler");
	
	register_concmd("ultrahc_ds_send_msg", "HookMsgFromDs");
	
	bind_pcvar_string(create_cvar("ultrahc_ds_webhook_token", ""), __cvar_str_list[_webhook_token], 32);
	bind_pcvar_string(create_cvar("ultrahc_ds_webhook_url", ""), __cvar_str_list[_webhook_url], 32);
	
	AutoExecConfig(true, PLUGIN_CFG_NAME);
}

//-----------------------------------------

public SayMessageHandler(owner_id) {
	new con_cmd_text[TEXT_LENGHT];

	// read a command. In this context it will be "say" or "say_team"
	read_argv(0, con_cmd_text, charsmax(con_cmd_text));
	new is_say_team = (con_cmd_text[3] == '_'); // "say_team"[3] = "_"
	
	// read an argument
	read_args(con_cmd_text, charsmax(con_cmd_text));
	remove_quotes(con_cmd_text);
	trim(con_cmd_text);
	
	if(con_cmd_text[0] == '/') return PLUGIN_CONTINUE; // command
	if(con_cmd_text[0] == '@') return PLUGIN_CONTINUE; // admin chat
	if(equali(con_cmd_text, "")) return PLUGIN_CONTINUE; // empty string
	
	new is_owner_alive = is_user_alive(owner_id);
	new owner_team = get_user_team(owner_id);
	new channel_in_use = GetChannel(is_say_team, is_owner_alive, owner_team);
	
	new owner_name[MAX_NAME_LENGTH];
	get_user_name(owner_id, owner_name, charsmax(owner_name));


	// send to discord webhook
	new EzHttpOptions:options_id = ezhttp_create_options()
	
	ezhttp_option_set_header(options_id, "Authorization", __cvar_str_list[_webhook_token])
	ezhttp_option_set_header(options_id, "Content-Type", "application/json")
  
	new json[1024];
	new json_len = 0;
  
	json_len += formatex(json[json_len], charsmax(json) - json_len, "{");
	
	replace_string(owner_name, charsmax(owner_name), "^"", "'");
	replace_string(con_cmd_text, charsmax(con_cmd_text), "^"", "'");
	
	new steam_id[64];
	get_user_authid(owner_id, steam_id, charsmax(steam_id));
  
	json_len += formatex(json[json_len], charsmax(json) - json_len, "^"nick^": ^"%s^",", owner_name);
	json_len += formatex(json[json_len], charsmax(json) - json_len, "^"message^": ^"%s^",", con_cmd_text);
	json_len += formatex(json[json_len], charsmax(json) - json_len, "^"team^": %i,", owner_team);
	json_len += formatex(json[json_len], charsmax(json) - json_len, "^"channel^": ^"%s^",", __saytext_teams[channel_in_use]);
	json_len += formatex(json[json_len], charsmax(json) - json_len, "^"steam_id^": ^"%s^"", steam_id);
  
	json_len += formatex(json[json_len], charsmax(json) - json_len, "}");

	ezhttp_option_set_body(options_id, json)

	ezhttp_post(__cvar_str_list[_webhook_url], "HTTPComplete", options_id)
	
	return PLUGIN_CONTINUE;
}

//-----------------------------------------

public HTTPComplete(EzHttpRequest:request_id) {
	if (ezhttp_get_error_code(request_id) != EZH_OK) {
      new error[64];
      ezhttp_get_error_message(request_id, error, charsmax(error));
      server_print("Response error: %s", error);
      return;
  }

	new data[512];
	ezhttp_get_data(request_id, data, charsmax(data));
	server_print("Response data: %s", data);
}

//-----------------------------------------

public HookMsgFromDs() {
	new str[64];
	read_args(str, charsmax(str));
	
	new author[64];
	new msg[128];
	parse(str, author, charsmax(author), msg, charsmax(msg));

	client_print_color(0, print_team_blue, "%s ^3%s^1 : ^4%s", DISCORD_PREFIX, author, msg);
}

//-----------------------------------------

GetChannel(is_say_team, is_player_alive, player_team) {
	new channel;
	if(is_say_team) {
		switch(player_team) {
			case CS_TEAM_T:
				channel = (is_player_alive) ? 2 : 3;
			case CS_TEAM_CT:
				channel = (is_player_alive) ? 4 : 5;
			default:
				channel = 6;
		}	
	} else {
		channel = (player_team == _:CS_TEAM_SPECTATOR) ? 7 : (!is_player_alive ? 1 : 0);
	}
	
	return channel;
}