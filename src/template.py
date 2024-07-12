from itertools import chain, repeat
import sys
from typing import Literal, NamedTuple
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

def main(template_file, output_file=sys.stdout, *,
        filling: Literal[True]|None|dict[SeatData, int] = None,
        toggles: dict[str, bool]|None = None,
        use_classes: bool|None = None,
        ) -> int|str|None:
    """
    Considers the template file and the output file to be a file descriptor or a file path.

    If filling is None, prints the number of seats.
    If filling is a SeatData: nseats dict,
    and the sum of nseats is the number of seats,
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
        # TODO: actually if filling is not True,
        # compute a ratio between the number of seats and the number of parties
        use_classes = filling is not True

    template_str = template_file.read()
    template = ET.fromstring(template_str)

    if filling is True:
        nseats = _scan_template(template).nseats
        filling = {SeatData(fill=color): 1 for color in _generate_rainbow(nseats, 250)}

    if filling is None:
        print(_scan_template(template), file=output_file)
    else:
        _fill_template(template, filling, toggles or {}, use_classes)
        print(ET.tostring(template, encoding="unicode"), file=output_file)

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


class _TemplateData(NamedTuple):
    nseats: int
    togglable_elements: tuple[str, ...]

def _scan_template(template: ET.Element) -> _TemplateData:
    seat_elements, togglable_elements = _extract_template(template, check_unicity=True)
    return _TemplateData(len(seat_elements), tuple(togglable_elements))

def _extract_template(template: ET.Element, *,
        check_unicity=True,
        ) -> tuple[dict[int, ET.Element], dict[str, list[ET.Element]]]:

    seat_elements = {}
    togglable_elements = {}

    for node in template.findall(".//"):
        if (id := node.get(_pardiag_prefix+"id", None)):
            if not id.isdecimal():
                raise ValueError(f"Invalid id : {id!r}")
            seat = int(id)
            if check_unicity and (seat in seat_elements):
                raise Exception(f"Duplicate seat : {id}")
            seat_elements[seat] = node

        if (togglable := node.get(_pardiag_prefix+"togglable", None)):
            if id:
                raise ValueError(f"Node {node} has both an id and a togglable attribute")
            togglable_elements.setdefault(togglable, []).append(node)

    return seat_elements, togglable_elements


def _fill_template(template: ET.Element,
        fillings: dict[SeatData, int],
        toggles: dict[str, bool],
        use_classes: bool,
        ) -> None:

    metadata = _get_template_metadata(template)

    seat_elements, togglable_elements = _extract_template(template)

    if frozenset(toggles).difference(togglable_elements):
        raise ValueError("Unknown toggles : " + ", ".join(frozenset(toggles).difference(togglable_elements)))

    if use_classes:
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
    # for each seat element:
    for element_id in sorted(seat_elements, reverse=bool(metadata["reversed"])):
        try:
            nparty, seat_data = next(fillings_iter)
        except StopIteration:
            raise ValueError("filling does not contain enough seats")

        node = seat_elements[element_id]
        del node.attrib[_pardiag_prefix+"id"]

        if use_classes:
            node_class = f"party{nparty}"
            if "class" in node.attrib:
                node_class = node.attrib["class"] + " " + node_class
            node.set("class", node_class)

            for d in ("title", "desc"):
                v = seat_data.get(d)
                if v:
                    el = ET.Element(d)
                    el.text = v
                    node.append(el)

        else:
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

    for toggle, state in toggles.items():
        if not state:
            for node in togglable_elements[toggle]:
                node.find("..").remove(node) # type: ignore

if __name__ == "__main__":
    if len(sys.argv) > 1:
        sys.exit(main(*sys.argv[1:]))
