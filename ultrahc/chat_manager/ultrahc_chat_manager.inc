#if defined _ultrahc_chat_manager_included
    #endinput
#endif
#define _ultrahc_chat_manager_included

/**
 * Get prefix
 * return empty string if no prefix
 *
 * @param client_id             Client id
 * @param prefix_id             Prefix id
 * @param buffer                buffer to save prefix
 * @param buf_size              size of buffer
 *
 * @noreturn
 */
native ultrahc_get_prefix(client_id, prefix_id, buffer[], buf_size);

/**
 * Is prefix file loaded
 *
 * @return true or false
 */
native ultrahc_is_pref_file_load();

/**
 * player_team as CS_TEAM_*
 *
 * @return nothing
 */
native ultrahc_sql_chat_insert(player_id, player_name[], player_name_size, player_team, channel[], message[], message_size, msg_color);