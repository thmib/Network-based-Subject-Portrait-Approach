import os
import time
import string
import sys
import getopt
import subprocess
import operator
import traceback
import re
import math
from optparse import OptionParser
import ConfigParser

def arrayToString(someArray, joinDelimiter='_'):
    return joinDelimiter.join([str(x) for x in someArray])

def parseBool(theString):
    return theString[0].upper() == 'T'

#from http://stackoverflow.com/questions/752308/split-array-into-smaller-arrays/752562#752562
def split_list(alist, wanted_parts=1):
    length = len(alist)
    return [ alist[i*length // wanted_parts: (i+1)*length // wanted_parts] 
             for i in range(wanted_parts) ]


def main():
    parser = OptionParser("""usage: %prog [options] dataset(s)
          %prog -h to see all options
          To use:
              1. Run this script with appropriate parameters. This initial run will submit jobs to the cluster.
              2. Wait for all jobs submitted by the script to complete, otherwise only partial results collated.
              3. Run the script again with the identical parameters.
              If all worked well results will be in a newly created file. See new files by 'ls -ct | head -1'. There will also be a folder with a similar name containing
              the raw output from the cluster. As long as this exists, results will be collated
              from the raw outputs. If the folder or its contents are deleted, then if the
              script is run again, new jobs will be submitted and run.

          This script's purpose is to make it easy to run mdr on subfolder(s) of text file on a cluster
          If you do not have access to a cluster, a way to get this to simply run the jobs is to pass --qsubCmd=sh
          It will run all files ending in .txt as MDR input files.
          This script runs many cluster jobs and then collates the results.""")
    parser.disable_interspersed_args()
    #CAREFUL -- short versions of args such as '-m' for --mdr can cause problems if there are other options starting with the same letter. If a user passed
    #'-max=1' (by mistake, meaning --max=1) that would be interpreted as '-m ax=1' so mdr would be set to 'ax=1' and max would not be set
    parser.add_option('--min', dest='min', help='1 for 1-way, 2 for 2-way. etcetera [default: %default]', type='int', default=1)
    parser.add_option('--max', dest='max', help='1 for 1-way, 2 for 2-way. etcetera [default: %default]', type='int', default=4)
    parser.add_option('--CVC', dest='CVC', help='how many subsets of the dataset to create and test separately [default: %default]', type='int', default=10)
    parser.add_option('--randomSeed', dest='randomSeed',
                      help='random seed for the runs. All runs will use the same seed. [default: %default]', type='int', default=0)
    parser.add_option('--topModelLandscapeSize', dest='topModelLandscapeSize', help='topModel landscape sizes [default: %default]', type='int', default=1000)
    parser.add_option('--showPickByLevel', dest='showPickByLevel', help='show what levels results would be picked by either testing accuracy or CVC or by  [default: %default]', type='choice', choices=['true','false'], default='false')
    parser.add_option('--mdr', dest='mdr', help='file path to the mdr jar file [default: %default]', default='mdr.jar')
    parser.add_option('--maximumFilesPerJob', dest='maximumFilesPerJob', help='how many calls to files will be processed in each job [default: %default]', type='int', default=20)
    parser.add_option('--email', dest='email', help='email address to notify if job has trouble [default: %default]', default='')
    parser.add_option('--time', dest='time', help='maximum walltime a job can use. Specify the time in the format HH:MM:SS. Hours can be more than 24. [default: %default]', default='24:00:00')
    parser.add_option('--doNotSubmit', dest='doNotSubmit', help='Only collate results.  [default: %default]', type='choice', choices=['true','false'], default='false')
    parser.add_option('--resubmitJobsWithErrors', dest='resubmitJobsWithErrors', help='if the error file contains errors size resubmit the job [default: %default]', type='choice', choices=['true','false'], default='false')
    parser.add_option('--resubmitJobsWithoutOutput', dest='resubmitJobsWithoutOutput', help='if the error file does not exist resubmit the job [default: %default]', type='choice', choices=['true','false'], default='false')
    parser.add_option('--queue', dest='queue', help='queue to submit jobs to [default: %default]', default='largeq')
    parser.add_option('--qsubCmd', dest='qsubCmd', help='command needed to submit a job to cluster [default: %default]', default='qsub')
    parser.add_option('--qsubSleepSeconds', dest='qsubSleepSeconds', help='time to wait after submitting a job. Fractional numbers such as 0.1 for tenth of a second is fine [default: %default]', type='float', default=0)
    parser.add_option('--mem', dest='mem',
                      help='megabytes allocated on the cluster node. Should be less than or equal to totalMem/#processors per node) [default: %default]',
                      type='int', default=3800)

    sweepParameters = [
    ] 
    
   
    fileNameTableDataRegEx = re.compile('^heritability-([^_]+)_maf-([^_]+)_EDM_(.[^0-9]+)([0-9]+).txt$')
    try:
        (options, args) = parser.parse_args()
        options.mdr = os.path.abspath(options.mdr)

        print("Options: " + '\n'.join(str(options).split(',')))
        if not args:
            raise RuntimeError('You must pass in at least one directory to look for datasets ending in \'.txt.\': ' + str(args))

        if not os.path.isfile(os.path.abspath(options.mdr)):
            raise RuntimeError('MDR jar file not found at '' + os.path.abspath(options.mdr) + ''')
        numLevels = options.max - options.min + 1
        numExpectedResults = numLevels * max(1,len(sweepParameters))


        mdrCommand = 'java -XX:+UseSerialGC' + \
                   ' -Xms' + str(options.mem) + 'm' + \
                   ' -Xmx' + str(options.mem) + 'm' + \
                   ' -jar ' + options.mdr + \
                   ' -min=' + str(options.min) + \
                   ' -max=' + str(options.max) + \
                   ' -cv=' + str(options.CVC) + \
                   ' -seed=' + str(options.randomSeed) + \
                   ' -top_models_landscape_size=' + str(options.topModelLandscapeSize) + \
                   ' -minimal_output=true' + \
                   ' -nolandscape'

 	for dirName in args:
	    jobsSubmitted = 0
	    jobsQueuedUp = 0
	    jobsInProcess = 0
	    jobsCompletedWithoutErrors = 0
	    jobsCompletedWithErrors = 0
	    jobsSuccessfullyCollated = 0
	    jobsWithCollationErrors = 0
	    dirGroupCtr = 0
	    if not os.path.isdir(dirName):
		raise RuntimeError('Passed in value is not a directory \'' + dirName + '\'')
	    runIdentifier =  (dirName.replace('/','_') + '_' + \
		          arrayToString(sweepParameters).replace('=','-').replace(',','_'))[-75:] + \
		            '_min-' + str(options.min) + \
		            '_max-' + str(options.max) + \
		            '_topModelSize-' + str(options.topModelLandscapeSize) + \
		            '_CVC-' + str(options.CVC) + \
		            '_seed-' + str(options.randomSeed)
	    mainOutputFilePath = runIdentifier + '.txt'
	    wroteHeader = False
	    workDirectory = os.path.abspath(runIdentifier) + '/'
	    if not os.path.isdir(workDirectory):
		os.makedirs(workDirectory)
	    #force disk system to read work directory to make sure it is mounted (Dartmouth discovery cluster kluge)
	    os.system('ls ' + workDirectory + '> /dev/null')
            if not os.path.isdir(dirName):
                raise RuntimeError('This is not a directory: ' + dirName)
            dirPath = os.path.abspath(dirName)
            dirFiles = os.listdir(dirPath)
            dirFiles.sort()
            numberOfJobs = int(math.ceil(len(dirFiles) / float(options.maximumFilesPerJob)))
            #print("len(dirFiles)",str(len(dirFiles)),"numberOfJobs",str(numberOfJobs),'\n')
	    dirFileGroups = split_list(dirFiles, numberOfJobs)
	    for dirFileGroup in dirFileGroups:
                dirGroupCtr += 1
                #print("dirFileGroup is size",str(len(dirFileGroup)),"with contents",dirFileGroup,'\n')
                #continue
                jobIdentifier = os.path.basename(dirPath) + '_group-' + str(dirGroupCtr)
                outputFilePath = workDirectory + jobIdentifier + '.out'
                errorFilePath = workDirectory + jobIdentifier + '.err'
                pbsFilePath = workDirectory + jobIdentifier + '.pbs'
                #if job does not exist create it and submit it
                submitJob = not os.path.isfile(pbsFilePath)
                resubmitJob = False
                if not submitJob and parseBool(options.resubmitJobsWithoutOutput) and not os.path.isfile(outputFilePath):
                    resubmitJob = True
                elif parseBool(options.resubmitJobsWithErrors) and os.path.isfile(errorFilePath) and (os.path.getsize(errorFilePath) > 0):
                    resubmitJob = True
                if resubmitJob:
                    print('About to resubmit job: ' + jobIdentifier)

                if submitJob or resubmitJob:
                    if os.path.isfile(errorFilePath):
                        os.remove(errorFilePath)
                    if os.path.isfile(outputFilePath):
                        os.remove(outputFilePath)
                    pbsFile = open(pbsFilePath, 'w')
                    pbsFile.write('#PBS -N ' + jobIdentifier + '\n')
                    pbsFile.write('#PBS -l walltime=' + options.time + '\n')
		    pbsFile.write('#PBS -o localhost:/dev/null\n')
		    pbsFile.write('#PBS -e localhost:' + errorFilePath + '\n')
                    pbsFile.write('#PBS -l nodes=1:ppn=1\n')
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
                    #cd to dirPath solely to force directory to be mounted before
                    #   mdr tries to read the input file. Workaround for automounter latency
                    pbsFile.write('cd ' + dirPath + '\n')
		    callingMDR = False
                    for filename in dirFileGroup:
                        dataFilePath = os.path.abspath(dirPath + '/' + filename)
                        if not os.path.isfile(dataFilePath) or not dataFilePath.endswith('.txt'):
			    #make recursive
			    if os.path.isdir(dataFilePath):
				print("Adding subdirectory to list of subfolders: " + dataFilePath)
				args.append(dataFilePath)
                            continue
                        regExMatch = fileNameTableDataRegEx.match(filename)
                        tableData=''
                        if regExMatch and len(regExMatch.groups()) == 4:
                            tableData += 'heritability=' + str(regExMatch.group(1)) + ',maf=' + str(regExMatch.group(2)) + ',EDM=' + str(regExMatch.group(3)) + ',replicate=' + str(regExMatch.group(4))
			if len(sweepParameters) > 0:
                            for sweepParameter in sweepParameters:
				callingMDR = True
                                pbsFile.write(mdrCommand +
                                          ' -' + sweepParameter.replace(',',' -') +
                                          ' -table_data="' +
                                          sweepParameter + ',' + tableData +
                                          '" "' + dataFilePath  + '" >> ' + outputFilePath + '\n')
                        else:
			    if len(tableData) == 0:
				tableData = 'true'
			    callingMDR = True
                            pbsFile.write(mdrCommand + ' -table_data="' + tableData + '" "' + dataFilePath  + '" >> ' + outputFilePath + '\n')
                    pbsFile.close()
		    if not callingMDR:
			os.remove(pbsFilePath)
		    else:
			jobsSubmitted = jobsSubmitted + 1
			if parseBool(options.doNotSubmit):
			    continue
			print('job submission #' + str(jobsSubmitted) + ': ' + os.path.basename(pbsFilePath))
			qsub_status = os.system(options.qsubCmd + ' ' + pbsFilePath)
			if qsub_status != 0:
			    os.rename(pbsFilePath, pbsFilePath + 'bad_status-' + str(qsub_status))
			    raise RuntimeError('qsub reported a non-zero status: ' + str(qsub_status) + ' which means something is wrong. Renaming pbs file so re-running script will not think job already in queue. ')
			if options.qsubSleepSeconds > 0:
			    time.sleep(options.qsubSleepSeconds)
                else:
                    for filename in dirFileGroup:
                        dataFilePath = os.path.abspath(dirPath + '/' + filename)
			if not os.path.isfile(dataFilePath) or not dataFilePath.endswith('.txt') or os.path.isfile(pbsFilePath):
			    #make recursive
			    if os.path.isdir(dataFilePath):
				print("Adding subdirectory to list of subfolders: " + dataFilePath)
				args.append(dataFilePath)
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
			print('This job has no output file: ' + outputFilePath + ' so may be queued up')
                    else:
                        if os.path.isfile(errorFilePath):
                            if os.path.getsize(errorFilePath) == 0:
                                jobsCompletedWithoutErrors += 1
                            else:
                                jobsCompletedWithErrors += 1
                                print('WARNING: error file exists for ' + jobIdentifier + '. Contents of error file:\n')
                                os.system('cat ' + errorFilePath)
                        else:
                            jobsInProcess += 1
                        outputHeaderLineSignature = 'Datafile\t'
                        proc = subprocess.Popen('grep -E "^(' + dirPath + '|' + outputHeaderLineSignature + ')" ' + outputFilePath,
                         shell=True,
                         stdin=subprocess.PIPE,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)
                        grepout, stderr_value = proc.communicate()
                        numberOfRows = 0
                        for line in grepout.split('\n'):
                            line = line.strip()
                            if len(line) != 0:
                                if line.startswith(outputHeaderLineSignature):
                                    if not wroteHeader:
                                        wroteHeader = True
                                        mainOutputFile = open(mainOutputFilePath, 'w')
                                        mainOutputFile.write(line + '\n')
                                        headerLine = line.split('\t')
                                        numAttributesColumnIndex = operator.indexOf(headerLine, '# Attributes')
                                else:
                                    numberOfRows += 1
                                    mainOutputFile.write(line + '\n')
                                            
                                            
                        numExpectedResultsForFileGroup = numExpectedResults * len(dirFileGroup)                    
                        if numberOfRows == numExpectedResultsForFileGroup:
                            jobsSuccessfullyCollated += 1
                        else:
                            jobsWithCollationErrors += 1
                            parseErrorMessage = 'WARNING: parse error on ' + os.path.basename(outputFilePath) + ': # of result rows (' +\
                                              str(numberOfRows) + ') was not the # expected (' + str(numExpectedResultsForFileGroup) + ').\n'
                            print(parseErrorMessage)
	    print('# of jobs newly submitted: ' + str(jobsSubmitted) + '\n' +
	          '# of jobs queued waiting to run: ' + str(jobsQueuedUp) + '\n' +
	          '# of jobs currently running: ' + str(jobsInProcess) + '\n' +
	          '# of jobs completed with errors: ' + str(jobsCompletedWithErrors) + '\n' +
	          '# of jobs completed without errors: ' + str(jobsCompletedWithoutErrors) + '\n' +
	          '# of jobs with parsing errors: ' + str(jobsWithCollationErrors) + '\n' +
	          '# of job results successfully collated: ' + str(jobsSuccessfullyCollated))
	    if wroteHeader:
		mainOutputFile.close()
		print('Collated results are in: ' + mainOutputFilePath)
        return 0
    except Exception, err:
        if str(err) == '0':
            return 0
        else:
            sys.stderr.write('ERROR: %s\n' % str(err))
            traceback.print_exc(file=sys.stdout)
            #parser.print_usage()
            return 1

if __name__ == '__main__':
    sys.exit(main())

