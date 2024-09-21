#include <amxmodx>
#include <ultrahc_chat_manager>
#include <easy_http>
#include <sqlx>

#tryinclude <map_manager>

#define PLUGIN_NAME 		"ULTRAHC Discord hooks"
#define PLUGIN_VERSION 	"0.3"
#define PLUGIN_AUTHOR 	"Asura"

//-----------------------------------------

#define PLUGIN_CFG_NAME "ultrahc_discord" // cfg name
#define DISCORD_PREFIX "[^4Discord^1]"

#define MESSAGEMODE_NAME "adminchat"

//-----------------------------------------

#define TEXT_LENGHT 128

#define CVARS_LENGTH 128

enum ECvarsList {
	_webhook_token,
	_webhook_url,
	
	_sql_host,
	_sql_user,
	_sql_pass,
	_sql_db
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

new __cvar_str_list[ECvarsList][CVARS_LENGTH];

new Handle:__sql_handle;

// new big_string[5000];

public plugin_init() {
	register_plugin(PLUGIN_NAME, PLUGIN_VERSION, PLUGIN_AUTHOR);
	
	register_clcmd("say", "SayMessageHandler");
	register_clcmd("say_team", "SayMessageHandler");
	
	register_clcmd(MESSAGEMODE_NAME, "MessageModeCallback");
	
	register_concmd("ultrahc_ds_send_msg", "HookMsgFromDs");
	register_concmd("ultrahc_ds_change_map", "HookChangeMapCmd");
	register_concmd("ultrahc_ds_kick_player", "HookKickPlayerCmd");
	
	register_concmd("ultrahc_ds_get_info", "HookGetinfoCmd");
	
	#if defined _map_manager_core_included
		register_concmd("ultrahc_ds_reload_map_list", "HookReloadMapList");
		mapm_block_load_maplist();
	#endif
	
	bind_pcvar_string(create_cvar("ultrahc_ds_webhook_token", ""), __cvar_str_list[_webhook_token], CVARS_LENGTH);
	bind_pcvar_string(create_cvar("ultrahc_ds_webhook_url", ""), __cvar_str_list[_webhook_url], CVARS_LENGTH);
	
	bind_pcvar_string(create_cvar("ultrahc_ds_sql_host", ""), __cvar_str_list[_sql_host], CVARS_LENGTH);
	bind_pcvar_string(create_cvar("ultrahc_ds_sql_user", ""), __cvar_str_list[_sql_user], CVARS_LENGTH);
	bind_pcvar_string(create_cvar("ultrahc_ds_sql_pass", ""), __cvar_str_list[_sql_pass], CVARS_LENGTH);
	bind_pcvar_string(create_cvar("ultrahc_ds_sql_db", ""), __cvar_str_list[_sql_db], CVARS_LENGTH);
	
	AutoExecConfig(true, PLUGIN_CFG_NAME);
}

//-----------------------------------------

public OnConfigsExecuted() {
	__sql_handle = SQL_MakeDbTuple(__cvar_str_list[_sql_host], __cvar_str_list[_sql_user], __cvar_str_list[_sql_pass], __cvar_str_list[_sql_db]);
	SQL_SetCharset(__sql_handle, "utf8");
}

//-----------------------------------------

public client_putinserver(client_id) {
	if(is_user_bot(client_id)) return;

	set_task(1.0, "ClientPutInhandler", client_id);
}

//-----------------------------------------
public ClientPutInhandler(client_id) {
	if(!ultrahc_is_pref_file_load()) {
		set_task(1.0, "ClientPutInhandler", client_id);
		return;
	}
	set_task(2.0, "GetMeTime", client_id);	
}
	
public GetMeTime(client_id) {
	new steam_id[32];
	get_user_authid(client_id, steam_id, charsmax(steam_id));
	
	new sql_request[512];
	formatex(sql_request, charsmax(sql_request), "SELECT ds_display_name FROM users WHERE steam_id = '%s'", steam_id);
	
	new data[8];
	num_to_str(client_id, data, charsmax(data));
	
	SQL_ThreadQuery(__sql_handle, "SQLHandler", sql_request, data, charsmax(data));
}

public SQLHandler(failstate, Handle:query, error[], errnum, data[], size, queuetime) {
	// failstate:
	// #define TQUERY_CONNECT_FAILED -2
	// #define TQUERY_QUERY_FAILED -1
	// #define TQUERY_SUCCESS 0
	if(failstate == TQUERY_CONNECT_FAILED) {
		server_print("===============================");
		server_print("	ultrahc_discord: SQL CONNECTION FAILED", failstate);
		server_print("	%s", error);
		server_print("===============================");
		return;
	}
	else if(failstate == TQUERY_QUERY_FAILED) {
		server_print("===============================");
		server_print("	ultrahc_discord: SQL QUERY FAILED", failstate);
		server_print("	%s", error);
		server_print("===============================");
		return;
	}

	if(SQL_NumResults(query) == 0) return;
	
	new username[64];
	SQL_ReadResult(query, 0, username, charsmax(username));
	
	new client_id = str_to_num(data);

	ultrahc_add_prefix(client_id, username, 4);
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
	
	if(con_cmd_text[0] == '/') {
		
		new match = contain(con_cmd_text, "/notify");
		if(match == 0) SetMsgModeNotify(owner_id);
	
		return PLUGIN_CONTINUE;
	}
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
  
	json_len += formatex(json[json_len], charsmax(json) - json_len, "^"type^": ^"message^",");
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

public SetMsgModeNotify(owner_id) {
	new msgmode[64];
	formatex(msgmode, charsmax(msgmode), "messagemode %s", MESSAGEMODE_NAME);
	client_cmd(owner_id, msgmode);
}

//-----------------------------------------

public MessageModeCallback(owner_id) {
	if(!is_user_connected(owner_id)) return PLUGIN_HANDLED;

	new message[128];
	read_args(message, charsmax(message));
	
	remove_quotes(message);
	trim(message);
	
	if(!message[0]) return PLUGIN_HANDLED;
	
	new owner_name[MAX_NAME_LENGTH];
	get_user_name(owner_id, owner_name, charsmax(owner_name));
	
	client_print(owner_id, print_chat, "Сообщение отправлено");
	
	// send to discord webhook
	new EzHttpOptions:options_id = ezhttp_create_options()
	
	ezhttp_option_set_header(options_id, "Authorization", __cvar_str_list[_webhook_token])
	ezhttp_option_set_header(options_id, "Content-Type", "application/json")
  
	new json[1024];
	new json_len = 0;
  
	json_len += formatex(json[json_len], charsmax(json) - json_len, "{");
	
	replace_string(owner_name, charsmax(owner_name), "^"", "'");
	replace_string(message, charsmax(message), "^"", "'");
	
	new steam_id[64];
	get_user_authid(owner_id, steam_id, charsmax(steam_id));
  
	json_len += formatex(json[json_len], charsmax(json) - json_len, "^"type^": ^"notify^",");
	json_len += formatex(json[json_len], charsmax(json) - json_len, "^"nick^": ^"%s^",", owner_name);
	json_len += formatex(json[json_len], charsmax(json) - json_len, "^"message^": ^"%s^",", message);
	json_len += formatex(json[json_len], charsmax(json) - json_len, "^"steam_id^": ^"%s^"", steam_id);
  
	json_len += formatex(json[json_len], charsmax(json) - json_len, "}");

	ezhttp_option_set_body(options_id, json)

	ezhttp_post(__cvar_str_list[_webhook_url], "HTTPComplete", options_id)
	
	return PLUGIN_HANDLED;
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

public HookChangeMapCmd() {
	new map[32];
	read_args(map, charsmax(map));
	
	trim(map);
	remove_quotes(map);
	
	if(!map[0])
		server_cmd("restart");
	else
		server_cmd("amx_map %s", map);
}

//-----------------------------------------

public HookGetinfoCmd() {
	// send to discord webhook
	new EzHttpOptions:options_id = ezhttp_create_options()
	
	ezhttp_option_set_header(options_id, "Authorization", __cvar_str_list[_webhook_token])
	ezhttp_option_set_header(options_id, "Content-Type", "application/json")
  
	new json[1024];
	new json_len = 0;
  
	json_len += formatex(json[json_len], charsmax(json) - json_len, "{");
	
	new map_name[32];
	get_mapname(map_name, charsmax(map_name));
  
	json_len += formatex(json[json_len], charsmax(json) - json_len, "^"type^":^"info^",");
	json_len += formatex(json[json_len], charsmax(json) - json_len, "^"map^":^"%s^",", map_name);
	
	json_len += formatex(json[json_len], charsmax(json) - json_len, "^"current_players^":[");
	
	new players[MAX_PLAYERS], num;
	get_players(players, num);
	
	for(new i=0; i < num; i++) {
		new id = players[i];
	
		if(!is_user_connected(id)) continue;
		
		new user_name[MAX_NAME_LENGTH];
		get_user_name(id, user_name, charsmax(user_name));
		
		new user_auth[64];
		get_user_authid(id, user_auth, charsmax(user_auth));
		
		replace_string(user_name, charsmax(user_name), "^"", "'");
		
		new user_frags = get_user_frags(id);
		new user_deaths = get_user_deaths(id);
		new user_team = get_user_team(id);
		
		json_len += formatex(json[json_len], charsmax(json) - json_len, "{^"name^":^"%s^",", user_name);
		json_len += formatex(json[json_len], charsmax(json) - json_len, "^"steam_id^":^"%s^",", user_auth);
		json_len += formatex(json[json_len], charsmax(json) - json_len, "^"stats^":[%i, %i, %i]}", user_frags, user_deaths, user_team);
		
		if(i < num-1) {
			json_len += formatex(json[json_len], charsmax(json) - json_len, ",");
		}
	}
	
	json_len += formatex(json[json_len], charsmax(json) - json_len, "],");
	
	json_len += formatex(json[json_len], charsmax(json) - json_len, "^"max_players^":%i", MaxClients);
  
	json_len += formatex(json[json_len], charsmax(json) - json_len, "}");

	ezhttp_option_set_body(options_id, json)

	ezhttp_post(__cvar_str_list[_webhook_url], "HTTPComplete", options_id)
}

//-----------------------------------------

public HookKickPlayerCmd() {
	new cmd_text[150];
	read_args(cmd_text, charsmax(cmd_text));
	
	new player_to_kick[32];
	new reason[128];
	parse(cmd_text, player_to_kick, charsmax(player_to_kick), reason, charsmax(reason));
	
	server_cmd("amx_kick ^"%s^" ^"%s^"", player_to_kick, reason);
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

#if defined _map_manager_core_included
	new file_name[] = "maps_ultrahc.ini";

	public plugin_cfg() {
		mapm_load_maplist(file_name)
	}

	public HookReloadMapList() {
		new sql_request[512] = "SELECT map_name, min_players, max_players, priority FROM maps WHERE activated=1";
		
		SQL_ThreadQuery(__sql_handle, "SQLHandlerForMapList", sql_request);
	}

	public SQLHandlerForMapList(failstate, Handle:query, error[], errnum, data[], size, queuetime) {
		new file_path[256]; 
		get_localinfo("amxx_configsdir", file_path, charsmax(file_path));
		formatex(file_path, charsmax(file_path), "%s/%s", file_path, file_name);
		
		new file = fopen(file_path, "w");
		
		if(!file) {
			server_print("ULTRAHC_DISCORD: Can't create/open map list");
			return;
		}
		
		while(SQL_MoreResults(query)) {
			new map_name[MAPNAME_LENGTH];
			SQL_ReadResult(query, 0, map_name, charsmax(map_name));
			
			new min_players = SQL_ReadResult(query, 1);
			new max_players = SQL_ReadResult(query, 2);
			new priority = SQL_ReadResult(query, 3);
			
			new str_to_put[128];
			
			formatex(str_to_put, charsmax(str_to_put), "%s %i %i %i^n", map_name, min_players, max_players, priority);
			
			fputs(file, str_to_put);
		
			SQL_NextRow(query);
		}
		
		fclose(file);
	}

#endif

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