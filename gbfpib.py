from __future__ import annotations
import asyncio
from contextlib import asynccontextmanager
from dataclasses import dataclass
from enum import IntEnum

from typing import Generator

from pathlib import Path
import time
import os
import sys
import traceback
import argparse

from base64 import b64encode

import json
from io import BytesIO

import importlib.util

# third party
import aiohttp
from PIL import Image, ImageFont, ImageDraw
import pyperclip

# class to manipulate a vector2-type structure (X, Y)
# call the 'i' property to obtain an integer tuple to use with Pillow
dataclass(slots=True)
class v2():
    x : int|float = 0
    y : int|float = 0
    
    def __init__(self : v2, X : int|float, Y : int|float):
        self.x = X
        self.y = Y
    
    def copy(self : v2) -> v2:
        return v2(self.x, self.y)
    
    # operators
    def __add__(self : v2, other : v2|tuple|list|int|float) -> v2:
        if isinstance(other, float) or isinstance(other, int):
            return v2(self.x + other, self.y + other)
        else:
            return v2(self.x + other[0], self.y + other[1])
    
    def __radd__(self : v2, other : v2|tuple|list|int|float) -> v2:
        return self.__add__(other)

    def __sub__(self : v2, other : v2|tuple|list|int|float) -> v2:
        if isinstance(other, float) or isinstance(other, int):
            return v2(self.x - other, self.y - other)
        else:
            return v2(self.x - other[0], self.y - other[1])
    
    def __rsub__(self : v2, other : v2|tuple|list|int|float) -> v2:
        return self.__sub__(other)

    def __mul__(self : v2, other : v2|tuple|list|int|float) -> v2:
        if isinstance(other, float) or isinstance(other, int):
            return v2(self.x * other, self.y * other)
        else:
            return v2(self.x * other[0], self.y * other[1])

    def __rmul__(self : v2, other : v2|tuple|list|int|float) -> v2:
        return self.__mul__(other)

    # for access via []
    def __getitem__(self : v2, key : int) -> int|float:
        if key == 0:
            return self.x
        elif key == 1:
            return self.y
        else:
            raise IndexError("Index out of range")

    def __setitem__(self : v2, key : int, value : int|float) -> None:
        if key == 0:
            self.x = value
        elif key == 1:
            self.y = value
        else:
            raise IndexError("Index out of range")

    # len is fixed at 2
    def __len__(self : v2) -> int:
        return 2

    # to convert to an integer tuple (needed for pillow)
    @property
    def i(self : v2) -> tuple[int, int]:
        return (int(self.x), int(self.y))

# wrapper class to store and manipulate Image objects
# handle the close() calls on destruction
dataclass(slots=True)
class IMG():
    image : Image = None
    buffer : BytesIO = None
    
    def __init__(self : IMG, src : str|bytes|IMG|Image) -> None:
        self.image = None
        self.buffer = None
        match src: # possible types
            case str(): # path to a local file
                self.image = Image.open(src)
                self.convert("RGBA")
            case bytes(): # bytes (usually received from a network request)
                self.buffer = BytesIO(src) # need a readable buffer for it, and it must stays alive
                self.image = Image.open(self.buffer)
                self.convert("RGBA")
            case IMG(): # another IMG wrapper
                self.image = src.image.copy()
            case _: # an Image instance. NOTE: I use 'case _' because of how import Pillow, the type isn't loaded at this point
                self.image = src

    def __del__(self : IMG) -> None:
        if self.image is not None:
            self.image.close()
        if self.buffer is not None:
            self.buffer.close()

    def convert(self : IMG, itype : str) -> None:
        tmp = self.image
        self.image = tmp.convert(itype)
        tmp.close()

    def copy(self : IMG) -> IMG:
        return IMG(self)

    def paste(self : IMG, other : IMG, offset : tuple[int, int]) -> None:
        self.image.paste(other.image, offset, other.image)

    def crop(self : IMG, size : tuple[int, int]|tuple[int, int, int, int]) -> IMG:
        # depending on the tuple size
        if len(size) == 4:
            return IMG(self.image.crop(size))
        elif len(size) == 2:
            return IMG(self.image.crop((0, 0, *size)))
        raise ValueError("Invalid size of the tuple passed to IMG.crop(). Expected 2 or 4, received {}.".format(len(size)))

    def resize(self : IMG, size : v2|tuple[int, int]) -> IMG:
        match size:
            case v2():
                return IMG(self.image.resize(size.i, Image.Resampling.LANCZOS))
            case tuple():
                return IMG(self.image.resize(size, Image.Resampling.LANCZOS))
        raise TypeError("Invalid type passed to IMG.resize(). Expected v2 or tuple[int, int], received {}.".format(type(size)))

    def alpha(self : IMG, layer : IMG) -> IMG:
        return IMG(Image.alpha_composite(self.image, layer.image))

# General enum
class PartyMode(IntEnum):
    normal = 0 # normal parties
    extended = 1 # 8 man party (Versusia)
    babyl = 2 # 12 man party (Babyl)

# Image Layout
IMAGE_SIZE : v2 = v2(1800, 2160)

dataclass(slots=True, frozen=True)
class LayoutPartyBase():
    origin : v2
    start : v2
    skip_zero : bool
    display_name : bool
    character_count : int
    portrait_layout : v2
    skill_box_offset : v2
    skill_box_size : v2
    skill_text_offset : v2
    job_icon_size : v2
    ring_icon_size : v2
    ring_offset : v2
    star_icon_size : v2
    star_offset : v2
    plus_mark_offset : v2
    name_offset : v2
    level_offset : v2
    bonus_count_offset : v2
    accessory_offset : v2
    background_offset : v2
    background_size : v2
    # constant
    accessory_size : v2 = v2(150, 150)
    skill_line_space : int = 48

    def get_portrait_position(self : LayoutPartyBase, index : int) -> v2:
        raise Exception("Unimplemented")

