# test data is stored in public_testdata/cli
# converted data should be placed in public_testdata/cli/output

# basic usabe
sif_parser public_testdata/cli/*.sif --output public_testdata/cli/output

# --join flag
sif_parser public_testdata/cli/*.sif --output public_testdata/cli/output --join

# --verbose flag
sif_parser public_testdata/cli/*.sif --output public_testdata/cli/output --verbose
