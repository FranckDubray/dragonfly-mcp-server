"""
Compression helpers: run-length encode along X per (y,z).
"""
from typing import Dict, Tuple, List


def rle_fill_commands(by_yz: Dict[Tuple[int, int], List[Tuple[int, str]]], CommandBuilder) -> List[str]:
    """Build /fill commands from (y,z)->[(x,block)...] mapping.
    Assumes each list is sorted by x.
    """
    commands: List[str] = []
    for (wy, wz) in sorted(by_yz.keys(), key=lambda t: (t[0], t[1])):
        items = by_yz[(wy, wz)]
        items.sort(key=lambda t: t[0])
        run_x1 = None
        run_blk = None
        prev_x = None
        for wx, blk in items:
            if run_x1 is None:
                run_x1, run_blk, prev_x = wx, blk, wx
                continue
            if blk == run_blk and wx == prev_x + 1:
                prev_x = wx
                continue
            commands.append(CommandBuilder.fill(run_x1, wy, wz, prev_x, wy, wz, run_blk))
            run_x1, run_blk, prev_x = wx, blk, wx
        if run_x1 is not None:
            commands.append(CommandBuilder.fill(run_x1, wy, wz, prev_x, wy, wz, run_blk))
    return commands
