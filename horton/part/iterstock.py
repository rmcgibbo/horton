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
'''Iterative Stockholder partitioning'''
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import


import numpy as np
from horton.cache import just_once
from horton.log import log
from horton.part.stockholder import StockholderWPart


__all__ = ['IterativeProatomMixin', 'IterativeStockholderWPart']


class IterativeProatomMixin():
    def compute_change(self, propars1, propars2):
        '''Compute the difference between an old and a new proatoms'''
        msd = 0.0 # mean-square deviation
        for index in xrange(self.system.natom):
            rgrid = self.get_rgrid(index)
            rho1, deriv1 = self.get_proatom_rho(index, propars1)
            rho2, deriv2 = self.get_proatom_rho(index, propars2)
            delta = rho1 - rho2
            msd +=  rgrid.integrate(delta, delta)
        return np.sqrt(msd)

    def _init_propars(self):
        self.history_propars = []
        self.history_charges = []

    def _update_propars(self):
        # Keep track of history
        self.history_propars.append(self.cache.load('propars').copy())

        # Update the partitioning based on the latest proatoms
        self.update_at_weights()

        # Update the proatoms
        for index in xrange(self.system.natom):
            self._update_propars_atom(index)

        # Keep track of history
        self.history_charges.append(self.cache.load('charges').copy())

    def _update_propars_atom(self, index):
        raise NotImplementedError

    def _finalize_propars(self):
        charges = self._cache.load('charges')
        self.cache.dump('history_propars', np.array(self.history_propars), tags='o')
        self.cache.dump('history_charges', np.array(self.history_charges), tags='o')
        self.cache.dump('populations', self.system.numbers - charges, tags='o')
        self.cache.dump('pseudo_populations', self.system.pseudo_numbers - charges, tags='o')

    @just_once
    def do_partitioning(self):
        # Perform one general check in the beginning to avoid recomputation
        new = any(('at_weights', i) not in self.cache for i in xrange(self.system.natom))
        new |= 'niter' not in self.cache
        new |= 'change'not in self.cache
        if new:
            # Need to compute density
            self.do_moldens()

            propars = self._init_propars()
            if log.medium:
                log.hline()
                log('Iteration       Change')
                log.hline()

            counter = 0
            change = 1e100

            while True:
                counter += 1

                # Update the parameters that determine the pro-atoms.
                old_propars = propars.copy()
                self._update_propars()

                # Check for convergence
                change = self.compute_change(propars, old_propars)
                if log.medium:
                    log('%9i   %10.5e' % (counter, change))
                if change < self._threshold or counter >= self._maxiter:
                    break

            if log.medium:
                log.hline()

            self._finalize_propars()
            self.cache.dump('niter', counter, tags='o')
            self.cache.dump('change', change, tags='o')


class IterativeStockholderWPart(IterativeProatomMixin, StockholderWPart):
    '''Class for Iterative Stockholder Partitioning'''
    name = 'is'
    options = ['slow', 'lmax', 'threshold', 'maxiter', 'epsilon']
    linear = False

    def __init__(self, system, grid, slow=False, lmax=3, epsilon=0, threshold=1e-6, maxiter=500):
        self._threshold = threshold
        self._maxiter = maxiter
        StockholderWPart.__init__(self, system, grid, True, slow, lmax, epsilon)

    def _init_log_scheme(self):
        if log.do_medium:
            log.deflist([
                ('Scheme', 'Iterative Stockholder'),
                ('Convergence threshold', '%.1e' % self._threshold),
                ('Maximum iterations', self._maxiter),
            ])
            log.cite('lillestolen2008', 'the use of Iterative Stockholder partitioning')

    def get_rgrid(self, index):
        return self.get_grid(index).rgrid

    def get_proatom_rho(self, index, propars=None):
        if propars is None:
            propars = self.cache.load('propars')
        return propars[self._ranges[index]:self._ranges[index+1]], None

    def _init_propars(self):
        IterativeProatomMixin._init_propars(self)
        self._ranges = [0]
        for index in xrange(self.system.natom):
            npoint = self.get_rgrid(index).size
            self._ranges.append(self._ranges[-1]+npoint)
        ntotal = self._ranges[-1]
        return self.cache.load('propars', alloc=ntotal, tags='o')[0]

    def _update_propars_atom(self, index):
        # compute spherical average
        atgrid = self.get_grid(index)
        dens = self.get_moldens(index)
        at_weights = self.cache.load('at_weights', index)
        radial_results = atgrid.integrate(at_weights, dens, segments=atgrid.nlls)
        radial_weights = atgrid.integrate(segments=atgrid.nlls)
        spherical_average = np.clip(radial_results/radial_weights, 1e-100, np.inf)

        # assign as new propars
        propars = self.cache.load('propars')
        propars[self._ranges[index]:self._ranges[index+1]] = spherical_average

        # compute the new charge
        pseudo_population = radial_results.sum()
        charges = self.cache.load('charges', alloc=self.system.natom, tags='o')[0]
        charges[index] = self.system.pseudo_numbers[index] - pseudo_population
