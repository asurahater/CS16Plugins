#include <amxmodx>
#include <amxmisc>
#include <reapi>
#include <nvault>

#pragma ctrlchar '\'
#pragma semicolon 1

enum Power {
	Power_0 = 0,
	Power_25,
	Power_50,
	Power_75,
	Power_100
}

new const kPluginName[] = "ULTRAHC Damage Blocker";
new const kPluginVersion[] = "0.1";
new const kPluginAuthor[] = "Asura";

new const kVaultName[] = "ultrahc_block_damage";

new const kPowerString[Power][32] = {
	"Block",
	"25%",
	"50%",
	"75%",
	"Unblock"
};

//-------------------------------------------------------

#define Pre 0
#define POWER_SLOT 6

#define SetBlockDmg(%0,%1) __player_block_damage[%0] = %1
#define IsBlockDmg(%0) __player_block_damage[%0]

#define SetBlockDmgPerc(%0,%1) __player_block_damage_perc[%0] = %1
#define GetBlockDmgPerc(%0) __player_block_damage_perc[%0]

//-------------------------------------------------------

new __player_block_damage[MAX_PLAYERS] = {0, ...};
new Float:__player_block_damage_perc[MAX_PLAYERS] = {1.0, ...};

//-------------------------------------------------------

public plugin_init() {
	register_plugin(kPluginName, kPluginVersion, kPluginAuthor);
	
	register_concmd("uhc_blockdmg_set", "OnBlockDamageSet", ADMIN_BAN, "<name or userid> <percentage of dmg> (Percentage from 0.0 to 1.0)");
	register_concmd("uhc_blockdmg_rem", "OnBlockDamageRemove", ADMIN_BAN, "<name or userid> (remove player from block)");
	register_concmd("uhc_blockdmg_menu", "OnBlockDamageMenu", ADMIN_BAN, "Block damage menu");

	register_clcmd("say /blockdamage", "OnBlockDamageMenu", ADMIN_BAN);
	
	RegisterHookChain(RG_CBasePlayer_TakeDamage, "OnTakeDamagePre", Pre);
}

//-------------------------------------------------------

public client_disconnected(client_id) {
	SetBlockDmg(client_id, 0);
	SetBlockDmgPerc(client_id, 1.0);
}

//-------------------------------------------------------

public client_authorized(client_id, const client_auth[]) {
	LoadFromVault(client_id, client_auth);
}

//-------------------------------------------------------

LoadFromVault(target_id, const target_auth[]) {
	new vault_handler = nvault_open(kVaultName);
	new dmg_percent[8];
	nvault_get(vault_handler, target_auth, dmg_percent, charsmax(dmg_percent));

	if(dmg_percent[0]) {
		new Float:dmg_perc = str_to_float(dmg_percent);
		SetBlockDmg(target_id, 1);
		SetBlockDmgPerc(target_id, dmg_perc);
	}

	nvault_close(vault_handler);
}

//-------------------------------------------------------

public OnBlockDamageSet(adm_id, flag_level, cmd_id) {
	if(!cmd_access(adm_id, flag_level, cmd_id, 1))
		return PLUGIN_HANDLED;
	
	new target_argv[32]; read_argv(1, target_argv, charsmax(target_argv));
	new target_id = cmd_target(adm_id, target_argv, CMDTARGET_ALLOW_SELF);
	
	if(!target_id)
		return PLUGIN_HANDLED;
	
	new dmg_perc_argv[32]; read_argv(2, dmg_perc_argv, charsmax(dmg_perc_argv));
	new Float:dmg_perc = Float:str_to_float(dmg_perc_argv);
	
	SaveToVault(target_id, dmg_perc);

	SetBlockDmg(target_id, 1);
	SetBlockDmgPerc(target_id, dmg_perc);

	return PLUGIN_HANDLED;
}

//-------------------------------------------------------

SaveToVault(target_id, Float:dmg_perc) {
	new vault_handler = nvault_open(kVaultName);
	new target_auth[32]; get_user_authid(target_id, target_auth, charsmax(target_auth));
	new perc_as_str[16]; float_to_str(Float:dmg_perc, perc_as_str, charsmax(perc_as_str));
	
	nvault_set(vault_handler, target_auth, perc_as_str);

	nvault_close(vault_handler);
}

//-------------------------------------------------------

public OnBlockDamageRemove(adm_id, flag_level, cmd_id) {
	if(!cmd_access(adm_id, flag_level, cmd_id, 1))
		return PLUGIN_HANDLED;
	
	new target_argv[32]; read_argv(1, target_argv, charsmax(target_argv));
	new target_id = cmd_target(adm_id, target_argv, CMDTARGET_ALLOW_SELF);
	
	if(!target_id)
		return PLUGIN_HANDLED;
	
	RemFromVault(target_id);
	
	SetBlockDmg(target_id, 0);
	SetBlockDmgPerc(target_id, 1.0);
	
	return PLUGIN_HANDLED;
}

//-------------------------------------------------------

RemFromVault(target_id) {
	new vault_handler = nvault_open(kVaultName);
	new target_auth[32]; get_user_authid(target_id, target_auth, charsmax(target_auth));
	
	nvault_remove(vault_handler, target_auth);

	nvault_close(vault_handler);
}

