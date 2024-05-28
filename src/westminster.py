#!/usr/bin/python3
import math
import os
import typing

class Party(typing.NamedTuple):
    name: str
    num: int
    group: str
    color: str

def treat_inputlist(nowstrftime, requesthash, *,
        option_wingrows: "int|None" = None,
        partylist = (),
        cozy: bool,
        fullwidth: bool,
        centercols: int,
        radius: float,
        spacing: float,
        **kwargs) -> str:
    # Create a filename that will be unique each time.  Old files are deleted with a cron script.
    svgfilename = f"svgfiles/{nowstrftime}-{requesthash}.svg"

    # initialize the list of parties
    parties = {} # type: dict[Party, int]
    # Keep a running total of the number of delegates in each part of the diagram, for use later.
    sumdelegates = {'left': 0, 'right': 0, 'center': 0, 'head': 0}

    for pl in partylist:
        p = Party(**pl)
        parties[p] = 0
        for g in sumdelegates:
            if g in p.group:
                sumdelegates[g] += p.num

    if sum(sumdelegates.values()) < 1:
        raise ValueError("No delegates.")

    poslist, wingrows, radius, blocksize, svgwidth, svgheight = seats(
        parties=parties,
        sumdelegates=sumdelegates,
        option_wingrows=option_wingrows,
        cozy=cozy,
        fullwidth=fullwidth,
        centercols_raw=centercols,
        option_radius=radius,
        option_spacing=spacing
    )

    # Open svg file for writing:
    with open(os.path.join("static", svgfilename), 'w') as outfile:
        # Write svg:
        print(build_svg(
                parties=parties,
                poslist=poslist,
                blockside=blocksize*(1-spacing),
                wingrows=wingrows,
                fullwidth_or_cozy=fullwidth or cozy,
                radius=radius,
                svgwidth=svgwidth,
                svgheight=svgheight,
            ), file=outfile)

    # Pass the output filename to the calling page.
    return svgfilename

