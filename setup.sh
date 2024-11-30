#!/bin/bash

## Submodules
git submodule init;
git submodule update;

### Java and Maven images
docker pull openjdk:11;
docker pull maven:3.9.8-eclipse-temurin-8;

### Defects4J image
cd benchmarks/defects4j;
cpanm --installdeps .;
./init.sh;
cd ../..;

### GitBug-Java
cd benchmarks/gitbug-java;
chmod +x gitbug-java;
poetry install --no-root;
# Skip setup if in CI
if [ -z "$CI" ]; then
 poetry run ./gitbug-java setup;
fi

mkdir benchmarks/run_bug_run
cd benchmarks/run_bug_run
wget https://github.com/giganticode/run_bug_run_data/releases/download/v0.0.1/python_valid0.jsonl.gz
wget https://github.com/giganticode/run_bug_run_data/releases/download/v0.0.1/tests_all.jsonl.gz

gzip -d python_valid0.jsonl.gz
gzip -d tests_all.jsonl.gz
gzip -d buggy_test_results.tgz
tar xvf buggy_test_results.tar
cd ../..
