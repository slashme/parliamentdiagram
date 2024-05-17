#!/usr/bin/python3
import cgi
import datetime
import hashlib
import json
import math
import os
import re

def main(**inputlist):
    """
    Doesn't return anything, but in case of success: prints a filename, which
    will hence be sent to the web interface.
    """
    start_time = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d-%H-%M-%S-%f")
    if inputlist:
        data = json.dumps(inputlist)
    else:
        data = cgi.FieldStorage().getvalue("data", "") # type: str
        inputlist = json.loads(data)

    # Open a log file and append input list to it:
    with open('log', 'a') as LOGFILE:
        print(start_time, inputlist, file=LOGFILE)

        # Create consistent hash of the request string:
        request_hash = hashlib.sha256(data.encode()).hexdigest()

        cached_filename = return_file_if_already_exist(request_hash)
        if cached_filename:
            print(cached_filename)
        elif inputlist:
            filename = treat_inputlist(start_time, request_hash, **inputlist)
            if filename is None :
                print('Something went wrong. Maybe the input list was badly '
                    'formatted, or had 0 delegates, or had too many delegates.', file=LOGFILE)
            else:
                print(filename)
        else:
            print('No inputlist', file=LOGFILE)

def treat_inputlist(start_time, request_hash, parties=(), denser_rows=False, **kwargs):
    """
    Generate a new SVG file and return its name.

    start_time : str
    request_hash : str
    parties : Iterable[dict]
        A list of dicts with the following format :
            {
                'name': <str>,
                'nb_seats': <int>,
                'color': <str> (fill color, as hex code),
                'border_size': <float>,
                'border_color': <str> (as hex code)
            }
    denser_rows : bool
    kwargs : dict
        The rest of the request (should be empty)
    """
    # Create a filename that will be unique each time.
    # Old files are deleted with a cron script.
    svg_filename = "svgfiles/{}-{}.svg".format(start_time, request_hash)

    sum_delegates = sum(party['nb_seats'] for party in parties)
    if sum_delegates > 0:
        nb_rows = get_number_of_rows(sum_delegates)
        # Maximum radius of spot is 0.5/nb_rows; leave a bit of space.
        radius = 1. / (4*nb_rows-2)

        pos_list = get_spots_centers(sum_delegates, nb_rows, radius, denser_rows)
        draw_svg(svg_filename, sum_delegates, parties, pos_list, radius)
        return svg_filename


def return_file_if_already_exist(request_hash):
    """
    If the requested file has been generated before, return its path/filename.
    Otherwise, return False

    request_hash : str
        A unique hash representing a POST request.
    """
    for file in os.listdir("svgfiles"):
        if file.count(str(request_hash)):
            return "svgfiles/{}".format(file)
    return False  # File doesn't already exist


def get_number_of_rows(nb_delegates):
    """
    How many rows will be needed to represent this many delegates.
    """
    i = 1
    while Totals(i) < nb_delegates:
        i += 1
    return i


def Totals(rows):
    """
    Total number of seats per number of rows in diagram.
    Returns the maximal number of seats available for that number of rows

    i : int
        A number of rows of seats
    """
    tot = 0
    rad = 1/float(4*rows-2)
    for r in range(1, rows+1):
        R = .5 + 2*(r-1)*rad
        tot += int(math.pi*R/(2*rad))
    return tot


