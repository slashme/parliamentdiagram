#!/usr/bin/python
import cgi
import re
import math
import datetime
import sys
import os
import json

# Initialize useful calculated fields:
# Total number of seats per number of rows in diagram:
TOTALS = [
    3, 15, 33, 61, 95, 138, 189, 247, 313, 388, 469, 559, 657, 762, 876,  997,
    1126, 1263, 1408, 1560, 1722, 1889, 2066, 2250, 2442, 2641, 2850, 3064,
    3289, 3519, 3759, 4005, 4261, 4522, 4794, 5071, 5358, 5652, 5953, 6263,
    6581, 6906, 7239, 7581, 7929, 8287, 8650, 9024, 9404, 9793, 10187, 10594,
    11003, 11425, 11850, 12288, 12729, 13183, 13638, 14109, 14580, 15066, 15553,
    16055, 16557, 17075, 17592, 18126, 18660, 19208, 19758, 20323, 20888, 21468,
    22050, 22645, 23243, 23853, 24467, 25094, 25723, 26364, 27011, 27667, 28329,
    29001, 29679, 30367, 31061
]

LOGFILE = None  # A file to log everything we want

def main():
    """
    Doesn't return anything, but in case of success: prints a filename, which
    will hence be sent to the web interface.
    """
    start_time = datetime.datetime.utcnow().strftime("%Y-%m-%d-%H-%M-%S-%f")
    form = cgi.FieldStorage()
    data = form.getvalue("data", "")
    inputlist = json.loads(data)
    # inputlist = sys.argv[1]

    # Open a log file and append input list to it:
    global LOGFILE
    LOGFILE = open('log', 'a')
    log("{} {}".format(start_time, inputlist))

    # Create always-positive hash of the request string:
    request_hash = str(hash(data) % ((sys.maxsize + 1) * 2))

    cached_filename = return_file_if_already_exist(request_hash)
    if cached_filename:
        print(cached_filename)
    elif inputlist:
        filename = treat_inputlist(inputlist, start_time, request_hash)
        if filename is None :
            log('Something went wrong. Maybe the input list was badly '
                'formatted, or had 0 delegates, or had too many delegates.')
        else :
            print(filename)
    else:
        log('No inputlist')
    LOGFILE.close()


def log(message, newline=True):
    """
    Add message to LOGFILE.

    Parameters
    ----------
    message : string
        Message to append to the LOGFILE
    newline : bool
        Should we append a \n at the end of the message
    """
    LOGFILE.write("{}{}".format(message, '\n' if newline else ''))


def treat_inputlist(input_list, start_time, request_hash):
    """
    Generate a new SVG file and return it.

    Parameters
    ----------
    input_list : dict
        The request. A dict with the following format : {
            'parties': [
                {
                    'name': <str>,
                    'nb_seats': <int>,
                    'color': <str> (fill color, as hex code),
                    'border_size': <float>,
                    'border_color': <str> (as hex code)
                },
                ... /* other parties */
            ],
            'denser_rows': <bool> (should we compact rows)
        }
    start_time : str
    request_hash : str

    Return
    ------
    string|None
    """
    # Create a filename that will be unique each time.
    # Old files are deleted with a cron script.
    svg_filename = "svgfiles/{}-{}.svg".format(start_time, request_hash)

    party_list = input_list['parties']
    dense_rows = input_list['denser_rows']
    sum_delegates = count_delegates(party_list)
    if sum_delegates > 0:
        nb_rows = get_number_of_rows(sum_delegates)
        # Maximum radius of spot is 0.5/nb_rows; leave a bit of space.
        radius = 0.4 / nb_rows

        pos_list = get_spots_centers(sum_delegates, nb_rows, radius, dense_rows)
        draw_svg(svg_filename, sum_delegates, party_list, pos_list, radius)
        return svg_filename


def return_file_if_already_exist(request_hash):
    """
    If the requested file has been generated before, return its path/filename.

    Parameters
    ----------
    request_hash : str
        A unique hash representing a POST request.

    Return
    ------
    string|bool
        Either a path/filename, or False if such a file doesn't exist.
    """
    for file in os.listdir("svgfiles"):
        if file.count(str(request_hash)):
            return "svgfiles/{}".format(file)
    return False  # File doesn't already exist


def count_delegates(party_list):
    """
    Sums all delegates from all parties. Return 0 if something fails.

    Parameters
    ----------
    party_list : <list>
        Data for each party, a dict with the following format : [
            {
                'name': <str>,
                'nb_seats': <int>,
                'color': <str> (fill color, as hex code),
                'border_size': <float>,
                'border_color': <str> (as hex code)
            },
            ... /* other parties */
        ]

    Return
    ------
    int
    """
    sum = 0
    for party in party_list:
        sum += party['nb_seats']
        if sum > TOTALS[-1]:  # Can't handle such big number
            return 0
    return sum


