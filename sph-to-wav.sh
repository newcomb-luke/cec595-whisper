#!/bin/bash

for f in ~/data_asr/atc0_comp/*/data/audio/*.sph; do
    sox "$f" "${f%.*}.wav";
done
