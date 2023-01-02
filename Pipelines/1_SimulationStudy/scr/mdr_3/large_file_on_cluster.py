import os
import time
import string
import sys
import getopt
import subprocess
import random
import operator
import traceback
import time
import re
import itertools

from optparse import OptionParser
#change standard out to be unbuffered so no need to flush.
sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 0)

def main():
    parser = OptionParser("""usage: %prog [options] dataset(s)
          %prog -h to see all options
          To use:
              1. Run this script with appropriate parameters. This initial run will submit jobs to the cluster.
              2. Wait for all jobs submitted by the script to complete, otherwise only partial results collated.
              3. Run the script again with the identical parameters
              If all worked well results will be in your current directory with a name similar to
              the dataset name you provided. There will also be a folder with a similar name containing
              the raw output from the cluster. As long as this exists, results will be collated
              from the raw outputs. If the folder or its contents are deleted, then if the
              script is run again, new jobs will be submitted and run.

          This script's purpose is to make it easy to run mdr on a very large dataset on a cluster.
          MDR java has the ability to run large datasets but it can take an excessive time.
          This script runs the mdr analysis in small chunks across many cluster jobs
          and then collates the results by the best models for each level
          Each job is given identical parameters except for which part of the data
          to work on so the result is the same as if a single large job had been run.

          The result is a file that shows all of the mdr analysis results in table form, as if from a single job.""")
    parser.disable_interspersed_args()
    #CAREFUL -- short versions of args such as '-m' for --mdr can cause problems if there are other options starting with the same letter. If a user passed
    #'-max=1' (by mistake, meaning --max=1) that would be interpreted as '-m ax=1' so mdr would be set to 'ax=1' and max would not be set
    parser.add_option('--min', dest='min', help='1 for 1-way, 2 for 2-way. etcetera [default: %default]', type='int', default=1)
    parser.add_option('--max', dest='max', help='1 for 1-way, 2 for 2-way. etcetera [default: %default]', type='int', default=2)
    parser.add_option('--cv', dest='cv', help='DO NOT SET: CVC MUST BE ONE. You can do cross-validation later on the top models[default: %default]', type='int', default=1)
    parser.add_option('--numTopModels', dest='numTopModels', help='MUST BE >= %default. How many models should be output? [default: %default]', type='int', default=500)
    parser.add_option('--numJobs', dest='numJobs', help='number of mdr processes to split work into [default: %default]', type='int', default=100)
    parser.add_option('--outputAllModels', dest='outputAllModels', help='NOT RECOMMENDED a file prefix where each job will store all of the models examined [default: %default]', type='string', default=None)
    parser.add_option('--randomSeed', dest='randomSeed',
                      help='random seed for the run. If not set will always be the default so results will be identical. [default: %default]', type='int', default=0)
    parser.add_option('--mdr', dest='mdr', help='file path to the mdr jar file [default: %default]', default='mdr.jar')
    parser.add_option('--email', dest='email', help='email address to notify if job has trouble [default: %default]', default='')
    parser.add_option('--hours', dest='hours', help='maximum time in hours of walltime a job can use [default: %default]', type='int', default=12)
    parser.add_option('--resubmitUnfinished', dest='resubmitUnfinished', help='if the error file has not been created or exists with non-zero size, then resubmit the job [default: %default]', type='choice', choices=['true','false'], default='false')
    parser.add_option('--queue', dest='queue', help='queue to submit jobs to [default: %default]', default='')
    parser.add_option('--qsubCmd', dest='qsubCmd', help='command needed to submit a job to cluster [default: %default]', default='qsub')
    parser.add_option('--qsubSleepSeconds', dest='qsubSleepSeconds', help='time to wait after submitting a job. Fractional numbers such as 0.1 for tenth of a second is fine [default: %default]', type='float', default=0)
    parser.add_option('--mem', dest='mem',
                      help='megabytes allocated on the cluster node. Should be less than or equal to totalMem/#processors per node) [default: %default]',
                      type='int', default=3800)
    try:
	global options
        (options, args) = parser.parse_args()
        options.mdr = os.path.abspath(options.mdr)
        scriptName = '.'.join(os.path.basename(sys.argv[0]).split('.')[:-1])

        print("Options: " + '\n'.join(str(options).split(',')))
        print('dataset(s): ' + str(args))
        #convert parameter to a boolean
        options.resubmitUnfinished = options.resubmitUnfinished == 'true'
        if options.numTopModels < 500:
            raise RuntimeError('You must have at least 500 top models')
        if len(args) == 0:
            raise RuntimeError('You must pass in mdr datasets after the options.')
        projectDirectory = os.path.split(os.path.abspath(sys.argv[0]))[0] + '/'      #project directory is the file this script is in
        if not os.path.isfile(os.path.abspath(options.mdr)):
            raise RuntimeError('MDR jar file not found at \'' + os.path.abspath(options.mdr) + '\'')
        numLevels = options.max - options.min + 1
        numExpectedResultsPerJob = numLevels * options.numTopModels
        mdrCommand = 'java -XX:+UseSerialGC -Xms' + str(options.mem) + 'm -Xmx' + str(options.mem) + 'm' + \
                   ' -jar ' + options.mdr + \
                   ' -nolandscape' + \
                   ' -min=' + str(options.min) + \
                   ' -max=' + str(options.max) + \
                   ' -cv=' + str(options.cv) + \
                   ' -seed=' + str(options.randomSeed) + \
                   ' -minimal_output=false' + \
                   ' -table_data=true' + \
                   ' -top_models_landscape_size=' + str(options.numTopModels)
        
        for inputFile in args:
	    jobsSubmitted = 0
	    jobsQueuedUp = 0
	    jobsInProcess = 0
	    jobsCompletedWithoutErrors = 0
	    jobsCompletedWithErrors = 0
	    jobsSuccessfullyCollated = 0
	    jobsWithCollationErrors = 0
	    searchResultLinesCollated = 0
	    needToReadHeader = True
	    global cvPartitionsResults
	    cvPartitionsResults = dict()   #list of results for each partition
	    global topModels
	    topModels = dict()
	    for index in range(1, options.cv+1):
		cvPartitionsResults[str(index)] = list()
	    for index in range(options.min, options.max+1):
		topModels[str(index)] = list()
            dataFilePath = os.path.abspath(inputFile)
            dataDirectory, dataFileName =  os.path.split(dataFilePath)
            if not os.path.isfile(dataFilePath):
                raise RuntimeError('Expected file '' + dataFileName + '' not found in directory '' + dataDirectory + ''.')
            else:
                #new outputfile

                #read in first line of file here to make sure that numJobs is not too high for the # of attribute combinations
                #the number of combinations is 'numAttibutes choose level' so if minLevel is 1, then if numJobs is greater than the # of attributes
                #mdr will throw a null pointer exception since the (numAttribute+1) run will not have any combinations and therefore no bestModel.
                #fix would be to read first line of file and determine # of attributes and force numJobs to be no more than that number.
                f = open(dataFilePath, 'r')
                firstLine = f.readline()
                f.close()
                numAttributes = len(firstLine.split()) - 1 #subtract one for class/status column at end
                maximumNumberOfJobsNeeded = pow(numAttributes, options.min)
                effectiveNumJobs = min(maximumNumberOfJobsNeeded, options.numJobs)
                if effectiveNumJobs < options.numJobs:
                    print('WARNING: node count reduced from: ' + str(options.numJobs) + ' to: '
                          + str(effectiveNumJobs) + ' because it was greater than the number of pow(#attributes, minLevel) in dataset: ' + dataFileName)
                totalNumExpectedResults = numExpectedResultsPerJob * effectiveNumJobs
                dataFileIdentifier = '.'.join(dataFileName.split('.')[:-1]).replace(' ', '_')
                runIdentifier = dataFileIdentifier + \
                '_min-' + str(options.min) + \
                '_max-' + str(options.max) + \
                '_CVC-' + str(options.cv) + \
                '_seed-' + str(options.randomSeed) + \
                '_numJobs-' + str(effectiveNumJobs) + \
                '_topModels-' + str(options.numTopModels)
                workDirectory = os.path.abspath(runIdentifier) + '/'
                if not os.path.isdir(workDirectory):
                    os.makedirs(workDirectory)
                #force disk system to read work directory to make sure it is mounted (Dartmouth discovery cluster kluge)
                os.system('ls ' + workDirectory + '> /dev/null')
                for nodeNumber in range(1,effectiveNumJobs+1):
                    jobIdentifier = 'MdrDistributedResultsPart-' + str(nodeNumber).zfill(5)
                    outputFilePath = workDirectory + jobIdentifier + '.out'
                    errorFilePath = workDirectory + jobIdentifier + '.err'
                    pbsFilePath = workDirectory + jobIdentifier + '.pbs'
                    #if job does not exist create it and submit it
                    submitJob = not os.path.isfile(pbsFilePath)
                    if not submitJob and options.resubmitUnfinished:
                        submitJob = (not os.path.isfile(errorFilePath)) or (os.path.getsize(errorFilePath) > 0)
                        if submitJob:
                            if os.path.isfile(errorFilePath):
                                os.remove(errorFilePath)
                            if os.path.isfile(outputFilePath):
                                os.remove(outputFilePath)
                            print('About to resubmit job: ' + jobIdentifier)

                    if submitJob:
                        pbsFile = open(pbsFilePath, 'w')
                        pbsFile.write('#PBS -N ' + str(nodeNumber).zfill(5) + '-' + runIdentifier + '\n')
                        pbsFile.write('#PBS -l walltime=' + str(options.hours) + ':01:00\n')
                        pbsFile.write('#PBS -o localhost:/dev/null\n')
                        pbsFile.write('#PBS -e localhost:' + errorFilePath + '\n')
                        pbsFile.write('#PBS -l nodes=1:ppn=1\n')
                        pbsFile.write('#PBS -l mem=' + str(options.min) + 'm\n')
                         #pbsFile.write('#PBS -l nodes=1:ppn=8\n')
                        #pbsFile.write('#PBS -l feature="cell1|cell2|cell3|cell4"\n')
                        #make sure people in my group can read my output files
                        pbsFile.write('#PBS -W umask=022\n')
                        #set priority so I can control order my jobs are pulled off routing queue.
                        #Priority is only relevant to the calling user
                        #pbsFile.write('#PBS -p 700\n')
                        if options.queue:
                            pbsFile.write('#PBS -q ' + options.queue + '\n')
                        if options.email:
                            pbsFile.write('#PBS -M ' + options.email + '\n')
                        
                        
                        if options.outputAllModels is None:
                            outputAllModelsParameter = ""
                        else:
                            outputAllModelsParameter = " -all_models_outfile=" + options.outputAllModels + '_' + str(nodeNumber).zfill(5) + '.txt'
                        #cd to dataDirectory solely to force directory to be mounted before
                        #   mdr tries to read the input file. Workaround for automounter latency
                        pbsFile.write('cd ' + dataDirectory + '\n')
                        pbsFile.write(mdrCommand +
                                      ' -distributed_node_count=' + str(effectiveNumJobs) +
                                      ' -distributed_node_number=' + str(nodeNumber).zfill(5) +
                                      outputAllModelsParameter +
                                      ' "' + dataFilePath + '" > ' + outputFilePath)
                        pbsFile.close()
                        jobsSubmitted = jobsSubmitted + 1
                        print('job submission #' + str(jobsSubmitted) + ': ' + os.path.basename(pbsFilePath))
                        qsub_status = os.system(options.qsubCmd + ' ' + pbsFilePath)
                        if qsub_status != 0:
                            #try submitting again -- it could just be a glitch (sysadmin says cluster does this occassionally when busy)
                            qsub_status = os.system(options.qsubCmd + ' ' + pbsFilePath)
                            if qsub_status != 0:
                                os.rename(pbsFilePath, pbsFilePath + 'bad_status-' + str(qsub_status))
                                raise RuntimeError('qsub reported a non-zero status: ' + str(qsub_status) + ' which means something is wrong. Renaming pbs file so re-running script will not think job already in queue. ')
                        if options.qsubSleepSeconds > 0:
                            time.sleep(options.qsubSleepSeconds)
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
                                #in some situations a .e file might not be the best way to tell if job is done.
                                #how about trying to open file for write?
                                isOutputFileWriteable = os.access(outputFilePath, os.W_OK)
                                if isOutputFileWriteable:
                                    jobsCompletedWithoutErrors += 1
                                else:
                                    jobsInProcess += 1
			    
			    if needToReadHeader:
				readHeader(outputFilePath)
				needToReadHeader = False
			    numberOfRows = readOneFileDistributedSearchResults(outputFilePath)
			    searchResultLinesCollated += numberOfRows
				
			    if numberOfRows == numExpectedResultsPerJob:
				jobsSuccessfullyCollated += 1
			    else:
				jobsWithCollationErrors += 1
				print('WARNING: parse error on ' + os.path.basename(outputFilePath) + ': # of result rows (' +
				          str(numberOfRows) + ') was not the # expected (' + str(numExpectedResultsPerJob) +
				          ').') # Grep results:\n' + grepout)
            #END OF LOOP OVER ALL NODES

            if jobsCompletedWithoutErrors == effectiveNumJobs:
                bestSingleAttributes = set()
                bestAttributeCombinations = set()
                for currentAttributeLevel in range(options.min, options.max+1):
		    topModelList = topModels[str(currentAttributeLevel)]
                    def addModelToBestAttributes(modelName):
                        bestAttributeCombinations.add(modelName)
                        for attribute in modelName.split(","):
                            bestSingleAttributes.add(attribute)
                            
                    for topModel in topModelList:
                        addModelToBestAttributes(topModel[attributesColumnIndex])
                        
                    #at this point we have a set containing the top models from each of the partitions for all the levels
                    #create a file listing so that it can be used to make a smaller subset for MDR to run on
        
                    topAttributesOutputFilePath = runIdentifier + '_level-' + str(currentAttributeLevel) + '_top_models.txt'
                    topAttributesOutputFile = open(topAttributesOutputFilePath, 'w')
                    for attribute in sorted(bestAttributeCombinations):
                        topAttributesOutputFile.write(attribute)
                        topAttributesOutputFile.write('\n')
                    topAttributesOutputFile.close()
                    
                topAttributesDatasetFile = runIdentifier + '_numAttributes-' + str(len(bestSingleAttributes)) + '_analysis.txt'
                mdrSaveForcedAnalysisCommand = 'java -XX:+UseSerialGC -Xms' + str(options.mem) + 'm -Xmx' + str(options.mem) + 'm' + \
                                      ' -jar ' + options.mdr + ' -nolandscape -table_data=true -cv=' + str(options.cv) + ' -minimal_output=true -filter_file="' + topAttributesOutputFilePath + '"' + \
                                      ' -forced_search="' + str(' '.join(bestAttributeCombinations)) + '"' + \
                                      ' -saveanalysis="' + topAttributesDatasetFile + '"' + \
                                      ' ' + dataFilePath
                print("mdrSaveForcedAnalysisCommand: " + mdrSaveForcedAnalysisCommand)
                mdrSaveForcedAnalysisCommand_status = os.system(mdrSaveForcedAnalysisCommand)
                if mdrSaveForcedAnalysisCommand_status != 0:
                    raise RuntimeError('mdrSaveForcedAnalysisCommand_status reported a non-zero status: ' \
                    + str(mdrSaveForcedAnalysisCommand_status) + ' which means something is wrong. ')
                print("\nThere are " + str(len(bestSingleAttributes)) + " attributes that occur in the top " + str(options.numTopModels) + " models. Created a saved analysis file that you can use in MDR gui mode:\n\n" + topAttributesDatasetFile)
                #END LOOP OVER LEVELS
            print('\n# of jobs newly submitted: ' + str(jobsSubmitted) + '\n' +
            '# of jobs queued waiting to run: ' + str(jobsQueuedUp) + '\n' +
            '# of jobs currently running: ' + str(jobsInProcess) + '\n' +
            '# of jobs completed with errors: ' + str(jobsCompletedWithErrors) + '\n' +
            '# of jobs completed without errors: ' + str(jobsCompletedWithoutErrors) + '\n')
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
    global numAttributesColumnIndex
    global attributesColumnIndex
    global topModelCompare
    global distributedResultHeaderLine

