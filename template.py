from collections import defaultdict
from itertools import chain, repeat
import re
import sys
import xml.etree.ElementTree as ET

# watch out for malformed templates and attacks
# maybe make one with no xml parsing whatsoever, relying only on regex, replacing id="&\d*&\d+" with the fill, stroke and stroke-width.

# SeatData = TypedDict("SeatData", {"fill": str, "stroke": str, "stroke-width": str, "title": str}, total=False)
SeatData = dict[str, str]
# Warning : all values must be str, no numbers allowed

def main(**kwargs) -> int|str|None:
    # switch between the two
    pass

def scan_ET_template(template) -> list[int]:
    # part 1:
    # identify the seats
    # return the number of seats per area to the form generator
    # (probably an ordered list of seat counts)
    _sorted_areas, l1_elements_by_area = extract_ET_template(template, check_unicity=True)
    return list(map(len, l1_elements_by_area))

def scan_str_template(template) -> list[int]:
    # part 1:
    # identify the seats
    # return the number of seats per area to the form generator
    # (probably an ordered list of seat counts)
    _sorted_areas, l1_elements_by_area = extract_str_template(template, check_unicity=True)
    return list(map(len, l1_elements_by_area))

def extract_ET_template(template, *, check_unicity=False):
    elements_by_area = defaultdict(dict[int, ET.Element])
    for node in template.findall(".*"): # check that it takes the subelements
        if (id := node.get("id", None)) and (ma := re.fullmatch(r'(?:&(\d+))?&(\d+)', id)) is not None:
            area = elements_by_area[int(ma.group(1) or "0")]
            seat = int(ma.group(2))
            if check_unicity and (seat in area):
                raise Exception(f"Duplicate seat : {ma.group(0)!r}")
            area[seat] = node
    sorted_areas = sorted(elements_by_area)
    l1_elements_by_area = [elements_by_area[area] for area in sorted_areas]

    return sorted_areas, l1_elements_by_area

def extract_str_template(template, *, check_unicity=False):
    elements_by_area = defaultdict(set[int])
    for ma in re.finditer(r'id="(?:&(\d+))?&(\d+)"', template):
        area = elements_by_area[int(ma.group(1) or "0")]
        seat = int(ma.group(2))
        if check_unicity and (seat in area):
            raise Exception(f"Duplicate seat : {ma.group(0)!r}")
        area.add(seat)
    sorted_areas = sorted(elements_by_area)
    l1_elements_by_area = [elements_by_area[area] for area in sorted_areas]

    return sorted_areas, l1_elements_by_area


def fill_ET_template(template: ET.ElementTree, filling: list[dict[SeatData, int]]) -> None:
    # The operation is done in-place and mutates the ElementTree
    # part 2 :
    # take a template (contents)
    # take a [{seat_data: nseats} for each area]

    # extract the seat svg elements again
    # group them by area
    sorted_areas, l1_elements_by_area = extract_ET_template(template)

    # check the size of each area (and the number of areas)
    if len(filling) != len(l1_elements_by_area):
        raise ValueError("Incorrect number of areas")

    # sort each area's set of seats (by number, not by alphabet)
    # converting from list of unsorted dicts to list of sorted dicts
    l2_elements_by_area = [{k: elements[k] for k in sorted(elements)} for elements in l1_elements_by_area]

    # for each area:
    for area_id, elements, fillings in zip(sorted_areas, l2_elements_by_area, filling):
        fillings_iter = chain(*(repeat(sd, r) for sd, r in fillings.items()))
        # for each seat element:
        for element_id in elements:
            try:
                seat_data = next(fillings_iter)
            except StopIteration:
                raise ValueError(f"Area {area_id} has the wrong number of filling seat data")

            # fill the seats progressively, by applying them the style properties and removing their id
            node: ET.Element = elements[element_id]
            del node.attrib["id"]
            for k, v in seat_data.items():
                if v:
                    node.set(k, v)

def fill_str_template(template: str, filling: list[dict[SeatData, int]]) -> str:
    # The operation is not done in-place since str is immutable
    # part 2 :
    # take a template (contents)
    # take a [{seat_data: nseats} for each area]

    # extract the seat svg elements again
    # group them by area
    sorted_areas, l1_elements_by_area = extract_str_template(template)

    # check the size of each area (and the number of areas)
    if len(filling) != len(l1_elements_by_area):
        raise ValueError("Incorrect number of areas")

    # sort each area's set of seats (by number, not by alphabet)
    # converting from list of sets to list of sorted lists
    l2_elements_by_area = list(map(sorted, l1_elements_by_area))

    # for each area:
    for area_id, elements, fillings in zip(sorted_areas, l2_elements_by_area, filling):
        fillings_iter = chain(*(repeat(sd, r) for sd, r in fillings.items()))
        # for each seat element:
        for element_id in elements:
            try:
                seat_data = next(fillings_iter)
            except StopIteration:
                raise ValueError(f"Area {area_id} has the wrong number of filling seat data")

            # fill the seats progressively, by applying them the style properties and removing their id
            template = template.replace(f'id="&{area_id}&{element_id}"', " ".join(f'{k}="{v}"' for k, v in seat_data.items()))

    return template

if __name__ == "__main__":
    sys.exit(main())
