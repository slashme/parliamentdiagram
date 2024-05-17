#!/usr/bin/python3
import cgi
import dataclasses
import datetime
import json
import math
import os
import sys

# TODO: adapt to the changes in JS and catch JSON data
# the object (dict) now contains an "options" dict and a "parties" list

@dataclasses.dataclass
class PartyEntry:
    name: str
    num: int
    group: str
    color: str
    given_seats: int = 0

def main():
    data = cgi.FieldStorage().getvalue("data", "")
    inputlist = json.loads(data)

    if not inputlist:
        return "No input."

    nowstrftime = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d-%H-%M-%S-%f")

    # Append input list to log file:
    with open('wmlog', 'a') as logfile:
        print(nowstrftime, inputlist, file=logfile)

    # Create always-positive hash of the request string:
    requesthash = str(hash(data) % ((sys.maxsize + 1) * 2))
    # Check whether we have a file made from this exact string in the directory:
    if print_file_if_already_exists(requesthash):
        return

    # If we get here, we didn't find a matching request, so continue.
    # Create a filename that will be unique each time.  Old files are deleted with a cron script.
    svgfilename = f"svgfiles/{nowstrftime}-{requesthash}.svg"

    options = data.get("options", {}) # type: dict
    partydictlist = data.get("parties", []) # type: list[dict]

    # initialize the list of parties
    parties = [] # type: list[PartyEntry]
    # Keep a running total of the number of delegates in each part of the diagram, for use later.
    sumdelegates = {'left': 0, 'right': 0, 'center': 0, 'head': 0}

    # TODO: obsolete, this is now name/num/group/color dicts instead of tuples
    # TODO: rewrite what needs to be so that it uses a dict instead of a list
    for i, pl in enumerate(partydictlist):
        p = PartyEntry(**pl)
        parties.append(p)
        for g in sumdelegates:
            if g in p.group:
                sumdelegates[g] += p.num

    if sum(sumdelegates.values()) < 1:
        return "No delegates."

    poslist, wingrows, radius, blocksize, svgwidth, svgheight = seats(
        partylist=partylist,
        sumdelegates=sumdelegates,
        option_wingrows=options.get('wingrows', None),
        cozy=options['cozy'],
        fullwidth=options['fullwidth'],
        centercols_raw=options['centercols'],
        option_radius=options['radius'],
        option_spacing=options['spacing']
    )

    # Open svg file for writing:
    with open(svgfilename, 'w') as outfile:
        # Write svg header:
        outfile.write(build_svg(partylist=partylist, poslist=poslist, blockside=blocksize*(1-options['spacing']), wingrows=wingrows, fullwidth_or_cozy=options['fullwidth'] or options['cozy'], radius=radius, svgwidth=svgwidth, svgheight=svgheight))
    # Pass the output filename to the calling page.
    print(svgfilename)

def print_file_if_already_exists(requesthash):
    """
    Returns whether the file has been found (and its path printed) or not.
    """
    for file in os.listdir("svgfiles"):
        if file.count(str(requesthash)):
            print(f"svgfiles/{file}")
            return True
    return False

