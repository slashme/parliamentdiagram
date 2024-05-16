#!/usr/bin/python3
import cgi
import re
import math
import datetime
import sys
import os

def main():
    inputlist = cgi.FieldStorage().getvalue("inputlist", "")
    # inputlist = sys.argv[1] #Uncomment for commandline debugging

    if not inputlist:
        return "No input."

    nowstrftime = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d-%H-%M-%S-%f")

    # Append input list to log file:
    with open('wmlog', 'a') as logfile:
        logfile.write(nowstrftime + " " + inputlist + '\n')

    # Create always-positive hash of the request string:
    requesthash = str(hash(inputlist) % ((sys.maxsize + 1) * 2))
    # Check whether we have a file made from this exact string in the directory:
    for file in os.listdir("svgfiles"):
        # We've done this diagram before, just serve it.
        if file.count(str(requesthash)):
            print("svgfiles/"+file)
            return

    # If we get here, we didn't find a matching request, so continue.
    # Create a filename that will be unique each time.  Old files are deleted with a cron script.
    svgfilename = 'svgfiles/' + nowstrftime + "-" + requesthash +'.svg'

    # initialize dictionary of options - this will hold things like spot radius, spacing, width of blocks, etc.
    optionlist = {}
    # initialize list of parties
    partylist = []
    # Keep a running total of the number of delegates in each part of the diagram, for use later.
    sumdelegates = {'left': 0, 'right': 0, 'center': 0, 'head': 0}
    # Keep a list of any empty seats we reserve to space out parties
    emptyseats = {'left': 0, 'right': 0, 'center': 0, 'head': 0}

    for i in re.split(r"\s*;\s*", inputlist):
        inputitem = re.split(r'\s*,\s*', i)
        # If it's an option, handle it separately
        if re.search("option", inputitem[0]):
            optionlist[inputitem[0][7:]] = float(inputitem[1])
        else:
            partylist.append(inputitem)

    for i, pl in enumerate(partylist):
        # Must contain: party name; number; party grouping (left/right/center/head); colour.
        if len(pl) != 4:
            return f"Incorrect number of columns in party n°{i}."
        elif re.search('[^0-9]', pl[1]):  # Must have at least a digit in the number
            return f"Invalid number of delegates : {pl[1]!r}."

        try:
            pl[1] = int(pl[1])
        except ValueError:
            pl[1] = 0

        # placeholder for empty seat count, for use when giving only one column per party.
        pl.append(0)

        # Iterate over the list of party groups, adding the number of delegates to the correct one:
        # g is the group name; n is the seat count for that group.
        for g in sumdelegates:
            if g in pl[2]:
                sumdelegates[g] += pl[1]

    if sum(sumdelegates.values()) < 1:
        return "No delegates."

    # Left and right are by default blocks of shape 5x1
    # Head (Speaker or whatever) is a single row of blocks down the middle,
    #  starting one block left of the party blocks, with a half-block gap on either side.
    # Cross-bench is by default a block of shape 1x4 at the back.
    #
    # First check whether the number of rows in the wings is defined:
    # If it isn't in the input list or can't be cast to an integer, set it to 0:
    try:
        optionlist['wingrows'] = int(optionlist['wingrows'])
    except (ValueError, KeyError):
        optionlist['wingrows'] = 0
    # If the number of rows in the wings is not defined, calculate it:
    if optionlist['wingrows'] == 0:
        optionlist['wingrows'] = int(math.ceil(math.sqrt(max(1, sumdelegates['left'], sumdelegates['right'])/20.0))*2)
    # Whether or not it's defined; now make it a dict with a value for left and right - this may later not be the same any more.
    wingrows = {'left': optionlist['wingrows'], 'right': optionlist['wingrows']}

    if optionlist['cozy']:
        wingcols = int(math.ceil(max(sumdelegates['left'], sumdelegates['right'])/float(wingrows['left'])))
    else:  # we will only allow one diagram column per party, so calculate how many empty seats to add to each wing's delegate count
        for wing in ['left', 'right']:
            for i in [party for party in partylist if party[2] == wing]:
                # per-party count of empty seats needed to space out diagram
                i[4] = -i[1] % wingrows[wing]
                # per-wing count kept separately for convenience
                emptyseats[wing] += i[4]

        # Now calculate the number of columns in the diagram based on the spaced-out count; wingrows['left'] and right are still the same at this point.
        wingcols = int(math.ceil(max(sumdelegates['left']+emptyseats['left'], sumdelegates['right']+emptyseats['right'])/float(wingrows['left'])))

    # Now slim down the diagram on one side if required:
    if optionlist['fullwidth']:  # If we want each wing to use the full width of the diagram
        for wing in ['left', 'right']:
            # If we are reserving blank seats to space out the diagram
            if optionlist['cozy']:
                # If we are not reserving blank seats to space out the diagram, just fit it suitably.
                # This will do nothing to the larger wing, but will slim down the smaller one.
                wingrows[wing] = int(math.ceil(sumdelegates[wing]/float(wingcols)))
            else:
                for i in range(wingrows[wing], 1, -1):
                    tempgaps = 0  # temporary variable to hold the number of empty seats with i-1 rows
                    for j in [party for party in partylist if party[2] == wing]:
                        tempgaps += -j[1] % (i-1)
                    # if it doesn't fit into i-1 rows
                    if (sumdelegates[wing] + tempgaps > wingcols*(i-1)):
                        # break out of the for loop: all should be set up correctly.
                        break
                    else:  # it fits in i-1 rows
                        # total necessarily empty seats per wing
                        emptyseats[wing] = tempgaps
                        wingrows[wing] = i-1
                        # This is really ugly: is there a better way than just calculating again?
                        for j in [party for party in partylist if party[2] == wing]:
                            j[4] = -j[1] % (i-1)
    # If the number of columns in the cross-bench is not defined, calculate it:
    if (not 'centercols' in optionlist) or optionlist['centercols'] == 0:
        optionlist['centercols'] = int(math.ceil(math.sqrt(sumdelegates['center']/4.0)))
    else:
        try:
            optionlist['centercols'] = int(optionlist['centercols'])
        # TODO: This is a hack - I seem to be getting a NaN here for some reason, need to fix it properly.
        except ValueError:
            # Do the same calculation as above if it's not a number.
            optionlist['centercols'] = int(math.ceil(math.sqrt(sumdelegates['center']/4.0)))
    try:
        centerrows = math.ceil(float(sumdelegates['center'])/optionlist['centercols'])
    except ZeroDivisionError:
        centerrows = 0
    # Calculate the total number of columns in the diagram. First see how many rows for head + wings:
    if sumdelegates['head']:
        totalcols = max(wingcols+1, sumdelegates['head'])
        leftoffset = 1  # Leave room for the Speaker's block to protrude on the left
    else:
        leftoffset = 0  # Don't leave room for the Speaker's block to protrude on the left
        totalcols = wingcols
    # Now, if there's a cross-bench, add an empty row plus the number of rows in the cross-bench:
    if sumdelegates['center']:
        totalcols += 1 + optionlist['centercols']
    # Calculate the total number of rows in the diagram
    totalrows = max(wingrows['left'] + wingrows['right'] + 2, centerrows)

    # How big is a seat? SVG canvas size is 360x360, with 5px border, so 350x350 diagram.
    blocksize = 350.0/max(totalcols, totalrows)

    # To make the code later a bit neater, calculate the absolute radius now:
    # radius 0.5 is already a circle
    optionlist['radius'] = min(0.5, optionlist['radius'])
    radius = optionlist['radius']*blocksize*(1-optionlist['spacing'])

    # So the diagram size is now fixed:
    svgwidth = blocksize*totalcols+10
    svgheight = blocksize*totalrows+10

    # Initialise list of positions for the various diagram elements:
    poslist = {'head': [], 'left': [], 'right': [], 'center': []}

    # All head blocks are in a single row with same y position. Call it centertop; we'll need it again:
    # The top y-coordinate of the center block if the wings are balanced.
    centertop = svgheight/2-blocksize*(1-optionlist['spacing'])/2
    # Move it down by half the difference of the wing widths
    centertop += (wingrows['left'] - wingrows['right']) * blocksize/2
    for x in range(sumdelegates['head']):
        poslist['head'].append([5.0+blocksize*(x+optionlist['spacing']/2), centertop])

    # Cross-bench parties are 5 from the edge, vertically centered:
    for x in range(optionlist['centercols']):
        # How many rows in this column of the cross-bench
        thiscol = int(min(centerrows, sumdelegates['center']-x*centerrows))
        for y in range(thiscol):
            poslist['center'].append([
                svgwidth-5.0-(optionlist['centercols']-x-optionlist['spacing']/2) * blocksize,
                ((svgheight-thiscol*blocksize)/2)+blocksize*(y+optionlist['spacing']/2)
            ])
            poslist['center'].sort(key=lambda point: point[1])

    # Left parties are in the top block:
    for x in range(wingcols):
        for y in range(wingrows['left']):
            poslist['left'].append([5+(leftoffset+x+optionlist['spacing']/2)*blocksize, centertop-(1.5+y)*blocksize])

    # Right parties are in the bottom block:
    for x in range(wingcols):
        for y in range(wingrows['right']):
            poslist['right'].append([5+(leftoffset+x+optionlist['spacing']/2)*blocksize, centertop+(1.5+y)*blocksize])

    for wing in ['left', 'right']:
        # If it's only one row, just fill from the left.
        if optionlist['fullwidth'] and wingrows[wing] > 1:
            # First sort the spots - will need this whether or not it's cozy.
            if wing == 'right':
                # sort by y coordinate if it's right wing
                poslist[wing].sort(key=lambda point: point[1])
            else:
                # sort by negative y coordinate if it's left wing
                poslist[wing].sort(key=lambda point: -point[1])
            # If we are smooshing them together without gaps, just fill from the bottom up
            if optionlist['cozy']:
                # Trim the block to the exact number of delegates, so that filling from the left will fill the whole horizontal space.
                poslist[wing] = poslist[wing][:sumdelegates[wing]]
                # Sort by x coordinate again.
                poslist[wing].sort(key=lambda point: point[0])
            else:  # Grab a block for each party; make the x coordinate of all the superfluous seats big, so that when it's sorted by x coordinate, they are not allocated.
                # Sort by x coordinate again.
                poslist[wing].sort(key=lambda point: point[0])
                counter = 0  # Number of seats in the parties we've done already
                # total filled and necessarily blank seats per wing
                totspots = sumdelegates[wing]+emptyseats[wing]
                # number of blank spots in this wing that need to be allocated to parties
                extraspots = wingrows[wing] * wingcols - totspots
                for j in [party for party in partylist if party[2] == wing]:
                    # total filled and necessarily blank seats per party
                    pspots = j[1]+j[4]
                    if totspots:
                        # apportion the extra spots by party size
                        addspots = round(extraspots * pspots / totspots)
                    else:  # if totspots is 0, don't add spots
                        addspots = 0
                    # Fill it up to a total column - note: pspots is already the right shape, so no need to use it here.
                    addspots += -addspots % wingrows[wing]
                    # Grab the slice of seats to work on. Sorting this doesn't affect poslist, but assigning does.
                    seatslice = poslist[wing][counter:counter+pspots+addspots]
                    extraspots -= addspots  # How many extra spots left to apportion now?
                    # Into how many spots do the remaining extra spots have to go?
                    totspots -= pspots+addspots
                    # if we're still on the left of the diagram:
                    if counter < (sumdelegates[wing]+emptyseats[wing])/2:
                        # sort by negative x value
                        seatslice.sort(key=lambda point: -point[0])
                    if wing == 'right':
                        # sort by y coordinate if it's right wing
                        seatslice.sort(key=lambda point: point[1])
                    else:
                        # sort by negative y coordinate if it's left wing
                        seatslice.sort(key=lambda point: -point[1])
                    for i in seatslice[j[1]:]:  # These seats must be blanked
                        # Set the x coordinate really big: canvas size is 360, so 999 is big enough. This changes the values in poslist, remember!
                        i[0] = 999
                    counter += pspots+addspots  # Where are we in the wing list now?
                poslist[wing].sort(key=lambda point: point[0])
        else:  # if not fullwidth and multirow
            poslist[wing].sort(key=lambda point: point[0])

    # Open svg file for writing:
    with open(svgfilename, 'w') as outfile:
        # Write svg header:
        outfile.write(build_svg(partylist=partylist, poslist=poslist, blockside=blocksize*(1-optionlist['spacing']), wingrows=wingrows, fullwidth_or_cozy=optionlist['fullwidth'] or optionlist['cozy'], radius=radius, svgwidth=svgwidth, svgheight=svgheight))
    # Pass the output filename to the calling page.
    print(svgfilename)

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