#table we are extracting data from looks like this:
#distributed_node_number/distributed_node_count	# Attributes	Attributes	Overall
#4/5	1	X15	0.53
#4/5	1	X16	0.5225
#4/5	1	X14	0.515
#4/5	1	X13	0.505
#4/5	2	X8,X16	0.57
#4/5	2	X11,X16	0.5675
#4/5	2	X11,X15	0.565
#4/5	2	X9,X20	0.5625
#4/5	2	X11,X18	0.5575

    headerIdentifier = 'distributed_node_number/distributed_node_count'
    grepExpression = 'grep -P "^' + headerIdentifier + '\t" '  + outputFilePath
    #print("grepExpression: " + grepExpression)
    proc = subprocess.Popen(grepExpression,
     shell=True,
     stdin=subprocess.PIPE,
     stdout=subprocess.PIPE,
     stderr=subprocess.PIPE)
    grepout, stderr_value = proc.communicate()
 
    distributedResultHeaderLine = grepout.split('\n')[0].strip().split('\t')
    #print("distributedResultHeaderLine", distributedResultHeaderLine)
    numAttributesColumnIndex = distributedResultHeaderLine.index('# Attributes')
    attributesColumnIndex = distributedResultHeaderLine.index('Attributes')
    overallColumnIndex = [distributedResultHeaderLine.index(header) for header in distributedResultHeaderLine if header.endswith("Overall")][0]
    def topModelCompare(row1, row2):
	overall1 = float(row1[overallColumnIndex])
	overall2 = float(row2[overallColumnIndex])
	#higher overall is better so row2 - row1
	overallComparisonResult = overall2 - overall1
	
	parsimony1 = row1[attributesColumnIndex].count(",")
	parsimony2 = row2[attributesColumnIndex].count(",")
	#lower parsimony is better so row1 - row2
	parsimonyComparisonResult = parsimony1 - parsimony2

	comparisonResult = overallComparisonResult
	if comparisonResult == 0.0:
	    comparisonResult = parsimonyComparisonResult
	return -1 if comparisonResult < 0 else 1 if comparisonResult > 0 else 0

