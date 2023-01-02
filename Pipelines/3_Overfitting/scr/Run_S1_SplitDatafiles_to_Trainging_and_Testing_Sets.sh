file_input=../data
file_out=../res/gwasSubsets
file_out_hpc=../res/hpc

# make output directory
mkdir -p $file_out
mkdir -p $file_out/training
mkdir -p $file_out/testing

# prepare datasets
for f in $file_input/GWAS_dataset/gwasSubsets/*.data
do
    echo "Processing $f file..."
    python split_dataset.py $f 0.2 25 $file_out/training/ $file_out/testing/
done

# prepare scr files
unzip ../data/bash_files.zip -d ../data
mkdir $file_out_hpc
cp $file_input/python/*.py $file_out_hpc/
cp $file_input/bash_files/kickoff_sbatch.sh $file_out_hpc/

# prepare datasets
cp $file_out/training/*.data $file_out_hpc/

# modify shell script

for f in ../data/bash_files/bipart/NLCRC*.sh
do
    file_name=$(basename $f)
    echo "Processing $file_name file..."
    python ChangeOneLine.py $f "#SBATCH -t 24:00:00" "#SBATCH -t 1:00:00" > $file_name.temp
    python ChangeOneLine.py $file_name.temp "#SBATCH --mem 12g" "#SBATCH --mem 4g" > $file_name
    mv $file_name $file_out_hpc/
    rm $file_name.temp
done

for f in ../data/bash_files/pairwise/NLCRC*.sh
do
    file_name=$(basename $f)
    echo "Processing $file_name file..."
    python ChangeOneLine.py $f "#SBATCH -t 24:00:00" "#SBATCH -t 1:00:00" > $file_name.temp
    python ChangeOneLine.py $file_name.temp "#SBATCH --mem 12g" "#SBATCH --mem 4g" > $file_name
    mv $file_name $file_out_hpc/
    rm $file_name.temp
done

zip -r hpc.zip ../res/hpc
mv hpc.zip ../res
rm -r ../data/bash_files
rm -r ../data/__MACOSX
rm -r ../res/hpc
