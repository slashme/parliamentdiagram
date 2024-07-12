from collections import defaultdict
from itertools import chain, repeat
import re
import sys
import xml.etree.ElementTree as ET

# SeatData = TypedDict("SeatData", {"fill": str, "stroke": str, "stroke-width": str, "title": str}, total=False)
# SeatData = dict[str, str]
# Warning : all values must be str, no numbers allowed
# class SeatData(dict[str, str]):
class SeatData:
    def __init__(self, **kwargs):
        self._dict = kwargs
        self.items = self._dict.items
        self.get = self._dict.get

    def __hash__(self):
        return hash(frozenset(self.items()))

_NAMESPACES = {
    "": "http://www.w3.org/2000/svg",
    # "svg": "http://www.w3.org/2000/svg",
    "xlink": "http://www.w3.org/1999/xlink",
    "pardiag": "http://parliamentdiagram.toolforge.org/2024/template",
}
for p, n in _NAMESPACES.items():
    ET.register_namespace(p, n)
del p, n

def _wrapped_namespace(ns: str) -> str:
    return "{" + _NAMESPACES.get(ns, ns) + "}"
_pardiag_prefix = _wrapped_namespace("pardiag")

def main(template_file, output_file=sys.stdout, *, filling=None, use_classes: bool|None = None) -> int|str|None:
    """
    Considers the template file and the output file to be a file descriptor or a file path.

    If filling is None, prints the number of seats by area.
    If filling is a list of SeatData: nseats dicts,
    where there is one dict per area
    and the sum of nseats is the number of seats in that area,
    then the template gets filled using that filling.
    If filling is True, it is replaced by a rainbow filling, in "demo mode".

    If use_classes is True, the style of each SeatData is written in a <style> entry
    with a class that is set to each seat.
    If False, the style is written separately on each seat.
    The False case is only better when each seat has different SeatData
    (which is typically the case in demo mode).
    The parameter defaults to the opposite of filling being True.
    """

    if isinstance(template_file, str):
        with open(template_file, "r") as file:
            return main(file, output_file, filling=filling)
    if isinstance(output_file, str):
        with open(output_file, "w") as file:
            return main(template_file, file, filling=filling)

    if use_classes is None:
        use_classes = filling is not True

    template_str = template_file.read()
    # template = _parse_without_namespaces(template_str)
    template = ET.fromstring(template_str)

    if filling is True:
        nseats = _scan_template(template)
        filling = {SeatData(fill=color): 1 for color in _generate_rainbow(nseats, 250)}

    if filling is None:
        print(_scan_template(template), file=output_file)
    else:
        if use_classes:
            _fill_template_by_class(template, filling)
        else:
            _fill_template_individually(template, filling)
        print(ET.tostring(template, encoding="unicode"), file=output_file)

def _parse_without_namespaces(string) -> ET.Element:
    """
    Prevents Python's xml parser from substituting the namespaces in the elements' tags.
    Warning : works only if the namespaces are on the outer node.
    """
    found_namespaces = {}
    for namespace_match in re.finditer(r'(xmlns(?::\w+)?)="([^"]+)"\s*', string):
        found_namespaces[namespace_match.group(1)] = namespace_match.group(2)
        string = string.replace(namespace_match.group(0), "")
    element = ET.fromstring(string)
    element.attrib = found_namespaces | element.attrib
    return element

def _generate_rainbow(n, boun=300):
    """
    Generates a rainbow of that many CSS colors going from full red (inclusive) to boun (inclusive, defaulting to purple).
    If boun is an integer, it is interpreted as a number of degrees. If it is a float, it is interpreted as a fraction of a turn.
    """
    if not isinstance(boun, int):
        boun = round(boun*360) # ints are more precise than floats

    if boun % (n-1):
        it = (f"hsl({boun*i/(n-1)}deg 100% 50%)" for i in range(n))
    else:
        # write ints, if possible without losing precision
        it = (f"hsl({boun*i//(n-1)}deg 100% 50%)" for i in range(n))
    yield from it


