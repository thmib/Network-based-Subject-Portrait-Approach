# This py will add one line to a bash file.

import sys
add=''
insert_s='' # string to add
replace_s='' # string to be replaced
def main():
    with open(add, 'r') as myfile:
        scr = myfile.read()
    print(scr.replace(replace_s,insert_s))
    

if __name__ == "__main__":
    add = sys.argv[1]
    replace_s = sys.argv[2]
    insert_s= sys.argv[3]
    main()
