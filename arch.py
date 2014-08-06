#!/usr/pkg/bin/python
import cgi, re, math, random, datetime
print "Content-type: text/html"
print """
<html>
<head><title>Format parliament diagram</title></head>
<body>
  <h1>Under construction</h1>
  <h2>Format parliament diagram</h2>
  <h3>See <a href="https://en.wikipedia.org/wiki/User:Slashme/parliament.py">the source code</a> and <a href="http://en.wikipedia.org/wiki/User_talk:Slashme/parliament.py">the bug list</a></h3>
  <h3>How to use this script:</h3>
  <ul>
  <li>Type the list of parties in the box marked "List of parties".  Each party
  must have a name and a number of seats (can be 0), and if you like you can also add a colour.
  The parties in the list must be separated by semicolons (";") and the party
  information must be separated by commas (",") (For example, if you type:
  "Party A, 33; Party B, 22, #99FF99" you will have two parties, one labeled "Party A" with 33 seats and
  a random colour, and one labeled "Party B" in light green.)</li>
  <li>The script will create an svg diagram when you press "send".
  <b> - don\'t worry if it doesn\'t render properly in your browser, just save and open!</b></li>
  <li>If you want to use it on a Wikimedia project, I'd recommend using it on Wikimedia Commons; in that case, please use an appropriate category, for example <a href="http://commons.wikimedia.org/wiki/Category:Election_apportionment_diagrams">Election apportionment diagrams</a>.</li>
  </ul>
  <form method="post" action="arch.py">
    <p>List of parties: <input type="text" name="inputlist"/></p>
    <p><INPUT type="submit" value="Send"></p>
  </form>
"""
form = cgi.FieldStorage()
inputlist = form.getvalue("inputlist", "")
#Create a filename that will be unique each time.  This means that I'll have to put something in my crontab to remove old files regularly.
filenameprefix = 'svgfiles/' + datetime.date.today().isoformat() + "." + str(hash(inputlist))
#Initialize useful calculated fields:
#Total number of seats per number of rows in diagram:
Totals=[ 3, 15, 33, 61, 95, 138, 189, 247, 313, 388, 469, 559, 657, 762, 876, 997, 1126, 1263, 1408, 1560, 1722, 1889, 2066, 2250, 2442, 2641, 2850, 3064, 3289, 3519, 3759, 4005, 4261, 4522, 4794, 5071, 5358, 5652, 5953, 6263, 6581, 6906, 7239, 7581, 7929, 8287, 8650, 9024, 9404]
if inputlist:
  print "[Party, support, colour]<br>"
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
      print "short record: "+str(i)+"<br>"
      error=1
    elif re.search('[^0-9]', i[1]):
      print "not a positive integer: "+i[1]+"<br>"
      error=1
    else:
      i[1]=int(i[1])
      sumdelegates += i[1]
      if sumdelegates > Totals[-1]:
        print "More than "+str(Totals[-1])+" members? That's an election result, not a legislature!<br>"
        error=1
    if len(i)<3:
      i.append("#%02x%02x%02x" % (random.randrange(255), random.randrange(255), random.randrange(255)))
    elif not re.match('^#[0-9a-fA-F][0-9a-fA-F][0-9a-fA-F][0-9a-fA-F][0-9a-fA-F][0-9a-fA-F]$',i[2]):
      print "RGB colour wanted, \""+i[2]+"\" found.  Random colour assigned."
      i[2]=("#%02x%02x%02x" % (random.randrange(255), random.randrange(255), random.randrange(255)))
    print str(i)+"<br>"
  if sumdelegates < 1:
    print "Must have at least one seat in the legislature.<br>"
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
    print '<a href="http://tools.wmflabs.org/parliamentdiagram/'+filenameprefix+'.svg">Your SVG diagram</a><b> - don\'t worry if it doesn\'t render correctly in your browser, just save and open it!</b>'
# Open svg file for writing:
    outfile=open(filenameprefix+'.svg','w')
    #Write svg header:
    outfile.write('<?xml version="1.0" encoding="UTF-8" standalone="no"?>\n')
    outfile.write('<svg xmlns:svg="http://www.w3.org/2000/svg"\n')
    outfile.write('xmlns="http://www.w3.org/2000/svg" version="1.0"\n')
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
      outfile.write('  <g style="fill:'+partylist[i][2]+'" id="'+partylist[i][0]+'">\n')
      for Counter in range(Counter+1, Counter+partylist[i][1]+1):
        #print('    <circle cx="'+str(poslist[Counter][1]*100.0)+'" cy="'+str(100.0*(1.75-poslist[Counter][2]))+'" r="'+str(radius*100.0)+'"/>')
        tempstring='    <circle cx="%5.2f" cy="%5.2f" r="%5.2f"/>' % (poslist[Counter][1]*100.0+5.0, 100.0*(1.75-poslist[Counter][2])+5.0, radius*100.0)
	outfile.write(tempstring+'\n')
      outfile.write('  </g>\n')
    outfile.write('</g>\n')
    outfile.write('</svg>\n')
    outfile.close()
print """
<br>
This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
<br>
This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more details.
<br>
For the text of the GNU General Public License, please see <a href=http://www.gnu.org/licenses/>http://www.gnu.org/licenses/</a>.
</body>
</html>
"""