def get_number_of_rows(nb_delegates):
    """
    How many rows will be needed to represent this many delegates.

    Parameters
    ----------
    int

    Return
    ------
    int
    """
    for i in range(len(TOTALS)):
        if TOTALS[i] >= nb_delegates:
            return i + 1


def get_spots_centers(nb_delegates, nb_rows, spot_radius, dense_rows):
    """
    Parameters
    ----------
    nb_delegates : int
    nb_rows : int
    spot_radius : float
    dense_rows: bool

    Return
    ------
    list<3-list<float>>
        The position of each single spot, represented as a list [angle, x, y]
    """
    if dense_rows:
        discarded_rows, diagram_fullness = optimize_rows(nb_delegates, nb_rows)
    else:
        discarded_rows = 0
        diagram_fullness = float(nb_delegates) / TOTALS[nb_rows - 1]

    positions = []
    for i in range(1 + discarded_rows, nb_rows):  # Fill the n-1 firsts rows
        add_ith_row_spots(positions, nb_rows, i, spot_radius, diagram_fullness)
    add_last_row_spots(positions, nb_delegates, nb_rows, spot_radius)
    positions.sort(reverse=True)
    return positions


def optimize_rows(nb_delegates, theoritical_nb_rows):
    """
    The number of seats may be small enough so we don't need to fill all the
    possible rows, but only the outermost ones. This says how much do we
    actually need.

    Parameters
    ----------
    nb_delegates : int
    theoritical_nb_rows : int
        The maximum number of rows we can fit in this diagram

    Return
    ------
    int
        The number of innermost rows to discard
    float
        The diagram fullness
    """
    handled_spots = 0
    rows_needed = 0
    for i in range(theoritical_nb_rows, 0, -1):
        # How many spots can we fit in each row
        # This 2 lines formula was determined by @slashme's math
        magic_number = 3.0 * theoritical_nb_rows + 4.0 * i - 2.0
        max_spot_in_row = math.pi / (2 * math.asin(2.0 / magic_number))
        handled_spots += int(max_spot_in_row)
        rows_needed += 1
        if handled_spots >= nb_delegates:
            nb_useless_rows = i - 1
            diagram_fullness = float(nb_delegates) / handled_spots
            return nb_useless_rows, diagram_fullness


def add_ith_row_spots(spots_positions, nb_rows, i,
                      spot_radius, diagram_fullness):
    """
    Assign spots to a row.

    Parameters
    ----------
    spots_positions : list<3-list<float>>
        New positions will be appened to this list.
    nb_rows : int
    i : int
        The number of the current row (1 being the centermost one)
    spot_radius : float
    diagram_fullness : float
        What proportion of the diagram is used
    """
    # Each row can contain pi/(2asin(2/(3n+4i-2))) spots, where n is the
    # number of rows and i is the number of the current row.
    magic_number = 3.0 * nb_rows + 4.0 * i - 2.0
    max_spot_in_row = math.pi / (2 * math.asin(2.0 / magic_number))

    # Fill the row proportionally to the "fullness" of the diagram
    nb_spots_in_ith_row = int(diagram_fullness * max_spot_in_row)

    # The radius of the ith row in an N-row diagram (Ri) is (3n+4*i-2)/(4n)
    ith_row_radius = magic_number / (4.0 * nb_rows)
    append_row_spots_positions(spots_positions, nb_spots_in_ith_row,
                               spot_radius, ith_row_radius)


def add_last_row_spots(spots_positions, nb_delegates, nb_rows, spot_radius):
    """
    All leftover seats must be added to the last row. So this function is an
    adapted version of `add_ith_row_spots()`.

    Parameters
    ----------
    spots_positions : list<3-list<float>>
        New positions will be appended to this list.
    nb_delegates : int
    nb_rows : int
    spot_radius : float
    """
    nb_leftover_seats = nb_delegates - len(spots_positions)
    last_row_radius = (7.0 * nb_rows - 2.0) / (4.0 * nb_rows)
    append_row_spots_positions(spots_positions, nb_leftover_seats,
                               spot_radius, last_row_radius)


