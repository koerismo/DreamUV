from collections.abc import Sequence
import enum


def fit_rect_to_surface(rects: Sequence[Rect], surf_dims: Vec2f, out_result: RectFitResult) -> int: ...

def get_score(dims_surf: Vec2f, rect: Rect, out_result: RectFitResult) -> None: ...

class RectFlags_t(enum.Flag):
    enable_rotation = 1

    enable_reflection = 2

    alt_group = 4

    tile_x = 8

    tile_y = 16

    tile_x_y = 24

enable_rotation: RectFlags_t = RectFlags_t.enable_rotation

enable_reflection: RectFlags_t = RectFlags_t.enable_reflection

alt_group: RectFlags_t = RectFlags_t.alt_group

tile_x: RectFlags_t = RectFlags_t.tile_x

tile_y: RectFlags_t = RectFlags_t.tile_y

tile_x_y: RectFlags_t = RectFlags_t.tile_x_y

class Vec2f:
    def __init__(self, x: float, y: float) -> None: ...

    @property
    def x(self) -> float: ...

    @x.setter
    def x(self, arg: float, /) -> None: ...

    @property
    def y(self) -> float: ...

    @y.setter
    def y(self, arg: float, /) -> None: ...

    def swapped(self) -> Vec2f: ...

    def dot(self, arg: Vec2f, /) -> float: ...

    def normalized(self, arg: float, /) -> Vec2f: ...

class Vec2i:
    def __init__(self, x: int, y: int) -> None: ...

    @property
    def x(self) -> int: ...

    @x.setter
    def x(self, arg: int, /) -> None: ...

    @property
    def y(self) -> int: ...

    @y.setter
    def y(self, arg: int, /) -> None: ...

    def swapped(self) -> Vec2i: ...

class Rect:
    def __init__(self, flags: int, mins: Vec2i, maxs: Vec2i) -> None: ...

    def get_width(self) -> int: ...

    def get_height(self) -> int: ...

    def can_rotate(self) -> bool: ...

    def can_reflect(self) -> bool: ...

    def can_tile(self) -> bool: ...

    def can_tile_x(self) -> bool: ...

    def can_tile_y(self) -> bool: ...

    def is_alt_group(self) -> bool: ...

class RectFitResult:
    def __init__(self, rect_idx: int, rotated: bool) -> None: ...

    @property
    def rect_idx(self) -> int: ...

    @property
    def tiling(self) -> Vec2i: ...

    @property
    def rotated(self) -> bool: ...

    @property
    def score(self) -> float: ...

class RectFile:
    def __init__(self, version: int, tex_size: Vec2i, rects: Sequence[Rect]) -> None: ...

    @property
    def flags(self) -> int: ...

    @flags.setter
    def flags(self, arg: int, /) -> None: ...

    @property
    def tex_size(self) -> Vec2i: ...

    @property
    def rects(self) -> list[Rect]: ...
