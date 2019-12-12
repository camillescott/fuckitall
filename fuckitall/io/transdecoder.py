#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# (c) Camille Scott, 2019
# File   : transdecoder.py
# License: MIT
# Author : Camille Scott <camille.scott.w@gmail.com>
# Date   : 11.12.2019

import pandas as pd
import screed

from .base import convert_dtypes, ChunkParser


class TransDecoderPepParser(ChunkParser):

    columns = [('full_transcript_name', str),
               ('transcript_name', str),
               ('feature_name', str),
               ('src_start', int),
               ('src_end', int),
               ('length', int),
               ('strand', str),
               ('feature_type', str)]
    
    def __init__(self, filename, **kwargs):
        super(TransDecoderPepParser, self).__init__(filename, **kwargs)

    def __iter__(self):

        data = []
        n_entries = 0
        for record in screed.open(self.filename):
            full_transcript_name, feature_type, length, \
                gen_code, src_coords = record.name.split(' ')

            transcript_name, _, feature_name = full_transcript_name.partition('.')
            _, _, coords = src_coords.partition(':')
            strand = coords.strip()[-2]
            _, _, length = length.partition(':')
            start, _, end = coords.strip('(-+)').partition('-')
            
            data.append([full_transcript_name,
                         transcript_name,
                         feature_name,
                         start,
                         end,
                         length,
                         strand,
                         feature_type])

            n_entries += 1
            if len(data) >= self.chunksize:
                yield self._build_df(data)
                data = []

        if n_entries == 0:
            self.raise_empty()
        if data:
            yield self._build_df(data)

    def _build_df(self, data):
        if not data:
            self.raise_empty()
        df = pd.DataFrame(data, columns=[k for k, _ in self.columns])
        convert_dtypes(df, dict(self.columns))
        # fix the evil coordinate system
        sidx = df.src_start > df.src_end
        df.loc[sidx, 'src_start'], df.loc[sidx, 'src_end'] = \
            df.loc[sidx, 'src_end'], df.loc[sidx, 'src_start']
        df.src_start = df.src_start - 1
        return df
