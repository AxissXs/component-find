#! /usr/bin/env python3

import sys

from PIL import Image

# todo: color edges of components

debug = print

class ComponentMap:
    """
    A class that maps points to component numbers. Basically a union-find
    datastructure. Hides implementation details from the user, returning a
    positive integer to represent each component.
    """
    def __init__(self):
        self._next_key = 1
        self.component_map = {} # maps points -> Components

    def get_component(self, point):
        return self.component_map.get(point)

    def get_components(self, points):
        """
        Given a list of points, returns their corresponding components.
        """
        return map(self.get_component, points)

    def _merge_set_into_base(self, merge_from, base):
        debug("Merging", merge_from, "into", base)
        # todo: make O(log n) instead of O(n)
        for k, v in self.component_map.items():
            if v == merge_from:
                self.component_map[k] = base

    def merge_components(self, components):
        """
        Given an iterable of components, merges them all and returns a
        canonical component for the set.
        """
        cset = set(components)
        assert None not in cset
        clist = list(cset)
        base = clist[0]
        for c in clist[1:]:
            self._merge_set_into_base(c, base)
        return base

    def add(self, point, component):
        self.component_map[point] = component

    def make_component(self, point):
        self.component_map[point] = self._next_key
        self._next_key += 1
        return self.component_map[point]

def get_prior_neighbors(pt):
    """
    Get neighboring points that are on a previous row, or are just to the left
    of the given point. In other words, neighbors that come previous to this
    one in the standard iteration order.
    """
    # todo: option for 4 vs 8-way
    x, y = pt
    result = []
    if x > 0:
        result.append((x-1, y))
    if y > 0:
        result.append((x, y-1))
    return result

def iterpixels(size):
    w, h = size
    for y in range(h):
        for x in range(w):
            yield (x, y)

def find_components(im):
    """
    Given an Image in mode 1, returns its ComponentMap.
    """
    cmap = ComponentMap()
    for p in iterpixels(im.size):
        # If it's a black pixel, do nothing
        if not im.getpixel(p):
            continue

        # It's a white pixel. Merge its set with those of it's left/above
        # neighbors.

        debug(p)
        neighbors = get_prior_neighbors(p)
        neighbor_components = cmap.get_components(neighbors)

        # get_component(s) returns None for black pixels. Remove those:
        # (ComponentMap never uses 0 for a component number)
        active_neighbor_components = list(filter(None, neighbor_components))
        debug(active_neighbor_components)

        if active_neighbor_components:
            c = cmap.merge_components(active_neighbor_components)
            debug("Merged into", c)
            cmap.add(p, c)
        else:
            cmap.make_component(p)
    return cmap

class ColorMap(dict):
    """Automatically assigns RGB color values."""
    def __init__(self):
        self.h = 0
        self.s = .7
        self.v = .8

    def __getitem__(self, k):
        # Black background
        if k is None:
            return (0, 0, 0)
        if k not in self:
            self[k] = self.next_color()
        return super().__getitem__(k)

    def next_color(self):
        import colorsys
        # Basically this: http://martin.ankerl.com/2009/12/09/how-to-create-random-colors-programmatically/
        self.h = (self.h + 0.61803) % 1
        rgb = colorsys.hsv_to_rgb(self.h, self.s, self.v)
        rgb_255 = tuple(map(lambda x: int(x*255), rgb))
        return rgb_255

def color_code_components(size, component_map):
    """
    Given a component map, returns an Image where
    each component is colored differently, keeping
    a black background.
    """
    color_map = ColorMap()
    im = Image.new("RGB", size)
    color_data = []
    for p in iterpixels(size):
        component = component_map.get_component(p)
        color_data.append(color_map[component])
    im.putdata(color_data)
    return im

def usage():
    print("Identifies connected components in an image and colors them")
    print("Usage: %s <input_image> <output_image>")
    sys.exit()

def main():
    if len(sys.argv) != 3:
        usage()
    input_file_path = sys.argv[1]
    output_file_path = sys.argv[2]
    input_image = Image.open(input_file_path).convert('1')
    components = find_components(input_image)
    output_image = color_code_components(input_image.size, components)
    output_image.save(output_file_path)
    print("Saved", output_file_path)

if __name__ == '__main__':
    main()
