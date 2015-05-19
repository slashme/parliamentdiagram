#!/usr/bin/python
import cgi, re, math, random, datetime, sys, os
#form = cgi.FieldStorage()
#inputlist = form.getvalue("inputlist", "")
inputlist = sys.argv[1] #Uncomment for commandline debugging
#Append input list to log file:
logfile=open('wmlog','a')
logfile.write(datetime.datetime.utcnow().strftime("%Y-%m-%d-%H-%M-%S-%f ") + inputlist + '\n')
logfile.close()
#Create always-positive hash of the request string:
requesthash = str(hash(inputlist) % ((sys.maxsize + 1) * 2))
#Check whether we have a file made from this exact string in the directory:
for file in os.listdir("svgfiles"):
    if file.count(str(requesthash)): #We've done this diagram before, just serve it.
        print("svgfiles/"+file)
        sys.exit()
#If we get here, we didn't find a matching request, so continue.
#Create a filename that will be unique each time.  Old files are deleted with a cron script.
svgfilename = 'svgfiles/' + datetime.datetime.utcnow().strftime("%Y-%m-%d-%H-%M-%S-%f") + "-" + str(hash(inputlist) % ((sys.maxsize + 1) * 2))+'.svg'
if inputlist:
  #initialize dictionary of options - this will hold things like spot radius, spacing, width of blocks, etc.
  optionlist={}
  #initialize list of parties
  partylist=[]
  #Keep a running total of the number of delegates in each part of the diagram, for use later.
  sumdelegates = {'left': 0, 'right': 0, 'center': 0, 'head': 0} 
  #Keep a list of any empty seats we reserve to space out parties
  emptyseats   = {'left': 0, 'right': 0, 'center': 0, 'head': 0} 
  #error flag: This seems ugly, but what should I do?
  error=0
  for i in re.split("\s*;\s*",inputlist):
    inputitem=re.split('\s*,\s*', i)
    #If it's an option, handle it separately
    if re.search("option",inputitem[0]):
      optionlist[inputitem[0][7:]]=float(inputitem[1])
    else:
      partylist.append(inputitem)
  for i in partylist:
    if len(i)<3: #Must contain at least: party name; number; party grouping (left/right/center/head)
      error=1
    elif re.search('[^0-9]', i[1]): #Must have at least a digit in the number
      error=1
    else:
      i[1]=int(i[1]) #TODO: What happens if this fails? Shouldn't, because it's from an input form, though.
    #Iterate over the list of party groups, adding the number of delegates to the correct one:
    for g, n in sumdelegates.iteritems(): #g is the group name in each case
      if re.search(g,i[2]):
        sumdelegates[g] += i[1]
  if sumdelegates < 1:
    error=1
  if not error:
    #Modified layout design:
    #Left and right are by default blocks of shape 5x1
    #Head (Speaker or whatever) is a single row of blocks down the middle,
    #  starting one block left of the party blocks.
    #Cross-bench is by default a block of shape 1x4 at the back.
    #
    #If the number of rows in the wings is not defined, calculate it:
    if (not 'wingrows' in optionlist) or optionlist['wingrows']==0:
      optionlist['wingrows']=int(math.ceil(math.sqrt(max(sumdelegates['left'],sumdelegates['right'])/20.0))*2)
    #Whether or not it's defined; now make it a dict with a value for left and right - this may later not be the same any more.
    optionlist['wingrows']={'left':int(optionlist['wingrows']), 'right':int(optionlist['wingrows'])}
    if optionlist['cozy']:
      wingcols=int(math.ceil(max(sumdelegates['left'],sumdelegates['right'])/float(optionlist['wingrows']['left'])))
    else: #we will only allow one diagram column per party, so calculate how many empty seats to add to each wing's delegate count
      for wing in ['left','right']:
        for i in [ party for party in partylist if party[2] == wing ]:
          emptyseats[wing] += optionlist['wingrows'][wing] - i[1] % optionlist['wingrows'][wing]
      #Now calculate the number of columns in the diagram based on the spaced-out count; wingrows['left'] and right are still the same at this point.
      wingcols=int(math.ceil(max(sumdelegates['left']+emptyseats['left'],sumdelegates['right']+emptyseats['right'])/float(optionlist['wingrows']['left'])))
    if (not 'centercols' in optionlist) or optionlist['centercols']==0: #If the number of columns in the cross-bench is not defined, calculate it:
      optionlist['centercols']=int(math.ceil(math.sqrt(sumdelegates['center']/4.0)))
    else:
      optionlist['centercols']=int(optionlist['centercols'])
    try:
      centerrows=math.ceil(float(sumdelegates['center'])/optionlist['centercols'])
    except ZeroDivisionError:
      centerrows=0
    #Calculate the total number of columns in the diagram. First see how many rows for head + wings:
    if sumdelegates['head']:
      totalcols=max(wingcols+1,sumdelegates['head'])
      leftoffset=1 #Leave room for the Speaker's block to protrude on the left
    else:
      leftoffset=0 #Don't leave room for the Speaker's block to protrude on the left
      totalcols=wingcols
    #Now, if there's a cross-bench, add an empty row plus the number of rows in the cross-bench:
    if sumdelegates['center']:
      totalcols += 1
      totalcols += optionlist['centercols']
    #Calculate the total number of rows in the diagram; wingrows left and right are still the same.
    totalrows = max(optionlist['wingrows']['left']*2+2,centerrows)
    #How big is a seat? SVG canvas size is 360x360, with 5px border, so 350x350 diagram.
    blocksize=350.0/max(totalcols,totalrows)
    #To make the code later a bit neater, calculate the absolute radius now:
    optionlist['radius']=min(0.5,optionlist['radius'])
    radius=optionlist['radius']*blocksize*(1-optionlist['spacing'])
    #So the diagram size is now fixed:
    svgwidth  = blocksize*totalcols+10
    svgheight = blocksize*totalrows+10
    #Initialise list of positions for the various diagram elements:
    poslist={'head':[], 'left':[], 'right':[], 'center':[]}
    #All head blocks are in a single row with same y position. Call it centertop; we'll need it again:
    centertop=svgheight/2-blocksize*(1-optionlist['spacing'])/2
    for x in range(sumdelegates['head']):
      poslist['head'].append([5.0+blocksize*(x+optionlist['spacing']/2),centertop])
    #Cross-bench parties are 5 from the edge, vertically centered:
    for x in range(optionlist['centercols']):
      thiscol= int(min(centerrows,sumdelegates['center']-x*centerrows)) #How many rows in this column of the cross-bench
      for y in range(thiscol):
        poslist['center'].append([svgwidth-5.0-(optionlist['centercols']-x-optionlist['spacing']/2)*blocksize,((svgheight-thiscol*blocksize)/2)+blocksize*(y+optionlist['spacing']/2)])
        poslist['center'].sort(key=lambda point: point[1]) 
    if optionlist['fullwidth']: #If we want each wing to use the full width of the diagram
      for wing in ['left','right']:
        if not optionlist['cozy']: #If we are reserving blank seats to space out the diagram 
          for i in range(optionlist['wingrows'][wing],1,-1):
            tempgaps = 0 #temporary variable to hold the number of empty seats with i-1 rows
            for j in [ party for party in partylist if party[2] == wing ]:
              tempgaps += (i-1) - j[1] % (i-1)
            if (sumdelegates[wing] + tempgaps > wingcols*(i-1)): #if it doesn't fit into i-1 rows
              break #break out of the for loop: all should be set up correctly.
            else: #it fits in i-1 rows
              emptyseats[wing] = tempgaps
              optionlist['wingrows'][wing]=i-1
        else: 
          #If we are not reserving blank seats to space out the diagram, just fit it suitably.
          #This will do nothing to the larger wing, but will slim down the smaller one.
          optionlist['wingrows']['left']=int(math.ceil(sumdelegates['left']/float(wingcols))) 
    #Left parties are in the top block:
    for x in range(wingcols):
      for y in range(optionlist['wingrows']['left']):
        poslist['left'].append([5+(leftoffset+x+optionlist['spacing']/2)*blocksize,centertop-(1.5+y)*blocksize])
    #Right parties are in the bottom block:
    for x in range(wingcols):
      for y in range(optionlist['wingrows']['right']):
        poslist['right'].append([5+(leftoffset+x+optionlist['spacing']/2)*blocksize,centertop+(1.5+y)*blocksize])
    # Open svg file for writing:
    outfile=open(svgfilename,'w')
    #Write svg header:
    outfile.write('<?xml version="1.0" encoding="UTF-8" standalone="no"?>\n')
    outfile.write('<svg xmlns:svg="http://www.w3.org/2000/svg"\n')
    outfile.write('xmlns="http://www.w3.org/2000/svg" version="1.1"\n')
    #Make 350 px wide, 175 px high diagram with a 5 px blank border
    tempstring='width="%.1f" height="%.1f">' % (svgwidth, svgheight)
    outfile.write(tempstring+'\n')
    outfile.write('<!-- Created with the Wikimedia westminster parliament diagram creator (http://tools.wmflabs.org/parliamentdiagram/westminsterinputform.html) -->\n')
    outfile.write('<g id="diagram">\n')
    #Draw the head parties; first create a group for them:
    outfile.write('  <g id="headbench">\n')
    Counter=-1 #How many spots have we drawn yet for this group?
    for i in [ party for party in partylist if party[2] == 'head' ]:
      outfile.write('  <g style="fill:'+i[3]+'" id="'+i[0]+'">\n')
      for Counter in range(Counter+1, Counter+1+i[1]):
        tempstring='    <rect x="%.4f" y="%.4f" rx="%.2f" ry="%.2f" width="%.2f" height="%.2f"/>' % (poslist['head'][Counter][0], poslist['head'][Counter][1], radius, radius, blocksize*(1.0-optionlist['spacing']), blocksize*(1.0-optionlist['spacing']) )
	outfile.write(tempstring+'\n')
      outfile.write('  </g>\n')
    outfile.write('  </g>\n')
    #Draw the left parties; first create a group for them:
    outfile.write('  <g id="leftbench">\n')
    Counter=-1 #How many spots have we drawn yet for this group?
    for i in [ party for party in partylist if party[2] == 'left' ]:
      outfile.write('  <g style="fill:'+i[3]+'" id="'+i[0]+'">\n')
      for Counter in range(Counter+1, Counter+1+i[1]):
        tempstring='    <rect x="%.4f" y="%.4f" rx="%.2f" ry="%.2f" width="%.2f" height="%.2f"/>' % (poslist['left'][Counter][0], poslist['left'][Counter][1], radius, radius, blocksize*(1.0-optionlist['spacing']), blocksize*(1.0-optionlist['spacing']) )
	outfile.write(tempstring+'\n')
      if not optionlist['cozy']: #If we're leaving gaps between parties, skip the leftover blocks in the row
        Counter += optionlist['wingrows']['left'] - i[1] % optionlist['wingrows']['left']
      outfile.write('  </g>\n')
    outfile.write('  </g>\n')
    #Draw the right parties; first create a group for them:
    outfile.write('  <g id="rightbench">\n')
    Counter=-1 #How many spots have we drawn yet for this group?
    for i in [ party for party in partylist if party[2] == 'right' ]:
      outfile.write('  <g style="fill:'+i[3]+'" id="'+i[0]+'">\n')
      for Counter in range(Counter+1, Counter+1+i[1]):
        tempstring='    <rect x="%.4f" y="%.4f" rx="%.2f" ry="%.2f" width="%.2f" height="%.2f"/>' % (poslist['right'][Counter][0], poslist['right'][Counter][1], radius, radius, blocksize*(1.0-optionlist['spacing']), blocksize*(1.0-optionlist['spacing']) )
	outfile.write(tempstring+'\n')
      if not optionlist['cozy']: #If we're leaving gaps between parties, skip the leftover blocks in the row
        Counter += optionlist['wingrows']['right'] - i[1] % optionlist['wingrows']['right']
      outfile.write('  </g>\n')
    outfile.write('  </g>\n')
    #Draw the center parties; first create a group for them:
    outfile.write('  <g id="centerbench">\n')
    Counter=-1 #How many spots have we drawn yet for this group?
    for i in [ party for party in partylist if party[2] == 'center' ]:
      outfile.write('  <g style="fill:'+i[3]+'" id="'+i[0]+'">\n')
      for Counter in range(Counter+1, Counter+1+i[1]):
        tempstring='    <rect x="%.4f" y="%.4f" rx="%.2f" ry="%.2f" width="%.2f" height="%.2f"/>' % (poslist['center'][Counter][0], poslist['center'][Counter][1], radius, radius, blocksize*(1.0-optionlist['spacing']), blocksize*(1.0-optionlist['spacing']) )
	outfile.write(tempstring+'\n')
      outfile.write('  </g>\n')
    outfile.write('  </g>\n')
    outfile.write('</g>\n')
    outfile.write('</svg>\n')
    outfile.close()
    #Pass the output filename to the calling page.
    print svgfilename
