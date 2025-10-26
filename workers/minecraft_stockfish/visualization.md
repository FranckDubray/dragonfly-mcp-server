# Minecraft_Stockfish — Visualisation complète (SSOT)

Ce document présente la vue globale et les vues détaillées des sous-graphes du worker Minecraft Stockfish refactoré (Init → TurnTimer → WandSelect → WandDrop → MovePipeline → ValidateMove → EngineTurn, avec SanctionTNT).

---

## Vue globale

```mermaid
flowchart LR
  START([START]) --> GI[GAME_INIT]
  GI --> TT[TURN_TIMER]

  TT -- timeout --> ST[SANCTION_TNT]
  TT -- ok --> WS[WAND_SELECT]

  WS -- idle --> TT
  WS -- selected --> WD[WAND_DROP]

  WD -- dropped --> MP[MOVE_PIPELINE]

  MP -- no_move --> TT
  MP -- moved --> VM[VALIDATE_MOVE]

  VM -- bad --> ST
  VM -- ok --> ET[ENGINE_TURN]

  ET -- loop --> TT

  ST --> EXIT([EXIT])
```

---

## Détail: GAME_INIT

```mermaid
flowchart TB
  INIT_START --> INIT_ENV --> INIT_PLATFORM --> BOARD_COORDS --> PAINT_TPL --> INIT_PAINT --> INIT_LEVER --> INIT_FW_RIG --> INIT_FW_TEST
  INIT_FW_TEST --> MC_TAG_OWNER --> MC_SCOREBOARD_INIT --> MC_GIVE_WAND --> SPAWN_TPL --> INIT_SPAWN --> INIT_LOCK --> LIST_INIT --> NORM_INIT --> STABLE_INIT --> SORT_INIT --> UNIQ_INIT --> SNAP_INIT
```

- Objet: préparation de l'environnement, damier, levier, rig feux d'artifice, tag propriétaire, scoreboard (ne sert plus au gameplay), baguette, spawn pièces, lock, snapshot initial.

---

## Détail: TURN_TIMER

```mermaid
flowchart TB
  TMR_GET_NOW --> TMR_GET_LAST --> TMR_LAST_EXISTS
  TMR_LAST_EXISTS -- true --> TMR_DIFF
  TMR_LAST_EXISTS -- false --> TT_STORE_START --> TMR_DIFF
  TMR_DIFF --> TMR_DECIDE
  TMR_DECIDE -- true: timeout --> EXIT_TIMEOUT
  TMR_DECIDE -- false: ok --> EXIT_OK
```

- Exits: timeout, ok

---

## Détail: WAND_SELECT

```mermaid
flowchart TB
  CLEAR_PREV_SEL --> SELECT_RAYCAST --> LIST_SELECTED --> HAS_SELECTION
  HAS_SELECTION -- false: idle --> EXIT_IDLE
  HAS_SELECTION -- true: selected --> WH_MSG_SELECTED --> EXIT_SELECTED
```

- Exits: idle, selected

---

## Détail: WAND_DROP

```mermaid
flowchart TB
  DROP_CAPTURE_SNAP --> WH_MSG_DROPPED --> EXIT_DROPPED
```

- Exits: dropped

---

## Détail: MOVE_PIPELINE

```mermaid
flowchart TB
  MD_LIST --> MD_NORM --> MD_SORT --> MD_UNIQ --> MD_SNAP --> MD_CMP --> MD_DEC_UNIQUE
  MD_DEC_UNIQUE -- false: no_move --> EXIT_NO
  MD_DEC_UNIQUE -- true: moved --> MD_SET_PREV --> MD_UCI --> EXIT_MOVED
```

- Exits: no_move, moved

---

## Détail: VALIDATE_MOVE

```mermaid
flowchart TB
  VP_BEFORE --> VP_AFTER --> VB_BEFORE_CP --> VB_AFTER_CP --> VB_BEFORE_CP_NUM --> VB_AFTER_CP_NUM --> VB_DELTA --> VP_DEC_BAD
  VP_DEC_BAD -- true: bad --> EXIT_BAD
  VP_DEC_BAD -- false: ok --> EXIT_OK
```

- Exits: bad, ok

---

## Détail: ENGINE_TURN

```mermaid
flowchart TB
  BM_REQ --> BM_PARSE --> HAS_BEST
  HAS_BEST -- false: loop --> NO_BEST_MSG --> EXIT_LOOP
  HAS_BEST -- true --> GAME_PUSH_MOVE --> GAME_PUSH_BLACK --> AB_ANIM --> AB_MSG --> ET_SLEEP --> TMR_GET_NOW --> TT_STORE_END --> EXIT_LOOP
```

- Exits: loop

---

## Détail: SANCTION_TNT

```mermaid
flowchart TB
  ST_ENTRY --> TNT_MSG --> TNT_SURV --> TNT_FIRE --> TNT_CLEAR_INV --> TNT_FORCELOAD --> FT_CLEAR_CMD --> TNT_CLEAR --> FT_TNT0 --> FT_TNT1 --> FT_TNT2 --> BUILD_TNT_LIST --> FILTER_TNT_LIST --> TNT_IGNITE --> TNT_TP --> ST_EXIT
```

- Exit unique: exit