def seats(*, partylist, sumdelegates, option_wingrows: "int|None", cozy, fullwidth, centercols_raw=None, option_radius, option_spacing):
    # Left and right are by default blocks of shape 5x1
    # Head (Speaker or whatever) is a single row of blocks down the middle,
    #  starting one block left of the party blocks, with a half-block gap on either side.
    # Cross-bench is by default a block of shape 1x4 at the back.

    # keep a list of any empty seats we reserve to space out parties
    emptyseats = dict.fromkeys(('left', 'right', 'center', 'head'), 0)

    # compute the number of ranks
    wingrows = dict.fromkeys(('left', 'right'),
        option_wingrows or math.ceil(math.sqrt(max(1, sumdelegates['left'], sumdelegates['right'])/20))*2)

    # compute the number of columns
    if cozy:
        wingcols = math.ceil(max(sumdelegates['left'], sumdelegates['right'])/wingrows['left'])
    else:
        # calculate the number of empty seats to add to each wing's delegate count
        for wing in wingrows:
            for party in partylist:
                if party[2] == wing:
                    # per-party count of empty seats needed to space out the diagram
                    party[4] = -party[1] % wingrows[wing]
                    # per-wing count kept separately for convenience
                    emptyseats[wing] += party[4]

        # calculate the number of columns in the diagram based on the spaced-out count
        # the two wingrows values are still the same at this point
        wingcols = math.ceil(max(sumdelegates['left']+emptyseats['left'], sumdelegates['right']+emptyseats['right'])/wingrows['left'])

    # slim down the diagram on one side if required
    if fullwidth:
        for wing in wingrows:
            if cozy:
                # if we are not reserving blank seats to space out the diagram, just fit it suitably
                # this will do nothing to the larger wing, but will slim down the smaller one
                wingrows[wing] = math.ceil(sumdelegates[wing]/wingcols)
            else:
                for i in range(wingrows[wing], 1, -1):
                    tempgaps = []
                    for party2 in partylist:
                        if party2[2] == wing:
                            tempgaps.append(-party2[1] % (i-1))

                    sumtempgaps = sum(tempgaps)

                    # if it doesn't fit into i-1 rows
                    if sumdelegates[wing] + sumtempgaps > wingcols*(i-1):
                        break

                    # it fits in i-1 rows
                    # total necessarily empty seats per wing
                    emptyseats[wing] = sumtempgaps
                    wingrows[wing] = i-1

                    for party2 in partylist:
                        if party2[2] == wing:
                            party2[4] = tempgaps.pop(0)

    # calculate the number of columns in the cross-bench if not defined
    if centercols_raw:
        try:
            centercols = int(centercols_raw)
        except ValueError:
            centercols_raw = None
    if not centercols_raw:
        centercols = math.ceil(math.sqrt(sumdelegates['center']/4))

    if centercols:
        centerrows = math.ceil(sumdelegates['center']/centercols)
    else:
        centerrows = 0

    # calculate the total number of columns in the diagram
    # first see how many rows for head + wings
    if sumdelegates['head']:
        totalcols = max(wingcols+1, sumdelegates['head'])
        # leave room for the Speaker's block to protrude on the left
        leftoffset = 1
    else:
        # don't leave room for the Speaker's block to protrude on the left
        leftoffset = 0
        totalcols = wingcols

    # if there's a cross-bench, add an empty row plus the number of rows in the cross-bench
    if sumdelegates['center']:
        totalcols += 1 + centercols

    # calculate the total number of rows in the diagram
    totalrows = max(wingrows['left'] + wingrows['right'] + 2, centerrows)

    # how big is a seat? SVG canvas size is 360x360, with 5px border, so 350x350 diagram
    blocksize = 350/max(totalcols, totalrows)

    # to make the code later a bit neater, calculate the absolute radius now
    # radius 0.5 is already a circle
    radius = min(.5, option_radius)*blocksize*(1-option_spacing)

    # so the diagram size is now fixed
    svgwidth = blocksize*totalcols+10
    svgheight = blocksize*totalrows+10

    # initialise list of positions for the various diagram elements
    poslist = {'head': [], 'left': [], 'right': [], 'center': []}

    # all head blocks are in a single row with same y position
    # the top y-coordinate of the center block if the wings are balanced
    # move it down by half the difference of the wing widths
    centertop = svgheight/2-blocksize*(1-option_spacing)/2 + (wingrows['left'] - wingrows['right']) * blocksize/2

    # the head
    for x in range(sumdelegates['head']):
        poslist['head'].append([5+blocksize*(x+option_spacing/2), centertop])

    # the cross-bench
    # 5 from the edge, vertically centered
    for x in range(centercols):
        thiscol = min(centerrows, sumdelegates['center']-x*centerrows)
        poslist['center'].append([
            svgwidth-5-(centercols-x-option_spacing/2) * blocksize,
            (svgheight-thiscol*blocksize)/2+blocksize*(option_spacing/2)
        ])
    poslist['center'].sort(key=lambda point: point[1])

    for x in range(wingcols):
        # left parties are in the top block
        for y in range(wingrows['left']):
            poslist['left'].append([
                5+(leftoffset+x+option_spacing/2)*blocksize,
                centertop-(1.5+y)*blocksize
            ])

        # right parties are in the bottom block
        for y in range(wingrows['right']):
            poslist['right'].append([
                5+(leftoffset+x+option_spacing/2)*blocksize,
                centertop+(1.5+y)*blocksize
            ])

    for wing in ('left', 'right'):
        if fullwidth and wingrows[wing] > 1:
            # first sort the spots - will need this whether or not it's cozy
            if wing == 'right':
                # sort by y coordinate if it's right wing
                poslist[wing].sort(key=lambda point: point[1])
            else:
                # sort by negative y coordinate if it's left wing
                poslist[wing].sort(key=lambda point: -point[1])

            # if we are smooshing them together without gaps, just fill from the bottom up
            if cozy:
                # trim the block to the exact number of delegates
                # so that filling from the left will fill the whole horizontal space
                poslist[wing] = poslist[wing][:sumdelegates[wing]]

            else:
                # grab a block for each party
                # make the x coordinate of all the superfluous seats big
                # so that when it's sorted by x coordinate, they are not allocated

                # sort by x coordinate again
                poslist[wing].sort(key=lambda point: point[0])

                # number of seats in the parties we've done already
                counter = 0

                # total filled and necessarily blank seats per wing
                totspots = sumdelegates[wing]+emptyseats[wing]

                # number of blank spots in this wing that need to be allocated to parties
                extraspots = wingrows[wing] * wingcols - totspots

                for party in partylist:
                    if party[2] == wing:
                        # total filled and necessarily blank seats per party
                        pspots = party[1]+party[4]

                        if totspots:
                            # apportion the extra spots by party size
                            addspots = round(extraspots * pspots / totspots)
                        else:
                            # if totspots is 0, don't add spots
                            addspots = 0

                        # fill it up to a total column
                        addspots += -addspots % wingrows[wing]

                        # grab the slice of seats to work on
                        # sorting this doesn't affect poslist, but assigning does
                        seatslice = poslist[wing][counter:counter+pspots+addspots]
                        extraspots -= addspots

                        # into how many spots do the remaining extra spots have to go?
                        totspots -= pspots+addspots

                        # if we're still on the left of the diagram
                        if counter < (sumdelegates[wing]+emptyseats[wing])/2:
                            # sort by negative x value
                            seatslice.sort(key=lambda point: -point[0])

                        if wing == 'right':
                            # sort by y coordinate if it's right wing
                            seatslice.sort(key=lambda point: point[1])
                        else:
                            # sort by negative y coordinate if it's left wing
                            seatslice.sort(key=lambda point: -point[1])

                        for i in seatslice[party[1]:]:
                            # set the x coordinate really big
                            # canvas size is 360, so 999 is big enough
                            # this changes the values in poslist, remember
                            i[0] = 999

                        counter += pspots+addspots

        poslist[wing].sort(key=lambda point: point[0])

    return poslist, wingrows, radius, blocksize, svgwidth, svgheight

