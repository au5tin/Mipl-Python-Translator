
# Where to find sample input files
INPUT="./input"

# Where to place the compiled files
COMPILED="./compiled"

# Where to place the actual output of running the program
OUTPUT="./output"

# Where to find the expected output
EXPECTED="./expected"
# EXPECTED="./expectedOutput_unabridged"

# Where to place generated diffs
REPORTS="./reports"


green=`tput setaf 2`
red=`tput setaf 1`
reset=`tput sgr0`

#inputs=`find $INPUT -iname "*$1*"`
fails=0
passes=0

for i in $INPUT/*; do
    filename=$(basename $i) # strip path
    testname="${filename%.*}" # strip extension

    # actually run file
    python3 hw8.py "$INPUT/$filename" "$COMPILED/$filename.py"
    python3 "$COMPILED/$filename.py" < "read/$filename" > "$OUTPUT/$filename.out"

    diff -b "$OUTPUT/$filename.out" "$EXPECTED/$filename.out" > "$REPORTS/$filename"

    # count number of lines in diff
    lines=`wc -l < $REPORTS/$filename`

    if [ "$lines" -gt "0" ]; then
        fails=$[ $fails + 1 ]
        echo "check: ${red}[fail]${reset} $testname ($lines lines)"
#        head "$REPORTS/$filename"
    else
        passes=$[ $passes + 1 ]
        echo "check: ${green}[pass]${reset} $testname"
    fi

done

echo "check: ${green}$passes tests passed${reset}"
echo "check: ${red}$fails tests failed${reset}"
