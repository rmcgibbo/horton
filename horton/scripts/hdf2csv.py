# -*- coding: utf-8 -*-
# Horton is a development platform for electronic structure methods.
# Copyright (C) 2011-2013 Toon Verstraelen <Toon.Verstraelen@UGent.be>
#
# This file is part of Horton.
#
# Horton is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 3
# of the License, or (at your option) any later version.
#
# Horton is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, see <http://www.gnu.org/licenses/>
#
#--
'''Code used by ``horton-hdf2csv.py``'''
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import


import h5py as h5

__all__ = ['iter_datasets']


def iter_datasets(grp):
    '''Iterate recursively over all datasets in the given group

       **Arguments:**

       grp
            The h5.Group instance to parse.

       This function iterators over all (name,dset) pairs it can find. The name
       is the full path of the dataset relative to the given group object.
    '''
    for name, item in sorted(grp.iteritems()):
        if isinstance(item, h5.Dataset):
            yield name, item
        elif isinstance(item, h5.Group):
            for subname, subitem in iter_datasets(item):
                yield name + '/' + subname, subitem
