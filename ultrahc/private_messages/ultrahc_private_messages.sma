#include <amxmodx>
#include <ultrahc_chat_manager>

#define PLUGIN_NAME "ULTRAHC Private messages"
#define PLUGIN_VERSION "0.1"
#define PLUGIN_AUTHOR "Asura"

#define MESSAGEMODE_NAME "private"

#define SetTarget(%0,%1) __player_pm_target[%0]=%1
#define GetTarget(%0) __player_pm_target[%0]

enum {
	private_from = 0,
	private_to
}

enum ePcvarsList {
	_save_db,
	_name_coeff
}

new __player_pm_target[MAX_PLAYERS];
new __pcvars_list[ePcvarsList];

new float:__sim_coeff;
new __save_db;

public plugin_init() {
	register_plugin(PLUGIN_NAME, PLUGIN_VERSION, PLUGIN_AUTHOR);
	
	__pcvars_list[_save_db] = create_cvar("ultrahc_private_save_db", "0", _, "[1/0] Save private messages to db", true, 0.0, true, 1.0);
	__pcvars_list[_name_coeff] = create_cvar("ultrahc_private_name_coeff", "0.3", _, "[0.0 to 1.0] Coeff of similarity for pm menu", true, 0.0, true, 1.0);
	
	bind_pcvar_float(__pcvars_list[_save_db], __save_db);
	bind_pcvar_float(__pcvars_list[_name_coeff], __sim_coeff);

	register_clcmd("say", "SayPMCallback");
	register_clcmd("say_team", "SayPMCallback");
	
	register_clcmd(MESSAGEMODE_NAME, "MessageModeCallback");
	
	AutoExecConfig(_, "ultrahc_private_messages");
}

//-----------------------------------------------

public MessageModeCallback(owner_id) {
	if(!is_user_connected(GetTarget(owner_id))) return PLUGIN_HANDLED;

	new message[128];
	read_args(message, charsmax(message));
	
	remove_quotes(message);
	trim(message);
	
	if(!message[0]) return PLUGIN_HANDLED;
	
	new target_name[MAX_NAME_LENGTH], owner_name[MAX_NAME_LENGTH];
	get_user_name(GetTarget(owner_id), target_name, charsmax(target_name));
	get_user_name(owner_id, owner_name, charsmax(owner_name));
	
	// target
	client_print_color(GetTarget(owner_id), owner_id, "^4(Private from) ^3%s: ^1%s", owner_name, message);
	// sender
	client_print_color(owner_id, GetTarget(owner_id), "^4(Private to) ^3%s: ^1%s", target_name, message);
	
	if(_:__save_db) {
		new channel[64];
		formatex(channel, charsmax(channel), "Private to %s", target_name);
		
		ultrahc_sql_chat_insert(owner_id, owner_name, charsmax(owner_name), get_user_team(owner_id), channel, message, charsmax(message), 0);
	}
	
	return PLUGIN_HANDLED;
}

//-----------------------------------------------

public SayPMCallback(owner_id) {
	new args[64]
	read_args(args, charsmax(args));
	
	remove_quotes(args);
	trim(args);
	
	new match = contain(args, "/pm");
	if(match != 0) return PLUGIN_CONTINUE;
	
	replace_all(args, charsmax(args), "/pm", "");

	trim(args);

	if(!args[0]) {
		// create all list players
		CreateDefaultMenu(owner_id);
	} else {
		// create with founds
		CreateWithFoundsMenu(owner_id, args, strlen(args));
	}
		
	

	return PLUGIN_CONTINUE;
}

//-----------------------------------------------

CreateDefaultMenu(player_id) {
	
	new menu_handle = menu_create("Private message to:", "PrivateMenuHandler");
	
	for(new i=1; i < MaxClients; i++) {
		if(!is_user_connected(i)) continue;
		
		// if(is_user_bot(i)) continue;
		// if(i == player_id) continue;
		
		new user_name[MAX_NAME_LENGTH];
		get_user_name(i, user_name, charsmax(user_name));
		
		new id_as_str[8];
		num_to_str(i, id_as_str, charsmax(id_as_str));
		menu_additem(menu_handle, user_name, id_as_str);
	}
	
	menu_display(player_id, menu_handle);
	
	return PLUGIN_HANDLED
}

