# get network 
cp ../res/CN_ig_0.015.ig .
python networkInvestigation.py > networkStat.tsv # get network statistics
rm CN_ig_0.015.ig
mv networkStat.tsv ../res