def get_spots_centers(nb_delegates, nb_rows, spot_radius, dense_rows):
    """
    Returns the position of each single spot, represented as a [angle, x, y] tuple.

    nb_delegates : int
    nb_rows : int
    spot_radius : float
    dense_rows : bool
    """
    startnumber = 1
    if dense_rows:
        rows_capacity = []
        # fit as many seats as we can in each row, starting from the outermost one
        for i in range(nb_rows, 0, -1):
            R = .5 + 2*(i-1)*spot_radius
            # the max number of seats in this row
            max_ = int(math.pi*R/(2*spot_radius))
            rows_capacity.append(max_)
            if sum(rows_capacity) > nb_delegates:
                break
        # rows_capacity' length is how many rows we need a minima to store all these delegates
        startnumber = nb_rows-len(rows_capacity)+1

    total = Totals(nb_rows)
    positions = []
    for r in range(startnumber, nb_rows+1):
        # R : row radius (radius of the circle crossing the center of each seat in the row)
        R = .5 + 2*(r-1)*spot_radius
        if r == nb_rows: # if it's the last row
            # fit all the remaining seats
            nb_seats_to_place = nb_delegates-len(positions)
        elif dense_rows:
            nb_seats_to_place = round(nb_delegates * rows_capacity[nb_rows-r]/sum(rows_capacity))
        else:
            # fullness of the diagram (relative to the correspondng Totals) times the maximum seats in that row
            nb_seats_to_place = int(float(nb_delegates) / total * math.pi*R/(2*spot_radius))
        if nb_seats_to_place == 1:
            positions.append([math.pi/2.0, 1.0, R])
        else:
            for j in range(nb_seats_to_place):
                # angle of the seat's position relative to the center of the hemicycle
                angle = float(j) * (math.pi-2.0*math.asin(spot_radius/R)) / (float(nb_seats_to_place)-1.0) + math.asin(spot_radius/R)
                # position relative to the center of the hemicycle
                positions.append([angle, R*math.cos(angle)+1, R*math.sin(angle)])
    positions.sort(reverse=True)
    return positions


def draw_svg(svg_filename, nb_delegates, party_list, positions_list, radius):
    """
    Draw the actual <circle>s in the SVG

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
    with open(svg_filename, 'w') as out_file:
        write_svg_header(out_file)
        write_svg_number_of_seats(out_file, nb_delegates)
        write_svg_seats(out_file, party_list, positions_list, radius)
        write_svg_footer(out_file)


def write_svg_header(out_file):
    # Write svg header:
    out_file.write(
        '<?xml version="1.0" encoding="UTF-8" standalone="no"?>\n'
        '<svg xmlns:svg="http://www.w3.org/2000/svg"\n'
        '     xmlns="http://www.w3.org/2000/svg" version="1.1"\n'
    # Make 350 px wide, 175 px high diagram with a 5 px blank border
        '     width="360" height="185">\n'
        '    <!-- Created with the Wikimedia parliament diagram creator (http://parliamentdiagram.toolforge.org/archinputform.php) -->\n'
        '    <g>\n')


def write_svg_number_of_seats(out_file, nb_seats):
    # Print the number of seats in the middle at the bottom.
    out_file.write(
        '        <text x="180" y="175" \n'
        '              style="font-size:36px;font-weight:bold;text-align:center;text-anchor:middle;font-family:sans-serif">\n'
        '            {}\n'
        '        </text>\n'
        .format(nb_seats))


def write_svg_seats(out_file, party_list, positions_list, radius):
    """
    Write the main part of the SVG, each party will have its own <g>, and each
    delegate will be a <circle> inside this <g>.

    out_file : file
    party_list : list<dict>
    positions_list : list<3-list<float>>
    radius : float
    """
    drawn_spots = 0
    for i, party in enumerate(party_list):
        # Remove illegal characters from party's name to make an svg id
        party_name = party['name']
        sanitized_party_name = re.sub(r'[^a-zA-Z0-9_-]+', '-', party_name)
        block_id = "{}_{}".format(i, sanitized_party_name)

        party_nb_seats = party['nb_seats']
        party_fill_color = party['color']
        party_border_width = party['border_size'] * radius * 175 * .8
        party_border_color = party['border_color']

        out_file.write(  # <g> header
            '        <g style="fill:{0}; stroke-width:{1:.2f}; stroke:{2}" \n'
            '           id="{3}"> \n'.format(
                party_fill_color,
                party_border_width,
                party_border_color,
                block_id))
        out_file.write(  # Party name in a tooltip
            '            <title>{}</title>\n'.format(party_name.encode('utf-8')))

        for j in range(drawn_spots, drawn_spots + party_nb_seats):
            x = 5.0 + 175 * positions_list[j][1]
            y = 5.0 + 175 * (1 - positions_list[j][2])
            r = radius * 175 * .8 - party_border_width / 2.0
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
