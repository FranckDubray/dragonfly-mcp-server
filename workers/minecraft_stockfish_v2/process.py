from py_orch import Process, SubGraphRef

PROCESS = Process(
    name="MINECRAFT_STOCKFISH_V2",
    entry="GI_ENV",
    parts=[
        SubGraphRef("GI_ENV", module="subgraphs.gi_env", next={"success": "GI_CLEAR_AREA"}),

        # INIT
        SubGraphRef("GI_CLEAR_AREA", module="subgraphs.gi_clear_area", next={"success": "GI_PLATFORM_BOARD"}),
        SubGraphRef("GI_PLATFORM_BOARD", module="subgraphs.gi_platform_board", next={"success": "GI_SPAWN_WHITE_BACK"}),
        SubGraphRef("GI_SPAWN_WHITE_BACK", module="subgraphs.gi_spawn_white_back", next={"success": "GI_SPAWN_WHITE_PAWNS"}),
        SubGraphRef("GI_SPAWN_WHITE_PAWNS", module="subgraphs.gi_spawn_white_pawns", next={"success": "GI_SPAWN_BLACK_BACK"}),
        SubGraphRef("GI_SPAWN_BLACK_BACK", module="subgraphs.gi_spawn_black_back", next={"success": "GI_SPAWN_BLACK_PAWNS"}),
        SubGraphRef("GI_SPAWN_BLACK_PAWNS", module="subgraphs.gi_spawn_black_pawns", next={"success": "GI_SPAWN_COMBINE_AND_SNAP"}),
        SubGraphRef("GI_SPAWN_COMBINE_AND_SNAP", module="subgraphs.gi_spawn_combine_and_snap", next={"success": "GI_LEVER_FW"}),
        SubGraphRef("GI_LEVER_FW", module="subgraphs.gi_lever_fw", next={"success": "GI_IA_VILLAGER"}),
        SubGraphRef("GI_IA_VILLAGER", module="subgraphs.gi_ia_villager", next={"success": "GI_OWNER_SETUP"}),
        SubGraphRef("GI_OWNER_SETUP", module="subgraphs.gi_owner_setup", next={"success": "TURN_TIMER"}),

        # TURN
        SubGraphRef("TURN_TIMER", module="subgraphs.turn_timer", next={"fail": "GAME_END_UI", "success": "TURN_LEVER_RESET"}),
        SubGraphRef("TURN_LEVER_RESET", module="subgraphs.turn_lever_reset", next={"success": "WAND_SELECT"}),
        SubGraphRef("WAND_SELECT", module="subgraphs.wand_select", next={"success": "WAND_DROP"}),
        SubGraphRef("WAND_DROP", module="subgraphs.wand_drop", next={"success": "MOVE_PIPELINE"}),
        SubGraphRef("MOVE_PIPELINE", module="subgraphs.move_pipeline", next={"fail": "GAME_END_UI", "success": "VALIDATE_MOVE"}),
        SubGraphRef("VALIDATE_MOVE", module="subgraphs.validate_move", next={"fail": "GAME_END_UI", "success": "WHITE_WN_PARSE_LOCATE"}),

        # WHITE
        SubGraphRef("WHITE_WN_PARSE_LOCATE", module="subgraphs.white_wn_parse_locate", next={"success": "WHITE_WN_CASTLING_DETECT"}),
        SubGraphRef("WHITE_WN_CASTLING_DETECT", module="subgraphs.white_wn_castling_detect", next={"success": "WHITE_WN_CASTLING_COORDS"}),
        SubGraphRef("WHITE_WN_CASTLING_COORDS", module="subgraphs.white_wn_castling_coords", next={"success": "WHITE_WN_CASTLING_MOVE"}),
        SubGraphRef("WHITE_WN_CASTLING_MOVE", module="subgraphs.white_wn_castling_move", next={"success": "WHITE_WN_PROMO"}),
        SubGraphRef("WHITE_WN_PROMO", module="subgraphs.white_wn_promo", next={"success": "WHITE_WN_EP"}),
        SubGraphRef("WHITE_WN_EP", module="subgraphs.white_wn_ep", next={"success": "ENGINE_B_COMPUTE"}),

        # ENGINE
        SubGraphRef("ENGINE_B_COMPUTE", module="subgraphs.engine_b_compute", next={"fail": "BOARD_PROTECT", "success": "ENGINE_B_PARSE_LOCATE"}),
        SubGraphRef("ENGINE_B_PARSE_LOCATE", module="subgraphs.engine_b_parse_locate", next={"success": "ENGINE_B_ANIM_CAPTURE_TP"}),
        SubGraphRef("ENGINE_B_ANIM_CAPTURE_TP", module="subgraphs.engine_b_anim_capture_tp", next={"success": "ENGINE_B_EP_STRICT"}),
        SubGraphRef("ENGINE_B_EP_STRICT", module="subgraphs.engine_b_ep_strict", next={"success": "ENGINE_B_CASTLING_DETECT"}),
        SubGraphRef("ENGINE_B_CASTLING_DETECT", module="subgraphs.engine_b_castling_detect", next={"success": "ENGINE_B_CASTLING_COORDS"}),
        SubGraphRef("ENGINE_B_CASTLING_COORDS", module="subgraphs.engine_b_castling_coords", next={"success": "ENGINE_B_CASTLING_MOVE"}),
        SubGraphRef("ENGINE_B_CASTLING_MOVE", module="subgraphs.engine_b_castling_move", next={"success": "ENGINE_B_PROMOTION"}),
        SubGraphRef("ENGINE_B_PROMOTION", module="subgraphs.engine_b_promotion", next={"success": "ENGINE_SNAPSHOT_TURN"}),
        SubGraphRef("ENGINE_SNAPSHOT_TURN", module="subgraphs.engine_snapshot_turn", next={"success": "BOARD_PROTECT"}),

        # END + UI
        SubGraphRef("BOARD_PROTECT", module="subgraphs.board_protect", next={"success": "GAME_END_CHECK"}),
        SubGraphRef("GAME_END_CHECK", module="subgraphs.game_end_check", next={"success": "GAME_END_UI"}),
        SubGraphRef("GAME_END_UI", module="subgraphs.game_end_ui", next={"fail": "SANCTION_TNT", "success": "GI_CLEAR_AREA"}),
        SubGraphRef("SANCTION_TNT", module="subgraphs.sanction_tnt", next={"success": "GI_CLEAR_AREA"}),
    ],
    metadata={
        "description": "Minecraft Stockfish v2 with spawn refactor into smaller subgraphs.",
        "author": "orchestrator-team",
    }
)
