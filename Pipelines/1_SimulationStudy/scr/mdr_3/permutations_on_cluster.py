import os
import time
import string
import sys
import stat
import getopt
import subprocess
import random
import traceback
import multiprocessing
from optparse import OptionParser

#change standard out to be unbuffered so no need to flush.
sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 0)

CV_TESTING_CVC = "CV_TESTING-CVC-MODEL_OVERALL-MODEL_ATTRIBUTES"
CVC_CV_TESTING = "CVC-CV_TESTING-MODEL_OVERALL-MODEL_ATTRIBUTES"
CVC_MODEL_TESTING = "CVC-MODEL_TESTING-MODEL_OVERALL-MODEL_ATTRIBUTES"

def main():
    parser = OptionParser("""usage: %prog [options] dataset(s)
          %prog -h to see all options
          To use:
              1. Run this script with appropriate parameters. This initial run will submit jobs to the cluster.
              2. Wait for all jobs submitted by the script to complete, otherwise only partial results collated.
              3. Run the script again with the identical parameters.
              If all worked well results will be in your current directory with a name similar to
              the dataset name you provided. There will also be a folder with a similar name containing
              the raw output from the cluster. As long as this exists, results will be collated
              from the raw outputs. If the folder or its contents are deleted, then if the
              script is run again, new jobs will be submitted and run.

          This script's purpose is to make it easy to run mdr permutation tests on a cluster.
          MDR java has the ability to run permutation tests but it can take an excessive time.
          This script runs the permutation in small chunks across many cluster jobs
          and then collates the results. Each job is given a different random seed
          so each job will have different results, as desired.

          The result is a file that shows all of the permutation results and, at the bottom,
          the normal unpermuted mdr results along with their significance. The permutation
          results are sorted in descending order on the column "bal. acc. CV testing" which
          is correct and what mdrpt uses.""")
    parser.disable_interspersed_args()
    #CAREFUL -- short versions of args such as '-m' for --mdr can cause problems if there are other options starting with the same letter. If a user passed
    #'-max=1' (by mistake, meaning --max=1) that would be interpreted as '-m ax=1' so mdr would be set to 'ax=1' and max would not be set
    parser.add_option('--min', dest='min', help='1 for 1-way, 2 for 2-way. etcetera [default: %default]', type='int', default=1)
    parser.add_option('--max', dest='max', help='1 for 1-way, 2 for 2-way. etcetera [default: %default]', type='int', default=2)
    parser.add_option('--CVC', dest='CVC', help='how many subsets of the dataset to create and test separately [default: %default]', type='int', default=10)
    parser.add_option('--adjustForCovariate', dest='adjustForCovariate', help='if passed in, MDR will modify the dataset to remove main effects of the passed in attribute name [default: %default]', type='string', default='')
    parser.add_option('--topModelLandscapeSize', dest='topModelLandscapeSize', help='topModel landscape sizes [default: %default]', type='int', default=1000)
    parser.add_option('--permutations', dest='permutations', help='number of permutations [default: %default]', type='int', default=1000)
    parser.add_option('--acrossLevelsFitnessCriteriaOrder', dest='acrossLevelsFitnessCriteriaOrder', help='MOORE lab users only: alternate method for picking best model across levels [default: %default]', type='choice', choices=["CV_TESTING_CVC","CVC_CV_TESTING","CVC_MODEL_TESTING"], default="CV_TESTING_CVC")
    parser.add_option('--permutationsPerJob', dest='permutationsPerJob', help='how many permutations per job [default: %default]', type='int', default=20)
    parser.add_option('--useExplicitTestOfInteraction', dest='useExplicitTestOfInteraction',
                      help='if present, use explicit test. If absent, normal permutation [default: %default]', action='store_true', default=False)
    parser.add_option('--email', dest='email', help='email address to notify if job has trouble [default: %default]', default='')
    parser.add_option('--randomSeed', dest='randomSeed',
                      help='random seed for the run. If not set will always be the default so results will be identical. [default: %default]', type='int', default=0)
    parser.add_option('--mdr', dest='mdr', help='file path to the mdr jar file [default: %default]', default='mdr.jar')
    parser.add_option('--hours', dest='hours', help='maximum time in hours of walltime a job can use [default: %default]', type='int', default=12)
    parser.add_option('--priority', dest='priority', help='Defines the priority of the job relative to other jobs BY THE SAME USER (can be used to move to front of queue). The priority must be a integer between -1024 and +1023 inclusive. [default: %default]', type='int', default=0)
    parser.add_option('--resubmitUnfinished', dest='resubmitUnfinished', help='if the error file does not exist or is non-zero size resubmit the job [default: %default]', type='choice', choices=['true','false'], default='false')
    parser.add_option('--queue', dest='queue', help='queue to submit jobs to [default: %default]', default='')
    parser.add_option('--qsubCmd', dest='qsubCmd', help='command needed to submit a job to cluster. Trick: if set to "bash" this will run on the local machine rather than submitting to the cluster [default: %default]', default='qsub')
    parser.add_option('--qsubSleepSeconds', dest='qsubSleepSeconds', help='time to wait after submitting a job. Fractional numbers such as 0.1 for tenth of a second is fine [default: %default]', type='float', default=0)
    parser.add_option('--mem', dest='mem',
                      help='megabytes allocated on the cluster node. Should be less than or equal to totalMem/#processors per node) [default: %default]',
                      type='int', default=3800)

    sweepParameters = [
    ] 
    
    try:
	global options
        (options, args) = parser.parse_args()
        options.mdr = os.path.abspath(options.mdr)
        scriptName = '.'.join(os.path.basename(sys.argv[0]).split('.')[:-1])

        print('Options: ' + '\n'.join(str(options).split(',')))
        print('dataset(s): ' + str(args))
        if len(args) == 0:
            raise RuntimeError('You must pass in mdr datasets after the options.')
	
	#make sure acrossLevelsFitnessCriteriaOrder refers to a defined item (redundant with 'choices' but good to make sure)
	try:
	    acrossLevelsFitnessCriteriaOrder = eval(options.acrossLevelsFitnessCriteriaOrder)
	except NameError:
	    raise RuntimeError('Script programming error: options.acrossLevelsFitnessCriteriaOrder does not refer to a known variable.')
	
        projectDirectory = os.path.split(os.path.abspath(sys.argv[0]))[0] + '/'      #project directory is the file this script is in
        if not os.path.isfile(os.path.abspath(options.mdr)):
            raise RuntimeError('MDR jar file not found at \'' + os.path.abspath(options.mdr) + '\'')
        #convert parameter to a boolean
        options.resubmitUnfinished = options.resubmitUnfinished == 'true'
        numLevels = options.max - options.min + 1
        if (options.permutations % options.permutationsPerJob) != 0:
            raise RuntimeError('permutations(' + str(options.permutations) + ') must be evenly divisible by permutationsPerJob(' + str(options.permutationsPerJob) + ').')
        totalJobsNeeded = options.permutations / options.permutationsPerJob
        print("totalJobsNeeded based on permutations(" + str(options.permutations) + ") / permutationsPerJob(" + str(options.permutationsPerJob) + ") is " + str(totalJobsNeeded))
	useCluster = options.qsubCmd != "bash"
	if not useCluster:
	    runningJobs = []
	    cpu_count = multiprocessing.cpu_count()

	#numLevels does not affect numExpectedResultsPerPermutation because MDR permutation only outputs best row per permutation
	numExpectedResultsPerPermutation = 1 * max(1,len(sweepParameters))
	numLevels = options.max - options.min + 1
	extraResultsExpectedForFirstChunk = numLevels * max(1,len(sweepParameters))
        numExpectedResultsPerJob = options.permutationsPerJob * numExpectedResultsPerPermutation
	numExpectedResultsTotal = numExpectedResultsPerPermutation * options.permutations + extraResultsExpectedForFirstChunk
                        
        MDR_CMD = 'java -XX:+UseSerialGC -Xms' + str(options.mem) + 'm -Xmx' + str(options.mem) + 'm' + \
                    ' -jar ' + options.mdr + \
                    ' -min=' + str(options.min) +\
                    ' -max=' + str(options.max) + \
                    ' -cv=' + str(options.CVC) + \
                    ' -minimal_output=false' + \
	            ' -seed=' + str(options.randomSeed) + \
                    ' -top_models_landscape_size=' + str(options.topModelLandscapeSize) + \
                    ' -fitness_criteria_order_across_levels=' + eval(options.acrossLevelsFitnessCriteriaOrder) + \
                    ' -nolandscape' + \
                    ' -permute_with_explicit_test_of_interaction=' + str(options.useExplicitTestOfInteraction) +\
                    ' -permutations=' + str(options.permutationsPerJob)
        
        if len(options.adjustForCovariate) > 0:
            MDR_CMD += ' -adjust_for_covariate="' + options.adjustForCovariate + '"'

	collateOnly = False
	while True:    #loop again if necessary if not using a cluster
	    for inputFile in args:
		jobsSubmitted = 0
		jobsQueuedUp = 0
		jobsInProcess = 0
		jobsCompletedWithoutErrors = 0
		jobsCompletedWithErrors = 0
		jobsSuccessfullyCollated = 0
		jobsWithCollationErrors = 0
		permutationsLinesCollated = 0
		extraResultsFoundForFirstChunk = 0
		needToReadHeader = True
		global allPermutationResults
		allPermutationResults = []
		global bestModels
		bestModels = list()
		dataFilePath = os.path.abspath(inputFile)
		dataDirectory, dataFileName =  os.path.split(dataFilePath)
		if not os.path.isfile(dataFilePath):
		    raise RuntimeError('Expected file \'' + inputFile + '\' not found in directory \'' + dataDirectory + '\'.')
		else:
		    #new outputfile
		    dataFileIdentifier = '.'.join(dataFileName.split('.')[:-1]).replace(' ', '_')
		    runIdentifier = dataFileIdentifier + \
			          '_min-' + str(options.min) + \
			          '_max-' + str(options.max) + \
			          '_CVC-' + str(options.CVC) + \
			          '_seed-' + str(options.randomSeed) + \
			          '_permutations-' + str(options.permutations) + '-' + str(options.permutationsPerJob)
		    if options.useExplicitTestOfInteraction:
			runIdentifier += '_explicitTest-' + str(options.useExplicitTestOfInteraction)
		    if options.acrossLevelsFitnessCriteriaOrder != "CV_TESTING_CVC":
			runIdentifier += '_fitnessCriteria-' + options.acrossLevelsFitnessCriteriaOrder
			
		    workDirectory = os.path.abspath(runIdentifier) + '/'
		    if not os.path.isdir(workDirectory):
			os.makedirs(workDirectory)
		    #force disk system to read work directory to make sure it is mounted (Dartmouth discovery cluster kluge)
		    os.system('ls ' + workDirectory + '> /dev/null')
		    for permutationChunk in range(1,totalJobsNeeded+1):
			permuationStartIndex = (permutationChunk-1) * options.permutationsPerJob
			jobIdentifier = 'chunk-' + str(permutationChunk).zfill(5)
			outputFilePath = workDirectory + jobIdentifier + '.out'
			errorFilePath = workDirectory + jobIdentifier + '.err'
			pbsFilePath = workDirectory + jobIdentifier + '.pbs'
			#We want the 'regular' results we show at the end to match MDR results created with the passed random seed.
			#To do that, we use the passed in seed as the actual seed for the first job file and later get the 'regular' results
			#from the first file
			if permutationChunk == 1:
			    firstOutputFilePath = outputFilePath
			#if job does not exist create it and submit it
			submitJob = (not collateOnly) and (not os.path.isfile(pbsFilePath))
			if not submitJob and options.resubmitUnfinished:
			    submitJob = (not os.path.isfile(errorFilePath)) or (os.path.getsize(errorFilePath) > 0)
			    if submitJob:
				print('About to resubmit job: ' + jobIdentifier)
    
			if submitJob:
			    if os.path.isfile(pbsFilePath):
				os.remove(pbsFilePath)
			    if os.path.isfile(errorFilePath):
				os.remove(errorFilePath)
			    if os.path.isfile(outputFilePath):
				os.remove(outputFilePath)
			    mdrCommands = []
			    tableData=''
			    if len(sweepParameters) > 0:
				for sweepParameter in sweepParameters:
				    mdrCommands.append(MDR_CMD + ' -permutation_start_index=' + str(permuationStartIndex) + 
					      ' -' + sweepParameter.replace(',',' -') +
					      ' -table_data="' +
					      sweepParameter +
					      '" "' + dataFilePath  + '" >> ' + outputFilePath + '\n')
			    else:
				if len(tableData) == 0:
				    tableData = 'true'
				mdrCommands.append(MDR_CMD + ' -permutation_start_index=' + str(permuationStartIndex) + ' -table_data="' + tableData + '" "' + dataFilePath  + '" >> ' + outputFilePath + '\n')
			    jobsSubmitted = jobsSubmitted + 1
			    if useCluster:
				pbsFile = open(pbsFilePath, 'w')
				pbsFile.write('#PBS -N ' + str(permutationChunk).zfill(5) + '-' + runIdentifier + '\n')
				pbsFile.write('#PBS -l walltime=' + str(options.hours) + ':00:00\n')
				pbsFile.write('#PBS -o localhost:/dev/null\n')
				pbsFile.write('#PBS -e localhost:' + errorFilePath + '\n')
				pbsFile.write('#PBS -l nodes=1:ppn=1\n')
				#make sure people in my group can read my output files
				pbsFile.write('#PBS -W umask=022\n')
				#set priority so I can control order my jobs are pulled off routing queue.
				#Priority is only relevant to the calling user
				pbsFile.write('#PBS -p ' + str(options.priority) + '\n')
				if options.queue:
				    pbsFile.write('#PBS -q ' + options.queue + '\n')
				if options.email:
				    pbsFile.write('#PBS -M ' + options.email + '\n')
				#cd to dataDirectory solely to force directory to be mounted before
				#   mdr tries to read the input file. Workaround for automounter latency
				pbsFile.write('cd ' + dataDirectory + '\n')
				for mdrCommand in mdrCommands:
				    pbsFile.write(mdrCommand + '\n')
				pbsFile.close()
				qsub_status = os.system(options.qsubCmd + ' ' + pbsFilePath)
				print('job submission #' + str(jobsSubmitted) + ': ' + os.path.basename(pbsFilePath))
				if qsub_status != 0:
				    os.rename(pbsFilePath, pbsFilePath + 'bad_status-' + str(qsub_status))
				    raise RuntimeError('qsub reported a non-zero status: ' + str(qsub_status) + ' which means something is wrong. Renaming pbs file so re-running script will not think job already in queue. ')
				if options.qsubSleepSeconds > 0:
				    time.sleep(options.qsubSleepSeconds)
			    else:
				for mdrCommand in mdrCommands:
				    #run job in background
				    while len(runningJobs) >= cpu_count:
					for openJob in runningJobs:
					    if openJob.poll() != None:
						openJob.wait() #trying to prevent 'defunct' jobs from showing up in Top
						openJob.communicate() #trying to prevent 'defunct' jobs from showing up in Top
						runningJobs.remove(openJob)
						break
					if len(runningJobs) >= cpu_count:
					    print('Waiting before starting more permutations since ' + str(len(runningJobs)) + ' instances of MDR are already running.\n')
					    time.sleep(5)
				    runningJobs.append(subprocess.Popen(mdrCommand, shell=True))
				    print('started MDR instance #' + str(jobsSubmitted))

			    jobsInProcess += 1
			else:
			    """if job exists then it must be in one of these states:
			    1) queued up
			    2) finished successfully
			    3) finished with error
			    4) running
			    if finished or running the results may be
			       1) successfully parsed
			       or 2) not successfully parsed (note unsuccessful could be because job is not complete so results are incomplete)
			    """
			    if not os.path.isfile(outputFilePath):
				jobsQueuedUp += 1
			    else:
				if os.path.isfile(errorFilePath):
				    if os.path.getsize(errorFilePath) == 0:
					jobsCompletedWithoutErrors += 1
				    else:
					jobsCompletedWithErrors += 1
					print('WARNING: error file exists for ' + jobIdentifier + '. Contents of error file:\n')
					os.system('cat ' + errorFilePath)
				elif not useCluster:
				    jobsCompletedWithoutErrors += 1
				else:
				    jobsInProcess += 1
				
				if needToReadHeader:
				    readHeader(outputFilePath)
				    needToReadHeader = False
				numberOfRows = readOneFilePermutationResults(outputFilePath)
				permutationsLinesCollated += numberOfRows
				
				expectedResultsForThisJob = numExpectedResultsPerJob
				if permutationChunk == 1:
				    expectedResultsForThisJob += extraResultsExpectedForFirstChunk
				    extraResultsFoundForFirstChunk = max(0,numberOfRows - numExpectedResultsPerJob)
				    
			    if numberOfRows == expectedResultsForThisJob:
				jobsSuccessfullyCollated += 1
			    else:
				jobsWithCollationErrors += 1
				print('WARNING: parse error on ' + os.path.basename(outputFilePath) + ': # of result rows (' +
			                  str(numberOfRows) + ') was not the # expected (' + str(numExpectedResultsPerJob) +
			                  ').') # Grep results:\n' + grepout)
		    if len(allPermutationResults) != 0:
			allPermutationResults.sort(cmp=permutationResultCompare)
			
			numPermutationsParsed = len(allPermutationResults) - extraResultsFoundForFirstChunk
			outputSummaryText = str(permutationsLinesCollated) + \
			                  ' lines successfully parsed out of ' + str(numExpectedResultsTotal) + \
			                  ' expected for a total of ' + \
			                  str(numPermutationsParsed) + \
			                  ' out of ' + str(options.permutations) + ' requested permutations.'
			collationOutputFilePath = runIdentifier + '.txt'
			collationFile = open(collationOutputFilePath, 'w')
			if permutationsLinesCollated != numExpectedResultsTotal:
			    collationFile.write('\nWARNING: PARTIAL RESULTS! ' + outputSummaryText + '\n\n')
			    
			#write the header
			collationFile.write('\t'.join(permutationsHeaderLine) + '\n')
			rankCtr = 1
			unpermutedModelRank = -1
			unpermutedModelLines = dict()
			for permutationLine in allPermutationResults:
			    if permutationLine[rankColumnIndex] == unpermutedModelIdentifier:
				unpermutedModelRank = rankCtr
				collationFile.write("\t".join(permutationLine) + '\n')
				permutationLine[rankColumnIndex] = rankCtr
				parsimony = permutationLine[attributesColumnIndex].count(",")
				unpermutedModelLines[parsimony] = permutationLine
			    else:
				collationFile.write(str(rankCtr) + '\t' + '\t'.join(permutationLine[attributesColumnIndex:]) + '\n')
				rankCtr += 1
			collationFile.write('\n')
			
			if len(sweepParameters) > 0:
			    collationFile.write("SINCE SWEEP PARAMETERS ARE PRESENT, RANKS ARE WRONG AND P_VALUES  WILL NOT BE CALCULATED")
			elif len(unpermutedModelLines) > 0:
			    collationFile.write("For " + str(numPermutationsParsed) + " permutations, best models picked using " +\
			                        acrossLevelsFitnessCriteriaOrder + '\n\n')
			    collationFile.write('P-value\t' + '\t'.join(permutationsHeaderLine[attributesColumnIndex:]) + '\n')
			    for parsimony in unpermutedModelLines:
				unpermutedModelLine = unpermutedModelLines[parsimony]
				unpermutedModelRank = int(unpermutedModelLine[rankColumnIndex])
				pValue = unpermutedModelRank/float(numPermutationsParsed + 1)
				collationFile.write('%.4f' % (pValue) + '\t' + '\t'.join(unpermutedModelLine[attributesColumnIndex:]) + '\n')
			                        
			#at the end of the file put the base mdr results
			if permutationsLinesCollated != numExpectedResultsTotal:
			    collationFile.write('\nWARNING: PARTIAL RESULTS! ' + outputSummaryText + '\n')
			collationFile.close()
			print(outputSummaryText + '\nResults for permutations on ' + dataFileName + \
			      ' stored into results file:\n    ' + collationOutputFilePath)
		    else:
			print('Did not collate results for: ' + dataFileName + ' because no results are ready yet.')
		    print('# of jobs newly submitted: ' + str(jobsSubmitted) + '\n' +
			  '# of jobs queued waiting to run: ' + str(jobsQueuedUp) + '\n' +
			  '# of jobs currently running: ' + str(jobsInProcess) + '\n' +
			  '# of jobs completed with errors: ' + str(jobsCompletedWithErrors) + '\n' +
			  '# of jobs completed without errors: ' + str(jobsCompletedWithoutErrors) + '\n' +
			  '# of jobs with parsing errors: ' + str(jobsWithCollationErrors) + '\n' +
			  '# of job results successfully collated: ' + str(jobsSuccessfullyCollated) + '\n')
	    if not useCluster and jobsInProcess > 0:
		while len(runningJobs) > 0:
		    for openJob in runningJobs:
			if openJob.poll() != None:
			    runningJobs.remove(openJob)
		    time.sleep(5)
		    print('Waiting for ' + str(len(runningJobs)) + ' instances of MDR to finish.\n')
		collateOnly = True
		continue #repeat program once more to collate results
	    else:
		break

        return 0
    except Exception, err:
        if str(err) == '0':
            return 0
        else:
            sys.stderr.write('ERROR: %s\n' % str(err))
            traceback.print_exc(file=sys.stdout)
            #parser.print_usage()
            return 1

	