def seats(*,
        parties: dict[Party, int],
        sumdelegates: dict[str, int],
        option_wingrows: "int|None",
        cozy: bool,
        fullwidth: bool,
        centercols_raw: "int|None" = None,
        option_radius: float,
        option_spacing: float,
        ) -> tuple[dict[str, list[tuple[float, float]]], dict[str, int], float, float, float, float]:
    # Left and right are by default blocks of shape 5x1
    # Head (Speaker or whatever) is a single row of blocks down the middle,
    #  starting one block left of the party blocks, with a half-block gap on either side.
    # Cross-bench is by default a block of shape 1x4 at the back.

    # keep a list of any empty seats we reserve to space out parties
    emptyseats = dict.fromkeys(('left', 'right', 'center', 'head'), 0) # type: dict[str, int]

    # compute the number of ranks
    wingrows = dict.fromkeys(('left', 'right'),
        option_wingrows or math.ceil(math.sqrt(max(1, sumdelegates['left'], sumdelegates['right'])/20))*2
    ) # type: dict[str, int]

    # compute the number of columns
    if cozy:
        wingcols = math.ceil(max(sumdelegates['left'], sumdelegates['right'])/wingrows['left'])
    else:
        # calculate the number of empty seats to add to each wing's delegate count
        for wing in wingrows:
            for party in parties:
                if party.group == wing:
                    # per-party count of empty seats needed to space out the diagram
                    parties[party] = -party.num % wingrows[wing]
                    # per-wing count kept separately for convenience
                    emptyseats[wing] += parties[party]

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
                    for party in parties:
                        if party.group == wing:
                            tempgaps.append(-party.num % (i-1))

                    sumtempgaps = sum(tempgaps)

                    # if it doesn't fit into i-1 rows
                    if sumdelegates[wing] + sumtempgaps > wingcols*(i-1):
                        break

                    # it fits in i-1 rows
                    # total necessarily empty seats per wing
                    emptyseats[wing] = sumtempgaps
                    wingrows[wing] = i-1

                    for party in parties:
                        if party.group == wing:
                            parties[party] = tempgaps.pop(0)

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
    poslist = {'head': [], 'left': [], 'right': [], 'center': []} # type: dict[str, list[tuple[float, float]]]

    # all head blocks are in a single row with same y position
    # the top y-coordinate of the center block if the wings are balanced
    # move it down by half the difference of the wing widths
    centertop = svgheight/2-blocksize*(1-option_spacing)/2 + (wingrows['left'] - wingrows['right']) * blocksize/2

    # the head
    for x in range(sumdelegates['head']):
        poslist['head'].append((
            5+blocksize*(x+option_spacing/2),
            centertop,
        ))

    # the cross-bench
    # 5 from the edge, vertically centered
    for x in range(centercols):
        thiscol = min(centerrows, sumdelegates['center']-x*centerrows)
        for y in range(thiscol):
            poslist['center'].append((
                svgwidth-5-(centercols-x+option_spacing/2) * blocksize,
                (svgheight-thiscol*blocksize)/2+blocksize*(y+option_spacing/2),
            ))
    poslist['center'].sort(key=lambda point: point[1])

    for x in range(wingcols):
        # left parties are in the top block
        for y in range(wingrows['left']):
            poslist['left'].append((
                5+(leftoffset+x+option_spacing/2)*blocksize,
                centertop-(1.5+y)*blocksize,
            ))

        # right parties are in the bottom block
        for y in range(wingrows['right']):
            poslist['right'].append((
                5+(leftoffset+x+option_spacing/2)*blocksize,
                centertop+(1.5+y)*blocksize,
            ))

    for wing in ('left', 'right'):
        wingposlist = poslist[wing]
        if fullwidth and wingrows[wing] > 1:
            # first sort the spots - will need this whether or not it's cozy
            if wing == 'right':
                # sort by y coordinate if it's right wing
                wingposlist.sort(key=lambda point: point[1])
            else:
                # sort by negative y coordinate if it's left wing
                wingposlist.sort(key=lambda point: -point[1])

            # if we are smooshing them together without gaps, just fill from the bottom up
            if cozy:
                # trim the block to the exact number of delegates
                # so that filling from the left will fill the whole horizontal space
                poslist[wing] = wingposlist[:sumdelegates[wing]]

            else:
                # grab a block for each party
                # make the x coordinate of all the superfluous seats big
                # so that when it's sorted by x coordinate, they are not allocated

                # sort by x coordinate again
                wingposlist.sort(key=lambda point: point[0])

                # number of seats in the parties we've done already
                counter = 0

                # total filled and necessarily blank seats per wing
                totspots = sumdelegates[wing]+emptyseats[wing]

                # number of blank spots in this wing that need to be allocated to parties
                extraspots = wingrows[wing] * wingcols - totspots

                for party, val in parties.items():
                    if party.group == wing:
                        # total filled and necessarily blank seats per party
                        pspots = party.num+val

                        if totspots:
                            # apportion the extra spots by party size
                            addspots = round(extraspots * pspots / totspots)
                        else:
                            # if totspots is 0, don't add spots
                            addspots = 0

                        # fill it up to a total column
                        addspots += -addspots % wingrows[wing]

                        # grab the slice of seats to work on
                        # sorting this doesn't affect poslist
                        seatslice = wingposlist[counter:counter+pspots+addspots]
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

                        for point in seatslice[party.num:]:
                            wingposlist.remove(point)

                        counter += pspots+addspots

        wingposlist.sort(key=lambda point: point[0])

    return poslist, wingrows, radius, blocksize, svgwidth, svgheight

def build_svg(*,
        parties: dict[Party, int],
        poslist,
        blockside,
        wingrows,
        fullwidth_or_cozy,
        radius,
        svgwidth,
        svgheight,
        ) -> str:
    svglines = [
        '<?xml version="1.0" encoding="UTF-8" standalone="no"?>',
        '<svg xmlns:svg="http://www.w3.org/2000/svg"',
        '     xmlns="http://www.w3.org/2000/svg" version="1.1"',
       f'     width="{svgwidth:.1f}" height="{svgheight:.1f}">',
        '  <!-- Created with the Wikimedia westminster parliament diagram creator (http://parliamentdiagram.toolforge.org/westminsterinputform.php) -->',
        '  <g id="diagram">',
    ]

    for areaname, possublist in poslist.items():
        # Draw the parties of that area; first create a group for them:
        svglines.append(f'    <g id="{areaname}bench">')
        counter = 0 # How many spots have we drawn yet for this group?
        for party in parties:
            if party.group == areaname:
                svglines.append(f'      <g style="fill:{party.color}" id="{party.name}">')
                for subcounter in range(counter, counter+party.num):
                    svglines.append(
                        '        <rect x="{0:.4f}" y="{1:.4f}" rx="{2:.2f}" ry="{2:.2f}" width="{3:.2f}" height="{3:.2f}"/>'.format(
                            possublist[subcounter][0],
                            possublist[subcounter][1],
                            radius,
                            blockside
                        ))
                counter = subcounter + 1
                svglines.append('      </g>')

                # If we're leaving gaps between parties, skip the leftover blocks in the row
                if areaname in ('left', 'right') and not fullwidth_or_cozy:
                    counter += -party.num % wingrows[areaname]

        svglines.append('    </g>')

    svglines.append('  </g>')
    svglines.append('</svg>')

    return "\n".join(svglines)
