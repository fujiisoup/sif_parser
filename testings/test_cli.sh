# script should be run from root folder
# test data is stored in public_testdata/cli
# converted data should be placed in public_testdata/cli/output

# basic usabe
sif_parser ./testings/public_testdata/cli/*.sif --output ./testings/public_testdata/cli/output

# --join flag
sif_parser ./testings/public_testdata/cli/*.sif --output ./testings/public_testdata/cli/output --join

# --verbose flag
sif_parser ./testings/public_testdata/cli/*.sif --output ./testings/public_testdata/cli/output --verbose

exit 0
