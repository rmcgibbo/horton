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
'''Molecular integration grids'''
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import



import numpy as np

from horton.grid.base import IntGrid
from horton.grid.atgrid import AtomicGrid, AtomicGridSpec
from horton.grid.cext import becke_helper_atom
from horton.log import log, timer
from horton.periodic import periodic
from horton.system import System


__all__ = [
    'BeckeMolGrid'
]



class BeckeMolGrid(IntGrid):
    '''Molecular integration grid using Becke weights'''

    @timer.with_section('Becke-Lebedev')
    def __init__(self, system, agspec='medium', k=3, random_rotate=True, mode='discard'):
        '''
           **Arguments:**

           system
                The System object for which the molecular grid must be made.
                Alternatively, this may also be a tuple (centers, numbers,
                pseudo_numbers).

           **Optional arguments:**

           agspec
                A specifications of the atomic grid. This can either be an
                instance of the AtomicGridSpec object, or the first argument
                of its constructor.

           k
                The order of the switching function in Becke's weighting scheme.

           random_rotate
                Flag to control random rotation of spherical grids.

           mode
                Select one of the following options regarding atomic subgrids:

                * ``'discard'`` (the default) means that all information about
                  subgrids gets discarded.

                * ``'keep'`` means that a list of subgrids is kept, including
                  the integration weights of the local grids.

                * ``'only'`` means that only the subgrids are constructed and
                  that the computation of the molecular integration weights
                  (based on the Becke partitioning) is skipped.
        '''
        if isinstance(system, System):
            self._centers = system.coordinates.copy()
            self._numbers = system.numbers.copy()
            self._pseudo_numbers = system.pseudo_numbers.copy()
            natom = system.natom
        else:
            self._centers, self._numbers, self._pseudo_numbers = system
            natom = len(self.centers)

        # check if the mode argument is valid
        if mode not in ['discard', 'keep', 'only']:
            raise ValueError('The mode argument must be \'discard\', \'keep\' or \'only\'.')

        # transform agspec into a usable format
        if not isinstance(agspec, AtomicGridSpec):
            agspec = AtomicGridSpec(agspec)
        self._agspec = agspec

        # assign attributes
        self._k = k
        self._random_rotate = random_rotate
        self._mode = mode

        # allocate memory for the grid
        size = sum(agspec.get_size(self.numbers[i], self.pseudo_numbers[i]) for i in xrange(natom))
        points = np.zeros((size, 3), float)
        weights = np.zeros(size, float)
        log.mem.announce(points.nbytes + weights.nbytes)

        # construct the atomic grids
        if mode != 'discard':
            atgrids = []
        else:
            atgrids = None
        offset = 0

        if mode != 'only':
            # More recent covalent radii are used than in the original work of Becke.
            cov_radii = np.array([periodic[n].cov_radius for n in self.numbers])

        # The actual work:
        if log.do_medium:
            log('Preparing Becke-Lebedev molecular integration grid.')
        pb = log.progress(natom)
        for i in xrange(natom):
            atsize = agspec.get_size(self.numbers[i], self.pseudo_numbers[i])
            atgrid = AtomicGrid(
                self.numbers[i], self.pseudo_numbers[i],
                self.centers[i], agspec, random_rotate,
                points[offset:offset+atsize])
            if mode != 'only':
                weights[offset:offset+atsize] = atgrid.weights
                becke_helper_atom(
                    points[offset:offset+atsize], weights[offset:offset+atsize],
                    cov_radii, self.centers, i, self._k)
            if mode != 'discard':
                atgrids.append(atgrid)
            offset += atsize
            pb()

        # finish
        IntGrid.__init__(self, points, weights, atgrids)

        # Some screen info
        self._log_init()

    def __del__(self):
        if log is not None and hasattr(self, 'weights'):
            log.mem.denounce(self.points.nbytes + self.weights.nbytes)

    @classmethod
    def from_hdf5(cls, grp, lf):
        return BeckeMolGrid(
            (grp['centers'][:], grp['numbers'][:], grp['psuedo_numbers'][:]),
            AtomicGridSpec.from_hdf5(grp['agspec'], lf),
            grp['k'][()],
            grp['random_rotate'][()],
            grp.attrs['mode'],
        )

    def to_hdf5(self, grp):
        grp.attrs['class'] = self.__class__.__name__
        grp['centers'] = self._centers
        grp['numbers'] = self._numbers
        grp['psuedo_numbers'] = self._pseudo_numbers
        grp_agspec = grp.require_group('agspec')
        self.agspec.to_hdf5(grp_agspec, (self._numbers, self._pseudo_numbers))
        grp['random_rotate'] = self._random_rotate
        grp['k'] = self._k
        grp.attrs['mode'] = self._mode

    def _get_centers(self):
        '''The positions of the nuclei'''
        return self._centers.view()

    centers = property(_get_centers)

    def _get_numbers(self):
        '''The element numbers'''
        return self._numbers.view()

    numbers = property(_get_numbers)

    def _get_pseudo_numbers(self):
        '''The effective core charges'''
        return self._pseudo_numbers.view()

    pseudo_numbers = property(_get_pseudo_numbers)

    def _get_agspec(self):
        '''The specifications of the atomic grids.'''
        return self._agspec

    agspec = property(_get_agspec)

    def _get_k(self):
        '''The order of the Becke switching function.'''
        return self._k

    k = property(_get_k)

    def _get_random_rotate(self):
        '''The random rotation flag.'''
        return self._random_rotate

    random_rotate = property(_get_random_rotate)

    def _get_mode(self):
        '''The MO of this molecular grid'''
        return self._mode

    mode = property(_get_mode)

    def _log_init(self):
        if log.do_medium:
            log('Initialized: %s' % self)
            log.deflist([
                ('Size', self.size),
                ('Switching function', 'k=%i' % self._k),
            ])
            log.blank()
        # Cite reference
        log.cite('becke1988_multicenter', 'the multicenter integration scheme used for the molecular integration grid')
        log.cite('cordero2008', 'the covalent radii used for the Becke-Lebedev molecular integration grid')

    def integrate(self, *args, **kwargs):
        if self.mode == 'only':
            raise NotImplementedError('When mode==\'only\', only the subgrids can be used for integration.')
        return IntGrid.integrate(self, *args, **kwargs)

    def update_centers(self, system):
        if self.subgrids is None:
            raise RuntimeError('It is only possible to update the centers of a molecular grid when the subgrids are kept.')
        if len(self.subgrids) != system.natom:
            raise ValueError('The number of grid centers and the number of atoms does not match.')
        if (self.numbers != system.numbers).any() or (self.pseudo_numbers != system.pseudo_numbers).any():
            raise ValueError('The elements of the grid and the system do not match.')
        offset = 0
        # More recent covalent radii are used than in the original work of Becke.
        self.centers[:] = system.coordinates
        cov_radii = np.array([periodic[n].cov_radius for n in self.numbers])
        for i in xrange(system.natom):
            atgrid = self.subgrids[i]
            atsize = atgrid.size
            atgrid.update_center(self.centers[i])
            self.weights[offset:offset+atsize] = atgrid.weights
            becke_helper_atom(
                self.points[offset:offset+atsize],
                self.weights[offset:offset+atsize],
                cov_radii, self.centers, i, self._k)
            offset += atgrid.size
