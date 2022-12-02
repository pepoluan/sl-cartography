# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import argparse
from itertools import cycle
from pathlib import Path

from PIL import Image, ImageDraw

from roadmapper_v3.draw import Point
from roadmapper_v3.draw.colors import AUTO_COLORS
from roadmapper_v3.model import Continent, Route, Segment, SegmentMode, merge_all_routes
from roadmapper_v3.model.yaml import load_from


def options():
    parser = argparse.ArgumentParser()
    parser.add_argument("--savedir", "-s", required=True, type=Path, help="Directory to save the road overlays in")
    parser.add_argument("--conti", "-c", default="", help="Comma-separated continents to render (defaults to all)")
    parser.add_argument("yaml_file", nargs="+", type=Path, help="One (or more) YAML files to process & merge")
    return parser.parse_args()


# noinspection PyUnusedLocal
def conti_cb(continent: Continent, phase: str, route: Route, drawer: ImageDraw.ImageDraw, sw: Point):
    if phase == "outline":
        return
    if route is None:
        print(flush=True)
        return
    print(f"{continent.name}::{route.name}", end="", flush=True)


# noinspection PyUnusedLocal
def route_cb(route: Route, phase: str, segment: Segment, color, drawer, sw):
    if phase == "outline":
        return
    if segment is None:
        print(flush=True)
        return
    if segment.mode == SegmentMode.SOLID:
        print(".", end="", flush=True)
    elif segment.mode == SegmentMode.DASHED:
        print("-", end="", flush=True)
    elif segment.mode == SegmentMode.RAILS:
        print("=", end="", flush=True)
    elif segment.mode == SegmentMode.ARC:
        print("(", end="", flush=True)


def main(savedir: Path, conti: str, yaml_file: list[Path]):
    if not savedir.exists():
        raise FileNotFoundError(f"Directory not found: {savedir}")
    if not savedir.is_dir():
        raise NotADirectoryError(f"Is not a directory: {savedir}")

    nf = [yf for yf in yaml_file if not yf.exists()]
    if nf:
        raise FileNotFoundError(f"These files are not found: {nf}")

    conti_set = set(c.casefold() for c in conti.split(",")) if conti else None

    Continent.DrawCallback = conti_cb
    Route.DrawCallback = route_cb
    Route.ColorCycler = cycle(AUTO_COLORS.values())

    all_routes = {}
    for yf in yaml_file:
        data = load_from(yf)
        all_routes = merge_all_routes(all_routes, data)

    for conti_name, continent in all_routes.items():
        if conti_set and conti_name.casefold() not in conti_set:
            print(f"Skipping {conti_name}", flush=True)
            continue
        canvas = Image.new("RGBA", continent.canvas_dim)
        draw = ImageDraw.Draw(canvas)
        continent.draw(draw)
        targ = savedir / f"{conti_name}_Roads3.png"
        print(f"Saving to {targ} ...", end="", flush=True)
        canvas.save(targ)
        print()


if __name__ == "__main__":
    opts = options()
    main(**vars(opts))
