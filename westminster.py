#!/usr/bin/python
import cgi, re, math, random, datetime, sys, os
form = cgi.FieldStorage()
inputlist = form.getvalue("inputlist", "")
#Append input list to log file:
logfile=open('log','a')
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
  #initialize list of parties
  partylist=[]
  #Keep a running total of the number of delegates in each part of the diagram, for use later.
  sumdelegates = {'left': 0, 'right': 0, 'center': 0, 'head': 0} 
  #error flag: This seems ugly, but what should I do?
  error=0
  for i in re.split("\s*;\s*",inputlist):
    partylist.append(re.split('\s*,\s*', i))
  for i in partylist:
    if len(i)<3: #Must contain at least: number; party name; party grouping (left/right/center/head)
      error=1
    elif re.search('[^0-9]', i[1]): #Must have at least a digit in the number
      error=1
    else:
      i[1]=int(i[1]) #TODO: What happens if this fails? Shouldn't, because it's from an input form, though.
      sumdelegates += i[1]
    if len(i)<3:
      i.append("#%02x%02x%02x" % (random.randrange(255), random.randrange(255), random.randrange(255)))
    elif not re.match('^#[0-9a-fA-F][0-9a-fA-F][0-9a-fA-F][0-9a-fA-F][0-9a-fA-F][0-9a-fA-F]$',i[2]):
      i[2]=("#%02x%02x%02x" % (random.randrange(255), random.randrange(255), random.randrange(255)))
  if sumdelegates < 1:
    error=1
  if not error:
    #Initialize counters for use in layout
    spotcounter=0
    lines=0
    #Figure out how many rows are needed:
    for i in range(len(Totals)):
      if Totals[i] >= sumdelegates:
	rows=i+1
	break
    #Maximum radius of spot is 0.5/rows; leave a bit of space.
    radius=0.4/rows
# Open svg file for writing:
    outfile=open(svgfilename,'w')
    #Write svg header:
    outfile.write('<?xml version="1.0" encoding="UTF-8" standalone="no"?>\n')
    outfile.write('<svg xmlns:svg="http://www.w3.org/2000/svg"\n')
    outfile.write('xmlns="http://www.w3.org/2000/svg" version="1.1"\n')
    #Make 350 px wide, 175 px high diagram with a 5 px blank border
    outfile.write('width="360" height="185">\n')
    outfile.write('<!-- Created with the Wikimedia parliament diagram creator (http://tools.wmflabs.org/parliamentdiagram/parliamentinputform.html) -->\n')
    outfile.write('<g>\n')
    #Print the number of seats in the middle at the bottom.
    outfile.write('<text x="175" y="175" style="font-size:36px;font-weight:bold;text-align:center;text-anchor:middle;font-family:Sans">'+str(sumdelegates)+'</text>\n')
    #Create list of centre spots
    poslist=[]
    for i in range(1,rows):
      #Each row can contain pi/(2asin(2/(3n+4i-2))) spots, where n is the number of rows and i is the number of the current row.
      J=int(float(sumdelegates)/Totals[rows-1]*math.pi/(2*math.asin(2.0/(3.0*rows+4.0*i-2.0))))
      #The radius of the ith row in an N-row diagram (Ri) is (3*N+4*i-2)/(4*N)
      R=(3.0*rows+4.0*i-2.0)/(4.0*rows)
      if J==1:
        poslist.append([math.pi/2.0, 1.75*R, R])
      else:
        for j in range(J):
          #The angle to a spot is n.(pi-2sin(r/Ri))/(Ni-1)+sin(r/Ri) where Ni is the number in the arc
          #x=R.cos(theta) + 1.75
          #y=R.sin(theta)
          angle=float(j)*(math.pi-2.0*math.sin(radius/R))/(float(J)-1.0)+math.sin(radius/R)
          poslist.append([angle,R*math.cos(angle)+1.75,R*math.sin(angle)])
    J=sumdelegates-len(poslist)
    R=(7.0*rows-2.0)/(4.0*rows)
    if J==1:
      poslist.append([math.pi/2.0, 1.75*R, R])
    else:
      for j in range(J):
        angle=float(j)*(math.pi-2.0*math.sin(radius/R))/(float(J)-1.0)+math.sin(radius/R)
        poslist.append([angle,R*math.cos(angle)+1.75,R*math.sin(angle)])
    poslist.sort(reverse=True)
    Counter=-1 #How many spots have we drawn?
    for i in range(len(partylist)):
      #Make each party's blocks an svg group
      outfile.write('  <g style="fill:'+partylist[i][2]+'" id="'+''.join(partylist[i][0].split())+'">\n')
      for Counter in range(Counter+1, Counter+partylist[i][1]+1):
        tempstring='    <circle cx="%.2f" cy="%.2f" r="%.2f"/>' % (poslist[Counter][1]*100.0+5.0, 100.0*(1.75-poslist[Counter][2])+5.0, radius*100.0)
	outfile.write(tempstring+'\n')
      outfile.write('  </g>\n')
    outfile.write('</g>\n')
    outfile.write('</svg>\n')
    outfile.close()
    #Pass the output filename to the calling page.
    print svgfilename
