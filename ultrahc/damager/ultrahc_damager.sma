#include <amxmodx>
#include <reapi>

#define GetDamage(%0) __damage[%0]
#define SetDamage(%0,%1) __damage[%0] = %1

#define GetDamageTime(%0) __damage_time[%0]
#define SetDamageTime(%0,%1) __damage_time[%0] = %1

new const kPluginName[] = "ULTRAHC Damager";
new const kPluginVersion[] = "0.1";
new const kPluginAuthor[] = "Asura";

new __damage[MAX_PLAYERS] = {0, ...};
new float:__damage_time[MAX_PLAYERS] = {0.0, ...};

public plugin_init() {
	register_plugin(kPluginName, kPluginVersion, kPluginAuthor);

	RegisterHookChain(RG_CBasePlayer_TakeDamage, "PlayerTakeDamage", 1);
}

public PlayerTakeDamage(const this, pev_inflictor, pev_attacker, float:damage, bits_damage_type) {
	if(!GetHookChainReturn(ATYPE_INTEGER) && is_user_alive(this)) return HC_CONTINUE;
	
	new float:time = get_gametime();
	new time_passed = floatround(time) - floatround(GetDamageTime(pev_attacker));
	if(time_passed > 3) {
		SetDamage(pev_attacker, 0);
	}
	
	new damage_additive = GetDamage(pev_attacker) + floatround(damage);
	SetDamage(pev_attacker, damage_additive);
	SetDamageTime(pev_attacker, time);
	
	ClearDHUD(pev_attacker);
	set_dhudmessage(255, 0, 0, -1.0, 0.54, 0, _, 2.0, 0.1, 0.5);
	show_dhudmessage(pev_attacker, "%i", damage_additive);
	
	return HC_CONTINUE;
}

ClearDHUD(user_id) {
	for(new i=0; i<8; i++) {
		show_dhudmessage(user_id, "");
	}
}