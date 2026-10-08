from PySide6.QtCore import QPoint

from pulse.ui.window import island_region


def test_mask_covers_pill_but_excludes_transparent_corners():
    region = island_region(195, 12, 30, 30, 15)
    assert region.contains(QPoint(210, 27))
    assert not region.contains(QPoint(195, 12))
    assert not region.contains(QPoint(100, 27))


def test_expanded_mask_moves_with_centered_island():
    collapsed = island_region(195, 12, 30, 30, 15)
    expanded = island_region(60, 12, 300, 64, 32)
    assert not collapsed.contains(QPoint(80, 44))
    assert expanded.contains(QPoint(80, 44))
    assert expanded.contains(QPoint(340, 44))
    assert not expanded.contains(QPoint(60, 12))