def append_row_spots_positions(
        spots_positions, nb_seats_to_place, spot_radius, row_radius):
    """
    Will compute the positions of each spot of the current row, and add them to
    the list. For each spot, it will compute its angle, x and y according to
    theese formulas:
    The angle to a spot is n.(pi-2sin(r/Ri))/(Ni-1)+sin(r/Ri) where:
    - n is the spot's number in the row
    - Ni is the number of spots in this row
    - r is the radius of a spot
    - Ri is the radius of the current row
    x=R.cos(angle) + 1.75
    y=R.sin(angle)

    Parameters
    ----------
    spots_positions : list<3-list<float>>
        New positions will be appened to this list.
    nb_seats_to_place : int
        Number of seats in this row.
    spot_radius : float
        The radius of one single spot.
    row_radius : float
        The radius of the current row (since a row is actually a half-circle).
    """
    sin_r_rr = math.sin(spot_radius / row_radius)
    for i in range(nb_seats_to_place):
        if nb_seats_to_place == 1:
            angle = math.pi / 2.0
        else:
            angle = float(i)                               \
                        * (math.pi - 2.0 * sin_r_rr)       \
                        / (float(nb_seats_to_place) - 1.0) \
                    + sin_r_rr
        spots_positions.append([
            angle,
            row_radius * math.cos(angle) + 1.75,
            row_radius * math.sin(angle)])


def draw_svg(svg_filename, nb_delegates, party_list, positions_list, radius):
    """
    Draw the actual <circle>s in the SVG

    Parameters
    ----------
    svg_filename : str
    nb_delegates : int
    party_list : list<dict>
        A list of parties. Each party being a dict with the form {
            'name': <str>,
            'nb_seats': <int>,
            'color': <str> (fill color, as hex code),
            'border_size': <float>,
            'border_color': <str> (as hex code)}
    positions_list : list<3-list<float>
        [angle (useless in this function), x, y]
    radius : float
        Radius of a single spot
    """
    out_file = open(svg_filename, 'w')
    write_svg_header(out_file)
    write_svg_number_of_seats(out_file, nb_delegates)
    write_svg_seats(out_file, party_list, positions_list, radius)
    write_svg_footer(out_file)
    out_file.close()


def write_svg_header(out_file):
    # Write svg header:
    out_file.write(
        '<?xml version="1.0" encoding="UTF-8" standalone="no"?>\n'
        '<svg xmlns:svg="http://www.w3.org/2000/svg"\n'
        '     xmlns="http://www.w3.org/2000/svg" version="1.1"\n'
    # Make 350 px wide, 175 px high diagram with a 5 px blank border
        '     width="360" height="185">\n'
        '    <!-- Created with the Wikimedia parliament diagram creator (http://parliamentdiagram.toolforge.org/parliamentinputform.html) -->\n'
        '    <g>\n')


def write_svg_number_of_seats(out_file, nb_seats):
    # Print the number of seats in the middle at the bottom.
    out_file.write(
        '        <text x="175" y="175" \n'
        '              style="font-size:36px;font-weight:bold;text-align:center;text-anchor:middle;font-family:sans-serif">\n'
        '            {}\n'
        '        </text>\n'
        .format(nb_seats))


def write_svg_seats(out_file, party_list, positions_list, radius):
    """
    Write the main part of the SVG, each party will have its own <g>, and each
    delegate will be a <circle> inside this <g>.

    Parameters
    ----------
    out_file : file
    party_list : list<dict>
    positions_list : list<3-list<float>>
    radius : float
    """
    drawn_spots = 0
    for i in range(len(party_list)):
        # Remove illegal characters from party's name to make an svg id
        party_name = party_list[i]['name']
        sanitized_party_name = re.sub(r'[^a-zA-Z0-9_-]+', '-', party_name)
        block_id = "{}_{}".format(i, sanitized_party_name)

        party_nb_seats = party_list[i]['nb_seats']
        party_fill_color = party_list[i]['color']
        party_border_width = party_list[i]['border_size'] * radius * 100
        party_border_color = party_list[i]['border_color']

        out_file.write(  # <g> header
            '        <g style="fill:{0}; stroke-width:{1:.2f}; stroke:{2}" \n'
            '           id="{3}"> \n'.format(
                party_fill_color,
                party_border_width,
                party_border_color,
                block_id))
        out_file.write(  # Party name in a tooltip
            '            <title>{}</title>'.format(party_name))

        for j in range(drawn_spots, drawn_spots + party_nb_seats):
            x = 5.0 + 100.0 * positions_list[j][1]
            y = 5.0 + 100.0 * (1.75 - positions_list[j][2])
            r = radius * 100.0 - party_border_width / 2.0
            out_file.write(  # <circle> element
                '            <circle cx="{0:.2f}" cy="{1:.2f}" r="{2:.2f}"/> \n'
                .format(x, y, r))

        out_file.write('        </g>\n')  # Close <g>
        drawn_spots += party_nb_seats


def write_svg_footer(out_file):
    out_file.write(
        '    </g>\n'
        '</svg>\n')


if __name__ == '__main__':
    main()