def readOneFileDistributedSearchResults(outputFilePath):
#table we are extracting data from looks like this:
#distributed_node_number/distributed_node_count	# Attributes	Attributes	Overall
#4/5	1	X15	0.53
#4/5	1	X16	0.5225
#4/5	1	X14	0.515
#4/5	1	X13	0.505
#4/5	2	X8,X16	0.57
#4/5	2	X11,X16	0.5675
#4/5	2	X11,X15	0.565
#4/5	2	X9,X20	0.5625
#4/5	2	X11,X18	0.5575
    grepExpression = 'grep -P "^[0-9]+[/][0-9]+\t" '  + outputFilePath
    #print("grepExpression: " + grepExpression)
    proc = subprocess.Popen(grepExpression,
     shell=True,
     stdin=subprocess.PIPE,
     stdout=subprocess.PIPE,
     stderr=subprocess.PIPE)
    grepout, stderr_value = proc.communicate()
    numberOfRows = 0
    for line in grepout.split('\n'):
	#print("line", line)
	#line = line.strip()#do not strip because line could have a blank final field
	if len(line.strip()) != 0:
	    numberOfRows += 1
	    oneLevelDistributedResult = line.split('\t')
	    if len(oneLevelDistributedResult) != len(distributedResultHeaderLine):
		raise RuntimeError('ERROR: len(oneLevelDistributedResult) != len(distributedResultHeaderLine) for file: ' + outputFilePath + '\nlen(oneLevelDistributedResult): ' + str(len(oneLevelDistributedResult)) + ' len(distributedResultHeaderLine): ' + str(len(distributedResultHeaderLine)) + '\nline: ' + line)
	    topModelList = topModels[oneLevelDistributedResult[numAttributesColumnIndex]]
	    topModelList.append(oneLevelDistributedResult)
	    topModelList.sort(cmp=topModelCompare)
	    #now remove all but the topModels overall
	    del topModelList[options.numTopModels:]
    return numberOfRows
	

	
if __name__ == '__main__':
    sys.exit(main())

