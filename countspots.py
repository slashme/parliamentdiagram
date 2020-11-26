import math

def maxspotsinarch(R,r,i):
  # Calculate how many spots can fit into a single arch when the
  # outside radius is R, the spot radius is r, and we're on arch
  # number i counting from the outside, with the outermost arch
  # counted as 0
  return(math.pi*R/2/r - math.pi*(2*i+1)/2)

def calcradiusbyspots(R,n,i):
  # Calculate the radius of spots that will just fit into arch number
  # i when the outside radius is R and there are n spots in the arch.
  return(math.pi*R/(2*n + math.pi*(2*i + 1)))

#Initialise spot radius for three spots
r=math.pi/(6+math.pi)
#String representation of the spot radius
rstring='%.5f' % r

#Create an empty dict to hold the numbers of spots per arch
nums={}

while r > 0.1:
  i=0
  nums[rstring]=[]
  while 1-r-2*i*r >= r:
    nums[rstring].append(round(maxspotsinarch(1,r,i),4))
    i += 1
  worstfit=[0, 0]
  for j in range(len(nums[rstring])):
    if nums[rstring][j] - int(nums[rstring][j]) > worstfit[1]:
      worstfit[0] = j
      worstfit[1] = nums[rstring][j] - int(nums[rstring][j])
  r=calcradiusbyspots(1,nums[rstring][worstfit[0]]-worstfit[1]+1,worstfit[0])
  rstring='%.5f' % r
