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
#pylint: skip-file


from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from horton.test.common import check_script
from horton import context


def test_example_001_hf_water():
    check_script('./run.py', context.get_fn('examples/001_hf_water'))


def test_example_002_hfs_water():
    check_script('./run.py', context.get_fn('examples/002_hfs_water'))


def test_example_003_o3lyp_water():
    check_script('./run.py', context.get_fn('examples/003_o3lyp_water'))


def test_example_004_wpart():
    check_script('./run.py', context.get_fn('examples/004_wpart'))
