#!/usr/bin/python
import cgi, re, math, random, datetime, sys, os
#form = cgi.FieldStorage()
#inputlist = form.getvalue("inputlist", "")
inputlist = sys.argv[1]
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
    #Left and right are by default blocks of shape 6x2
    #Head (Speaker or whatever) is a single row of blocks down the middle,
    #  starting one block left of the party blocks.
    #Cross-bench is by default a block of shape 1x4 at the back.
    #
    #If the number of rows in the wings is not defined, calculate it:
    if (not 'wingrows' in optionlist) or optionlist['wingrows']==0:
      optionlist['wingrows']=int(math.ceil(math.sqrt(max(sumdelegates['left'],sumdelegates['right'])/12.0))*2)
    wingcols=int(math.ceil(max(sumdelegates['left'],sumdelegates['right'])/optionlist['wingrows']))
    if (not 'centercols' in optionlist) or optionlist['centercols']==0: #If the number of columns in the cross-bench is not defined, calculate it:
      optionlist['centercols']=int(math.ceil(math.sqrt(sumdelegates['center']/4.0)))
    try:
      centerrows=math.ceil(sumdelegates['center']/optionlist['centercols'])
    except ZeroDivisionError:
      centerrows=0
    #Calculate the total number of columns in the diagram. First see how many rows for head + wings:
    if sumdelegates['head']:
      totalcols=max(wingcols+1,sumdelegates['head'])
    else:
      totalcols=wingcols
    #Now, if there's a cross-bench, add an empty row plus the number of rows in the cross-bench:
    if sumdelegates['center']:
      totalcols += 1
      totalcols += optionlist['centercols']
      leftoffset=1 #Leave room for the Speaker's block to protrude on the left
    else:
      leftoffset=0 #Don't leave room for the Speaker's block to protrude on the left
    #Calculate the total number of rows in the diagram:
    totalrows = max(optionlist['wingrows']*2+1,centerrows)
    #How big is a block? SVG canvas size is 360x360, with 5px border, so 350x350 diagram.
    blocksize=350.0/max(totalcols,totalrows)
    #So the diagram size is now fixed:
    svgwidth  = blocksize*totalcols
    svgheight = blocksize*totalrows
    #Initialise list of positions for the various diagram elements:
    poslist={'head':[], 'left':[], 'right':[], 'center':[]}
    #All head blocks are in a single row with same y position. Call it centertop; we'll need it again:
    centertop=5+blocksize*optionlist['wingrows']
    for x in range(sumdelegates['head']):
      poslist['head'].append([5.0+blocksize*(x+optionlist['spacing']/2),centertop+optionlist['spacing']/2*blocksize])
    #Cross-bench parties are 5 from the edge, vertically centered:
    for x in range(optionlist['centercols']):
      thiscol= min(centerrows,sumdelegates['center']-x*centerrows) #How many rows in this column of the cross-bench
      for y in range(thiscol):
        poslist['center'].append([355-(optionlist['centercols']-x+optionlist['spacing']/2)*blocksize,(5+(355-thiscol*blocksize)/2)+blocksize*(y+optionlist['spacing']/2)])
    #Left parties are in the top block:
    for x in range(wingcols):
      for y in range(optionlist['wingrows']):
        poslist['left'].append([5+(leftoffset+x+optionlist['spacing']/2)*blocksize,(centertop-1-y+optionlist['spacing']/2)*blocksize])
    #Right parties are in the bottom block:
    for x in range(wingcols):
      for y in range(optionlist['wingrows']):
        poslist['right'].append([5+(leftoffset+x+optionlist['spacing']/2)*blocksize,(centertop+1+y+optionlist['spacing']/2)*blocksize])
    # Open svg file for writing:
    outfile=open(svgfilename,'w')
    #Write svg header:
    outfile.write('<?xml version="1.0" encoding="UTF-8" standalone="no"?>\n')
    outfile.write('<svg xmlns:svg="http://www.w3.org/2000/svg"\n')
    outfile.write('xmlns="http://www.w3.org/2000/svg" version="1.1"\n')
    #Make 350 px wide, 175 px high diagram with a 5 px blank border
    outfile.write('width="360" height="185">\n')
    outfile.write('<!-- Created with the Wikimedia westminster parliament diagram creator (http://tools.wmflabs.org/parliamentdiagram/westminsterinputform.html) -->\n')
    outfile.write('<g id="diagram">\n')
    #Draw the head parties; first create a group for them:
    outfile.write('  <g id="headbench">\n')
    Counter=-1 #How many spots have we drawn yet for this group?
    for i in [ party for party in partylist if party[2] == 'head' ]:
      outfile.write('  <g style="fill:'+i[3]+'" id="'+i[0]+'">\n')
      for Counter in range(Counter+1, Counter+1+i[1]):
        tempstring='    <rect x="%.4f" y="%.4f" rx="%.2f" ry="%.2f" width="%.2f" height="%.2f"/>' % (poslist['head'][Counter][0], poslist['head'][Counter][1], optionlist['radius']/blocksize, optionlist['radius']/blocksize, 25/blocksize*(1.0-optionlist['spacing']), 25/blocksize*(1.0-optionlist['spacing']) )
	outfile.write(tempstring+'\n')
      outfile.write('  </g>\n')
    outfile.write('  </g>\n')
    #Draw the left parties; first create a group for them:
    outfile.write('  <g id="leftbench">\n')
    Counter=-1 #How many spots have we drawn yet for this group?
    for i in [ party for party in partylist if party[2] == 'left' ]:
      outfile.write('  <g style="fill:'+i[3]+'" id="'+i[0]+'">\n')
      for Counter in range(Counter+1, Counter+1+i[1]):
        tempstring='    <rect x="%.4f" y="%.4f" rx="%.2f" ry="%.2f" width="%.2f" height="%.2f"/>' % (poslist['left'][Counter][0], poslist['left'][Counter][1], optionlist['radius']/blocksize, optionlist['radius']/blocksize, 25/blocksize*(1.0-optionlist['spacing']), 25/blocksize*(1.0-optionlist['spacing']) )
	outfile.write(tempstring+'\n')
      outfile.write('  </g>\n')
    outfile.write('  </g>\n')
    #Draw the right parties; first create a group for them:
    outfile.write('  <g id="rightbench">\n')
    Counter=-1 #How many spots have we drawn yet for this group?
    for i in [ party for party in partylist if party[2] == 'right' ]:
      outfile.write('  <g style="fill:'+i[3]+'" id="'+i[0]+'">\n')
      for Counter in range(Counter+1, Counter+1+i[1]):
        tempstring='    <rect x="%.4f" y="%.4f" rx="%.2f" ry="%.2f" width="%.2f" height="%.2f"/>' % (poslist['right'][Counter][0], poslist['right'][Counter][1], optionlist['radius']/blocksize, optionlist['radius']/blocksize, 25/blocksize*(1.0-optionlist['spacing']), 25/blocksize*(1.0-optionlist['spacing']) )
	outfile.write(tempstring+'\n')
      outfile.write('  </g>\n')
    outfile.write('  </g>\n')
    #Draw the center parties; first create a group for them:
    outfile.write('  <g id="centerbench">\n')
    Counter=-1 #How many spots have we drawn yet for this group?
    for i in [ party for party in partylist if party[2] == 'center' ]:
      outfile.write('  <g style="fill:'+i[3]+'" id="'+i[0]+'">\n')
      for Counter in range(Counter+1, Counter+1+i[1]):
        tempstring='    <rect x="%.4f" y="%.4f" rx="%.2f" ry="%.2f" width="%.2f" height="%.2f"/>' % (poslist['center'][Counter][0], poslist['center'][Counter][1], optionlist['radius']/blocksize, optionlist['radius']/blocksize, 25/blocksize*(1.0-optionlist['spacing']), 25/blocksize*(1.0-optionlist['spacing']) )
	outfile.write(tempstring+'\n')
      outfile.write('  </g>\n')
    outfile.write('  </g>\n')
    outfile.write('</g>\n')
    outfile.write('</svg>\n')
    outfile.close()
    #Pass the output filename to the calling page.
    print svgfilename