//-------------------------------------------------------
//-- Take Damage
//-------------------------------------------------------

public OnTakeDamagePre(const this, pev_inflictor, pev_attacker, Float:damage, damage_type) {
	if(IsBlockDmg(pev_attacker)) {

		if(_:GetBlockDmgPerc(pev_attacker) == 0) {
			SetHookChainReturn(ATYPE_INTEGER, 0);
			return HC_BREAK;
		}

		damage = damage * Float:GetBlockDmgPerc(pev_attacker);
		SetHookChainArg(4, ATYPE_FLOAT, damage);
	}
	
	return HC_CONTINUE;
}

//-------------------------------------------------------
//-- Menu
//-------------------------------------------------------

public OnBlockDamageMenu(adm_id, flag_level, cmd_id) {
	if(!cmd_access(adm_id, flag_level, cmd_id, 1))
		return PLUGIN_HANDLED;

	CreateMenu(adm_id, flag_level, Power:Power_0);
		
	return PLUGIN_HANDLED;
}

//-------------------------------------------------------

CreateMenu(adm_id, flag_level, Power:power) {
	new menu_handler  = menu_create("Block Damage", "MenuHandler");
	// menu_setprop(menu_handler, MPROP_EXIT, MEXIT_NEVER);

	new players[MAX_PLAYERS], players_num;
	get_players(players, players_num, "h");

	for(new i=0, j=1; i < players_num; ++i, ++j) {
		if((j % 7) == 0) {
			new item_name[128];
			formatex(item_name, charsmax(item_name), "Set damage: %s", kPowerString[power]);

			new power_str[6];
			num_to_str(_:power, power_str, charsmax(power_str));
			menu_addblank(menu_handler, 0);
			menu_additem(menu_handler, item_name, power_str, flag_level);
			
			continue;
		}

		new player_name[MAX_NAME_LENGTH]; get_user_name(players[i], player_name, charsmax(player_name));

		new user_uid[6];
		num_to_str(get_user_userid(players[i]), user_uid, charsmax(user_uid));

		new blocked[32] = "";
		if(IsBlockDmg(players[i])) {

			new Float:dmg_perc = GetBlockDmgPerc(players[i]);
			if(_:dmg_perc == 0) {
				blocked = "\\r(BLOCKED)";
			} else {
				formatex(blocked, charsmax(blocked), "\\r(%i%%)", floatround(dmg_perc * 100));
			}   

		}
		new item_name[128];
		formatex(item_name, charsmax(item_name), "%s %s", player_name, blocked);

		menu_additem(menu_handler, item_name, user_uid, flag_level);

		if((i+1) == players_num) {

			for(new k=0; k < (5-i); ++k) {
				menu_addblank2(menu_handler);
			}

			new item_name[128];
			formatex(item_name, charsmax(item_name), "Set damage: %s", kPowerString[power]);

			new power_str[6];
			num_to_str(_:power, power_str, charsmax(power_str));
			menu_addblank(menu_handler, 0);
			menu_additem(menu_handler, item_name, power_str, flag_level);
			
			continue;
		}
	}

	menu_display(adm_id, menu_handler, 0);
}

//-------------------------------------------------------

public MenuHandler(adm_id, menu_handler, item) {
	if(item == MENU_EXIT) {
		return PLUGIN_HANDLED;
	}

	new power_as_str[8], flag_level;
	menu_item_getinfo(menu_handler, POWER_SLOT, flag_level, power_as_str, charsmax(power_as_str));
	new Power:power = Power:str_to_num(power_as_str);

	// Из-за сдвига в 1 вниз, у нас 7 идет в 6, 14 в 13, и тд.
	// т.е. перестают быть нулем по модулю 7
	// поэтому сдвигаем обратно до 7, выравнвиая все
	if(((item+1) % (POWER_SLOT+1)) == 0) {
		if(power == Power:Power_100) power = Power:Power_0;
		else ++power;

		CreateMenu(adm_id, flag_level, power);
		return PLUGIN_HANDLED;
	}

	new item_info[8];
	menu_item_getinfo(menu_handler, item, flag_level, item_info, charsmax(item_info));

	new user_uid[6];
	formatex(user_uid, charsmax(user_uid), "#%s", item_info);

	new user_idx = cmd_target(adm_id, user_uid, CMDTARGET_ALLOW_SELF);

	if(!user_idx) {
		CreateMenu(adm_id, flag_level, power);
		return PLUGIN_HANDLED;
	}

	switch(power) {
		case (Power:Power_0): {
			amxclient_cmd(adm_id, "uhc_blockdmg_set", user_uid, "0");
		}
		case (Power:Power_25): {
			amxclient_cmd(adm_id, "uhc_blockdmg_set", user_uid, "0.25");
		}
		case (Power:Power_50): {
			amxclient_cmd(adm_id, "uhc_blockdmg_set", user_uid, "0.5");
		}
		case (Power:Power_75): {
			amxclient_cmd(adm_id, "uhc_blockdmg_set", user_uid, "0.75");
		}
		case (Power:Power_100): {
			amxclient_cmd(adm_id, "uhc_blockdmg_rem", user_uid);
		}
	}

	CreateMenu(adm_id, flag_level, power);
	return PLUGIN_HANDLED;
}