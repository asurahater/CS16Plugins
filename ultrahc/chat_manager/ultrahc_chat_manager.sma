#include <amxmodx>
#include <amxmisc>
#include <reapi>
#include <sqlx>

#include <easy_http>

#define PLUGIN_NAME 		"ULTRAHC Chat manager"
#define PLUGIN_VERSION 	"0.5"
#define PLUGIN_AUTHOR 	"Asura"

// #define SHOW_PREFIXES_ON_LOAD // comment it to off prefix list to server console (better to comment for perfomance)

//-----------------------------------------
// You can change it
// -----------------------------------------
#define PLUGIN_CFG_NAME "ultrahc_chat_manager" // cfg name
#define PLUGIN_PREFIX_LIST_INI "ultrahc_prefix.ini" // prefix list

#define STEAM_USER_PREFIX "Steam" // If user is steam, it prefix will be use
//-----------------------------------------
// Change carefully
//-----------------------------------------
#define MAX_PREF_PLAYER_HAVE 4 // Max count of prefix player can have

//-----------------------------------------
// dont change
//-----------------------------------------
#define MAX_PREFIX_LENGTH 32 // 32 
#define COLOR_BUFFER 6
#define TEXT_LENGHT 128
#define MESSAGE_LENGHT 189

#define CVAR_CONTENT_SIZE 16

#define GetPrefix(%0,%1) __players_prefix_list[%0][%1]

#define DISCORD_API_KEY "VMN1wcutEIuczGaglb0Pg69Q8aW9XioBiC8icAbyq2k"

enum Color {
	_color_def = 0,
	_color_team,
	_color_green
}

enum id_cvars {
	_use_sql = 0,
	_sql_host,
	_sql_user,
	_sql_pass,
	_sql_db,

	_pref_opener,
	_pref_closer,
	_name_opener,
	_name_closer,
	
