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


__all__ = ['compute_mulliken_charges']


def compute_mulliken_charges(sys):
    operators = get_mulliken_operators(sys)
    populations = np.array([operator.expectation_value(sys.wfn.dm_full) for operator in operators])
    return sys.numbers - np.array(populations)
