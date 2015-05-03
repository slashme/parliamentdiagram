#!/usr/bin/python
import cgi, re, math, random, datetime, sys, os
#form = cgi.FieldStorage()
#inputlist = form.getvalue("inputlist", "")
#For debugging:
inputlist = 'Socialist Party, 34, left, #660066; Labour Party, 171, left, #FF0000; Conservative Party, 175, right, #000000; Socialist Party, 1, head, #660066; Boring Party, 9, center, #555555; Neutral Party, 15, center, #663366'
#Append input list to log file:
#logfile=open('log','a')
#logfile.write(datetime.datetime.utcnow().strftime("%Y-%m-%d-%H-%M-%S-%f ") + inputlist + '\n')
#logfile.close()
#Create always-positive hash of the request string:
#requesthash = str(hash(inputlist) % ((sys.maxsize + 1) * 2))
#Check whether we have a file made from this exact string in the directory:
#for file in os.listdir("svgfiles"):
#    if file.count(str(requesthash)): #We've done this diagram before, just serve it.
#        print("svgfiles/"+file)
#        sys.exit()
#If we get here, we didn't find a matching request, so continue.
#Create a filename that will be unique each time.  Old files are deleted with a cron script.
svgfilename = 'svgfiles/' + datetime.datetime.utcnow().strftime("%Y-%m-%d-%H-%M-%S-%f") + "-" + str(hash(inputlist) % ((sys.maxsize + 1) * 2))+'.svg'
if inputlist:
  #initialize list of parties
  partylist=[]
  #Keep a running total of the number of delegates in each part of the diagram, for use later.
  sumdelegates = {'left': 0, 'right': 0, 'center': 0, 'head': 0} 
  #error flag: This seems ugly, but what should I do?
  error=0
  for i in re.split("\s*;\s*",inputlist):
    partylist.append(re.split('\s*,\s*', i))
  for i in partylist:
    if len(i)<3: #Must contain at least: party name; number; party grouping (left/right/center/head)
      error=1
    elif re.search('[^0-9]', i[1]): #Must have at least a digit in the number
      error=1
    else:
      i[1]=int(i[1]) #TODO: What happens if this fails? Shouldn't, because it's from an input form, though.
    #Iterate over the list of party groups, adding the number of delegates to the correct one:
    for g, n in sumdelegates.iteritems():
      if re.search(g,i[2]):
        sumdelegates[g] += i[1]
  if sumdelegates < 1:
    error=1
  if not error:
    #Initial layout design (subject to change):
    #Left and right are blocks of shape 12x2
    #Head (Speaker or whatever) is a 1x1 block
    #Center is a 1x4 block.
    #What size are our blocks?
    blockdensity = {} 
    blockdensity['left']=math.ceil(math.sqrt(sumdelegates['left']/24.0))
    blockdensity['right']=math.ceil(math.sqrt(sumdelegates['right']/24.0))
    blockdensity['center']=math.ceil(math.sqrt(sumdelegates['center']/4.0))
    blockdensity['head']=math.ceil(math.sqrt(sumdelegates['head']/1.0))
    maxdensity=max(list(blockdensity.values()))
    #We will draw this on a canvas that is 350x175px, so 25 times the unit size.
    #Initialise list of positions for the various blocks:
    poslist={'head':[], 'left':[], 'right':[], 'center':[]}
    #Head parties are in a block starting at 0,100 to 25,75
    #Always use the whole area for the head: this is speaker of parliament or whatever.
    for x in range(int(blockdensity['head'])):
      for y in range(int(blockdensity['head'])):
        poslist['head'].append([x/blockdensity['head']*25+5,(3-y/blockdensity['head'])*25+5])
    #Left parties are in a block starting at 50,175 to 350,125
    for x in range(int(maxdensity*12)):
      for y in range(int(maxdensity*2)):
        poslist['left'].append([x/maxdensity*25+50+5,(5+y/maxdensity)*25+5])
    #Right parties are in a block starting at 50,50 to 350,0
    for x in range(int(maxdensity*12)):
      for y in range(int(maxdensity*2)):
        poslist['right'].append([x/maxdensity*25+50+5,(y/maxdensity)*25+5])
    #Center parties are in a block starting at 175,100 to 275,75
    for x in range(int(maxdensity*12)):
      for y in range(int(maxdensity)):
        poslist['center'].append([x/maxdensity*25+175+5,(3+y/maxdensity)*25+5])
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
        tempstring='    <rect x="%.4f" y="%.4f" rx="%.2f" ry="%.2f" width="%.2f" height="%.2f"/>' % (poslist['head'][Counter][0], poslist['head'][Counter][1], 3/blockdensity['head'], 3/blockdensity['head'], 25/blockdensity['head'], 25/blockdensity['head'] )
	outfile.write(tempstring+'\n')
      outfile.write('  </g>\n')
    outfile.write('  </g>\n')
    #Draw the left parties; first create a group for them:
    outfile.write('  <g id="leftbench">\n')
    Counter=-1 #How many spots have we drawn yet for this group?
    for i in [ party for party in partylist if party[2] == 'left' ]:
      outfile.write('  <g style="fill:'+i[3]+'" id="'+i[0]+'">\n')
      for Counter in range(Counter+1, Counter+1+i[1]):
        tempstring='    <rect x="%.4f" y="%.4f" rx="%.2f" ry="%.2f" width="%.2f" height="%.2f"/>' % (poslist['left'][Counter][0], poslist['left'][Counter][1], 3/maxdensity, 3/maxdensity, 25/maxdensity, 25/maxdensity )
	outfile.write(tempstring+'\n')
      outfile.write('  </g>\n')
    outfile.write('  </g>\n')
    #Draw the right parties; first create a group for them:
    outfile.write('  <g id="rightbench">\n')
    Counter=-1 #How many spots have we drawn yet for this group?
    for i in [ party for party in partylist if party[2] == 'right' ]:
      outfile.write('  <g style="fill:'+i[3]+'" id="'+i[0]+'">\n')
      for Counter in range(Counter+1, Counter+1+i[1]):
        tempstring='    <rect x="%.4f" y="%.4f" rx="%.2f" ry="%.2f" width="%.2f" height="%.2f"/>' % (poslist['right'][Counter][0], poslist['right'][Counter][1], 3/maxdensity, 3/maxdensity, 25/maxdensity, 25/maxdensity )
	outfile.write(tempstring+'\n')
      outfile.write('  </g>\n')
    outfile.write('  </g>\n')
    #Draw the center parties; first create a group for them:
    outfile.write('  <g id="centerbench">\n')
    Counter=-1 #How many spots have we drawn yet for this group?
    for i in [ party for party in partylist if party[2] == 'center' ]:
      outfile.write('  <g style="fill:'+i[3]+'" id="'+i[0]+'">\n')
      for Counter in range(Counter+1, Counter+1+i[1]):
        tempstring='    <rect x="%.4f" y="%.4f" rx="%.2f" ry="%.2f" width="%.2f" height="%.2f"/>' % (poslist['center'][Counter][0], poslist['center'][Counter][1], 3/maxdensity, 3/maxdensity, 25/maxdensity, 25/maxdensity )
	outfile.write(tempstring+'\n')
      outfile.write('  </g>\n')
    outfile.write('  </g>\n')
    outfile.write('</g>\n')
    outfile.write('</svg>\n')
    outfile.close()
    #Pass the output filename to the calling page.
    print svgfilename