	_steam,
	_admin_see_all,
	_admin_see_all_flags,
	_alive_see_deads
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

new __cvars_list[id_cvars];
new __cvar_pref_opener[CVAR_CONTENT_SIZE], __cvar_pref_closer[CVAR_CONTENT_SIZE];
new __cvar_name_opener[CVAR_CONTENT_SIZE], __cvar_name_closer[CVAR_CONTENT_SIZE];
new __cvar_admin_see_all_flags[CVAR_CONTENT_SIZE];
new __cvar_show_steam, __cvar_admin_see_all, __cvar_alive_see_deads;
new saytext_msg_id;

new Trie:__steamid_prefs;
new Trie:__name_prefs;
new Trie:__flag_prefs;

new const __max_prefix_buf = MAX_PREFIX_LENGTH*MAX_PREF_PLAYER_HAVE+1;
new __players_prefix_list[MAX_PLAYERS][MAX_PREF_PLAYER_HAVE][MAX_PREFIX_LENGTH+1];

new __players_prefix_color[MAX_PLAYERS];

new bool:__is_preffile_loaded = false;

// new const __webhook_uri[] = "https://discord.com/api/webhooks/1284089649958092931/2yKTv04kp8quJ4RLIHYXIDFSw_a7J65pBv536Ov3ResFxVspoFGMNyuRANrjI6v9uHrT";
new const __webhook_uri[] = "http://localhost:8080/webhook";

// sql
new Handle:__sql_handle, __is_use_sql;
new __cvar_sql_host[32], __cvar_sql_user[32], __cvar_sql_pass[32], __cvar_sql_db[32];
new __sql_responce_info[256];
new __server_ip[32];

public plugin_init() {
	register_plugin(PLUGIN_NAME, PLUGIN_VERSION, PLUGIN_AUTHOR);
	
	register_clcmd("say", "OnSayClCmd");
	register_clcmd("say_team", "OnSayClCmd");
	
	__cvars_list[_use_sql] = create_cvar("ultrahc_use_sql", "0", _, "[1/0] use sql to save chat", true, 0.0, true, 1.0);
	__cvars_list[_sql_host] = create_cvar("ultrahc_sql_host", "127.0.0.1", _, "");
	__cvars_list[_sql_user] = create_cvar("ultrahc_sql_user", "", _, "");
	__cvars_list[_sql_pass] = create_cvar("ultrahc_sql_pass", "", _, "");
	__cvars_list[_sql_db] = create_cvar("ultrahc_sql_db", "", _, "");
	
	__cvars_list[_pref_opener] = create_cvar("ultrahc_pref_opener", "[", _, "prefix opener. [#prefix if '['");
	__cvars_list[_pref_closer] = create_cvar("ultrahc_pref_closer", "]", _, "prefix closer. #prefix] if ']'");
	
	__cvars_list[_name_opener] = create_cvar("ultrahc_name_opener", "", _, "name opener. <#name if '<'");
	__cvars_list[_name_closer] = create_cvar("ultrahc_name_closer", "", _, "name closer. #name> if '>'");
	
	__cvars_list[_steam] = create_cvar("ultrahc_show_steam", "1", _, "[1/0] show steam prefix", true, 0.0, true, 1.0);
	
	__cvars_list[_admin_see_all] = create_cvar("ultrahc_admin_see_all", "1", _, "[1/0] admin can see any chat", true, 0.0, true, 1.0);
	__cvars_list[_admin_see_all_flags] = create_cvar("ultrahc_admin_see_all", "d", _, "flags to see all chat. Also if alive can't see deads, admin's message will see everyone. See user.ini access flags", true, 0.0, true, 1.0);
	
	__cvars_list[_alive_see_deads] = create_cvar("ultrahc_alive_see_deads", "0", _, "[1/0] can alive see deads", true, 0.0, true, 1.0);
	
	saytext_msg_id = get_user_msgid("SayText");
	AutoExecConfig(true, PLUGIN_CFG_NAME);
	
	__steamid_prefs = TrieCreate();
	__name_prefs = TrieCreate();
	__flag_prefs = TrieCreate();
	
	get_user_ip(0, __server_ip, charsmax(__server_ip));
}

//-----------------------------------------

public plugin_end() {
	SQL_FreeHandle(__sql_handle);
}

//-----------------------------------------

public plugin_natives() {
	register_native("ultrahc_is_pref_file_load", "native_is_pref_file_load");
	register_native("ultrahc_get_prefix", "native_get_prefix");
	register_native("ultrahc_sql_chat_insert", "native_sql_chat_insert");
}

//-----------------------------------------

public bool:native_is_pref_file_load() {
	return __is_preffile_loaded;
}

public native_get_prefix(client_id, prefix_id, buffer[], buf_size) {

	enum {
		arg_client_id = 1,
		arg_prefix_id,
		arg_buffer,
		arg_buf_size
	}

	set_string(arg_buffer, GetPrefix(get_param(arg_client_id), get_param(arg_prefix_id)), get_param(arg_buf_size));
}

public native_sql_chat_insert(player_id, player_name[], player_name_size, player_team, channel[], message[], message_size, msg_color) {
	if(!__is_use_sql) return;
	
	enum {
		arg_player_id = 1,
		arg_player_name,
		arg_player_name_size,
		arg_player_team,
		arg_channel,
		arg_message,
		arg_message_size,
		arg_msg_color
	}
	new _player_name[MAX_NAME_LENGTH];
	new _channel[128];
	new _message[256];
	
	get_string(arg_player_name, _player_name, charsmax(_player_name));
	get_string(arg_channel, _channel, charsmax(_channel));
	get_string(arg_message, _message, charsmax(_message));
	
	SQLChatInsert(get_param(arg_player_id), _player_name, get_param(arg_player_name_size), get_param(arg_player_team), _channel, _message, get_param(arg_message_size), get_param(arg_msg_color));
}

//-----------------------------------------

public OnConfigsExecuted() {
	get_pcvar_string(__cvars_list[_sql_host], __cvar_sql_host, sizeof(__cvar_sql_host));
	get_pcvar_string(__cvars_list[_sql_user], __cvar_sql_user, sizeof(__cvar_sql_user));
	get_pcvar_string(__cvars_list[_sql_pass], __cvar_sql_pass, sizeof(__cvar_sql_pass));
	get_pcvar_string(__cvars_list[_sql_db], __cvar_sql_db, sizeof(__cvar_sql_db));
	
	get_pcvar_string(__cvars_list[_pref_opener], __cvar_pref_opener, CVAR_CONTENT_SIZE);
	get_pcvar_string(__cvars_list[_pref_closer], __cvar_pref_closer, CVAR_CONTENT_SIZE);
	
	get_pcvar_string(__cvars_list[_name_opener], __cvar_name_opener, CVAR_CONTENT_SIZE);
	get_pcvar_string(__cvars_list[_name_closer], __cvar_name_closer, CVAR_CONTENT_SIZE);
	
	get_pcvar_string(__cvars_list[_admin_see_all_flags], __cvar_admin_see_all_flags, CVAR_CONTENT_SIZE);
	
	__is_use_sql = get_pcvar_num(__cvars_list[_use_sql]);
	
	__cvar_show_steam = get_pcvar_num(__cvars_list[_steam]);
	__cvar_admin_see_all = get_pcvar_num(__cvars_list[_admin_see_all]);
	__cvar_alive_see_deads = get_pcvar_num(__cvars_list[_alive_see_deads]);
	
	if(__is_use_sql) {
		__sql_handle = SQL_MakeDbTuple(__cvar_sql_host, __cvar_sql_user, __cvar_sql_pass, __cvar_sql_db);
		SQL_SetCharset(__sql_handle, "utf8");
	}
	
	LoadPrefixList();
}

//-----------------------------------------

public client_putinserver(client_id) {
	GetPlayerPrefixes(client_id);
}

//-----------------------------------------

public GetPlayerPrefixes(client_id) {
	if(!__is_preffile_loaded) {
		set_task(2.0, "GetPlayerPrefixes", client_id);
		return;
	}
	
	new msg_color = 0;
	new msg_cmp_color = msg_color;
	new msg_str_color[8]; // comprasion

	new pref_count = 0;
	new prefix_arr[MAX_PREF_PLAYER_HAVE][MAX_PREFIX_LENGTH+1];
	
	if(__cvar_show_steam && is_user_steam(client_id)) {
		prefix_arr[pref_count] = STEAM_USER_PREFIX;
		pref_count++;
	}
	
	if(pref_count < MAX_PREF_PLAYER_HAVE && GetFlagPrefixes(client_id, prefix_arr, MAX_PREFIX_LENGTH, pref_count, msg_str_color, charsmax(msg_str_color))) {		
		msg_cmp_color = str_to_num(msg_str_color);
		if(msg_cmp_color > msg_color) {
			msg_color = msg_cmp_color;
		}
	}
	
	if(pref_count < MAX_PREF_PLAYER_HAVE && GetSteamPrefix(client_id, prefix_arr, MAX_PREFIX_LENGTH, pref_count, msg_str_color, charsmax(msg_str_color))) {
		msg_cmp_color = str_to_num(msg_str_color);
		if(msg_cmp_color > msg_color) {
			msg_color = msg_cmp_color;
		}
	}

	if(pref_count < MAX_PREF_PLAYER_HAVE && GetNamePrefix(client_id, prefix_arr, MAX_PREFIX_LENGTH, pref_count, msg_str_color, charsmax(msg_str_color))) {	
		msg_cmp_color = str_to_num(msg_str_color);
		if(msg_cmp_color > msg_color) {
			msg_color = msg_cmp_color;
		}
	}
	for(new i=0; i<pref_count; i++) {
		copy(__players_prefix_list[client_id][i], __max_prefix_buf, prefix_arr[i]);
	}
	
	__players_prefix_color[client_id] = msg_color;
}

//-----------------------------------------

public OnSayClCmd(owner_id) {
	new con_cmd_text[TEXT_LENGHT];

	// read a command. In this context it will be "say" or "say_team"
	read_argv(0, con_cmd_text, charsmax(con_cmd_text));
	new is_say_team = (con_cmd_text[3] == '_'); // "say_team"[3] = "_"
	
	// read an argument
	read_args(con_cmd_text, charsmax(con_cmd_text));
	remove_quotes(con_cmd_text);
	trim(con_cmd_text);
	
	if(con_cmd_text[0] == '/') return PLUGIN_HANDLED_MAIN; // command
	if(con_cmd_text[0] == '@') return PLUGIN_HANDLED_MAIN; // admin chat
	if(equali(con_cmd_text, "")) return PLUGIN_HANDLED; // empty string
	
	new is_owner_alive = is_user_alive(owner_id);
	new player_team_str[64];
	new owner_team = get_user_team(owner_id, player_team_str, charsmax(player_team_str));
	new channel_in_use = GetChannel(is_say_team, is_owner_alive, owner_team);
	
	new owner_name[MAX_NAME_LENGTH];
	get_user_name(owner_id, owner_name, charsmax(owner_name));
	
	new msg_color = __players_prefix_color[owner_id];
	
	new message_color[8];
	switch(msg_color) {
		case _color_team:
			message_color = "^3";
		case _color_green:
			message_color = "^4"
		default:
			message_color = "^1";
	}
	
	// Here a place to edit message
	new format_text[MESSAGE_LENGHT];
	new len = 0;
	// add team
	len += formatex(format_text[len], charsmax(format_text) - len, "^1%s", __saytext_teams[channel_in_use]);
	
	// add pref
	for(new i=0; i<MAX_PREF_PLAYER_HAVE; i++) {
		if(equali(GetPrefix(owner_id, i), "")) continue;
		len += formatex(format_text[len], charsmax(format_text) - len, "%s^4%s^1%s", __cvar_pref_opener, GetPrefix(owner_id, i), __cvar_pref_closer);
	}
	
	// add name. Add whitespace before last %s if u want whitespace between prefixes and name
	len += formatex(format_text[len], charsmax(format_text) - len, "%s^3%s^1%s", __cvar_name_opener, owner_name, __cvar_name_closer);
	// add text
	len += formatex(format_text[len], charsmax(format_text) - len, "%s: %s", message_color, con_cmd_text);
	
	// Message ready. Now will send it
	for(new i=1; i<MaxClients; i++) {
		if(!is_user_connected(i)) continue;
		if(owner_id == i) continue;
		
		if(!(__cvar_admin_see_all && has_flag(i, __cvar_admin_see_all_flags))) {
			if(is_say_team && (get_user_team(i) != owner_team)) continue; // say_team but not in same team
			if(!__cvar_alive_see_deads && !is_owner_alive && is_user_alive(i)) continue; // dead owner but not dead reciever. Here a place for put flag if alive can see deads
		}
		
		emessage_begin(MSG_ONE, saytext_msg_id, _, i);
		{
			ewrite_byte(owner_id);
			ewrite_string(format_text);
			ewrite_string("");
			ewrite_string("");
		} emessage_end();
		
	}
	
	emessage_begin(MSG_ONE, saytext_msg_id, _, owner_id);
	{
		ewrite_byte(owner_id);
		ewrite_string(format_text);
		ewrite_string("");
		ewrite_string("");
	} emessage_end();
	
	// database
	if(__is_use_sql) {
		SQLChatInsert(owner_id, owner_name, charsmax(owner_name), owner_team, __saytext_teams[channel_in_use], con_cmd_text, charsmax(con_cmd_text), msg_color)
	}
	
	// send to discord webhook
	new EzHttpOptions:options_id = ezhttp_create_options()
	
  ezhttp_option_set_header(options_id, "Authorization", DISCORD_API_KEY)
  ezhttp_option_set_header(options_id, "Content-Type", "application/json")
  
  new json[1024]; // json content. Free to modify
  new json_len = 0;
  
  json_len += formatex(json[json_len], charsmax(json) - json_len, "{");
	
	replace_string(owner_name, charsmax(owner_name), "^"", "'");
	replace_string(con_cmd_text, charsmax(con_cmd_text), "^"", "'");
  
  json_len += formatex(json[json_len], charsmax(json) - json_len, "^"nick^": ^"%s^",", owner_name);
  json_len += formatex(json[json_len], charsmax(json) - json_len, "^"message^": ^"%s^",", con_cmd_text);
  json_len += formatex(json[json_len], charsmax(json) - json_len, "^"team^": %i,", owner_team);
  json_len += formatex(json[json_len], charsmax(json) - json_len, "^"channel^": ^"%s^"", __saytext_teams[channel_in_use]);
  
  json_len += formatex(json[json_len], charsmax(json) - json_len, "}");

  ezhttp_option_set_body(options_id, json)

  ezhttp_post(__webhook_uri, "HTTPComplete", options_id)

	// to stop default say message, bc we have our own
	return PLUGIN_HANDLED_MAIN;
}

//-----------------------------------------

public HTTPComplete(EzHttpRequest:request_id) {
	if (ezhttp_get_error_code(request_id) != EZH_OK) {
      new error[64]
      ezhttp_get_error_message(request_id, error, charsmax(error))
      server_print("Response error: %s", error);
      return
  }

  new data[512]
  ezhttp_get_data(request_id, data, charsmax(data))
  server_print("Response data: %s", data)
}

//-----------------------------------------

public SQLChatInsert(owner_id, owner_name[], owner_name_size, owner_team, channel[], message[], message_size, msg_color) {
	new sql_request[2048];
	new time_now[64], date_now[64];
	new steam_id[64];
	new sql_len = 0;
	
	get_time("%H:%M:%S", time_now, sizeof(time_now));
	get_time("%Y-%m-%d", date_now, sizeof(date_now));
	
	new datetime[64];
	formatex(datetime, charsmax(datetime), "%s %s", date_now, time_now);
	
	get_user_authid(owner_id, steam_id, charsmax(steam_id));
	
	new sql_cols[] = "INSERT INTO chat (__server_ip, username, steam_id, datetime, team, channelmsg, prefix, message, msg_color) VALUES (";
	
	sql_len += formatex(sql_request[sql_len], charsmax(sql_request) - sql_len, sql_cols);
	// __server_ip
	sql_len += formatex(sql_request[sql_len], charsmax(sql_request) - sql_len, "'%s', ", __server_ip);
	// name
	replace_string(owner_name, owner_name_size, "'", "\'");
	sql_len += formatex(sql_request[sql_len], charsmax(sql_request) - sql_len, "'%s', ", owner_name);
	// steamid
	sql_len += formatex(sql_request[sql_len], charsmax(sql_request) - sql_len, "'%s', ", steam_id);
	// date_now
	sql_len += formatex(sql_request[sql_len], charsmax(sql_request) - sql_len, "'%s', ", datetime);
	// owner_team
	sql_len += formatex(sql_request[sql_len], charsmax(sql_request) - sql_len, "%i, ", (owner_team+1));
	// team channel
	sql_len += formatex(sql_request[sql_len], charsmax(sql_request) - sql_len, "'%s', ", channel);
	
	// prefixes
	sql_len += formatex(sql_request[sql_len], charsmax(sql_request) - sql_len, "^"{");
	
	for(new i=0; i<MAX_PREF_PLAYER_HAVE; i++) {
		if(equali(GetPrefix(owner_id, i), "")) continue;
		
		sql_len += formatex(sql_request[sql_len], charsmax(sql_request) - sql_len, "'%s'", GetPrefix(owner_id,i));
		
		if((i+1)<MAX_PREF_PLAYER_HAVE)
			sql_len += formatex(sql_request[sql_len], charsmax(sql_request) - sql_len, ", ");
	}
	sql_len += formatex(sql_request[sql_len], charsmax(sql_request) - sql_len, "}^", ");
	
	// message
	replace_string(message, message_size, "'", "\'");
	sql_len += formatex(sql_request[sql_len], charsmax(sql_request) - sql_len, "'%s', ", message);
	
	// message color
	sql_len += formatex(sql_request[sql_len], charsmax(sql_request) - sql_len, "%i);", (msg_color+1));
	
	SQL_ThreadQuery(__sql_handle, "SQLHandler", sql_request, __sql_responce_info, charsmax(__sql_responce_info));
}

//-----------------------------------------

public SQLHandler(failstate, query, error[], errnum, data[], size, queuetime) { 
	// failstate:
	// #define TQUERY_CONNECT_FAILED -2
	// #define TQUERY_QUERY_FAILED -1
	// #define TQUERY_SUCCESS 0
	if(failstate == TQUERY_CONNECT_FAILED) {
		server_print("===============================");
		server_print("	ultrahc_chat_manager: SQL CONNECTION FAILED", failstate);
		server_print("	%s", error);
		server_print("===============================");
	}
	else if(failstate == TQUERY_QUERY_FAILED) {
		server_print("===============================");
		server_print("	ultrahc_chat_manager: SQL QUERY FAILED", failstate);
		server_print("	%s", error);
		server_print("===============================");
	}
}

//-----------------------------------------

bool:GetSteamPrefix(player_id, prefix_arr[][], pref_size, &pref_count, pref_color[], pref_color_size) {
	new steam_id[MAX_AUTHID_LENGTH], value[MAX_PREFIX_LENGTH+10];
	new bool:is_done = false;
	
	new prefix[MAX_PREFIX_LENGTH+1];
	
	get_user_authid(player_id, steam_id, sizeof(steam_id));
	if(TrieKeyExists(__steamid_prefs, steam_id)) {
		TrieGetString(__steamid_prefs, steam_id, value, sizeof(value));
		
		parse(value, prefix, charsmax(prefix), pref_color, pref_color_size);
		copy(prefix_arr[pref_count], pref_size, prefix);
		pref_count++;
		is_done = true;
	}
	
	return is_done;
}

//-----------------------------------------

bool:GetNamePrefix(player_id, prefix_arr[][], pref_size, &pref_count, pref_color[], pref_color_size) {
	new name[MAX_NAME_LENGTH], value[MAX_PREFIX_LENGTH+10];
	new bool:is_done = false;
	
	new prefix[MAX_PREFIX_LENGTH+1];
	
	get_user_name(player_id, name, sizeof(name));
	if(TrieKeyExists(__name_prefs, name)) {
 		TrieGetString(__name_prefs, name, value, sizeof value);
 		
 		parse(value, prefix, charsmax(prefix), pref_color, pref_color_size);
		copy(prefix_arr[pref_count], pref_size, prefix);
		pref_count++;
		is_done = true;
 	}
 	
 	return is_done;
}

//-----------------------------------------

bool:GetFlagPrefixes(player_id, prefix_arr[][], pref_size, &pref_count, pref_color[], pref_color_size) {
	new TrieIter:iter = TrieIterCreate(__flag_prefs);
	new bool:is_done = false;
	new key[64];
	new value[MAX_PREFIX_LENGTH+10], prefix[MAX_PREFIX_LENGTH+1];
	new color_str[8], ret_color_str[8];
	new color = 0;
	
	while(!TrieIterEnded(iter)) {
		TrieIterGetKey(iter, key, sizeof(key));
		
		if(has_flag(player_id, key)) {
			if(pref_count >= MAX_PREF_PLAYER_HAVE) break;
		
			TrieIterGetString(iter, value, sizeof(value));
			parse(value, prefix, charsmax(prefix), color_str, charsmax(color_str));

			copy(prefix_arr[pref_count], pref_size, prefix);
			
			new compare_color = str_to_num(color_str);
			if(compare_color > color) {
				color = compare_color;
				copy(ret_color_str, charsmax(ret_color_str), color_str);
			}
			pref_count++;
			is_done = true;
		}
	
		TrieIterNext(iter);
	}
	TrieIterDestroy(iter);
	
	copy(pref_color, pref_color_size, ret_color_str);
	
 	return is_done;
}

//-----------------------------------------

LoadPrefixList() {
	new directory[128], path[128];
	
	// core.ini: amxx_configsdir addons/amxmodx/configs
	get_localinfo("amxx_configsdir", directory, charsmax(directory));
	formatex(path, charsmax(path), "%s/plugins/%s", directory, PLUGIN_PREFIX_LIST_INI);

	new file = fopen(path, "r");
	if(!file) {
		if(!CreateFile(path)) {
			server_print("");
			server_print("	ULTRAHC CHAT MESSANGER: Can't open prefix list	");
			server_print("");
			return;
		}
	}
		
	file = fopen(path, "r");
	
	new read_line[128];
	new pref_type[8], pref_param[64];
	new read_prefix[MAX_PREFIX_LENGTH+1], prefix_and_color[MAX_PREFIX_LENGTH+3];
	new pref_color[8];
	
	#if defined SHOW_PREFIXES_ON_LOAD
		server_print("==================================");
		server_print("ULTRAHC Chat Messanger v%s", PLUGIN_VERSION);
		server_print("Loaded prefixes");
	#endif
	
	new iter = 1;
	while(!feof(file)) {
		pref_type = "";
		pref_param = "";
		pref_color = "";
		
		// gets line
		fgets(file, read_line, sizeof(read_line));
		trim(read_line);
		
		parse(read_line, pref_type, sizeof(pref_type), pref_param, sizeof(pref_param), read_prefix, sizeof(read_prefix), pref_color, sizeof(pref_color));

		// let ; be comment
		if(!pref_type[0] || pref_type[0] == ';' || !pref_param[0] || !read_prefix[0]) continue;
		
		// dont sure it needs here
		if(!pref_color[0])
			pref_color[0] = 'd';
			
		switch(pref_color[0]) {
			case 't': {
				num_to_str(_:_color_team, pref_color, sizeof(pref_color));
			}
			case 'g': {
				num_to_str(_:_color_green, pref_color, sizeof(pref_color));
			}
			default: {
				num_to_str(_:_color_def, pref_color, sizeof(pref_color));
			}
		}
			
		// for saving it as a string to push it to trie(NO ARRAY NO ARRAY NO ARRAY NO ARRAY NO ARRAY NO ARRAY )
		formatex(prefix_and_color, sizeof(prefix_and_color), "^"%s^" %s", read_prefix, pref_color);
			
		switch(pref_type[0]) {
			case 's': { // steam
				#if defined SHOW_PREFIXES_ON_LOAD
					if(TrieSetString(__steamid_prefs, pref_param, prefix_and_color, false))
						server_print("	%i. [%s : %s : %s : %s]", iter, pref_type, pref_param, read_prefix, pref_color);
				#else
					TrieSetString(__steamid_prefs, pref_param, prefix_and_color, false)
				#endif
			}
			case 'n': { // name
				#if defined SHOW_PREFIXES_ON_LOAD
					if(TrieSetString(__name_prefs, pref_param, prefix_and_color, false))
						server_print("	%i. [%s : %s : %s : %s]", iter, pref_type, pref_param, read_prefix, pref_color);
				#else
					TrieSetString(__name_prefs, pref_param, prefix_and_color, false)
				#endif
			}
			case 'f': { // flag
				#if defined SHOW_PREFIXES_ON_LOAD
					if(TrieSetString(__flag_prefs, pref_param, prefix_and_color, false))
						server_print("	%i. [%s : %s : %s : %s]", iter, pref_type, pref_param, read_prefix, pref_color);
				#else
					TrieSetString(__flag_prefs, pref_param, prefix_and_color, false)
				#endif
			}
		}
		
		iter++;
	}
	#if defined SHOW_PREFIXES_ON_LOAD
		server_print("==================================");
	#endif
	fclose(file);
	
	__is_preffile_loaded = true;
}

//-----------------------------------------

CreateFile(path[]) {
	new file = fopen(path, "w");
	if(file) {
		// guide
		fputs(file, "; [type] [param] [prefix] [optional: color]^n");
		fputs(file, "; [type]: n by nickname, s by steamid, f by flags^n");
		fputs(file, "; [param]: nickname, steamid or flags^n");
		fputs(file, "; [prefix]: you can use ^"for multiline prefix^"^n");
		fputs(file, "; [color]: color of message. empty = default^n");
		fputs(file, "; d for default^n");
		fputs(file, "; t for team color (red/blue)^n");
		fputs(file, "; g for freen^n");
		fputs(file, "; example:^n");
		fputs(file, "; f a AdminPrefix g^n");
		fputs(file, "; n playerNickname ^"Multiline prefix^" g^n");
		
		fclose(file);
	}
	// after fclose, file variable still have magical numbers
	return file;
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
		// channel = (!is_player_alive) ? 1 : (player_team == _:CS_TEAM_SPECTATOR ? 7 : 0);
	}
	
	return channel;
}