def readHeader(outputFilePath):
    global headerIdentifier
    global rankColumnIndex
    global attributesColumnIndex
    global permutationResultCompare

    headerIdentifier = "Rank"
    grepExpression = 'grep -P "^' + headerIdentifier + '\t" '  + outputFilePath
    #print("grepExpression: " + grepExpression)
    proc = subprocess.Popen(grepExpression,
     shell=True,
     stdin=subprocess.PIPE,
     stdout=subprocess.PIPE,
     stderr=subprocess.PIPE)
    grepout, stderr_value = proc.communicate()
 
    global permutationsHeaderLine
    permutationsHeaderLine = grepout.split('\n')[0].strip().split('\t')
    #print("permutationsHeaderLine: " + line)
    #need to aggregate results from all permutation jobs into one sorted output
    rankColumnIndex = permutationsHeaderLine.index(headerIdentifier)
    attributesColumnIndex = permutationsHeaderLine.index('Attributes')
    if options.CVC > 1:
	cvTestingColumnIndex = [permutationsHeaderLine.index(header) for header in permutationsHeaderLine if header.endswith("CV Testing")][0]
	modelTestingColumnIndex = [permutationsHeaderLine.index(header) for header in permutationsHeaderLine if header.endswith("Model Testing")][0]
	cvcColumnIndex = permutationsHeaderLine.index('CVC')
    overallColumnIndex = [permutationsHeaderLine.index(header) for header in permutationsHeaderLine if header.endswith("Overall")][0]
    def permutationResultCompare(row1, row2):
	if options.CVC > 1:
	    cvc1 = int(row1[cvcColumnIndex].split("/")[0])
	    cvc2 = int(row2[cvcColumnIndex].split("/")[0])
	    #higher cvc is better so row2 - row1
	    cvcComparisonResult = cvc2 - cvc1
    
	    cvTesting1 = float(row1[cvTestingColumnIndex])
	    cvTesting2 = float(row2[cvTestingColumnIndex])
	    #higher cvTesting is better so row2 - row1
	    cvTestingComparisonResult = cvTesting2 - cvTesting1
	    
	    modelTesting1 = float(row1[modelTestingColumnIndex])
	    modelTesting2 = float(row2[modelTestingColumnIndex])
	    #higher modelTesting is better so row2 - row1
	    modelTestingComparisonResult = modelTesting2 - modelTesting1
	else:
	    cvcComparisonResult = 0
	    cvTestingComparisonResult = float(0)
	    modelTestingComparisonResult = float(0)
	    
	overall1 = float(row1[overallColumnIndex])
	overall2 = float(row2[overallColumnIndex])
	#higher overall is better so row2 - row1
	overallComparisonResult = overall2 - overall1
	
	parsimony1 = row1[attributesColumnIndex].count(",")
	parsimony2 = row2[attributesColumnIndex].count(",")
	#lower parsimony is better so row1 - row2
	parsimonyComparisonResult = parsimony1 - parsimony2
	
	if (options.acrossLevelsFitnessCriteriaOrder == "CV_TESTING_CVC"):
	    primaryComparisonResult = cvTestingComparisonResult
	    secondaryComparisonResult = float(cvcComparisonResult)
	elif options.acrossLevelsFitnessCriteriaOrder == "CVC_CV_TESTING":
	    primaryComparisonResult = float(cvcComparisonResult)
	    secondaryComparisonResult = cvTestingComparisonResult
	elif options.acrossLevelsFitnessCriteriaOrder == "CVC_MODEL_TESTING":
	    primaryComparisonResult = float(cvcComparisonResult)
	    secondaryComparisonResult = modelTestingComparisonResult
	else:
	    raise RuntimeError('options.acrossLevelsFitnessCriteriaOrder: ' + options.acrossLevelsFitnessCriteriaOrder + ' not implemented')
	comparisonResult = primaryComparisonResult
	if comparisonResult == 0.0:
	    comparisonResult = secondaryComparisonResult
	if comparisonResult == 0.0:
	    comparisonResult = overallComparisonResult
	if comparisonResult == 0.0:
	    comparisonResult = parsimonyComparisonResult
	return -1 if comparisonResult < 0 else 1 if comparisonResult > 0 else 0
    