//-----------------------------------------------

CreateWithFoundsMenu(player_id, target_name[], target_name_len) {
	// using Dice-Sørensen coefficient
	new list_founds[MAX_PLAYERS][MAX_NAME_LENGTH];
	new list_founds_size = 0;
	
	// set bigram for target_name
	new tarname_bigrams_set[MAX_NAME_LENGTH][16];
	new tarname_bigrams_size = 0;
	
	new bigram[16];
	for(new i=0; i<target_name_len-1; i++) {
		if((i+1) >= MAX_NAME_LENGTH) break;
	
		formatex(bigram, charsmax(bigram), "%c%c", target_name[i], target_name[i+1]);
		
		copy(tarname_bigrams_set[i], 16, bigram);
		tarname_bigrams_size++;
	}
	
	new i_username[MAX_NAME_LENGTH];
	new i_bigrams_set[MAX_NAME_LENGTH][4];
	new i_bigrams_size = 0;
	new i_bigram[4];
	
	new sets_intersects = 0;
	for(new i=1; i<MaxClients; i++) {
		if(!is_user_connected(i)) continue;
		get_user_name(i, i_username, charsmax(i_username));
		// set bigram for i
		i_bigrams_size = 0;
		sets_intersects = 0;
		
		for(new j=0; j<strlen(i_username)-1; j++) {
			if((j+1) >= MAX_NAME_LENGTH) break;
		
			formatex(i_bigram, charsmax(i_bigram), "%c%c", i_username[j], i_username[j+1]);
			
			copy(i_bigrams_set[j], 16, i_bigram);
			i_bigrams_size++;
		}
		// count set intersects
		for(new j=0; j<i_bigrams_size; j++) {
			for(new k=0; k<tarname_bigrams_size; k++) {
				if(equali(i_bigrams_set[j], tarname_bigrams_set[k])) {
					sets_intersects++;
				}
			}
		}
		
		new float:calc_coef = floatdiv(2*sets_intersects, i_bigrams_size + tarname_bigrams_size); //mul_inter / count_all;
		
		if(calc_coef >= __sim_coeff) {
			copy(list_founds[i], MAX_NAME_LENGTH, i_username);
			list_founds_size++;
		}
	}
	
	new menu_handle = menu_create("Private message to:", "PrivateMenuHandler");
	
	for(new i=1; i < MaxClients; i++) {
		if(!is_user_connected(i)) continue;
		// if(is_user_bot(i)) continue;
		// if(i == player_id) continue;
		
		if(!list_founds[i][0]) continue;
		
		new user_name[MAX_NAME_LENGTH];
		get_user_name(i, user_name, charsmax(user_name));
		
		new id_as_str[8];
		num_to_str(i, id_as_str, charsmax(id_as_str));
		menu_additem(menu_handle, user_name, id_as_str);
	}
	
	menu_display(player_id, menu_handle);
	
	return PLUGIN_HANDLED
	
}

//-----------------------------------------------

public PrivateMenuHandler(player_id, menu_id, item_id) {
	if(item_id == MENU_EXIT){
		menu_destroy(menu_id);
		return PLUGIN_HANDLED;
	}
	
	new item_info[8];
	new item_text[MAX_NAME_LENGTH];
	menu_item_getinfo(menu_id, item_id, _, item_info, charsmax(item_info), item_text, charsmax(item_text));
	
	new msgmode[64];
	formatex(msgmode, charsmax(msgmode), "messagemode %s", MESSAGEMODE_NAME);
	client_cmd(player_id, msgmode);
	
	new target_id = str_to_num(item_info);
	
	SetTarget(player_id, target_id);
	
	return PLUGIN_HANDLED;
}