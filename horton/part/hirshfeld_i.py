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
'''Iterative Hirshfeld Partitioning'''
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import


import numpy as np

from horton.log import log
from horton.part.hirshfeld import HirshfeldWPart, HirshfeldCPart
from horton.part.iterstock import IterativeProatomMixin


__all__ = ['HirshfeldIWPart', 'HirshfeldICPart']


class HirshfeldIMixin(IterativeProatomMixin):
    name = 'hi'
    options = ['slow', 'lmax', 'threshold', 'maxiter', 'greedy']
    linear = False

    def __init__(self, threshold=1e-6, maxiter=500, greedy=False):
        self._threshold = threshold
        self._maxiter = maxiter
        self._greedy = greedy

    def _init_log_scheme(self):
        if log.do_medium:
            log.deflist([
                ('Scheme', 'Hirshfeld-I'),
                ('Convergence threshold', '%.1e' % self._threshold),
                ('Maximum iterations', self._maxiter),
                ('Proatomic DB',  self._proatomdb),
            ])
            log.cite('bultinck2007', 'the use of Hirshfeld-I partitioning')

    def get_memory_estimates(self):
        if self._greedy:
            return [('Isolated atoms', np.ones(self.system.natom)*3, 0),] # This is a conservative estimate.
        else:
            return []

    def get_interpolation_info(self, i, charges=None):
        if charges is None:
            charges = self.cache.load('charges')
        target_charge = charges[i]
        icharge = int(np.floor(target_charge))
        x = target_charge - icharge
        return icharge, x

    def get_proatom_rho(self, index, charges=None):
        icharge, x = self.get_interpolation_info(index, charges)
        # check if icharge record should exist
        pseudo_pop = self.system.pseudo_numbers[index] - icharge
        number = self.system.numbers[index]
        if pseudo_pop == 1 or x == 0.0:
            return self.proatomdb.get_rho(number, {icharge: 1-x}, do_deriv=True)
        elif pseudo_pop > 1:
            return self.proatomdb.get_rho(number, {icharge: 1-x, icharge+1: x}, do_deriv=True)
        elif pseudo_pop <= 0:
            raise ValueError('Requesting a pro-atom with a negative (pseudo) population')

    def get_somefn(self, index, spline, key, label, grid=None):
        if grid is None:
            grid = self.get_grid(index)
        key = key + (index, id(grid))
        if self._greedy:
            result, new = self.cache.load(*key, alloc=grid.shape)
        else:
            result = grid.zeros()
            new = True
        if new:
            self.eval_spline(index, spline, result, grid, label)
        return result

    def get_isolated(self, index, charge, grid=None):
        number = self.system.numbers[index]
        spline = self.proatomdb.get_spline(number, charge)
        return self.get_somefn(index, spline, ('isolated', charge), 'isolated q=%+i' % charge, grid)

    def eval_proatom(self, index, output, grid=None):
        # Greedy version of eval_proatom
        icharge, x = self.get_interpolation_info(index)
        output[:] = self.get_isolated(index, icharge, grid)
        output *= 1-x
        pseudo_pop = self.system.pseudo_numbers[index] - icharge
        if pseudo_pop > 1 and x != 0.0:
            output += self.get_isolated(index, icharge+1, grid)*x
        elif pseudo_pop <= 0:
            raise ValueError('Requesting a pro-atom with a negative (pseudo) population')
        output += 1e-100

    def _init_propars(self):
        IterativeProatomMixin._init_propars(self)
        charges = self.cache.load('charges', alloc=self._system.natom, tags='o')[0]
        self.cache.dump('propars', charges, tags='o')
        return charges

    def _update_propars_atom(self, index):
        # Compute population
        pseudo_population = self.compute_pseudo_population(index)

        # Store charge
        charges = self.cache.load('charges')
        charges[index] = self.system.pseudo_numbers[index] - pseudo_population


class HirshfeldIWPart(HirshfeldIMixin, HirshfeldWPart):
    options = HirshfeldIMixin.options + ['epsilon']

    def __init__(self, system, grid, proatomdb, local=True, slow=False, lmax=3, epsilon=0, threshold=1e-6, maxiter=500, greedy=False):
        '''
           **Optional arguments:** (that are not present in the base class)

           threshold
                The procedure is considered to be converged when the maximum
                change of the charges between two iterations drops below this
                threshold.

           maxiter
                The maximum number of iterations. If no convergence is reached
                in the end, no warning is given.
        '''
        HirshfeldIMixin.__init__(self, threshold, maxiter, greedy)
        HirshfeldWPart.__init__(self, system, grid, proatomdb, local, slow, lmax, epsilon)

    def get_memory_estimates(self):
        return (
            HirshfeldWPart.get_memory_estimates(self) +
            HirshfeldIMixin.get_memory_estimates(self)
        )

    def eval_proatom(self, index, output, grid=None):
        if self._greedy:
            HirshfeldIMixin.eval_proatom(self, index, output, grid)
        else:
            HirshfeldWPart.eval_proatom(self, index, output, grid)


class HirshfeldICPart(HirshfeldIMixin, HirshfeldCPart):
    def __init__(self, system, grid, local, moldens, proatomdb, wcor_numbers=None, wcor_rcut_max=2.0, wcor_rcond=0.1, lmax=3, threshold=1e-6, maxiter=500, greedy=False):
        '''
           **Optional arguments:** (that are not present in the base class)

           threshold
                The procedure is considered to be converged when the maximum
                change of the charges between two iterations drops below this
                threshold.

           maxiter
                The maximum number of iterations. If no convergence is reached
                in the end, no warning is given.
        '''
        HirshfeldIMixin.__init__(self, threshold, maxiter, greedy)
        HirshfeldCPart.__init__(self, system, grid, local, moldens, proatomdb, wcor_numbers, wcor_rcut_max, wcor_rcond, lmax)

    def get_memory_estimates(self):
        return (
            HirshfeldCPart.get_memory_estimates(self) +
            HirshfeldIMixin.get_memory_estimates(self)
        )

    def eval_proatom(self, index, output, grid=None):
        if self._greedy:
            HirshfeldIMixin.eval_proatom(self, index, output, grid)
        else:
            HirshfeldCPart.eval_proatom(self, index, output, grid)