def readOneFilePermutationResults(outputFilePath):
    global unpermutedModelIdentifier
    unpermutedModelIdentifier = "=====>"
    grepExpression = 'grep -P "^(' + unpermutedModelIdentifier + '|[0-9]+)\t" '  + outputFilePath
    #print("grepExpression: " + grepExpression)
    proc = subprocess.Popen(grepExpression,
     shell=True,
     stdin=subprocess.PIPE,
     stdout=subprocess.PIPE,
     stderr=subprocess.PIPE)
    grepout, stderr_value = proc.communicate()
    numberOfRows = 0
    for line in grepout.split('\n'):
	#line = line.strip()#do not strip because line could have a blank final field
	if len(line.strip()) != 0:
	    numberOfRows += 1
	    oneLevelPermutationResults = line.split('\t')
	    if len(oneLevelPermutationResults) != len(permutationsHeaderLine):
		raise RuntimeError('ERROR: len(oneLevelPermutationResults) != len(permutationsHeaderLine) for file: ' + outputFilePath + '\nlen(oneLevelPermutationResults): ' + str(len(oneLevelPermutationResults)) + ' len(permutationsHeaderLine): ' + str(len(permutationsHeaderLine)) + '\nline: ' + line)
	    allPermutationResults.append(oneLevelPermutationResults)
    return numberOfRows

if __name__ == '__main__':
    sys.exit(main())

