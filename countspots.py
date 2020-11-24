import math

def maxspotsinarch(R,r,i):
  return(math.pi*R/2/r - math.pi*(2*i+1)/2)

def calcradiusbyspots(R,n,i):
    return(math.pi*R/(2*n + math.pi*(2*i + 1)))

r=math.pi/(6+math.pi)
rstring='%.5f' % r

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
    r=math.pi/(2*(nums[rstring][0]+1)+math.pi) # Now calculate with n(i)= one more than the number in the worstfit row and i = the worstfit row.
    rstring='%.5f' % r