def build_svg(*, partylist, poslist, blockside, wingrows, fullwidth_or_cozy, radius, svgwidth, svgheight) -> str:
    svglines = [
        '<?xml version="1.0" encoding="UTF-8" standalone="no"?>',
        '<svg xmlns:svg="http://www.w3.org/2000/svg"',
        '     xmlns="http://www.w3.org/2000/svg" version="1.1"',
       f'     width="{svgwidth:.1f}" height="{svgheight:.1f}">',
        '<!-- Created with the Wikimedia westminster parliament diagram creator (http://parliamentdiagram.toolforge.org/westminsterinputform.php) -->',
        '<g id="diagram">',
    ]

    for areaname, possublist in poslist.items():
        # Draw the parties of that area; first create a group for them:
        svglines.append(f'  <g id="{areaname}bench">\n')
        counter = 0 # How many spots have we drawn yet for this group?
        for party in partylist:
            if party[2] == areaname:
                svglines.append(f'    <g style="fill:{party[3]}" id="{party[0]}">')
                for subcounter in range(counter, counter+party[1]):
                    svglines.append(
                        '      <rect x="{0:.4f}" y="{1:.4f}" rx="{2:.2f}" ry="{2:.2f}" width="{3:.2f}" height="{3:.2f}"/>'.format(
                            possublist[subcounter][0],
                            possublist[subcounter][1],
                            radius,
                            blockside
                        ))
                counter = subcounter + 1
                svglines.append('    </g>')

                # If we're leaving gaps between parties, skip the leftover blocks in the row
                if areaname in ('left', 'right') and not fullwidth_or_cozy:
                    counter += -party[1] % wingrows[areaname]

        svglines.append('  </g>')

    svglines.append('</g>')
    svglines.append('</svg>')

    return "\n".join(svglines)

if __name__ == "__main__":
    sys.exit(main())
