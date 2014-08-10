#!/usr/pkg/bin/python
import cgi, re, math, random, datetime
form = cgi.FieldStorage()
inputlist = form.getvalue("inputlist", "")
#Create a filename that will be unique each time.  This means that I'll have to put something in my crontab to remove old files regularly.
filenameprefix = 'svgfiles/' + datetime.date.today().isoformat() + "." + str(hash(inputlist))
#Initialize useful calculated fields:
#Total number of seats per number of rows in diagram:
Totals=[ 3, 15, 33, 61, 95, 138, 189, 247, 313, 388, 469, 559, 657, 762, 876, 997, 1126, 1263, 1408, 1560, 1722, 1889, 2066, 2250, 2442, 2641, 2850, 3064, 3289, 3519, 3759, 4005, 4261, 4522, 4794, 5071, 5358, 5652, 5953, 6263, 6581, 6906, 7239, 7581, 7929, 8287, 8650, 9024, 9404]
if inputlist:
  #initialize list of parties
  partylist=[]
  #Keep a running total of the number of delegates in the diagram, for use later.
  sumdelegates=0
  #error flag: This seems ugly, but what should I do?
  error=0
  for i in re.split("\s*;\s*",inputlist):
    partylist.append(re.split('\s*,\s*', i))
  for i in partylist:
    if len(i)<2:
      error=1
    elif re.search('[^0-9]', i[1]):
      error=1
    else:
      i[1]=int(i[1])
      sumdelegates += i[1]
      if sumdelegates > Totals[-1]:
        error=1
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
    outfile=open(filenameprefix+'.svg','w')
    #Write svg header:
    outfile.write('<?xml version="1.0" encoding="UTF-8" standalone="no"?>\n')
    outfile.write('<svg xmlns:svg="http://www.w3.org/2000/svg"\n')
    outfile.write('xmlns="http://www.w3.org/2000/svg" version="1.1"\n')
    #Make 350 px wide, 175 px high diagram with a 5 px blank border
    outfile.write('width="360" height="185">\n')
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
        tempstring='    <circle cx="%5.2f" cy="%5.2f" r="%.2f"/>' % (poslist[Counter][1]*100.0+5.0, 100.0*(1.75-poslist[Counter][2])+5.0, radius*100.0)
	outfile.write(tempstring+'\n')
      outfile.write('  </g>\n')
    outfile.write('</g>\n')
    outfile.write('</svg>\n')
    outfile.close()
    #Pass the output filename to the calling page.
    print filenameprefix+'.svg'
