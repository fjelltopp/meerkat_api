if [ "$TRAVIS_BUILD" = "docs" ]
then
    pip install .
elif [ "$TRAVIS_BUILD" = "tests" ]
then
    wget https://repo.continuum.io/miniconda/Miniconda3-latest-Linux-x86_64.sh -O miniconda.sh;
    bash miniconda.sh -b -p $HOME/miniconda
    export PATH="$HOME/miniconda/bin:$PATH"
    hash -r
    conda config --set always_yes yes --set changeps1 no
    conda update -q conda
    conda install pandas
    pip install .
    pip install ./api_background
    git clone --branch $MEERKAT_BRANCH --single-branch https://github.com/meerkat-code/meerkat_libs.git ../meerkat_libs
    pip install ../meerkat_libs
    git clone --branch $MEERKAT_BRANCH --single-branch https://github.com/meerkat-code/meerkat_analysis.git ../meerkat_analysis
    pip install ../meerkat_analysis
    git clone --branch $MEERKAT_BRANCH https://github.com/meerkat-code/meerkat_abacus.git ../meerkat_abacus
    pip install ../meerkat_abacus
    python ../meerkat_abacus/manage.py create-d
fi