def _get_template_metadata(template: ET.Element) -> dict[str, str]:
    """
    Extracts the metadata from the template.
    """
    metadata = {}

    for key, value in template.attrib.items():
        if key.startswith(_pardiag_prefix):
            metadata[key.removeprefix(_pardiag_prefix)] = value

    # metadata["reversed"] = bool(metadata.get("reversed"))
    return metadata


def _scan_template(template: ET.Element) -> int:
    # part 1:
    # identify the seats
    # return the number of seats per area to the form generator
    # (probably an ordered list of seat counts)
    elements = _extract_template(template, check_unicity=True)
    return len(elements)

def _extract_template(template: ET.Element, *, check_unicity=False):
    elements: dict[int, ET.Element] = {}

    for node in template.findall(".//"): # check that it takes the subelements
        if (id := node.get(_pardiag_prefix+"id", None)) and id.isdecimal():
            seat = int(id)
            if check_unicity and (seat in elements):
                raise Exception(f"Duplicate seat : {id}")
            elements[seat] = node

    return elements


def _fill_template_individually(template: ET.Element, fillings: dict[SeatData, int]) -> None:
    """
    The operation is done in-place and mutates the ElementTree.
    This method is the only one to properly support the title and desc seat data.
    """

    metadata = _get_template_metadata(template)

    # the SVG elements by seat id, not sorted
    elements = _extract_template(template)

    fillings_iter = chain(*(repeat(sd, r) for sd, r in fillings.items()))
    # for each seat element:
    for element_id in sorted(elements, reverse=bool(metadata["reversed"])):
        try:
            seat_data = next(fillings_iter)
        except StopIteration:
            raise ValueError("filling does not contain enough seats")

        # fill the seats progressively, by applying them the style properties and removing their id
        node = elements[element_id]
        del node.attrib[_pardiag_prefix+"id"]
        for k, v in seat_data.items():
            if v:
                if k in ("title", "desc"):
                    el = ET.Element(k)
                    el.text = v
                    node.append(el)
                else:
                    node.set(k, str(v))

    if tuple(fillings_iter):
        raise ValueError("filling contains too many seats")

def _fill_template_by_class(template: ET.Element, fillings: dict[SeatData, int]) -> None:
    """
    This does it more cleanly, taking advantage of the ET.
    Each party's class definition is put in a <style> node.
    Then the class is added to the seats.
    title and desc are not properly managed (treated as attributes).
    """

    metadata = _get_template_metadata(template)

    # the SVG elements by seat id, not sorted
    elements = _extract_template(template)

    # add the style node
    style_node = ET.Element("style", type="text/css")
    sep = (template.text or "")
    style_node.tail = sep
    template.insert(0, style_node)
    # fill the style node
    style_node_text = [""]
    for i, seat_data in enumerate(fillings, start=1):
        style_node_text.append(f"    .party{i}" "{" + "".join(f"{k}:{v};" for k, v in seat_data.items() if k not in ("title", "desc")) + "}")
    style_node_text.append("")
    style_node.text = sep.join(style_node_text)

    fillings_iter = chain(*(repeat((i, sd), r) for i, (sd, r) in enumerate(fillings.items(), start=1)))
    for element_id in sorted(elements, reverse=bool(metadata["reversed"])):
        try:
            nparty, seat_data = next(fillings_iter)
        except StopIteration:
            raise ValueError(f"filling does not contain enough seats")

        node = elements[element_id]
        node_class = f"party{nparty}"
        if "class" in node.attrib:
            node_class = node.attrib["class"] + " " + node_class
        node.set("class", node_class)
        del node.attrib[_pardiag_prefix+"id"]

        for d in ("title", "desc"):
            v = seat_data.get(d)
            if v:
                el = ET.Element(d)
                el.text = v
                node.append(el)

    if tuple(fillings_iter):
        raise ValueError("filling contains too many seats")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        sys.exit(main(*sys.argv[1:]))
