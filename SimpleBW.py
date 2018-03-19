import math
import itertools
from TestDataSquares import *

'''
Assuming that the image file has been uploaded as aa array of pixels with their
value equalling the color stored in it. Current calculations assume
that images are in grayscale, and that each pixel has an intensity between 0 and 1.
This should be changed to a more applicable number scale later on.


TO DO:
-Finish writing preliminary alignPatterns function
-Update Shape object structure in analyzeImage to create an absolute order of angle sets in resulting pattern
-Decide how alignPatterns should handle patterns that contain different numbers of parts / elements
-Replace findMatchRatio with alignPatterns
-Clean-up updateChildren function - edit the way weights are used
-Look into better ways to determine "completeness" of image analysis in analyzeImage
-Adjust analyzeImage to understand curves

'''

class OOI: #ObjectOfInterest

     def __init__(self, parents = None, children = None, pattern = None):
          self.parents = parents
          self.children = children
          self.pattern = pattern


     def getPattern(self):
          return self.pattern



     #Takes in two patterns, and returns the permuatation of the first pattern that results in the most agreement between the elements
     #Patterns given to function with format: [number of parts, [angleSet1, angleSet2, ...]], where angleSetN is a list of angles pertaining to a specific part
     #It is assumed that items within angleSets are in absolute order - Shape dictionary in analyzeImage() needs to be altered to reflect this
     #Currently assumes that each angle set has the same number of parts - FIX THIS
     #Assumes each element is either a list or a float
     def alignPatterns(self, patt1, patt2):
          bestRatio = float('inf')
          bestPerm = None
          #Since number of parts will currently be assumed to be the same, only need to check permutations of one of the angleSets
          for test in itertools.permutations(patt1[1]):
               totalMatch = 0
               for i in range(len(test)):
                    as1 = test[i]
                    as2 = patt2[1][i]
                    setMatch = 0
                    weight = len(as1)
                    for j in range(weight):
                         if as1[j] != 0:
                              setMatch += (as2[j] - as1[j])/abs(as1[j])
                         else:
                              setMatch += (as2[j] - 0.000001)/0.000001 #Check to make sure this is an okay approximation

                    setRatio = setMatch / weight
                    totalMatch += setRatio

               testRatio = totalMatch / (len(test)+1) #Since the assumption is that the number of parts are the same, their difference is zero
               if testRatio < bestRatio:
                    bestRatio = testRatio
                    bestPerm = test

          return bestRatio, bestPerm
               
          
          
