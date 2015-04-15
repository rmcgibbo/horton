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
import numpy as np
from horton import *
from horton.test.common import get_random_cell


def test_pair_ewald3d_invariance_rcut():
    np.random.seed(0)
    alpha_scale = 4.5
    gcut_scale = 1.5
    delta = np.random.normal(0, 1, 3)
    delta /= np.linalg.norm(delta)
    cell = get_random_cell(1.0, 3)
    results = []
    for rcut in np.arange(10.0, 20.001, 1.0):
        alpha = alpha_scale/rcut
        gcut = gcut_scale*alpha
        results.append(pair_ewald(delta, cell, rcut, alpha, gcut))
    results = np.array(results)
    assert abs(results - results.mean()).max() < 1e-7