class LayoutPartyNormal(LayoutPartyBase):
    def __init__(self : LayoutPartyNormal):
        self.origin = v2(15, 10)
        self.skip_zero = False
        self.display_name = True
        self.character_count = 5
        self.portrait_layout = v2(250, 250)
        self.skill_box_offset = self.origin + (0, self.portrait_layout.y)
        self.skill_box_size = v2(420, 147)
        self.skill_text_offset = self.skill_box_offset + (3, 3)
        self.job_icon_size = v2(72, 60)
        self.ring_icon_size = v2(90, 90)
        self.ring_offset = v2(-10, -10)
        self.star_icon_size = v2(66, 66)
        self.star_offset = self.portrait_layout + (- self.portrait_layout.x + self.portrait_layout.x //2, - self.portrait_layout.y)
        self.plus_mark_offset = self.portrait_layout + (-110, -40)
        self.name_offset = v2(9, self.portrait_layout.y + 10)
        self.level_offset = v2(10, self.portrait_layout.y + 6 + 60)
        self.bonus_count_offset = v2(10, self.portrait_layout.y + 6 + 60)
        self.accessory_offset = self.skill_box_offset + (0, -150)
        self.start = self.origin + (self.skill_box_size.x - self.portrait_layout.x, 0)
        self.background_offset = self.start + (-15, -10)
        self.background_size = self.portrait_layout * (6,1) + (30+25,175)

    def get_portrait_position(self : LayoutPartyNormal, index : int) -> v2:
        position : v2 = self.origin + (self.skill_box_size.x + self.portrait_layout.x * index, 0)
        if index >= 3:
            position = position + (25, 0)
        return position

class LayoutPartyExtended(LayoutPartyBase):
    def __init__(self : LayoutPartyExtended):
        self.origin = v2(120, 10)
        self.skip_zero = False
        self.display_name = False
        self.character_count = 8
        self.portrait_layout = v2(180, 180)
        self.start = self.origin + (30, 0)
        self.skill_box_offset = self.origin + (60 + self.portrait_layout.x * 4, 10)
        self.skill_box_size = v2(420, 147)
        self.skill_text_offset = self.skill_box_offset + (3, 3)
        self.job_icon_size = v2(54, 45)
        self.ring_icon_size = v2(60, 60)
        self.ring_offset = v2(-6, -6)
        self.star_icon_size = v2(50, 50)
        self.star_offset = self.portrait_layout + (- self.portrait_layout.x, - self.star_icon_size.y * 5 // 3)
        self.plus_mark_offset = self.portrait_layout + (-105, -45)
        self.name_offset = v2(9, self.portrait_layout.y + 10)
        self.level_offset = v2(10, self.portrait_layout.y + 6 + 60)
        self.bonus_count_offset = v2(10, self.portrait_layout.y + 6 + 60)
        self.background_offset = self.start + (-15, -15)
        self.background_size = self.portrait_layout * (7, 2) + (0, 55)
        self.accessory_offset = self.start + (self.portrait_layout.x * 5 + 30, self.portrait_layout.y + 30)

    def get_portrait_position(self : LayoutPartyExtended, index : int) -> v2:
        if index < 3:
            return self.start + (self.portrait_layout.x * (index + 1), 0)
        else:
            return self.start + (0, 10 + self.portrait_layout.y) + (self.portrait_layout.x * (index - 3), 0)

class LayoutPartyBabyl(LayoutPartyBase):
    def __init__(self : LayoutPartyNormal):
        self.origin = v2(15, 10)
        self.start = self.origin + (30, 0)
        self.skip_zero = True
        self.display_name = False
        self.character_count = 12
        self.portrait_layout = v2(180, 180)
        self.skill_box_offset = self.start + (0, 10 + self.portrait_layout.y)
        self.skill_box_size = v2(420, 147)
        self.skill_text_offset = self.skill_box_offset + (3, 3)
        self.job_icon_size = v2(54, 45)
        self.ring_icon_size = v2(60, 60)
        self.ring_offset = v2(-6, -6)
        self.star_icon_size = v2(50, 50)
        self.star_offset = self.portrait_layout + (- self.portrait_layout.x, - self.star_icon_size.y * 5 // 3)
        self.plus_mark_offset = self.portrait_layout + (-105, -45)
        self.name_offset = v2(9, self.portrait_layout.y + 10)
        self.level_offset = v2(10, self.portrait_layout.y + 6 + 60)
        self.bonus_count_offset = v2(10, self.portrait_layout.y + 6 + 60)
        self.accessory_offset = self.skill_box_offset + (447, 0)
        self.background_offset = self.start + (-15, -15)
        self.background_size = self.portrait_layout * (8,2) + (40,55)

    def get_portrait_position(self : LayoutPartyBabyl, index : int) -> v2:
        if index < 4:
            return self.origin + (self.portrait_layout.x * index + 30, 0)
        elif index < 8:
            return self.origin + (self.portrait_layout.x * index + 40, 0)
        else:
            return self.origin + (self.portrait_layout.x * (index - 4) + 40, 10 + self.portrait_layout.y * (index // 8))

dataclass(slots=True, frozen=True)
class LayoutSummon():
    origin : v2 = v2(170, 425)
    main_size : v2 = v2(271, 472)
    main_asset : str = "party_main"
    main_empty : str = "ls"
    sub_size : v2 = v2(266, 200)
    extra_size : v2 = v2(273, 155)
    other_asset : str = "party_sub"
    other_empty : str = "m"
    background_offset : v2 = origin + v2(-15, -15)
    background_size : v2 = v2(
        148 + main_size.x + 2 * sub_size.x + extra_size.x,
        143 + main_size.y
    )
    sub_marker_offset : v2 = origin + (main_size.x + 100 + 18 + 2 * sub_size.x + 45, 0)
    sub_marker_size : v2 = v2(180, 72)
    skin_icon_offset : v2 = (main_size.x - 85, 15)
    skin_icon_size : v2 = v2(76, 85)
    icon_size : v2 = v2(66, 66)
    plus_offset : v2 = v2(-95, -50)
    stat_offset : v2 = origin + main_size + v2(68, 60)
    stat_size : v2 = v2(sub_size.x * 2, 60)
    stat_icon_offset : v2 = v2(9, 9)
    stat_atk_text_offset : v2 = v2(120, 9)
    stat_hp_text_offset : v2 = v2(sub_size.x + 80, 9)
    stat_atk_size : v2 = v2(90, 39)
    stat_hp_size : v2 = v2(66, 39)

    def get_portrait_position(self : LayoutSummon, index : int) -> v2:
        if index == 0:
            return self.origin
        elif index < 5:
            pos : v2 = self.origin + (self.main_size.x + 50 + 18, 0)
            pos += (((index - 1) % 2) * self.sub_size.x, self.sub_size.x * ((index - 1) // 2))
            return pos
        else:
            pos : v2 = self.origin + (self.main_size.x + 100 + 18, 102)
            pos += (2 * self.sub_size.x, (index - 5) * (self.extra_size.y + 60))
            return pos

    def get_portrait_size(self : LayoutSummon, index : int) -> v2:
        if index == 0:
            return self.main_size
        elif index < 5:
            return self.sub_size
        else:
            return self.extra_size

    def get_asset_folder(self : LayoutSummon, index : int) -> tuple[str, str]:
        if index == 0:
            return self.main_asset, self.main_empty
        elif index < 5:
            return self.other_asset, self.other_empty
        else:
            return self.other_empty, self.other_empty

dataclass(slots=True, frozen=True)
class LayoutWeaponBase():
    origin : v2
    background_size : v2
    #constant
    background_offset : v2
    mainhand_size : v2 = v2(300, 630)
    sub_size : v2 = v2(288, 165)
    skill_box_height : int = 144
    skill_icon_size : v2 = v2(72, 72)
    ax_icon_size : v2 = v2(86, 86)
    ax_separator : int = 144
    stat_size : v2 = mainhand_size
    stat_box_height : int = 75
    stat_icon_position : v2 = v2(9, 15)
    stat_text_position : v2 = v2(111, 15)
    auxiliary_offset : v2 = v2(-2, -2)
    auxiliary_size : v2 = v2(5, 5 + skill_box_height)
    skin_icon_offset : v2 = v2(-76, 0)
    skin_icon_size : v2 = v2(76, 85)
    extra_grid_icon_offset : v2
    extra_grid_icon_size : v2 = v2(288, 1145)
    plus_text_position_shift : v2 = v2(-105, -60)
    skill_level_position_shift : v2 = v2(-51, 15)
    ax_text_position_shift : v2 = v2(6, 15)
    ax_indicator_mainhand_multiplier : float = 1.5
    ax_indicator_multiple_multiplier : float = 0.75
    estimated_damage_position : v2 = v2(15, 165)
    estimated_offset_size : v2 = v2(-15, 150)
    estimated_text_offset : v2 = v2(9, 9)
    estimated_other_text_offset : v2 = v2(15, 90)
    estimated_other_text2_offset : v2 = v2(66, 90)
    estimated_other_jp_text_offset : v2 = v2(54, 90)
    estimated_other_jp_text2_offset : v2 = v2(162, 90)
    support_text_offset : v2 = v2(-mainhand_size.x, 9 * 2)
    support_number_text_shift : v2 = v2(0, 60)
    support_box_offset : v2 = support_text_offset + (-15, -15)
    support_box_size : v2 = v2(mainhand_size.x, 150)
    support_art_box_size : v2 = v2(261, 150)
    support_art_box_offset : v2 = v2(-mainhand_size.x - 15 + 9, 0)
    hp_bar_text_offset : v2 = v2(25, 25)
    hp_bar_offset : v2 = v2(25, 90)
    hp_bar_size : v2 = v2(363, 45)
    hp_bar_crop : v2 = v2(484, 23)

    def get_portrait_position(self : LayoutWeaponBase, index : int) -> v2:
        raise Exception("Unimplemented")

    def get_portrait_size(self : LayoutWeaponBase, index : int) -> v2:
        return self.sub_size if index > 0 else self.mainhand_size

dataclass(slots=True, frozen=True)
class LayoutWeaponStandard(LayoutWeaponBase):
    def __init__(self : LayoutWeaponStandard) -> None:
        self.origin = v2(170, 1050)
        self.background_offset = self.origin + (-15, -15)
        self.background_size = v2(self.mainhand_size.x+ 3 * self.sub_size.x + 60, 1425)
        self.extra_grid_icon_offset = self.origin + (self.mainhand_size.x + 30 + self.sub_size.x * 3, 0)
    
    def get_portrait_position(self : LayoutWeaponStandard, index : int) -> v2:
        if index == 0:
            return self.origin
        else:
            return self.origin + (self.stat_size.x + 30, 0) + (self.sub_size + (0, self.skill_box_height)) * ((index - 1) % 3, (index - 1) // 3)

dataclass(slots=True, frozen=True)
class LayoutWeaponExtra(LayoutWeaponBase):
    def __init__(self : LayoutWeaponExtra) -> None:
        self.origin = v2(25, 1050)
        self.background_offset = self.origin + (-15, -15)
        self.background_size = v2(self.mainhand_size.x+ 4 * self.sub_size.x + 60, 1425 + 240)
        self.extra_grid_icon_offset = self.origin + (self.mainhand_size.x + 30 + self.sub_size.x * 3, 0)
    
    def get_portrait_position(self : LayoutWeaponExtra, index : int) -> v2:
        if index == 0:
            return self.origin
        elif index >= 10:
            return self.origin + (self.stat_size.x + 30, 0) + (self.sub_size + (0, self.skill_box_height)) * (3, (index - 1) % 3)
        else:
            return self.origin + (self.stat_size.x + 30, 0) + (self.sub_size + (0, self.skill_box_height)) * ((index - 1) % 3, (index - 1) // 3)

dataclass(slots=True, frozen=True)
class LayoutModifierBase():
    origin : v2
    font : str
    offset : v2
    background_size : v2
    size : v2
    image_offset : v2
    text_offset : v2
    spacer : int
    crop : v2|None
    # constant
    background_bottom_space : int = 50

    def get_crop(self : LayoutModifierBase) -> tuple[int, int]|None:
        if self.crop is None:
            return None
        else:
            return self.crop.i

dataclass(slots=True, frozen=True)
class LayoutModifierCompact(LayoutModifierBase):
    def __init__(self : LayoutModifierCompact) -> None:
        self.font = "mini"
        self.offset = v2(15, 15)
        self.background_size = v2(258, 114)
        self.size = v2(80, 40)
        self.image_offset = v2(-10, 0)
        self.text_offset = v2(80, 5)
        self.spacer = 42
        self.crop = v2(68, 34)

dataclass(slots=True, frozen=True)
class LayoutModifierMini(LayoutModifierBase):
    def __init__(self : LayoutModifierMini) -> None:
        self.font = "mini"
        self.offset = v2(15, 15)
        self.background_size = v2(185, 114)
        self.size = v2(150, 38)
        self.image_offset = v2(0, 0)
        self.text_offset = v2(0, 35)
        self.spacer = 66
        self.crop = None

dataclass(slots=True, frozen=True)
class LayoutModifierSmall(LayoutModifierBase):
    def __init__(self : LayoutModifierSmall) -> None:
        self.font = "small"
        self.offset = v2(27, 27)
        self.background_size = v2(222, 114)
        self.size = v2(174, 45)
        self.image_offset = v2(0, 0)
        self.text_offset = v2(0, 45)
        self.spacer = 84
        self.crop = None

dataclass(slots=True, frozen=True)
class LayoutModifierMedium(LayoutModifierBase):
    def __init__(self : LayoutModifierMedium) -> None:
        self.font = "medium"
        self.offset = v2(15, 15)
        self.background_size = v2(258, 114)
        self.size = v2(241, 60)
        self.image_offset = v2(0, 0)
        self.text_offset = v2(0, 60)
        self.spacer = 105
        self.crop = None

dataclass(slots=True, frozen=True)
class LayoutEMPBase():
    is_compact : bool
    folder : str
    portrait_size : v2
    shift : int
    emp_size : tuple[v2, v2]
    eternal_shift : int
    emp_text_offset : v2
    level_offset : v2
    plus_offset : v2
    background_size : v2
    #constant
    origin : v2 = v2(15, 0)
    emp_ring_offset : v2 = origin + (0, 10)
    emp_ring_size : v2 = v2(80, 80)
    ring_offset : v2 = v2(-10, -10)
    ring_size : v2 = v2(90, 90)
    awk_size : v2 = v2(65, 65)
    domain_offset : v2 = v2(75, 10)
    emp_text_shift : int = 200

    def get_ring_emp_position(self : LayoutEMPBase, emp_index : int, index : int, emp_count : int) -> v2:
        if self.is_compact:
            return v2(
                self.portrait_size.x + 15 + (200 + self.ring_size.x) * index,
                self.portrait_size.y - self.emp_ring_size.y - 15
            )
        else:
            return v2(
                self.portrait_size.x + 50 + self.get_eternal_shift(emp_count) * 2 + self.emp_size[emp_index].x * 5,
                15 + self.emp_ring_size.y * index
            )

    def get_eternal_shift(self : LayoutEMPBase, emp_count : int) -> v2:
        if emp_count > 15:
            return self.eternal_shift
        else:
            return 0

dataclass(slots=True, frozen=True)
class LayoutEMPStandard(LayoutEMPBase):
    def __init__(self : LayoutEMPStandard) -> None:
        self.is_compact = False
        self.folder = "f"
        self.portrait_size = v2(207, 432)
        self.shift = 0
        self.emp_text_offset = v2(100, 15)
        self.emp_size = (v2(133, 133), v2(100, 100))
        self.background_size = v2(
            IMAGE_SIZE.x - self.portrait_size.x - self.origin.x,
            self.portrait_size.y + self.shift
        )
        self.level_offset = self.portrait_size - (150, 50)
        self.plus_offset = self.portrait_size - (110, 100)
        self.eternal_shift = ((self.emp_size[0].x - self.emp_size[1].x) * 5) // 2

dataclass(slots=True, frozen=True)
class LayoutEMPCompact(LayoutEMPBase):
    def __init__(self : LayoutEMPCompact) -> None:
        self.is_compact = True
        self.folder = "s"
        self.portrait_size = v2(196, 196)
        self.shift = 74
        self.emp_text_offset = v2(100, 25)
        self.emp_size = (v2(104, 104), v2(77, 77))
        self.background_size = v2(
            IMAGE_SIZE.x - self.portrait_size.x - self.origin.x,
            self.portrait_size.y + self.shift
        )
        self.level_offset = self.portrait_size - (150, 50)
        self.plus_offset = self.portrait_size - (110, 100)
        self.eternal_shift = ((self.emp_size[0].x - self.emp_size[1].x) * 5) // 2

dataclass(slots=True, frozen=True)
class LayoutEMPSuperCompact(LayoutEMPCompact):
    def __init__(self : LayoutEMPSuperCompact) -> None:
        super().__init__()
        self.shift = 0

dataclass(slots=True, frozen=True)
class LayoutArtifactBase():
    is_compact : bool
    folder : str
    portrait_offset : v2
    portrait_size : v2
    vertical_size : int
    text_size_limit : int
    background_size : v2
    #constant
    origin : v2 = v2(15, 0)
    skill_offset : v2 = v2(80, 80)
    value_offset : v2 = v2(120, 0)
    description_offset : v2 = v2(210, 0)
    text_offset : v2 = v2(100, 15)

dataclass(slots=True, frozen=True)
class LayoutArtifactStandard(LayoutArtifactBase):
    def __init__(self : LayoutArtifactStandard) -> None:
        self.is_compact = False
        self.folder = "s"
        self.portrait_offset = v2(0, 7)
        self.portrait_size = v2(207, 207)
        self.vertical_size = 432
        self.text_size_limit = 55
        self.background_size = v2(IMAGE_SIZE.x - self.portrait_size.x - self.origin.x, self.vertical_size)

dataclass(slots=True, frozen=True)
class LayoutArtifactCompact(LayoutArtifactBase):
    def __init__(self : LayoutArtifactCompact) -> None:
        self.is_compact = True
        self.folder = "m"
        self.portrait_offset = v2(0, 2)
        self.portrait_size = v2(236, 135)
        self.vertical_size = 270
        self.text_size_limit = 11
        self.background_size = v2(IMAGE_SIZE.x - self.portrait_size.x - self.origin.x, self.vertical_size)

dataclass(slots=True, frozen=True)
class LayoutArtifactSuperCompact(LayoutArtifactCompact):
    def __init__(self : LayoutArtifactSuperCompact) -> None:
        super().__init__()
        self.folder = "s"
        self.portrait_size = v2(196, 196)
        self.vertical_size = 196
        self.background_size = v2(IMAGE_SIZE.x - self.portrait_size.x - self.origin.x, self.vertical_size)

dataclass(slots=True)
class GBFPIBLayout():
    mode : PartyMode
    party : LayoutPartyBase
    summon : LayoutSummon
    weapon : LayoutWeaponBase
    modifier : LayoutModifierBase
    emp : LayoutEMPBase|None
    artifact : LayoutEMPBase|None

    def __init__(self : GBFPIBLayout, mode : PartyMode, extra : bool, modifier_count : int) -> None:
        self.mode = mode
        match self.mode:
            case PartyMode.normal:
                self.party = LayoutPartyNormal()
            case PartyMode.extended:
                self.party = LayoutPartyExtended()
            case PartyMode.babyl:
                self.party = LayoutPartyBabyl()
            case _:
                raise Exception("Unimplemented")
        self.summon = LayoutSummon()
        self.weapon = LayoutWeaponExtra() if extra else LayoutWeaponStandard()
        if mode != PartyMode.normal: # more vertical space in those modes
            if modifier_count >= 32:
                self.modifier = LayoutModifierCompact()
            elif modifier_count >= 25:
                self.modifier = LayoutModifierMini()
            elif modifier_count >= 20:
                self.modifier = LayoutModifierSmall()
            else:
                self.modifier = LayoutModifierMedium()
            self.modifier.origin = v2(1560, 10)
        else:
            if modifier_count >= 27:
                self.modifier = LayoutModifierCompact()
            elif modifier_count >= 20:
                self.modifier = LayoutModifierMini()
            elif modifier_count >= 16:
                self.modifier = LayoutModifierSmall()
            else:
                self.modifier = LayoutModifierMedium()
            self.modifier.origin = v2(1560, 410)
        self.emp = None
        self.artifact = None

    def init_emp(self : GBFPIBLayout, character_count : int) -> None:
        if character_count > 8:
            self.emp = LayoutEMPSuperCompact()
        elif character_count > 5:
            self.emp = LayoutEMPCompact()
        else:
            self.emp = LayoutEMPStandard()

    def init_artifact(self : GBFPIBLayout, character_count : int) -> None:
        if character_count > 8:
            self.artifact = LayoutArtifactSuperCompact()
        elif character_count > 5:
            self.artifact = LayoutArtifactCompact()
        else:
            self.artifact = LayoutArtifactStandard()

# Main class
class GBFPIB():
    VERSION = "12.3"
    NULL_CHARACTER = [3030182000, 3020072000] # null character id list (lyria, cat...), need to be hardcoded
    # colors
    BLACK = (0, 0, 0)
    WHITE = (255, 255, 255)
    PLUS_COLOR = (255, 255, 95)
    MODIFIER_MAX_COLOR = (255, 168, 38, 255)
    AWK_COLOR = (198, 170, 240)
    DOMAIN_COLOR = (100, 210, 255)
    RADIANCE_COLOR = (110, 140, 250)
    SAINT_COLOR = (207, 145, 64)
    COLORS = { # color for estimated advantage, per element
        1:(243, 48, 33),
        2:(85, 176, 250),
        3:(227, 124, 32),
        4:(55, 232, 16),
        5:(253, 216, 67),
        6:(176, 84, 251)
    }
    COLORS_EN = { # color strings
        1:"Fire",
        2:"Water",
        3:"Earth",
        4:"Wind",
        5:"Light",
        6:"Dark"
    }
    COLORS_JP = { # color strings
        1:"火",
        2:"水",
        3:"土",
        4:"風",
        5:"光",
        6:"闇"
    }
    AUXILIARY_CLS = {
        100401, 300301, 300201, 120401, 140401, 180401
    }
    # IDs for special weapons
    DARK_OPUS_IDS = {
        "1040310600","1040310700","1040415000","1040415100","1040809400","1040809500","1040212500","1040212600","1040017000","1040017100","1040911000","1040911100",
        "1040310600_02","1040310700_02","1040415000_02","1040415100_02","1040809400_02","1040809500_02","1040212500_02","1040212600_02","1040017000_02","1040017100_02","1040911000_02","1040911100_02",
        "1040310600_03","1040310700_03","1040415000_03","1040415100_03","1040809400_03","1040809500_03","1040212500_03","1040212600_03","1040017000_03","1040017100_03","1040911000_03","1040911100_03"
    }
    ULTIMA_IDS = {
        "1040011900","1040012000","1040012100","1040012200","1040012300","1040012400",
        "1040109700","1040109800","1040109900","1040110000","1040110100","1040110200",
        "1040208800","1040208900","1040209000","1040209100","1040209200","1040209300",
        "1040307800","1040307900","1040308000","1040308100","1040308200","1040308300",
        "1040410800","1040410900","1040411000","1040411100","1040411200","1040411300",
        "1040507400","1040507500","1040507600","1040507700","1040507800","1040507900",
        "1040608100","1040608200","1040608300","1040608400","1040608500","1040608600",
        "1040706900","1040707000","1040707100","1040707200","1040707300","1040707400",
        "1040807000","1040807100","1040807200","1040807300","1040807400","1040807500",
        "1040907500","1040907600","1040907700","1040907800","1040907900","1040908000"
    }
    ORIGIN_DRACONIC_IDS = {
        "1040815900","1040316500","1040712800","1040422200","1040915600","1040516500"
    }
    DESTRUCTION_IDS = {
        "1040028900","1040122300","1040220300","1040621200","1040714700","1040817900"
    }
    # User Agent (required for the wiki)
    USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36 Rosetta/GBFPIB'
    
    def __init__(self : GBFPIB) -> None:
        self.gbftmr = None # will contain a GBFTMR instance if configured properly
        self.layout : GBFPIBLayout = None
        self.japanese : bool = False # True if the data is japanese, False if not
        self.classes : dict[str, str] = None # cached classes
        self.class_modified : bool = False
        self.prev_lang : str = None # Language used in the previous run
        self.extra_grid : bool = False # True if the data contains more than 10 weapons
        self.pending : set[str] = set() # pending downloads
        self.cache : dict[str, IMG] = {} # memory cache
        self.emp_cache : dict[str, dict] = {} # emp cache
        self.artifact_cache : dict[str, dict] = {} # artifact cache
        self.sumcache : dict[str, str] = {} # wiki summon cache
        self.fonts : dict[str, ImageFont] = {'mini':None, 'small':None, 'medium':None, 'big':None} # font to use during the processing
        self.quality : float = 1 # quality ratio in use currently
        self.definition : tuple[int, int] = None # image size
        self.running : bool = False # True if the image building is in progress
        self.settings : dict[str, str|int|bool] = {} # settings
        self.dummy_layer : IMG = self.blank_image() # blank image used during generation
        self.client : aiohttp.ClientSession = None # HTTP client

    # init the HTTP client
    @asynccontextmanager
    async def init_client(self : GBFPIB) -> Generator[aiohttp.ClientSession, None, None]:
        try:
            self.client = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=20))
            yield self.client
        finally:
            await self.client.close()

    # transform an exception to a readable string
    def pexc(self : GBFPIB, e : Exception) -> str:
        return "".join(traceback.format_exception(type(e), e, e.__traceback__))

    # load classes.json
    def loadClasses(self : GBFPIB) -> None:
        try:
            self.class_modified = False
            with open("classes.json", mode="r", encoding="utf-8") as f:
                self.classes = json.load(f)
        except:
            self.classes = {}

    # save classes.json
    def saveClasses(self : GBFPIB) -> None:
        try:
            if self.class_modified:
                with open("classes.json", mode='w', encoding='utf-8') as outfile:
                    json.dump(self.classes, outfile)
        except:
            pass

    # retrieve an image from the given path/url
    async def get(self : GBFPIB, path : str, remote : bool = True, forceDownload : bool = False) -> bytes:
        # check language
        if self.japanese:
            path = path.replace('assets_en', 'assets')
        # check if retrieval is pending
        while path in self.pending:
            await asyncio.sleep(0.005)
        self.pending.add(path)
        try:
            # retrieve
            if forceDownload or path not in self.cache:
                try: # get from disk cache if enabled
                    if forceDownload:
                        raise Exception() # go to exception/download block
                    if self.settings.get('caching', False):
                        with open("cache/" + b64encode(path.encode('utf-8')).decode('utf-8'), "rb") as f:
                            self.cache[path] = IMG(f.read())
                        await asyncio.sleep(0)
                    else:
                        raise Exception()
                except: # else request it from gbf
                    if remote:
                        print("[GET] *Downloading File", path)
                        response : aiohttp.Response = await self.client.get('https://' + self.settings.get('endpoint', 'prd-game-a-granbluefantasy.akamaized.net/') + path, headers={'connection':'keep-alive'})
                        async with response:
                            if response.status != 200:
                                raise Exception("HTTP Error code {} for url: {}".format(response.status, 'https://' + self.settings.get('endpoint', 'prd-game-a-granbluefantasy.akamaized.net/') + path))
                            io : bytes = await response.read()
                            self.cache[path] = IMG(io)
                            if self.settings.get('caching', False):
                                try:
                                    with open("cache/" + b64encode(path.encode('utf-8')).decode('utf-8'), "wb") as f:
                                        f.write(io)
                                    await asyncio.sleep(0)
                                except Exception as e:
                                    print(self.pexc(e))
                                    pass
                    else:
                        with open(path, "rb") as f:
                            self.cache[path] = IMG(f.read())
                        await asyncio.sleep(0)
            # end
            self.pending.remove(path)
            return self.cache[path]
        except Exception as ex:
            self.pending.remove(path) # failsafe
            raise ex

    # paste an image onto our list of images for given range
    async def paste(self : GBFPIB, imgs : list[IMG], indexes : range, file : str|IMG, offset : tuple[int, int], *, resize : tuple[int, int]|None = None, transparency : bool = False, crop : tuple[int, int]|tuple[int, int, int, int]|None = None) -> list[IMG]:
        # get file
        if isinstance(file, str):
            if self.japanese:
                file = file.replace('_EN', '')
            file = await self.get(file, remote=False)
        # crop
        if crop is not None:
            file = file.crop(crop)
        # resize
        if resize is not None:
            file = file.resize(resize)
        # paste
        if not transparency:
            for i in indexes:
                imgs[i].paste(file, offset)
        else:
            layer = self.dummy_layer.copy()
            layer.paste(file, offset)
            for i in indexes:
                imgs[i] = imgs[i].alpha(layer)
        await asyncio.sleep(0)
        # return
        return imgs

    # download and paste an image onto our list of images for given range
    async def pasteDL(self : GBFPIB, imgs : list[IMG], indexes : range, path : str, offset : tuple[int, int], *, resize : tuple[int, int]|None = None, transparency : bool = False, crop : tuple[int, int]|tuple[int, int, int, int]|None = None) -> list: # dl an image and call pasteImage()
        return await self.paste(imgs, indexes, await self.get(path), offset, resize=resize, transparency=transparency, crop=crop)

    # write text on images
    def text(self : GBFPIB, imgs : list[IMG], indexes : range, *args, **kwargs) -> None:
        for i in indexes:
            ImageDraw.Draw(imgs[i].image, 'RGBA').text(*args, **kwargs)

    # write multiline text on images
    def multiline_text(self : GBFPIB, imgs : list[IMG], indexes : range, *args, **kwargs) -> None:
        for i in indexes:
            ImageDraw.Draw(imgs[i].image, 'RGBA').multiline_text(*args, **kwargs)

    # search in the gbf.wiki cargo table to match a summon name to its id
    async def get_support_summon_from_wiki(self : GBFPIB, name : str) -> str|None: 
        try:
            name = name.lower()
            if name in self.sumcache:
                return self.sumcache[name]
            response : aiohttp.Response = await self.client.get(
                "https://gbf.wiki/index.php",
                headers={'connection':'close', 'User-Agent':self.USER_AGENT},
                params={
                    "title":"Special:CargoExport",
                    "table":"summons",
                    "fields":"id,name,jpname",
                    "format":"json",
                    "limit":"1",
                    "where":'name = "{}" OR jpname = "{}"'.format(name, name)
                }
            )
            async with response:
                if response.status != 200:
                    raise Exception()
                data : list = await response.json()
                for summon in data:
                    if summon["name"].lower() == name or summon["jpname"].lower():
                        self.sumcache[name] = summon["id"]
                        return summon["id"]
            return None
        except Exception as e:
            print(self.pexc(e))
            return None
    
    # get character portraits based on uncap levels
    def get_uncap_id(self : GBFPIB, cs : int) -> str:
        return {2:'02', 3:'02', 4:'02', 5:'03', 6:'04'}.get(cs, '01')

    # get character uncap star based on uncap levels
    def get_uncap_star(self : GBFPIB, cs : int, cl : int) -> str:
        match cs:
            case 4:
                return "assets/star_1.png"
            case 5:
                return "assets/star_2.png"
            case 6:
                if cl <= 110:
                    return "assets/star_4_1.png"
                elif cl <= 120:
                    return "assets/star_4_2.png"
                elif cl <= 130:
                    return "assets/star_4_3.png"
                elif cl <= 140:
                    return "assets/star_4_4.png"
                elif cl <= 150:
                    return "assets/star_4_5.png"
            case _:
                return "assets/star_0.png"

     # get summon star based on uncap levels
    def get_summon_star(self : GBFPIB, se : int, sl : int) -> str:
        match se:
            case 3:
                return "assets/star_1.png"
            case 4:
                return "assets/star_2.png"
            case 5:
                return "assets/star_3.png"
            case 6:
                if sl <= 210:
                    return "assets/star_4_1.png"
                elif sl <= 220:
                    return "assets/star_4_2.png"
                elif sl <= 230:
                    return "assets/star_4_3.png"
                elif sl <= 240:
                    return "assets/star_4_4.png"
                elif sl <= 250:
                    return "assets/star_4_5.png"
            case _:
                return "assets/star_0.png"

    # get portrait of character for given skin
    def get_character_look(self : GBFPIB, export : dict, i : int) -> str:
        style = ("" if str(export['cst'][i]) == '1' else "_st{}".format(export['cst'][i])) # style check
        # get uncap
        if style != "":
            uncap = "01"
        else:
            uncap = self.get_uncap_id(export['cs'][i])
        cid = export['c'][i]
        # Beginning of the part to fix some exceptions
        if str(cid).startswith('371'):
            match cid:
                case 3710098000: # seox skin
                    if export['cl'][i] > 80:
                        cid = 3040035000 # eternal seox
                    else:
                        cid = 3040262000 # event seox
                case 3710122000: # seofon skin
                    cid = 3040036000 # eternal seofon
                case 3710143000: # vikala skin
                    if export['ce'][i] == 3:
                        cid = 3040408000 # apply earth vikala
                    elif export['ce'][i] == 6:
                        if export['cl'][i] > 50:
                            cid = 3040252000 # SSR dark vikala
                        else:
                            cid = 3020073000 # R dark vikala
                case 3710154000: # clarisse skin
                    match export['ce'][i]:
                        case 2: cid = 3040413000 # water
                        case 3: cid = 3040067000 # earth
                        case 5: cid = 3040121000 # light
                        case 6: cid = 3040206000 # dark
                        case _: cid = 3040046000 # fire
                case 3710165000: # diantha skin
                    match export['ce'][i]:
                        case 2:
                            if export['cl'][i] > 70:
                                cid = 3040129000 # water SSR
                            else:
                                cid = 3030150000 # water SR
                        case 3:
                            cid = 3040296000 # earth
                case 3710172000: # tsubasa skin
                    cid = 3040180000
                case 3710176000: # mimlemel skin
                    if export['ce'][i] == 1:
                        cid = 3040292000 # apply fire mimlemel
                    elif export['ce'][i] == 3:
                        cid = 3030220000 # apply earth halloween mimlemel
                    elif export['ce'][i] == 4:
                        if export['cn'][i] in ('Mimlemel', 'ミムルメモル'):
                            cid = 3030043000 # first sr wind mimlemel
                        else:
                            cid = 3030166000 # second sr wind mimlemel
                case 3710191000: # cidala skin 1
                    if export['ce'][i] == 3:
                        cid = 3040377000 # apply earth cidala
                    elif export['ce'][i] == 5:
                        cid = 3040512000 # apply dark cidala
                case 3710195000: # cidala skin 2
                    if export['ce'][i] == 3:
                        cid = 3040377000 # apply earth cidala
                    elif export['ce'][i] == 5:
                        cid = 3040512000 # apply dark cidala
        # End of the exceptions
        
        # Return string
        if cid in self.NULL_CHARACTER: 
            if export['ce'][i] == 99:
                return "{}_{}{}_0{}".format(cid, uncap, style, export['pce'])
            else:
                return "{}_{}{}_0{}".format(cid, uncap, style, export['ce'][i])
        else:
            return "{}_{}{}".format(cid, uncap, style)

    # get MC portrait without skin
    async def get_mc_job_look(self : GBFPIB, skin : str, job : int) -> str:
        sjob : str = str((job//100) * 100 + 1)
        if sjob in self.classes:
            return "{}_{}_{}".format(sjob, self.classes[sjob], '_'.join(skin.split('_')[2:]))
        else:
            tasks = []
            # look for job MH
            for mh in ["sw", "kn", "sp", "ax", "wa", "gu", "me", "bw", "mc", "kr"]:
                tasks.append(self.get_mc_job_look_sub(sjob, mh))
            for r in await asyncio.gather(*tasks):
                if r is not None:
                    self.class_modified = True
                    self.classes[sjob] = r
                    return "{}_{}_{}".format(sjob, self.classes[sjob], '_'.join(skin.split('_')[2:])) 
        return ""

    # subroutine of get_mc_job_look
    async def get_mc_job_look_sub(self : GBFPIB, job : str, mh : str) -> str|None:
        response : aiohttp.Response = await self.client.head("https://prd-game-a5-granbluefantasy.akamaized.net/assets_en/img/sp/assets/leader/s/{}_{}_0_01.jpg".format(job, mh))
        async with response:
            if response.status != 200:
                return None
            return mh

    def process_special_weapon(self : GBFPIB, export : dict, i : int, j : int) -> bool:
        if export['wsn'][i][j] is not None and export['wsn'][i][j] == "skill_job_weapon":
            if j == 2: # skill 3, ultima, opus
                if export['w'][i] in self.DARK_OPUS_IDS:
                    bar_gain = 0
                    hp_cut = 0
                    turn_dmg = 0
                    prog = 0
                    ca_dmg = 0
                    ca_dmg_cap = 0
                    auto_amp_sp = 0
                    skill_amp_sp = 0
                    ca_amp_sp = 0
                    for m in export['mods']:
                        try:
                            match m['icon_img']:
                                case '04_icon_ca_gage.png':
                                    bar_gain = float(m['value'].replace('%', ''))
                                case '03_icon_hp_cut.png':
                                    hp_cut = float(m['value'].replace('%', ''))
                                case '03_icon_turn_dmg.png':
                                    turn_dmg = float(m['value'].replace('%', ''))
                                case '01_icon_e_atk_01.png':
                                    prog = float(m['value'].replace('%', ''))
                                case '04_icon_ca_dmg.png':
                                    ca_dmg = float(m['value'].replace('%', ''))
                                case '04_icon_ca_dmg_cap.png':
                                    ca_dmg_cap = float(m['value'].replace('%', ''))
                                case '04_icon_normal_dmg_amp_other.png':
                                    auto_amp_sp = float(m['value'].replace('%', ''))
                                case '04_icon_ability_dmg_amplify_other.png':
                                    skill_amp_sp = float(m['value'].replace('%', ''))
                                case '04_icon_ca_dmg_amplify_other.png':
                                    ca_amp_sp = float(m['value'].replace('%', ''))
                        except:
                            pass
                    if hp_cut >= 30: # temptation
                        export['wsn'][i][j] = "assets_en/img/sp/assets/item/skillplus/s/14014.jpg"
                        return True
                    elif auto_amp_sp >= 10: # extremity
                        export['wsn'][i][j] = "assets_en/img/sp/assets/item/skillplus/s/14005.jpg"
                        return True
                    elif skill_amp_sp >= 10: # sagacity
                        export['wsn'][i][j] = "assets_en/img/sp/assets/item/skillplus/s/14006.jpg"
                        return True
                    elif ca_amp_sp >= 10: # supremacy
                        export['wsn'][i][j] = "assets_en/img/sp/assets/item/skillplus/s/14007.jpg"
                        return True
                    elif bar_gain <= -50 and bar_gain > -200: # falsehood
                        export['wsn'][i][j] = "assets_en/img/sp/assets/item/skillplus/s/14017.jpg"
                        return True
                    elif prog > 0: # progression
                        export['wsn'][i][j] = "assets_en/img/sp/assets/item/skillplus/s/14004.jpg"
                        return True
                    elif ca_dmg >= 100 and ca_dmg_cap >= 30: # forbiddance
                        export['wsn'][i][j] = "assets_en/img/sp/assets/item/skillplus/s/14015.jpg"
                        return True
                    elif turn_dmg >= 5: # depravity
                        export['wsn'][i][j] = "assets_en/img/sp/assets/item/skillplus/s/14016.jpg"
                        return True
                elif export['w'][i] in self.ULTIMA_IDS:
                    seraphic = 0
                    heal_cap = 0
                    bar_gain = 0
                    cap_up = 0
                    for m in export['mods']:
                        try:
                            match m['icon_img']:
                                case '04_icon_elem_amplify.png':
                                    seraphic = float(m['value'].replace('%', ''))
                                case '04_icon_dmg_cap.png':
                                    cap_up = float(m['value'].replace('%', ''))
                                case '04_icon_ca_gage.png':
                                    bar_gain = float(m['value'].replace('%', ''))
                                case '03_icon_heal_cap.png':
                                    heal_cap = float(m['value'].replace('%', ''))
                        except:
                            pass
                    if seraphic >= 25: # tria
                        export['wsn'][i][2] = "assets_en/img/sp/assets/item/skillplus/s/17003.jpg"
                        return True
                    elif heal_cap >= 50 and bar_gain >= 10: # dio / tessera better guess (EXPERIMENTAL)
                        count = 0
                        for a in export['wsn']:
                            for b in a:
                                if b is None: continue
                                elif "heal_limit_m" in b: count += 1
                                elif "heal_limit" in b: count += 1
                        if count >= 3: export['wsn'][i][2] = "assets_en/img/sp/assets/item/skillplus/s/17004.jpg"
                        elif count == 2: return False # unsure
                        else: export['wsn'][i][2] = "assets_en/img/sp/assets/item/skillplus/s/17002.jpg"
                        return True
                    elif heal_cap >= 50: # dio
                        export['wsn'][i][2] = "assets_en/img/sp/assets/item/skillplus/s/17002.jpg"
                        return True
                    elif bar_gain >= 10: # tessera
                        export['wsn'][i][2] = "assets_en/img/sp/assets/item/skillplus/s/17004.jpg"
                        return True
                    elif cap_up >= 10: # ena
                        export['wsn'][i][2] = "assets_en/img/sp/assets/item/skillplus/s/17001.jpg"
                        return True
                elif export['w'][i] in self.DESTRUCTION_IDS:
                    skill_supp = 0
                    skill_cap = 0
                    ca_supp = 0
                    ca_cap = 0
                    auto_supp = 0
                    auto_cap = 0
                    for m in export['mods']:
                        try:
                            match m['icon_img']:
                                case '04_icon_skill_dmg_supp_other.png':
                                    skill_supp = int(m['value'].replace('+', ''))
                                case '04_icon_ca_supp_other.png':
                                    ca_supp = int(m['value'].replace('+', ''))
                                case '04_icon_normal_dmg_supp_other.png':
                                    auto_supp = int(m['value'].replace('+', ''))
                                case "04_icon_skill_dmg_cap.png":
                                    skill_cap = float(m['value'].replace('%', ''))
                                case "04_icon_ca_dmg_cap.png":
                                    ca_cap = float(m['value'].replace('%', ''))
                                case "04_icon_na_dmg_cap.png":
                                    auto_cap = float(m['value'].replace('%', ''))
                        except:
                            pass
                    if skill_supp >= 30000 and skill_cap >= 50:
                        export['wsn'][i][j] = "assets_en/img/sp/assets/item/skillplus/s/19002.jpg"
                        return True
                    if ca_supp >= 100000 and ca_cap >= 50:
                        print("WARNING: Destruction CA supplemental needs to be verified")
                        export['wsn'][i][j] = "assets_en/img/sp/assets/item/skillplus/s/19003.jpg"
                        return True
                    if auto_supp >= 20000 and auto_cap >= 10:
                        export['wsn'][i][j] = "assets_en/img/sp/assets/item/skillplus/s/19001.jpg"
                        return True
            elif j == 1: # skill 2, hexa draconic
                if export['w'][i] in self.ORIGIN_DRACONIC_IDS:
                    seraphic = 0
                    for m in export['mods']:
                        try:
                            match m['icon_img']:
                                case '04_icon_plain_amplify.png':
                                    seraphic = float(m['value'].replace('%', ''))
                        except:
                            pass
                    if seraphic >= 10: # oblivion teluma
                        export['wsn'][i][j] = "assets_en/img/sp/assets/item/skillplus/s/15009.jpg"
                        return True
        return False

    def blank_image(self : GBFPIB) -> IMG:
        i = Image.new('RGB', IMAGE_SIZE.i, "black")
        im_a = Image.new("L", IMAGE_SIZE.i, "black")
        i.putalpha(im_a)
        im_a.close()
        return IMG(i)

    async def make_party(self : GBFPIB, export : dict) -> str|tuple[str, list[IMG]]:
        try:
            imgs : list[IMG] = [self.blank_image(), self.blank_image()]
            print("[CHA] * Drawing Party...")
            # starting position
            pos = self.layout.party.start
            # background
            await self.paste(
                imgs, range(1),
                "assets/bg.png",
                self.layout.party.background_offset.i,
                resize=self.layout.party.background_size.i, 
                transparency=True
            )
            # mc
            print("[CHA] |--> MC Skin:", export['pcjs'])
            print("[CHA] |--> MC Job:", export['p'])
            print("[CHA] |--> MC Master Level:", export['cml'])
            print("[CHA] |--> MC Proof Level:", export['cbl'])
            # class
            class_id = await self.get_mc_job_look(export['pcjs'], export['p'])
            await self.pasteDL(
                imgs, range(1),
                "assets_en/img/sp/assets/leader/s/{}.jpg".format(class_id),
                pos.i,
                resize=self.layout.party.portrait_layout.i
            )
            # job icon
            await self.pasteDL(
                imgs, range(1),
                "assets_en/img/sp/ui/icon/job/{}.png".format(export['p']),
                pos.i,
                resize=self.layout.party.job_icon_size.i,
                transparency=True
            )
            if export['cbl'] == '6':
                await self.pasteDL(
                    imgs, range(1),
                    "assets_en/img/sp/ui/icon/job/ico_perfection.png",
                    (pos + (0, self.layout.party.job_icon_size[1])).i,
                    resize=self.layout.party.job_icon_size.i,
                    transparency=True
                )
            # skin
            if class_id != export['pcjs']:
                await self.pasteDL(
                    imgs, range(1, 2),
                    "assets_en/img/sp/assets/leader/s/{}.jpg".format(export['pcjs']),
                    pos.i,
                    resize=self.layout.party.portrait_layout.i
                )
                await self.pasteDL(
                    imgs, range(1, 2),
                    "assets_en/img/sp/ui/icon/job/{}.png".format(export['p']),
                    pos.i,
                    resize=self.layout.party.job_icon_size, 
                    transparency=True
                )
            # allies
            for i in range(0, self.layout.party.character_count):
                if i == 0 and self.layout.party.skip_zero:
                    continue
                await asyncio.sleep(0)
                pos = self.layout.party.get_portrait_position(i)
                # portrait
                if i >= len(export['c']) or export['c'][i] is None: # empty
                    await self.pasteDL(
                        imgs, range(1),
                        "assets_en/img/sp/tower/assets/npc/s/3999999999.jpg",
                        pos.i,
                        resize=self.layout.party.portrait_layout.i
                    )
                    continue
                print(
                    "[CHA] |--> Ally #{}:".format(i+1), export['c'][i], export['cn'][i],
                    "Lv {}".format(export['cl'][i]),
                    "Uncap-{}".format(export['cs'][i]),
                    "+{}".format(export['cp'][i]),
                    "Has Ring" if export['cwr'][i] else "No Ring"
                )
                # portrait
                cid = self.get_character_look(export, i)
                await self.pasteDL(
                    imgs, range(1),
                    "assets_en/img/sp/assets/npc/s/{}.jpg".format(cid),
                    pos.i,
                    resize=self.layout.party.portrait_layout.i
                )
                # skin
                has_skin : bool
                if cid != export['ci'][i]:
                    await self.pasteDL(
                        imgs, range(1, 2),
                        "assets_en/img/sp/assets/npc/s/{}.jpg".format(export['ci'][i]),
                        pos.i,
                        resize=self.layout.party.portrait_layout.i
                    )
                    has_skin = True
                else:
                    has_skin = False
                # star
                await self.paste(
                    imgs, range(2 if has_skin else 1),
                    self.get_uncap_star(export['cs'][i], export['cl'][i]),
                    (pos + self.layout.party.star_offset).i,
                    resize=self.layout.party.star_icon_size.i,
                    transparency=True
                )
                # rings
                if export['cwr'][i] == True:
                    await self.pasteDL(
                        imgs, range(2 if has_skin else 1),
                        "assets_en/img/sp/ui/icon/augment2/icon_augment2_l.png",
                        (pos + self.layout.party.ring_offset).i,
                        resize=self.layout.party.ring_icon_size.i,
                        transparency=True
                    )
                # plus
                if export['cp'][i] > 0:
                    self.text(
                        imgs, range(2 if has_skin else 1),
                        (pos + self.layout.party.plus_mark_offset).i,
                        "+{}".format(export['cp'][i]),
                        fill=self.PLUS_COLOR,
                        font=self.fonts['small'],
                        stroke_width=6,
                        stroke_fill=self.BLACK
                    )
                if self.layout.party.display_name:
                    # name
                    await self.paste(
                        imgs, range(1),
                        "assets/chara_stat.png",
                        (pos + (0, self.layout.party.portrait_layout.y)).i,
                        resize=(self.layout.party.portrait_layout.x, 60),
                        transparency=True
                    )
                    if len(export['cn'][i]) > 11:
                        name = export['cn'][i][:11] + ".."
                    else:
                        name = export['cn'][i]
                    self.text(
                        imgs, range(1),
                        (pos + self.layout.party.name_offset).i,
                        name,
                        fill=self.WHITE,
                        font=self.fonts['mini']
                    )
                    # skill count
                    await self.paste(
                        imgs, range(1),
                        "assets/skill_count_EN.png",
                        (pos + (0, self.layout.party.portrait_layout.y + 60)).i,
                        resize=(self.layout.party.portrait_layout.x, 60),
                        transparency=True
                    )
                    self.text(
                        imgs, range(1),
                        (pos + self.layout.party.bonus_count_offset + (150, 0)).i,
                        str(export['cb'][i+1]),
                        fill=self.WHITE,
                        font=self.fonts['medium'],
                        stroke_width=4,
                        stroke_fill=self.BLACK
                    )
            await asyncio.sleep(0)
            # mc sub skills
            await self.paste(
                imgs, range(2),
                "assets/subskills.png",
                self.layout.party.skill_box_offset.i,
                resize=self.layout.party.skill_box_size
            )
            count : int = 0
            f : str
            voff : int
            for i in range(len(export['ps'])):
                if export['ps'][i] is not None:
                    print("[CHA] |--> MC Skill #{}:".format(i), export['ps'][i])
                    if len(export['ps'][i]) > 20:
                        f = 'mini'
                        voff = 5
                    elif len(export['ps'][i]) > 15:
                        f = 'small'
                        voff = 2
                    else:
                        f = 'medium'
                        voff = 0
                    self.text(
                        imgs, range(2),
                        (self.layout.party.skill_text_offset + (0, self.layout.party.skill_line_space * count + voff)).i,
                        export['ps'][i],
                        fill=self.WHITE,
                        font=self.fonts[f]
                    )
                    count += 1
            await asyncio.sleep(0)
            # paladin shield/manadiver familiar
            if export['cpl'] is not None:
                print("[CHA] |--> Paladin shield:", export['cpl'])
                await self.pasteDL(
                    imgs, range(1),
                    "assets_en/img/sp/assets/shield/s/{}.jpg".format(export['cpl']),
                    self.layout.party.accessory_offset.i,
                    resize=self.layout.party.accessory_size
                )
            elif export['fpl'] is not None:
                print("[CHA] |--> Manadiver Manatura:", export['fpl'])
                await self.pasteDL(
                    imgs, range(1),
                    "assets_en/img/sp/assets/familiar/s/{}.jpg".format(export['fpl']),
                    self.layout.party.accessory_offset.i,
                    resize=self.layout.party.accessory_size
                )
            return ('party', imgs)
        except Exception as e:
            return self.pexc(e)

    async def make_summon(self : GBFPIB, export : dict) -> str|tuple:
        try:
            imgs : list[IMG] = [self.blank_image(), self.blank_image()]
            print("[SUM] * Drawing Summons...")
            # background setup
            await self.paste(
                imgs, range(1),
                "assets/bg.png",
                self.layout.summon.background_offset.i,
                resize=self.layout.summon.background_size.i,
                transparency=True
            )
            pos : v2
            for i in range(0, 7):
                await asyncio.sleep(0)
                if i == 5:
                    await self.paste(
                        imgs, range(1),
                        "assets/subsummon_EN.png",
                        self.layout.summon.sub_marker_offset.i,
                        resize=self.layout.summon.sub_marker_size.i,
                        transparency=True
                    )
                pos : v2 = self.layout.summon.get_portrait_position(i)
                psize : v2 = self.layout.summon.get_portrait_size(i)
                # portraits
                if export['s'][i] is None:
                    await self.pasteDL(
                        imgs, range(1),
                        "assets_en/img/sp/assets/summon/{}/2999999999.jpg".format(self.layout.summon.get_asset_folder(i)[1]),
                        pos.i,
                        resize=psize.i
                    )
                    continue
                else:
                    print(
                        "[SUM] |--> Summon #{}:".format(i+1),
                        export['ss'][i],
                        "Uncap Lv{}".format(export['se'][i]),
                        "Lv{}".format(export['sl'][i])
                    )
                    await self.pasteDL(
                        imgs, range(1),
                        "assets_en/img/sp/assets/summon/{}/{}.jpg".format(self.layout.summon.get_asset_folder(i)[0], export['ss'][i]),
                        pos.i,
                        resize=psize.i
                    )
                # main summon skin
                has_skin : bool
                if i == 0 and export['ssm'] is not None:
                    await self.pasteDL(
                        imgs, range(1, 2),
                        "assets_en/img/sp/assets/summon/{}/{}.jpg".format(self.layout.summon.get_asset_folder(i)[0], export['ssm']),
                        pos.i,
                        resize=psize.i
                    )
                    await self.paste(
                        imgs, range(1, 2),
                        "assets/skin.png",
                        (pos + self.layout.summon.skin_icon_offset).i,
                        resize=self.layout.summon.skin_icon_size.i
                    )
                    has_skin = True
                else:
                    has_skin = False
                # star
                await self.paste(
                    imgs, range(2 if has_skin else 1),
                    self.get_summon_star(export['se'][i], export['sl'][i]),
                    pos.i,
                    resize=self.layout.summon.icon_size.i,
                    transparency=True
                )
                # quick summon
                if export['qs'] is not None and export['qs'] == i:
                    await self.paste(
                        imgs, range(2 if has_skin else 1),
                        "assets/quick.png",
                        (pos + (0, self.layout.summon.icon_size.y)).i,
                        resize=self.layout.summon.icon_size.i,
                        transparency=True
                    )
                # level
                await self.paste(
                    imgs, range(1),
                    "assets/chara_stat.png",
                    (pos + (0, psize.y)).i,
                    resize=(psize.x, 60),
                    transparency=True
                )
                self.text(
                    imgs, range(1),
                    (pos + (6 , psize.y + 9)).i,
                    "Lv{}".format(export['sl'][i]),
                    fill=self.WHITE,
                    font=self.fonts['small']
                )
                # plus
                if export['sp'][i] > 0:
                    self.text(
                        imgs, range(2 if has_skin else 1),
                        (pos + psize + self.layout.summon.plus_offset),
                        "+{}".format(export['sp'][i]),
                        fill=self.PLUS_COLOR,
                        font=self.fonts['medium'],
                        stroke_width=6,
                        stroke_fill=self.BLACK
                    )
            await asyncio.sleep(0)
            # stats
            spos = self.layout.summon.stat_offset # position
            await self.paste(
                imgs, range(1), "assets/chara_stat.png", 
                spos.i,
                resize=self.layout.summon.stat_size.i,
                transparency=True
            )
            await self.paste(
                imgs, range(1),
                "assets/atk.png",
                (spos + self.layout.summon.stat_icon_offset).i,
                resize=self.layout.summon.stat_atk_size.i,
                transparency=True
            )
            await self.paste(
                imgs, range(1),
                "assets/hp.png",
                (spos + v2(self.layout.summon.sub_size.x, 0) + self.layout.summon.stat_icon_offset).i,
                resize=self.layout.summon.stat_hp_size.i,
                transparency=True
            )
            self.text(
                imgs, range(1),
                (spos + self.layout.summon.stat_atk_text_offset).i,
                "{}".format(export['satk']),
                fill=self.WHITE,
                font=self.fonts['small']
            )
            self.text(
                imgs, range(1),
                (spos + self.layout.summon.stat_hp_text_offset).i,
                "{}".format(export['shp']),
                fill=self.WHITE,
                font=self.fonts['small']
            )
            return ('summon', imgs)
        except Exception as e:
            return self.pexc(e)

    async def make_weapon(self : GBFPIB, export : dict) -> str|tuple:
        try:
            imgs = [self.blank_image(), self.blank_image()]
            self.multiline_text(
                imgs, range(2),
                (1540, 2125),
                "GBFPIB " + self.VERSION,
                fill=(120, 120, 120, 255),
                font=self.fonts['mini']
            )
            print("[WPN] * Drawing Weapons...")
            await self.paste(
                imgs, range(1),
                "assets/grid_bg.png",
                self.layout.weapon.background_offset.i,
                resize=self.layout.weapon.background_size.i,
                transparency=True
            )
            if self.extra_grid:
                await self.paste(
                    imgs, range(1),
                    "assets/grid_bg_extra.png",
                    self.layout.weapon.extra_grid_icon_offset.i,
                    resize=self.layout.weapon.extra_grid_icon_size.i,
                    transparency=True
                )

            for i in range(0, len(export['w'])):
                await asyncio.sleep(0)
                wt : str = "ls" if i == 0 else "m"
                pos : v2 = self.layout.weapon.get_portrait_position(i)
                size : v2 = self.layout.weapon.get_portrait_size(i)
                # dual blade class
                if i <= 1 and export['p'] in self.AUXILIARY_CLS:
                    await self.paste(
                        imgs, range(1),
                        ("assets/mh_dual.png" if i == 0 else "assets/aux_dual.png"),
                        (pos + self.layout.weapon.auxiliary_offset).i,
                        resize=(size + self.layout.weapon.auxiliary_size).i,
                        transparency=True
                    )
                # portrait
                if export['w'][i] is None or export['wl'][i] is None:
                    if i >= 10:
                        await self.paste(
                            imgs, range(1),
                            "assets/arca_slot.png",
                            pos.i,
                            resize=size.i
                        )
                    else:
                        await self.pasteDL(
                            imgs, range(1),
                            "assets_en/img/sp/assets/weapon/{}/1999999999.jpg".format(wt),
                            pos.i,
                            resize=size.i
                        )
                    continue
                # ax and awakening check
                has_ax : bool = len(export['waxt'][i]) > 0
                has_awakening : bool = (export['wakn'][i] is not None and export['wakn'][i]['is_arousal_weapon'] and export['wakn'][i]['level'] is not None and export['wakn'][i]['level'] > 1)
                # vertical shift of the skill boxes (if both ax and awk are presents)
                pos_shift : int = - self.layout.weapon.skill_icon_size.y if (has_ax and has_awakening) else 0
                # portrait draw
                print(
                    "[WPN] |--> Weapon #{}".format(i+1),
                    str(export['w'][i]),
                    ", AX:", has_ax,
                    ", Awakening:", has_awakening
                )
                await self.pasteDL(
                    imgs, range(1),
                    "assets_en/img/sp/assets/weapon/{}/{}.jpg".format(wt, export['w'][i]),
                    pos.i,
                    resize=size.i
                )
                # skin
                has_skin : bool = False
                if i <= 1 and export['wsm'][i] is not None:
                    if i == 0 or (i == 1 and export['p'] in self.AUXILIARY_CLS): # aux class check for 2nd weapon
                        await self.pasteDL(
                            imgs, range(1, 2),
                            "assets_en/img/sp/assets/weapon/{}/{}.jpg".format(wt, export['wsm'][i]),
                            pos.i,
                            resize=size.i
                        )
                        await self.paste(
                            imgs, range(1, 2),
                            "assets/skin.png",
                            (pos + (size.x, 0) + self.layout.weapon.skin_icon_offset).i,
                            resize=self.layout.weapon.skin_icon_size.i,
                            transparency=True
                        )
                        has_skin = True
                # skill box
                nbox : int = 1 # number of skill boxes to draw
                if has_ax:
                    nbox += 1
                if has_awakening:
                    nbox += 1
                for j in range(nbox):
                    # if 3 boxes and we aren't on the mainhand, we draw half of one for the first box
                    if i != 0 and j == 0 and nbox == 3:
                        await self.paste(
                            imgs, range(2 if (has_skin and j == 0) else 1),
                            "assets/skill.png",
                            (
                                pos.x + size.x // 2,
                                pos.y + size.y + pos_shift + self.layout.weapon.skill_icon_size.y * j
                            ),
                            resize=(size.x//2, self.layout.weapon.skill_icon_size.y),
                            transparency=True
                        )
                    else:
                        await self.paste(
                            imgs, range(2 if (has_skin and j == 0) else 1),
                            "assets/skill.png",
                            (
                                pos.x,
                                pos.y + size.y + pos_shift + self.layout.weapon.skill_icon_size.y * j
                            ),
                            resize=(size.x, self.layout.weapon.skill_icon_size.y),
                            transparency=True
                        )
                # plus
                if export['wp'][i] > 0:
                    # calculate shift of the position if AX and awakening are present
                    shift : v2
                    if pos_shift != 0:
                        if i > 0:
                            shift = v2(- size.x // 2, 0)
                        else:
                            shift = v2(0, pos_shift)
                    else:
                        shift = v2(0, 0)
                    # draw plus text
                    self.text(
                        imgs, range(2 if has_skin else 1),
                        pos + size + shift + self.layout.weapon.plus_text_position_shift,
                        "+{}".format(export['wp'][i]),
                        fill=self.PLUS_COLOR,
                        font=self.fonts['medium'],
                        stroke_width=6,
                        stroke_fill=self.BLACK
                    )
                # skill level
                if export['wl'][i] is not None and export['wl'][i] > 1:
                    self.text(
                        imgs, range(2 if has_skin else 1),
                        pos + (self.layout.weapon.skill_icon_size.x * 3, size.y + pos_shift) + self.layout.weapon.skill_level_position_shift,
                        "SL {}".format(export['wl'][i]),
                        fill=self.WHITE,
                        font=self.fonts['small']
                    )
                if i == 0 or not has_ax or not has_awakening: # don't draw if ax and awakening and not mainhand
                    # skill icon
                    for j in range(3):
                        if export['wsn'][i][j] is not None:
                            if self.settings.get('opus', False) and self.process_special_weapon(export, i, j): # 3rd skill guessing
                                await self.pasteDL(
                                    imgs, range(2 if has_skin else 1),
                                    export['wsn'][i][j],
                                    (
                                        pos.x + self.layout.weapon.skill_icon_size.x * j,
                                        pos.y + size.y + pos_shift
                                    ),
                                    resize=self.layout.weapon.skill_icon_size.i
                                )
                            else:
                                await self.pasteDL(
                                    imgs, range(2 if has_skin else 1),
                                    "assets_en/img/sp/ui/icon/skill/{}.png".format(export['wsn'][i][j]),
                                    (
                                        pos.x + self.layout.weapon.skill_icon_size.x * j,
                                        pos.y + size.y + pos_shift
                                    ),
                                    resize=self.layout.weapon.skill_icon_size.i
                                )
                pos_shift += self.layout.weapon.skill_icon_size.x
                # size of the big AX/Awakening icon
                main_ax_icon_size : v2  = self.layout.weapon.ax_icon_size
                if i == 0:
                    main_ax_icon_size *= self.layout.weapon.ax_indicator_mainhand_multiplier
                if has_ax and has_awakening: # double
                    main_ax_icon_size *= self.layout.weapon.ax_indicator_multiple_multiplier
                # ax skills
                if has_ax:
                    await self.pasteDL(
                        imgs, range(2 if has_skin else 1),
                        "assets_en/img/sp/ui/icon/augment_skill/{}.png".format(export['waxt'][i][0]),
                        pos.i,
                        resize=main_ax_icon_size.i
                    )
                    for j in range(len(export['waxi'][i])):
                        await self.pasteDL(
                            imgs, range(1),
                            "assets_en/img/sp/ui/icon/skill/{}.png".format(export['waxi'][i][j]),
                            (pos.x + self.layout.weapon.ax_separator * j, pos.y + size.y + pos_shift),
                            resize=self.layout.weapon.skill_icon_size.i
                        )
                        self.text(
                            imgs, range(1),
                            (
                                pos + (self.layout.weapon.ax_separator * j + self.layout.weapon.skill_icon_size.x, size.y + pos_shift) + self.layout.weapon.ax_text_position_shift
                            ).i,
                            "{}".format(export['wax'][i][0][j]['show_value']).replace('%', '').replace('+', ''),
                            fill=self.WHITE,
                            font=self.fonts['small']
                        )
                    pos_shift += self.layout.weapon.skill_icon_size.x
                # awakening
                if has_awakening:
                    shift = int(main_ax_icon_size.x / 2) if has_ax else 0 # shift the icon right a bit if also has AX icon
                    await self.pasteDL(
                        imgs, range(2 if has_skin else 1),
                        "assets_en/img/sp/ui/icon/arousal_type/type_{}.png".format(export['wakn'][i]['form']),
                        (pos + (shift, 0)).i,
                        resize=main_ax_icon_size.i
                    )
                    await self.pasteDL(
                        imgs, range(1),
                        "assets_en/img/sp/ui/icon/arousal_type/type_{}.png".format(export['wakn'][i]['form']),
                        (
                            pos.x + self.layout.weapon.skill_icon_size.x,
                            pos.y + size.y + pos_shift
                        ),
                        resize=self.layout.weapon.skill_icon_size.i
                    )
                    self.text(
                        imgs, range(1),
                        (
                            pos + (self.layout.weapon.skill_icon_size.x * 3, size.y + pos_shift) + self.layout.weapon.skill_level_position_shift
                        ).i,
                        "LV {}".format(export['wakn'][i]['level']),
                        fill=self.WHITE,
                        font=self.fonts['small']
                    )

            if self.extra_grid:
                await self.paste(
                    imgs, range(1),
                    "assets/sandbox.png",
                    (
                        pos.x,
                        self.layout.weapon.origin.y + (self.layout.weapon.skill_box_height + self.layout.weapon.sub_size.y) * 3
                    ),
                    resize=(size.x, int(66 * size.x / 159)),
                    transparency=True
                )
            # stats
            pos = self.layout.weapon.origin + v2(0, self.layout.weapon.mainhand_size.y + 150)
            await self.paste(
                imgs, range(1),
                "assets/skill.png",
                pos.i,
                resize=(self.layout.weapon.mainhand_size.x, self.layout.weapon.stat_box_height),
                transparency=True
            )
            await self.paste(
                imgs, range(1),
                "assets/skill.png",
                (pos + (0, self.layout.weapon.stat_box_height)).i,
                resize=(self.layout.weapon.mainhand_size.x, self.layout.weapon.stat_box_height),
                transparency=True
            )
            await self.paste(
                imgs, range(1),
                "assets/atk.png",
                (pos + self.layout.weapon.stat_icon_position).i,
                resize=(90, 39),
                transparency=True
            )
            await self.paste(
                imgs, range(1),
                "assets/hp.png",
                (pos + self.layout.weapon.stat_icon_position + (0, self.layout.weapon.stat_box_height)).i,
                resize=(66, 39),
                transparency=True
            )
            self.text(
                imgs, range(1),
                (pos + self.layout.weapon.stat_text_position).i,
                "{}".format(export['watk']),
                fill=self.WHITE,
                font=self.fonts['medium']
            )
            self.text(
                imgs, range(1),
                (pos + self.layout.weapon.stat_text_position + (0, self.layout.weapon.stat_box_height)).i,
                "{}".format(export['whp']),
                fill=self.WHITE,
                font=self.fonts['medium']
            )
            await asyncio.sleep(0)

            # estimated damage
            pos = pos + (self.layout.weapon.mainhand_size.x, 0) + self.layout.weapon.estimated_damage_position
            if (export['sps'] is not None and export['sps'] != '') or export['spsid'] is not None:
                await asyncio.sleep(0)
                # support summon
                if export['spsid'] is not None:
                    supp = export['spsid']
                else:
                    print("[WPN] |--> Looking up summon ID of", export['sps'], "on the wiki")
                    supp = await self.get_support_summon_from_wiki(export['sps'])
                if supp is None:
                    print("[WPN] |--> Support summon is", export['sps'], "(Note: searching its ID on gbf.wiki failed)")
                    await self.paste(
                        imgs, range(1),
                        "assets/big_stat.png",
                        (pos + self.layout.weapon.support_box_offset).i,
                        resize=self.layout.weapon.support_box_size.i,
                        transparency=True
                    )
                    self.text(
                        imgs, range(1),
                        (pos + self.layout.weapon.support_text_offset).i,
                        ("サポーター" if self.japanese else "Support"),
                        fill=self.WHITE,
                        font=self.fonts['medium']
                    )
                    supp = ""
                    if len(export['sps']) > 10:
                        supp = export['sps'][:10] + "..."
                    else:
                        supp = export['sps']
                    self.text(
                        imgs, range(1),
                        (pos + self.layout.weapon.support_text_offset + self.layout.weapon.support_number_text_shift).i,
                        supp,
                        fill=self.WHITE,
                        font=self.fonts['medium']
                    )
                else:
                    print("[WPN] |--> Support summon ID is", supp)
                    await self.pasteDL(
                        imgs, range(1),
                        "assets_en/img/sp/assets/summon/m/{}.jpg".format(supp),
                        (pos + self.layout.weapon.support_art_box_offset).i,
                        resize=self.layout.weapon.support_art_box_size.i
                    )
            # estimated stats
            est_width : int = ((size.x * 3) // 2)
            for i in range(0, 2):
                await asyncio.sleep(0)
                await self.paste(
                    imgs, range(1),
                    "assets/big_stat.png",
                    (pos + (est_width*i, 0)).i,
                    resize=(self.layout.weapon.estimated_offset_size + (est_width, 0)).i,
                    transparency=True
                )
                self.text(
                    imgs, range(1),
                        (pos + (est_width * i, 0) + self.layout.weapon.estimated_text_offset).i,
                        "{}".format(export['est'][i+1]),
                        fill=self.COLORS[int(export['est'][0])],
                        font=self.fonts['big'],
                        stroke_width=6,
                        stroke_fill=self.BLACK
                    )
                if i == 0:
                    self.text(
                        imgs, range(1),
                        (pos + (est_width * i, 0) + self.layout.weapon.estimated_other_text_offset).i,
                        ("予測ダメ一ジ" if self.japanese else "Estimated"),
                        fill=self.WHITE,
                        font=self.fonts['medium']
                    )
                elif i == 1:
                    vs : int
                    if int(export['est'][0]) <= 4:
                        vs = (int(export['est'][0]) + 2) % 4 + 1
                    else:
                        vs = (int(export['est'][0]) - 5 + 1) % 2 + 5
                    if self.japanese:
                        self.text(
                            imgs, range(1),
                            (pos + (est_width * i, 0) + self.layout.weapon.estimated_other_text_offset).i,
                            "対",
                            fill=self.WHITE,
                            font=self.fonts['medium']
                        )
                        self.text(
                            imgs, range(1),
                            (pos + (est_width * i, 0) + self.layout.weapon.estimated_other_jp_text_offset).i,
                            "{}属性".format(self.COLORS_JP[vs]),
                            fill=self.COLORS[vs],
                            font=self.fonts['medium']
                        )
                        self.text(
                            imgs, range(1),
                            (pos + (est_width * i, 0) + self.layout.weapon.estimated_other_jp_text2_offset).i,
                            "予測ダメ一ジ",
                            fill=self.WHITE,
                            font=self.fonts['medium']
                        )
                    else:
                        self.text(
                            imgs, range(1),
                            (pos + (est_width * i, 0) + self.layout.weapon.estimated_other_text_offset).i,
                            "vs",
                            fill=self.WHITE,
                            font=self.fonts['medium']
                        )
                        self.text(
                            imgs, range(1),
                            (pos + (est_width * i, 0) + self.layout.weapon.estimated_other_text2_offset).i,
                            "{}".format(self.COLORS_EN[vs]),
                            fill=self.COLORS[vs],
                            font=self.fonts['medium']
                        )
            # hp gauge
            if self.settings.get('hp', True):
                await asyncio.sleep(0)
                hpratio : int = 100
                for et in export['estx']:
                    if et[0].replace('txt-gauge-num ', '') == 'hp':
                        hpratio = et[1]
                        break
                await self.paste(
                    imgs, range(1, 2),
                    "assets/big_stat.png",
                    pos.i,
                    resize=(self.layout.weapon.estimated_offset_size + (est_width, 0)).i,
                    transparency=True
                )
                if self.japanese:
                    self.text(
                        imgs, range(1, 2),
                        (pos + self.layout.weapon.hp_bar_text_offset).i,
                        "HP{}%".format(hpratio),
                        fill=self.WHITE,
                        font=self.fonts['medium']
                    )
                else:
                    self.text(
                        imgs, range(1, 2),
                        (pos + self.layout.weapon.hp_bar_text_offset).i,
                        "{}% HP".format(hpratio),
                        fill=self.WHITE,
                        font=self.fonts['medium']
                    )
                await self.paste(
                    imgs, range(1, 2),
                    "assets/hp_bottom.png",
                    (pos + self.layout.weapon.hp_bar_offset).i,
                    resize=self.layout.weapon.hp_bar_size.i,
                    transparency=True
                )
                await self.paste(
                    imgs, range(1, 2),
                    "assets/hp_mid.png",
                    (pos + self.layout.weapon.hp_bar_offset).i,
                    resize=(int(self.layout.weapon.hp_bar_size.x * int(hpratio) / 100), self.layout.weapon.hp_bar_size.y),
                    transparency=True,
                    crop=(int(self.layout.weapon.hp_bar_crop.x * int(hpratio) / 100), self.layout.weapon.hp_bar_crop.y)
                )
                await self.paste(
                    imgs, range(1, 2),
                    "assets/hp_top.png",
                    (pos + self.layout.weapon.hp_bar_offset).i,
                    resize=self.layout.weapon.hp_bar_size.i,
                    transparency=True
                )
            return ('weapon', imgs)
        except Exception as e:
            return self.pexc(e)

    async def make_modifier(self : GBFPIB, export : dict) -> str|tuple:
        try:
            imgs : list[IMG] = [self.blank_image()]
            print("[MOD] * Drawing Modifiers...")
            print("[MOD] |--> Found", len(export['mods']), "modifier(s)...")
            # weapon modifier list
            if len(export['mods']) > 0:
                # background
                await self.paste(
                    imgs, range(1),
                    "assets/mod_bg.png",
                    (
                        self.layout.modifier.origin - (self.layout.modifier.offset.x, self.layout.modifier.offset.y // 2)
                    ).i,
                    resize=self.layout.modifier.background_size.i
                )
                try:
                    await self.paste(
                        imgs, range(1),
                        "assets/mod_bg_supp.png",
                        (
                            self.layout.modifier.origin - self.layout.modifier.offset + (0, self.layout.modifier.background_size.y)
                        ).i,
                        resize=(
                            self.layout.modifier.background_size.x,
                            self.layout.modifier.spacer * (len(export['mods'])-1)
                        )
                    )
                    await self.paste(
                        imgs, range(1),
                        "assets/mod_bg_bot.png",
                        (
                            self.layout.modifier.origin.x - self.layout.modifier.offset.x,
                            self.layout.modifier.origin.y + self.layout.modifier.spacer * (len(export['mods'])-1)
                        ),
                        resize=self.layout.modifier.background_size.i
                    )
                except:
                    await self.paste(
                        imgs, range(1),
                        "assets/mod_bg_bot.png",
                        (
                            self.layout.modifier.origin.x - self.layout.modifier.offset.x,
                            self.layout.modifier.origin.y + self.layout.modifier.background_bottom_space
                        ),
                        resize=self.layout.modifier.background_size.i
                    )
                offset = self.layout.modifier.origin.copy()
                # modifier draw
                for m in export['mods']:
                    await asyncio.sleep(0)
                    await self.pasteDL(
                        imgs, range(1),
                        "assets_en/img/sp/ui/icon/weapon_skill_label/" + m['icon_img'],
                        (offset + self.layout.modifier.image_offset).i,
                        resize=self.layout.modifier.size.i,
                        transparency=True,
                        crop=self.layout.modifier.get_crop()
                    )
                    self.text(
                        imgs, range(1),
                        (offset + self.layout.modifier.text_offset).i,
                        str(m['value']),
                        fill=(self.MODIFIER_MAX_COLOR if m['is_max'] else self.WHITE),
                        font=self.fonts[self.layout.modifier.font]
                    )
                    offset += (0, self.layout.modifier.spacer)
            return ('modifier', imgs)
        except Exception as e:
            return self.pexc(e)

    async def loadEMP(self : GBFPIB, id : str) -> dict|None:
        try:
            if id in self.emp_cache:
                return self.emp_cache[id]
            else:
                with open("emp/{}.json".format(id), mode="r", encoding="utf-8") as f:
                    self.emp_cache[id] = json.load(f)
                    await asyncio.sleep(0)
                    return self.emp_cache[id]
        except:
            return None

    async def loadArtifact(self : GBFPIB, id : str) -> dict|None:
        try:
            if id in self.artifact_cache:
                return self.artifact_cache[id]
            else:
                with open("artifact/{}.json".format(id), mode="r", encoding="utf-8") as f:
                    self.artifact_cache[id] = json.load(f)
                    await asyncio.sleep(0)
                    return self.artifact_cache[id]
        except:
            return None

    async def make_emp(self : GBFPIB, export : dict) -> str|tuple:
        try:
            imgs : list[IMG] = [self.blank_image()]
            print("[EMP] * Drawing EMPs...")
            # first, we attempt to load emp files
            # get chara count
            ccount : int = 0
            for i in range(0, self.layout.party.character_count):
                if i == 0 and self.layout.party.skip_zero:
                    continue # quirk of babyl party, mc is at index 0
                if i >= len(export['c']) or export['c'][i] is None: # no character in this spot
                    continue
                cid : str = self.get_character_look(export, i)
                data : dict|None = await self.loadEMP(cid.split('_')[0]) # preload and cache emp
                if data is None:
                    print("[EMP] |--> Ally #{}: emp/{}.json can't be loaded".format(i+1, cid.split('_')[0]))
                    continue
                elif self.japanese != (data['lang'] == 'ja'):
                    print("[EMP] |--> Ally #{}: WARNING, emp language doesn't match".format(i+1))
                ccount += 1
            self.layout.init_emp(ccount)
            # draw emps
            pos : v2 = self.layout.emp.origin + (0, self.layout.emp.origin.y - self.layout.emp.portrait_size.y -self.layout.emp.shift)
            # allies
            for i in range(0, self.layout.party.character_count):
                await asyncio.sleep(0)
                if i == 0 and self.layout.party.skip_zero:
                    continue # quirk of babyl party, mc is at index 0
                if i < len(export['c']) and export['c'][i] is not None:
                    cid : str = self.get_character_look(export, i)
                    data : dict|None = self.emp_cache.get(cid.split('_')[0], None)
                    if data is None:
                        continue
                    # set chara position
                    pos = pos + (0, self.layout.emp.portrait_size.y + self.layout.emp.shift)
                    # portrait
                    await self.pasteDL(
                        imgs, range(1),
                        "assets_en/img/sp/assets/npc/{}/{}.jpg".format(self.layout.emp.folder, cid),
                        pos.i,
                        resize=self.layout.emp.portrait_size.i
                    )
                    # rings
                    if export['cwr'][i] == True:
                        await self.pasteDL(
                            imgs, range(1),
                            "assets_en/img/sp/ui/icon/augment2/icon_augment2_l.png",
                            (pos + self.layout.emp.ring_offset).i,
                            resize=self.layout.emp.ring_size.i,
                            transparency=True
                        )
                    # level
                    self.text(
                        imgs, range(1),
                        (pos + self.layout.emp.level_offset).i,
                        "Lv{}".format(export['cl'][i]),
                        fill=self.WHITE,
                        font=self.fonts['small'],
                        stroke_width=6,
                        stroke_fill=self.BLACK
                    )
                    # plus
                    if export['cp'][i] > 0:
                        self.text(
                            imgs, range(1),
                            (pos + self.layout.emp.plus_offset).i,
                            "+{}".format(export['cp'][i]),
                            fill=self.PLUS_COLOR,
                            font=self.fonts['small'],
                            stroke_width=6,
                            stroke_fill=self.BLACK
                        )
                    # background
                    await self.paste(
                        imgs, range(1),
                        "assets/bg_emp.png",
                        (pos + (self.layout.emp.portrait_size.x, 0)).i,
                        resize=self.layout.emp.background_size.i,
                        transparency=True
                    )
                    # main EMP
                    nemp = len(data['emp'])
                    extra_lb = ""
                    if 'domain' in data and len(data['domain']) > 0:
                        extra_lb = ", Has Domain"
                    elif 'saint' in data and len(data['saint']) > 0:
                        extra_lb = ", Has Yupei"
                    elif 'extra' in data and len(data['extra']) > 0:
                        extra_lb = ", Has Extra EMP"
                    print("[EMP] |--> Ally #{}: {} EMPs, {} Ring EMPs, {}{}".format(i+1, nemp, len(data['ring']), ('{} Lv{}'.format(data['awaktype'], data['awakening'].split('lv')[-1]) if 'awakening' in data else 'Awakening not found'), extra_lb))
                    idx : int = int(nemp > 15) # check if 15 emp like transcended eternals
                    for j, emp in enumerate(data['emp']):
                        await asyncio.sleep(0)
                        if self.layout.emp.is_compact:
                            epos : v2 = pos + (
                                self.layout.emp.portrait_size.x + 15 + self.layout.emp.emp_size[idx].x * j,
                                5
                            )
                        elif j % 5 == 0: # new line
                            epos : v2 = pos + (
                                self.layout.emp.portrait_size.x + 15 + self.layout.emp.get_eternal_shift(nemp),
                                7 + self.layout.emp.emp_size[idx].y * j // 5
                            )
                        else:
                            epos : v2 = epos + (self.layout.emp.emp_size[idx].x, 0)
                        if emp.get('is_lock', False):
                            await self.pasteDL(
                                imgs, range(1),
                                "assets_en/img/sp/zenith/assets/ability/lock.png",
                                epos.i,
                                resize=self.layout.emp.emp_size[idx].i
                            )
                        else:
                            await self.pasteDL(
                                imgs, range(1),
                                "assets_en/img/sp/zenith/assets/ability/{}.png".format(emp['image']),
                                epos.i,
                                resize=self.layout.emp.emp_size[idx].i
                            )
                            if str(emp['current_level']) != "0":
                                self.text(
                                    imgs, range(1),
                                    (epos + self.layout.emp.emp_ring_offset).i,
                                    str(emp['current_level']),
                                    fill=(235, 227, 250),
                                    font=self.fonts['medium'] if self.layout.emp.is_compact and nemp > 15 else self.fonts['big'],
                                    stroke_width=6,
                                    stroke_fill=self.BLACK
                                )
                            else:
                                await self.paste(
                                    imgs, range(1),
                                    "assets/emp_unused.png",
                                    epos.i,
                                    resize=self.layout.emp.emp_size[idx].i,
                                    transparency=True
                                )
                    # ring EMP
                    for j, ring in enumerate(data['ring']):
                        await asyncio.sleep(0)
                        epos = pos + self.layout.emp.get_ring_emp_position(idx, j, nemp)
                        await self.paste(
                            imgs, range(1),
                            "assets/{}.png".format(ring['type']['image']),
                            epos.i,
                            resize=self.layout.emp.emp_ring_size.i,
                            transparency=True
                        )
                        if self.layout.emp.is_compact:
                            self.text(
                                imgs, range(1),
                                (epos + self.layout.emp.emp_text_offset).i,
                                ring['param']['disp_total_param'],
                                fill=self.PLUS_COLOR,
                                font=self.fonts['small'],
                                stroke_width=6,
                                stroke_fill=self.BLACK
                            )
                        else:
                            self.text(
                                imgs, range(1),
                                (epos + self.layout.emp.emp_text_offset).i,
                                ring['type']['name'] + " " + ring['param']['disp_total_param'],
                                fill=self.PLUS_COLOR,
                                font=self.fonts['medium'],
                                stroke_width=6,
                                stroke_fill=self.BLACK
                            )
                    # Awakening, domain...
                    if isinstance(self.layout.emp, LayoutEMPSuperCompact):
                        # for the super compact mode
                        # simply put the awakening icon over the portrait
                        # on the top right corner
                        apos : v2 = pos + v2(
                            self.layout.emp.portrait_size.x - self.layout.emp.awk_size.x,
                            0
                        )
                        if data.get('awakening', None) is not None:
                            url : str = ""
                            match data['awaktype']:
                                case "Attack"|"攻撃":
                                    url = "assets_en/img/sp/assets/item/npcarousal/s/1.jpg"
                                case "Defense"|"防御":
                                    url = "assets_en/img/sp/assets/item/npcarousal/s/2.jpg"
                                case "Multiattack"|"連続攻撃":
                                    url = "assets_en/img/sp/assets/item/npcarousal/s/3.jpg"
                                case _: # "Balanced"|"バランス"or others
                                    pass
                            if url != "":
                                await self.pasteDL(
                                    imgs, range(1),
                                    url,
                                    apos.i,
                                    resize=self.layout.emp.awk_size.i
                                )
                    else:
                        await asyncio.sleep(0)
                        icon_index : int = 1
                        # calc pos
                        apos1 : v2
                        apos2 : v2
                        if self.layout.emp.is_compact:
                            apos1 = v2(
                                pos.x + self.layout.emp.portrait_size.x + 25,
                                pos.y + self.layout.emp.portrait_size.y
                            )
                            apos2 = v2(
                                pos.x + self.layout.emp.portrait_size.x + 225,
                                pos.y + self.layout.emp.portrait_size.y
                            )
                        else:
                            apos1 = v2(IMAGE_SIZE.x - 420, pos.y + 20)
                            apos2 = v2(IMAGE_SIZE.x - 420, pos.y + 85)
                        # awakening
                        if data.get('awakening', None) is not None:
                            match data['awaktype']:
                                case "Attack"|"攻撃":
                                    url = "assets_en/img/sp/assets/item/npcarousal/s/1.jpg"
                                case "Defense"|"防御":
                                    url = "assets_en/img/sp/assets/item/npcarousal/s/2.jpg"
                                case "Multiattack"|"連続攻撃":
                                    url = "assets_en/img/sp/assets/item/npcarousal/s/3.jpg"
                                case _: # "Balanced"|"バランス"or others
                                    url = "assets/bal_awakening.png"
                            if url == "assets/bal_awakening.png":
                                await self.paste(
                                    imgs, range(1),
                                    url,
                                    apos1.i,
                                    resize=self.layout.emp.awk_size.i,
                                    transparency=True
                                )
                            else:
                                await self.pasteDL(
                                    imgs, range(1),
                                    url,
                                    apos1.i,
                                    resize=self.layout.emp.awk_size.i,
                                    transparency=True
                                )
                            self.text(
                                imgs, range(1),
                                (apos1 + (75, 10)).i,
                                "Lv" + data['awakening'].split('lv')[-1],
                                fill=self.AWK_COLOR,
                                font=self.fonts['medium'],
                                stroke_width=6, stroke_fill=self.BLACK
                            )
                        # domain and other extra upgrades
                        for key in ['domain', 'saint', 'extra']:
                            if key in data and len(data[key]) > 0:
                                extra_txt : str = ""
                                # set txt, icon and color according to specifics
                                icon_path : str
                                text_color : tuple[int, int, int]
                                match key:
                                    case 'domain':
                                        icon_path = "assets_en/img/sp/ui/icon/ability/m/1426_3.png"
                                        text_color = self.DOMAIN_COLOR
                                        lv = 0
                                        for el in data[key]:
                                            if el[2] is not None: lv += 1
                                        extra_txt = "Lv" + str(lv)
                                    case 'extra':
                                        icon_path = "assets_en/img/sp/ui/icon/ability/m/2487_3.png"
                                        text_color = self.RADIANCE_COLOR
                                        extra_txt = "Lv" + str(len(data[key]))
                                    case 'saint':
                                        icon_path = "assets_en/img/sp/ui/icon/skill/skill_job_weapon.png"
                                        text_color = self.SAINT_COLOR
                                        lv = [0, 0]
                                        for el in data[key]:
                                            if el[0].startswith("ico-progress-gauge"):
                                                if el[0].endswith(" on"):
                                                    lv[0] += 1
                                                lv[1] += 1
                                        extra_txt = "{}/{}".format(lv[0], lv[1])
                                    case _:
                                        icon_path = "assets_en/img/sp/ui/icon/skill/skill_job_weapon.png"
                                        text_color = self.SAINT_COLOR
                                        extra_txt = "Lv" + str(len(data[key]))
                                # add to image
                                await self.pasteDL(
                                    imgs, range(1),
                                    icon_path,
                                    apos2.i,
                                    resize=self.layout.emp.awk_size.i
                                )
                                self.text(
                                    imgs, range(1),
                                    (apos2 + self.layout.emp.domain_offset).i,
                                    extra_txt,
                                    fill=text_color,
                                    font=self.fonts['medium'],
                                    stroke_width=6,
                                    stroke_fill=self.BLACK
                                )
                                # increase index and move position accordingly
                                # NOTE: Should be unused for now, it's in case they add multiple in the future
                                icon_index += 1
                                if self.layout.emp.is_compact:
                                    apos2 += (self.layout.emp.emp_text_shift, 0)
                                else:
                                    if icon_index % 2 == 0:
                                        apos2 += (self.layout.emp.emp_text_shift, - self.layout.emp.awk_size.y)
                                    else:
                                        apos2 += (0, self.layout.emp.awk_size.y)
            return ('emp', imgs)
        except Exception as e:
            return self.pexc(e)

    async def make_artifact(self : GBFPIB, export : dict) -> str|tuple:
        try:
            imgs : list[IMG] = [self.blank_image()]
            print("[ART] * Drawing Artifacts...")
            # first, we attempt to load emp files
            # get chara count
            ccount : int = 0
            for i in range(0, self.layout.party.character_count):
                if i == 0 and self.layout.party.skip_zero:
                    continue # quirk of babyl party, mc is at index 0
                if i >= len(export['c']) or export['c'][i] is None: # no character in this spot
                    continue
                cid : str = self.get_character_look(export, i)
                data : dict|None = await self.loadArtifact(cid.split('_')[0]) # preload and cache emp
                if data is None:
                    print("[ART] |--> Ally #{}: artifact/{}.json can't be loaded".format(i+1, cid.split('_')[0]))
                    continue
                elif self.japanese != (data['lang'] == 'ja'):
                    print("[ART] |--> Ally #{}: WARNING, artifact language doesn't match".format(i+1))
                ccount += 1
            self.layout.init_artifact(ccount)
            # drawing artifacts
            pos : v2 = self.layout.artifact.origin.copy()
            # allies
            for i in range(0, self.layout.party.character_count):
                await asyncio.sleep(0)
                if i == 0 and self.layout.party.skip_zero:
                    continue # quirk of babyl party, mc is at index 0
                if i < len(export['c']) and export['c'][i] is not None:
                    cid : str = self.get_character_look(export, i)
                    data : dict|None = self.artifact_cache.get(cid.split('_')[0], None)
                    if data is None or "img" not in data["artifact"] or "skills" not in data["artifact"]:
                        continue
                    # background
                    await self.paste(
                        imgs, range(1),
                        "assets/bg_emp.png",
                        (pos + (self.layout.artifact.portrait_size.x, 0)).i,
                        resize=self.layout.artifact.background_size.i,
                        transparency=True
                    )
                    # portrait
                    await self.pasteDL(
                        imgs, range(1),
                        "assets_en/img/sp/assets/npc/{}/{}.jpg".format(self.layout.artifact.folder, cid),
                        (pos + self.layout.artifact.portrait_offset).i,
                        resize=self.layout.artifact.portrait_size.i
                    )
                    # artifact portrait
                    if not isinstance(self.layout.artifact, LayoutArtifactSuperCompact):
                        await self.pasteDL(
                            imgs, range(1),
                            "assets_en/img/sp/assets/artifact/{}/{}".format(self.layout.artifact.folder, data["artifact"]["img"]),
                            (pos + self.layout.artifact.portrait_offset + (0, self.layout.artifact.portrait_size.y)).i,
                            resize=self.layout.artifact.portrait_size.i
                        )
                    # skills
                    for j, skill in enumerate(data['artifact']['skills']):
                        await asyncio.sleep(0)
                        epos : v2
                        if not self.layout.artifact.is_compact:
                            epos = pos + (
                                self.layout.artifact.portrait_size.x + 50,
                                15 + self.layout.artifact.skill_offset.y * j
                            )
                        else:
                            epos = pos + (
                                self.layout.artifact.portrait_size.x + 50 + j // 2 * self.layout.artifact.background_size.x / 2,
                                15 + self.layout.artifact.skill_offset.y * (j % 2)
                            )
                        await self.pasteDL(
                            imgs, range(1),
                            "assets_en/img/sp/ui/icon/bonus/{}".format(skill['icon']),
                            epos.i,
                            resize=self.layout.artifact.skill_offset.i,
                            transparency=True
                        )
                        self.text(
                            imgs, range(1),
                            (epos + self.layout.artifact.text_offset).i,
                            "Lv "+skill['lvl'],
                            fill=self.WHITE,
                            font=self.fonts['small'],
                            stroke_width=6,
                            stroke_fill=self.BLACK
                        )
                        self.text(
                            imgs, range(1),
                            (epos + self.layout.artifact.text_offset + self.layout.artifact.value_offset).i,
                            (skill['value'] if len(skill['value']) <= 8 else skill['value'][:7] + "..."),
                            fill=self.PLUS_COLOR,
                            font=self.fonts['small'],
                            stroke_width=6,
                            stroke_fill=self.BLACK
                        )
                        desc = skill['desc'].replace(': ', ' ')
                        if len(desc) > self.layout.artifact.text_size_limit:
                            desc = desc[:self.layout.artifact.text_size_limit] + "..."
                        self.text(
                            imgs, range(1),
                            (epos + self.layout.artifact.text_offset + self.layout.artifact.value_offset + self.layout.artifact.description_offset).i,
                            desc,
                            fill=self.WHITE,
                            font=self.fonts['small'],
                            stroke_width=6,
                            stroke_fill=self.BLACK
                        )
                    pos = pos + (0, self.layout.artifact.vertical_size) # set chara position
            return ('artifact', imgs)
        except Exception as e:
            return self.pexc(e)

    def saveImage(self : GBFPIB, img : IMG, filename : str, resize : tuple|None = None) -> str|None:
        try:
            if resize is not None:
                # using NEAREST as we're downscaling anyway
                resized = img.resize(resize)
                resized.image.save(filename, "PNG")
            else:
                img.image.save(filename, "PNG")
            print("[OUT] *'{}' has been generated".format(filename))
            return None
        except Exception as e:
            return self.pexc(e)

    def clipboardToJSON(self : GBFPIB) -> dict:
        return json.loads(pyperclip.paste())

    def clean_memory_caches(self : GBFPIB) -> None:
        if len(self.cache.keys()) > 100:
            print("* Cleaning File Memory Cache...")
            tmp = {}
            for k, v in self.cache.items():
                if '/skill/' in k or '/zenith/' in k or len(k.split('/')) == 2: # keep important files
                    tmp[k] = v
            self.cache = tmp
        if len(self.emp_cache.keys()) > 80:
            print("* Cleaning EMP Memory Cache...")
            self.emp_cache = {}
        if len(self.artifact_cache.keys()) > 80:
            print("* Cleaning Artifact Memory Cache...")
            self.artifact_cache = {}

    async def generate(self : GBFPIB) -> bool: # main function
        try:
            self.running = True
            # get the data from clipboard
            export : dict = self.clipboardToJSON()
            if export.get('ver', 0) < 1:
                print("Your bookmark is outdated, please update it!")
                self.running = False
                return False
            # start
            if 'emp' in export:
                self.generate_emp(export)
            elif 'artifact' in export:
                self.generate_artifact(export)
            else:
                await self.generate_party(export)
                self.saveClasses()
                if self.gbftmr is not None:
                    print("Do you want to make a thumbnail with this party? (Y to confirm)")
                    if input().lower() == "y":
                        try:
                            await self.gbftmr.makeThumbnailManual(export)
                        except Exception as xe:
                            print(self.pexc(xe))
                            print("The above exception occured while trying to generate the thumbnail")
            self.running = False
            return True
        except Exception as e:
            print(self.pexc(e))
            print("An error occured")
            print("Did you click the bookmark?")
            self.running = False
            return False

    def completeBaseImages(self : GBFPIB, imgs : list, resize : tuple|None = None) -> None|str:
        # party - Merge the images and save the resulting image
        for k in ['summon', 'weapon', 'modifier']:
            imgs['party'][0] = imgs['party'][0].alpha(imgs[k][0])
        ex = self.saveImage(imgs['party'][0], "party.png", resize)
        if ex is not None:
            return ex
        # skin - Merge the images (if enabled) and save the resulting image
        if self.settings.get('skin', True):
            imgs['party'][1] = imgs['party'][0].alpha(imgs['party'][1]) # we don't close imgs['party'][0] in case its save process isn't finished
            for k in ['summon', 'weapon']:
                imgs['party'][1] = imgs['party'][1].alpha(imgs[k][1])
            return self.saveImage(imgs['party'][1], "skin.png", resize)

    async def generate_party(self : GBFPIB, export : dict) -> bool:
        if self.classes is None:
            self.loadClasses()
        self.clean_memory_caches()
        start : float = time.time()
        do_emp = self.settings.get('emp', False)
        do_artifact = self.settings.get('artifact', False)
        if self.settings.get('caching', False):
            self.checkDiskCache()
        self.quality = {'720p':1/3, '1080p':1/2, '4k':1}.get(self.settings.get('quality', '4k').lower(), 1/3)
        self.definition = {'720p':(600, 720), '1080p':(900, 1080), '4k':(1800, 2160)}.get(self.settings.get('quality', '4k').lower(), (600, 720))
        resize = None if self.quality == 1 else self.definition
        print("* Image Quality ratio:", self.quality)
        print("* Image Definition:", self.definition)
        self.japanese = (export['lang'] == 'ja')
        if self.japanese:
            print("* Japanese detected")
        else:
            print("* English detected")
        self.extra_grid = (len(export['w']) > 10 and not isinstance(export['est'][0], str))
        if self.extra_grid:
            print("* Extra Party Weapon Grid detected")
        if len(export['c']) > 8:
            self.layout = GBFPIBLayout(PartyMode.babyl, self.extra_grid, len(export['mods']))
            print("* Tower of Babyl Party detectd")
        elif len(export['c']) > 5:
            self.layout = GBFPIBLayout(PartyMode.extended, self.extra_grid, len(export['mods']))
            print("* Extended Party detectd")
        else:
            self.layout = GBFPIBLayout(PartyMode.normal, self.extra_grid, len(export['mods']))

        if self.prev_lang != self.japanese:
            print("* Preparing Font...")
            if self.japanese:
                self.fonts['big'] = ImageFont.truetype("assets/font_japanese.ttf", 72, encoding="unic")
                self.fonts['medium'] = ImageFont.truetype("assets/font_japanese.ttf", 36, encoding="unic")
                self.fonts['small'] = ImageFont.truetype("assets/font_japanese.ttf", 33, encoding="unic")
                self.fonts['mini'] = ImageFont.truetype("assets/font_japanese.ttf", 27, encoding="unic")
            else:
                self.fonts['big'] = ImageFont.truetype("assets/font_english.ttf", 90, encoding="unic")
                self.fonts['medium'] = ImageFont.truetype("assets/font_english.ttf", 48, encoding="unic")
                self.fonts['small'] = ImageFont.truetype("assets/font_english.ttf", 42, encoding="unic")
                self.fonts['mini'] = ImageFont.truetype("assets/font_english.ttf", 36, encoding="unic")
        self.prev_lang = self.japanese
        
        tasks = []
        imgs = {}
        async with asyncio.TaskGroup() as tg:
            print("* Starting...")
            if do_emp: # only start if enabled
                tasks.append(tg.create_task(self.make_emp(export)))
            if do_artifact: # only start if enabled
                tasks.append(tg.create_task(self.make_artifact(export)))
            tasks.append(tg.create_task(self.make_party(export)))
            tasks.append(tg.create_task(self.make_summon(export)))
            tasks.append(tg.create_task(self.make_weapon(export)))
            tasks.append(tg.create_task(self.make_modifier(export)))
        for t in tasks:
            r = t.result()
            if isinstance(r, tuple):
                imgs[r[0]] = r[1]
            else: # exception check
                raise Exception("Exception error and traceback:\n" + r)
            # as soon as available, we start generating the final images
        tasks = []
        async with asyncio.TaskGroup() as tg:
            tasks.append(tg.create_task(asyncio.to_thread(self.completeBaseImages, imgs, resize)))
            if do_emp:
                tasks.append(tg.create_task(asyncio.to_thread(self.saveImage, imgs['emp'][0], "emp.png", resize)))
            if do_artifact:
                tasks.append(tg.create_task(asyncio.to_thread(self.saveImage, imgs['artifact'][0], "artifact.png", resize)))
        for t in tasks:
            r = t.result()
            if r is not None:
                raise Exception("Exception error and traceback:\n" + r)
        for k, v in imgs.items():
            for i in v:
                try: i.close()
                except: pass
        end : float = time.time()
        print("* Task completed with success!")
        print("* Ended in {:.2f} seconds".format(end - start))
        return True

    def generate_emp(self : GBFPIB, export : dict) -> None:
        if 'emp' not in export or 'id' not in export or 'ring' not in export:
            raise Exception("Invalid EMP data, check your bookmark")
        print("* Saving EMP for Character", export['id'], "...")
        print("*", len(export['emp']), "Extended Masteries")
        print("*", len(export['ring']), "Over Masteries")
        if 'awakening' not in export:
            print("* No Awakening Data found, please update your bookmark")
        else:
            print("* Awakening Lvl Image:", export['awakening'], ", Awakening Type:", export['awaktype'])
        if 'domain' not in export:
            print("* No Domain Data found, please update your bookmark")
        else:
            print("* Domain #", len(export['domain']))
        if 'saint' not in export:
            print("* No Saint Data found, please update your bookmark")
        else:
            print("* Saint #", len(export['saint']))
        if 'extra' not in export:
            print("* No Extra Data found, please update your bookmark")
        else:
            print("* Extra #", len(export['extra']))
        self.checkEMP()
        self.emp_cache[str(export['id'])] = export
        with open('emp/{}.json'.format(export['id']), mode='w', encoding="utf-8") as outfile:
            json.dump(export, outfile)
        print("* Task completed with success!")

    def generate_artifact(self : GBFPIB, export : dict) -> None:
        if 'artifact' not in export:
            raise Exception("Invalid Artifact data, check your bookmark")
        print("* Saving Current Artifact for Character", export['id'], "...")
        if 'img' not in export["artifact"] or 'skills' not in export["artifact"]:
            print("* No Artifact equipped")
        else:
            export["artifact"]['img'] = export["artifact"]['img'].split('/')[-1]
            print("*", "Image is", export["artifact"]['img'])
            print("*", len(export["artifact"]['skills']), "skills")
            for i in range(len(export["artifact"]['skills'])):
                export["artifact"]['skills'][i]['icon'] = export["artifact"]['skills'][i]['icon'].split('/')[-1]
                export["artifact"]['skills'][i]['lvl'] = export["artifact"]['skills'][i]['lvl'].split(' ')[-1]
                print("*", "Skill", i+1, export["artifact"]['skills'][i]['icon'], export["artifact"]['skills'][i]['lvl'], export["artifact"]['skills'][i]['desc'], export["artifact"]['skills'][i]['value'])
        self.checkArtifact()
        self.artifact_cache[str(export['id'])] = export
        with open('artifact/{}.json'.format(export['id']), mode='w', encoding="utf-8") as outfile:
            json.dump(export, outfile)
        print("* Task completed with success!")

    def checkEMP(self : GBFPIB) -> None: # check if emp folder exists (and create it if needed)
        if not os.path.isdir('emp'):
            os.mkdir('emp')

    def checkArtifact(self : GBFPIB) -> None: # check if emp folder exists (and create it if needed)
        if not os.path.isdir('artifact'):
            os.mkdir('artifact')

    def checkDiskCache(self : GBFPIB) -> None: # check if cache folder exists (and create it if needed)
        if not os.path.isdir('cache'):
            os.mkdir('cache')

    def cpyBookmark(self : GBFPIB) -> bool:
        try:
            if self.bookmark is None:
                with open("bookmarklet.txt", mode="r", encoding="utf-8") as f:
                    self.bookmark = f.read()
            pyperclip.copy(self.bookmark)
            return True
        except Exception as e:
            print(self.pexc(e))
            print("Couldn't open bookmarklet.txt")
            return False

    def importGBFTMR(self : GBFPIB, path : str) -> bool:
        try:
            if self.gbftmr is not None:
                return True
            p : Path = Path(path)
            p.resolve()
            spec = importlib.util.spec_from_file_location("GBFTMR.gbftmr", (p / "gbftmr.py").as_posix())
            module = importlib.util.module_from_spec(spec)
            sys.modules["GBFTMR.gbftmr"] = module
            spec.loader.exec_module(module)
            self.gbftmr = module.GBFTMR(p.as_posix() + "/", self.client)
            if self.gbftmr.VERSION[0] >= 2 and self.gbftmr.VERSION[1] >= 0:
                return True
            self.gbftmr = None
            return False
        except Exception as e:
            print(e)
            self.gbftmr = None
            return False

    async def start(self : GBFPIB) -> None:
        async with self.init_client():
            # parse parameters
            prog_name : str
            try:
                prog_name = sys.argv[0].replace('\\', '/').split('/')[-1]
            except:
                prog_name = "gbfpib.py" # fallback to default
            # Set Argument Parser
            parser : argparse.ArgumentParser = argparse.ArgumentParser(prog=prog_name, description="Granblue Fantasy Party Image Builder v{} https://github.com/MizaGBF/GBFPIB".format(self.VERSION))
            settings = parser.add_argument_group('settings', 'commands to alter the script behavior.')
            settings.add_argument('-q', '--quality', help="set the image size. Default is %(default)s", choices=['1080p', '720p', '4k'], default='4k')
            settings.add_argument('-nd', '--nodiskcache', help="disable the use of the disk cache.", action='store_const', const=True, default=False, metavar='')
            settings.add_argument('-nps', '--nopartyskin', help="disable the generation of skin.png.", action='store_const', const=True, default=False, metavar='')
            settings.add_argument('-npe', '--nopartyemp', help="disable the generation of emp.png.", action='store_const', const=True, default=False, metavar='')
            settings.add_argument('-npa', '--nopartyartifact', help="disable the generation of artifact.png.", action='store_const', const=True, default=False, metavar='')
            settings.add_argument('-ep', '--endpoint', help="set the GBF CDN endpoint.", nargs='?', const=".", metavar='URL')
            settings.add_argument('-hp', '--showhp', help="draw the HP slider on skin.png.", action='store_const', const=True, default=False, metavar='')
            settings.add_argument('-sk', '--skillguess', help="Guess the skill icon to use for Opus, Ultima, Draconic, etc...", action='store_const', const=True, default=False, metavar='')
            settings.add_argument('-tm', '--gbftmr', help="set the GBFMTR path.", nargs='?', const=".", metavar='GBFTMR')
            settings.add_argument('-w', '--wait', help="add a 10 seconds wait after the generation.", action='store_const', const=True, default=False, metavar='')
            args : argparse.Namespace = parser.parse_args()

            if args.gbftmr is not None and self.importGBFTMR(args.gbftmr):
                print("GBFTMR imported with success")

            if args.endpoint is not None:
                self.settings["endpoint"] = args.endpoint
            self.settings["quality"] = args.quality
            self.settings["caching"] = not args.nodiskcache
            self.settings["skin"] = not args.nopartyskin
            self.settings["emp"] = not args.nopartyemp
            self.settings["artifact"] = not args.nopartyartifact
            self.settings["opus"] = args.skillguess
            self.settings["hp"] = args.showhp
            print("Granblue Fantasy Party Image Builder", self.VERSION)
            await self.generate()
            if args.wait:
                print("Closing in 10 seconds...")
                time.sleep(10)

if __name__ == "__main__":
    asyncio.run(GBFPIB().start())