#!/usr/bin/python
import cgi
import re
import math
import datetime
import sys
import os
import json

LOGFILE = None  # A file to log everything we want

def main(inputlist=None):
    """
    Doesn't return anything, but in case of success: prints a filename, which
    will hence be sent to the web interface.
    """
    start_time = datetime.datetime.utcnow().strftime("%Y-%m-%d-%H-%M-%S-%f")
    form = cgi.FieldStorage()
    data = form.getvalue("data", "")
    if inputlist is None:
        inputlist = json.loads(data)
    else:
        data = str(inputlist)

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
    sum_delegates = count_delegates(party_list)
    if sum_delegates > 0:
        nb_rows = get_number_of_rows(sum_delegates)
        # Maximum radius of spot is 0.5/nb_rows; leave a bit of space.
        radius = 1. / (4*nb_rows-2)

        pos_list = get_spots_centers(sum_delegates, nb_rows, radius)
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
    i = 0
    while True:
        i += 1
        if Totals(i) >= nb_delegates:
            return i


def Totals(i):
    """
    Total number of seats per number of rows in diagram.

    Parameters
    ----------
    i : int
        A number of rows of seats

    Return
    ------
    int
        The maximal number of seats available for that number of rows
    """
    if isinstance(i, int) and (i >= 0):
        rows = i + 1
        tot = 0
        rad = 1/float(4*rows-2)
        for r in range(1, rows+1):
            R = .5 + 2*(r-1)*rad
            tot += int(math.pi*R/(2*rad))
        return tot


def get_spots_centers(nb_delegates, nb_rows, spot_radius):
    """
    Parameters
    ----------
    nb_delegates : int
    nb_rows : int
    spot_radius : float

    Return
    ------
    list<3-list<float>>
        The position of each single spot, represented as a list [angle, x, y]
    """
    positions = []
    for r in range(1, nb_rows+1):  # Fill the n-1 firsts rows
        # R : row radius (radius of the circle crossing the center of each seat in the row)
        R = .5 + 2*(r-1)*spot_radius
        if r == nb_rows: # if it's the last row
            # fit all the remaining seats
            nb_seats_to_place = nb_delegates-len(positions)
        elif nb_delegates in {3, 4}:
            # places all seats in the last row, not necessary but prettier
            continue
        else:
            # fullness of the diagram (relative to the correspondng Totals) times the maximum seats in that row
            nb_seats_to_place = int(float(nb_delegates) / Totals(nb_rows-1)* math.pi*R/(2*spot_radius))
        if nb_seats_to_place == 1:
            positions.append([math.pi/2.0, 1.0, R])
        else:
            for j in range(nb_seats_to_place):
                # angle of the seat's position relative to the center of the hemicycle
                angle = float(j) * (math.pi-2.0*math.asin(spot_radius/R)) / (float(nb_seats_to_place)-1.0) + math.asin(spot_radius/R)
                # position relative to the center of the hemicycle
                positions.append([angle, R*math.cos(angle)+1.75, R*math.sin(angle)])
    positions.sort(reverse=True)
    return positions


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
        party_border_width = party_list[i]['border_size'] * radius * 100 * .8
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
            r = radius * 100.0 * .8 - party_border_width / 2.0
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