'''
Simple Black and White Image (Single object images)

Children will eventually consist of the different shapes (square, rectangle, etc). Stored as a dictionary?
Functions:
     identifyImage: Given an image, will return what shape the program identifies it as
     updatePattern: Updates what it means to be a SimpleBWImage given an image
     updateChildren: Given an image and what shape that image represents, updates the pattern of the corresponding child
     analyzeImage: Used to determine the pattern shown by a given image
     isPOI: Determines if a given pixel is within the focus bounds
     findPOI: Finds the initial pixel of interest by scanning the image
     expand: Finds the next POI for the program to look at
     setRelations: After POI analysis, determines the relations between the different parts of the object
'''
class SimpleBWImage(OOI):

     def __init__(self, parents = {}, children = {}, pattern = []):
          super().__init__(parents, children, pattern)


     def updatePattern(self, image, focus = 0.5, unityLimit = 0.8):
          return
     

     def identifyImage(self, image, focus = 0.5, unityLimit = 0.8, proxRatio = 0.8):
          imagePattern = self.analyzeImage(image, focus, unityLimit)
          bestRatio = 0.0
          bestChild = None
          #Determines which child best matches the pattern given
          for child in self.children:
               matchRatio = self.findMatchRatio(self.children[child], imagePattern)
               if matchRatio >= bestRatio:
                    bestRatio = matchRatio
                    bestChild = child

          if bestRatio >= proxRatio:
               return bestChild, bestRatio
          else:
               return None, 0.0


     #Each pattern needs a certain weight to it, so that "new" patterns are changed more by new inputs, while old patterns are changed less
     def updateChildren(self, image, childName, focus = 0.5, unityLimit = 0.8):
          imagePattern = self.analyzeImage(image, focus, unityLimit)
          if childName not in self.children:
               self.children[childName] = [1, imagePattern] #Follows format [weight, pattern]
          else:
               self.children[childName][0] += 1 #Increases weight of pattern by 1
               if imagePattern[0] > self.children[childName][1][0]: #Checks number of parts in each pattern
                    self.children[childName][1][0] = self.children[childName][1][0] + (imagePattern[0]/self.children[childName][0])
               else:
                    self.children[childName][1][0] = self.children[childName][1][0] - (imagePattern[0]/self.children[childName][0])

               angleSetPairs = self.patternMatch(imagePattern[1], self.children[childName][1][1]) #Matches which sets of angles are the closest matches to each other

               #Adjusts each angle within the list of angles (assumed that within a single angle set, each angle is in a fixed order)
               for anglePair in angleSetPairs:
                    for angle in self.children[childName][1][1][anglePair[1]]:
                         if self.children[childName][1][1][anglePair[1]][angle] > imagePattern[1][anglePair[0]][angle]:
                              self.children[childName][1][1][anglePair[1]][angle] = self.children[childName][1][1][anglePair[1]][angle] + (imagePattern[1][anglePair[0]][angle]/self.children[childName][0])
                         else:
                              self.children[childName][1][1][anglePair[1]][angle] = self.children[childName][1][1][anglePair[1]][angle] - (imagePattern[1][anglePair[0]][angle]/self.children[childName][0])

          return
          

     #Focus is what is used to determine if there is enough intensity in the pixel to determine if it is a PIO
     #Continuity is being defined as having a straight line (~1). Anything breaking that by a significant portion
     #is considered to be a new "part" of the object
     def analyzeImage(self, image, focus, unityLimit):
          y, x = self.findPOI(image, focus)
          shape = {1: {"start": [y, x], "end": [y, x], "equation": None}} #Holds information on the different parts of the image
          cShape = 1
          #Can we just save the previous pixel instead of all of the pixels in the current part?
          cPixels = [[y,x]] #Holds pixels of the active part
          complete = False
          count = 0
          direction = None

          testPrint = False
          
          while not complete and count<(len(image)*10): #Extra condition to make sure no infinite loops at the moment. Fix later
               nextY, nextX, direction = self.expand(image, x, y, focus, direction)
               for s in shape: #Makes sure that pixels are not analyzed twice
                    if s != cShape and ([nextY, nextX] == shape[s]["start"] or [nextY, nextX] == shape[s]["end"]):
                         complete = True
                    
               failed = True
               if not complete:
                    #Check continuity between current pixel and previous pixels
                    #Create a way to adjust the "vision" of comparison (how far back should comparisons go?)
                    try:
                         pixSlope = (nextY - cPixels[-1][0])/(nextX - cPixels[-1][1])
                    except ZeroDivisionError:
                         pixSlope = float('inf') #Vertical Lines

                    #Checks if the slope between the current pixel and the previous pixel match the total slope of the current part
                    if shape[cShape]["equation"] == None:
                         failed = False
                    elif shape[cShape]["equation"] == 0 and abs(pixSlope) <= unityLimit:
                         failed = False
                    elif shape[cShape]["equation"] == float('inf') or shape[cShape]["equation"] != 0:
                         
                         if pixSlope == shape[cShape]["equation"]:
                              failed = False
                         elif (shape[cShape]["equation"] == float('inf')) and (pixSlope >= (1-unityLimit)*((cPixels[-1][0]-0.99999*shape[cShape]["start"][0])/(cPixels[-1][1] - 0.99999*shape[cShape]["start"][1]))):
                              failed = False
                         elif ((pixSlope-shape[cShape]["equation"])/abs(shape[cShape]["equation"]) <= unityLimit):
                              failed = False
                      
               if failed or complete:
                    shape[cShape]["end"] = [cPixels[-1][0], cPixels[-1][1]]
                    if (shape[cShape]["end"][1] - shape[cShape]["start"][1]) == 0:
                         shape[cShape]["equation"] = float('inf')
                    else:
                         shape[cShape]["equation"] = (shape[cShape]["end"][0] - shape[cShape]["start"][0])/(shape[cShape]["end"][1] - shape[cShape]["start"][1])
                    if not complete:
                         shape[(len(shape)+1)] = {"start": [nextY, nextX], "end": [nextY, nextX], "equation": None}
                         cPixels = [[nextY, nextX]]
                         cShape = len(shape)
               else:
                    cPixels.append([nextY, nextX])
                    try:
                         shape[cShape]["equation"] = (nextY - shape[cShape]["start"][0])/(nextX - shape[cShape]["start"][1]) #This makes an imperfect line. Replace with a best fit line (Also, needs to incorporate curves)
                    except ZeroDivisionError:
                         shape[cShape]["equation"] = float('inf')

                         
               y = nextY
               x = nextX
               count += 1

          print(shape)
          newPatt = self.setRelations(shape) #Defines the relations between different parts of the object. At this point, all data concerning the image can be deleted from memory
     
          return newPatt


     def isPOI(self, coords, image, focus):
          if image[coords[1]][coords[0]] > focus:
               return True
          return False

      
     def findPOI(self, image, focus):
          #Scans document to find the first pixel that falls within the focus range
          #Look to see if this can be optimized
          for y in range(0, len(image)):
               for x in range(0, len(image[y])):
                    if image[y][x] > focus:
                         return y, x

          return None, None


     '''
     The function expand will look at the 8 pixels surrounding the pixel coordinates it is given. From there,
     it will first look right, then left, then down, then up. Pixels along borders are chosen over pixels with
     neighbors.
     '''
     def expand(self, image, x, y, focus, previousDirection):
          #Is there a more intelligent way to do this?
          #Fix this - breaks at corners

          #Looking right
          if previousDirection != "left" and (x+1)<len(image[y]):
               right = [[x+1, y+1], [x+1, y], [x+1, y-1]]
               rightPOI = [self.isPOI([x+1, y+1], image, focus), self.isPOI([x+1, y], image, focus), self.isPOI([x+1, y-1], image, focus)]
               if True in rightPOI:
                    if False in rightPOI: #If there are no non-POI, then there are no border pixels to grab
                         if (not rightPOI[0]) and rightPOI[1]:
                              return right[1][1], right[1][0], "right"
                         elif not (rightPOI[0] or rightPOI[1]) and rightPOI[2]:
                              return right[2][1], right[2][0], "right"
                         elif (not rightPOI[2]) and rightPOI[1]:
                              return right[1][1], right[1][0], "right"
                         else:
                              return right[0][1], right[0][0], "right"

          #Looking left
          if previousDirection != "right" and (x-1)>=0:
               left = [[x-1, y+1], [x-1, y], [x-1, y-1]]
               leftPOI = [self.isPOI([x-1, y+1], image, focus), self.isPOI([x-1, y], image, focus), self.isPOI([x-1, y-1], image, focus)]
               if True in leftPOI:
                    if False in leftPOI: #If there are no non-POI, then there are no border pixels to grab
                         if (not leftPOI[0]) and leftPOI[1]:
                              return left[1][1], left[1][0], "left"
                         elif not (leftPOI[0] or leftPOI[1]) and leftPOI[2]:
                              return left[2][1], left[2][0], "left"
                         elif (not leftPOI[2]) and leftPOI[1]:
                              return left[1][1], left[1][0], "left"
                         else:
                              return left[0][1], left[0][0], "left"

          #Looking down
          if previousDirection != "up" and (y-1)>=0:
               down = [[x-1, y-1], [x, y-1], [x+1, y-1]]
               downPOI = [self.isPOI([x-1, y-1], image, focus), self.isPOI([x, y-1], image, focus), self.isPOI([x+1, y-1], image, focus)]
               if True in downPOI:
                    if False in downPOI: #If there are no non-POI, then there are no border pixels to grab
                         if (not downPOI[0]) and downPOI[1]:
                              return down[1][1], down[1][0], "down"
                         elif not (downPOI[0] or downPOI[1]) and downPOI[2]:
                              return down[2][1], down[2][0], "down"
                         elif (not downPOI[2]) and downPOI[1]:
                              return down[1][1], down[1][0], "down"
                         else:
                              return down[0][1], down[0][0], "down"

          #Looking up
          if previousDirection != "down" and (y+1)<len(image):
               up = [[x-1, y+1], [x, y+1], [x+1, y+1]]
               upPOI = [self.isPOI([x-1, y+1], image, focus), self.isPOI([x, y+1], image, focus), self.isPOI([x+1, y+1], image, focus)]
               if True in upPOI:
                    if False in upPOI: #If there are no non-POI, then there are no border pixels to grab
                         if (not upPOI[0]) and upPOI[1]:
                              return up[1][1], up[1][0], "up"
                         elif not (upPOI[0] or upPOI[1]) and upPOI[2]:
                              return up[2][1], up[2][0], "up"
                         elif (not upPOI[2]) and upPOI[1]:
                              return up[1][1], up[1][0], "up"
                         else:
                              return up[0][1], up[0][0], "up"

          return y, x, previousDirection



     def setRelations(self, shape): #What criteria are necessary to identify shapes?
          pattern = [] #Format currently follows: [number of parts, list of angles (each element is a list of angles pertaining to a single part)]
          for s1 in shape:
               angles = []
               #Calculates the angle between any two lines (fix this to create a relation between curves)
               for s2 in shape:
                    if s1 != s2:
                         angle = math.atan(shape[s1]["equation"])-math.atan(shape[s2]["equation"])
                         angles.append(angle)
                         
               pattern.append(angles)

          return pattern
                         

data = makeTestImage()
SBW1 = SimpleBWImage()

def runTest1():
     SBW1.updateChildren(data, "square")
     print(SBW1.children)

dataSet = makeTestData(50)
def runTest2():
     for i in range(0, 45):
          SBW1.updateChildren(dataSet[i], "square")

     for i in range(45, 50):
          print(SBW1.identifyImage(dataSet[i]))



     
















          
                         
                         










          
