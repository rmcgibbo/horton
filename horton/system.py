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
'''Molecular system and all aspects relevant for a computation

   Objects of the System class specify the geometry (and atomic elements) of the
   molecule on which Horton will perform a computation. Also other parameters
   that determine several aspects of the molecular wavefunction, are attributes
   of a :class:`System` instance, e.g. basis sets, pseudo-potentials, ghost atoms,
   etc.
'''
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import


import numpy as np
import h5py as h5

from horton.cache import Cache
from horton.cext import compute_grid_nucpot
from horton.io import load_system_args, dump_system
from horton.log import log, timer
from horton.matrix import DenseLinalgFactory, LinalgObject
from horton.periodic import periodic


__all__ = ['System']


class System(object):
    def __init__(self, coordinates, numbers, obasis=None, grid=None, wfn=None,
                 lf=None, cache=None, extra=None, cell=None,
                 pseudo_numbers=None, chk=None):
        """
           **Arguments:**

           coordinates
                A (N, 3) float numpy array with Cartesian coordinates of the
                atoms.

           numbers
                A (N,) int numpy vector with the atomic numbers.

           **Optional arguments:**

           obasis
                A string or an instance of either the basis set or basis set
                description classes, e.g. 'STO-3G', GOBasisDesc('STO-3G'), ...
                for the orbitals.

           grid
                A grid object used for molecular integration.

           wfn
                A wavefunction object.

           lf
                A LinalgFactory instance. When not given, a DenseLinalgFactory
                is used by default.

           cache
                A cache object with computed results that depend on other
                attributes of the system class. Cached items should be tagged
                according to the attributes they depend on:

                    - ``o``: obasis
                    - ``c``: coordinates
                    - ``g``: grid

                When given as a dictionary, each value must consist of two
                items: the object to be cached and the tags.

           extra
                A dictionary with additional information about the system. The
                keys must be strings.

           cell
                A Cell object that describes the (generally triclinic) periodic
                boundary conditions. So far, this is nearly nowhere supported in
                Horton, so don't get too excited.

           pseudo_numbers
                The core charges of the pseudo potential, if applicable

           chk
                A filename for the checkpoint file or an open h5.File object.
                If the file does not exist yet, it will be created. If the file
                already exists, it must be an HDF5 file that is structured
                such that it adheres to the format that Horton creates itself.
                If chk is an open h5.File object, it will not be closed when the
                System instance is deleted.
        """

        # A) Assign all attributes
        self._coordinates = np.array(coordinates, dtype=float, copy=False)
        self._numbers = np.array(numbers, dtype=int, copy=False)
        # some checks
        if len(self._coordinates.shape) != 2 or self._coordinates.shape[1] != 3:
            raise TypeError('coordinates argument must be a 2D array with three columns')
        if len(self._numbers.shape) != 1:
            raise TypeError('numbers must a vector of integers.')
        if self._numbers.shape[0] != self._coordinates.shape[0]:
            raise TypeError('numbers and coordinates must have compatible array shapes.')
        #
        self._grid = grid
        #
        self._wfn = wfn
        #
        if cache is None:
            self._cache = Cache()
        elif isinstance(cache, Cache):
            self._cache = cache
        elif isinstance(cache, dict):
            self._cache = Cache()
            for key, (value, tags) in cache.iteritems():
                self._cache.dump(key, value, tags=tags)
        else:
            raise TypeError('Could not interpret the cache argument.')
        #
        if lf is None:
            self._lf = DenseLinalgFactory()
        else:
            self._lf = lf
        #
        if extra is None:
            self._extra = {}
        else:
            self._extra = extra
        #
        self._obasis = None
        self._obasis_desc = None
        if obasis is not None:
            self.update_obasis(obasis)

        self._cell = cell
        self._pseudo_numbers = pseudo_numbers

        # The checkpoint file
        self._chk = None
        self._close_chk = False
        self.assign_chk(chk)

        self._log_init()

    def __del__(self):
        # Close the HD5 checkpoint file. This must be done carefully to avoid
        # spurious error messages when an unrelated exception occurs.
        if hasattr(self, '_chk') and self.chk is not None and self._close_chk:
            self.chk.close()

    def _get_natom(self):
        '''The number of atoms'''
        return len(self.numbers)

    natom = property(_get_natom)

    def _get_coordinates(self):
        '''The positions of the nuclei'''
        return self._coordinates.view()

    coordinates = property(_get_coordinates)

    def _get_numbers(self):
        '''An array with the atomic numbers'''
        return self._numbers.view()

    numbers = property(_get_numbers)

    def _get_obasis(self):
        '''The orbital basis'''
        return self._obasis

    obasis = property(_get_obasis)

    def _get_obasis_desc(self):
        '''The orbital basis description'''
        return self._obasis_desc

    obasis_desc = property(_get_obasis_desc)

    def _get_grid(self):
        '''The integration grid'''
        return self._grid

    grid = property(_get_grid)

    def _get_wfn(self):
        '''The wavefunction'''
        return self._wfn

    wfn = property(_get_wfn)

    def _get_lf(self):
        '''The LinalgFactory for this system'''
        return self._lf

    lf = property(_get_lf)

    def _get_cache(self):
        '''A cache of intermediate results that depend on the coordinates'''
        return self._cache

    cache = property(_get_cache)

    def _get_extra(self):
        '''A dictionary with extra properties of the system.'''
        return self._extra

    extra = property(_get_extra)

    def _get_cell(self):
        '''A Cell object describing the periodic boundary conditions.'''
        return self._cell

    cell = property(_get_cell)

    def _get_pseudo_numbers(self):
        result = self._pseudo_numbers
        if result is None:
            result = self._numbers
        return result

    pseudo_numbers = property(_get_pseudo_numbers)

    def _get_chk(self):
        '''A ``h5.File`` instance used as checkpoint file or ``None``'''
        return self._chk

    chk = property(_get_chk)

    @classmethod
    def from_file(cls, *args, **kwargs):
        """Create a System object from a file.

           A list of filenames may be provided, which will be loaded in that
           order. Each file complements or overrides the information loaded
           from a previous file in the list. Furthermore, keyword arguments
           may be used to specify additional constructor arguments.

           The ``lf`` optional argument is picked up from the kwargs list to
           contstruct (when needed) arrays to store the results loaded from
           file. When ``lf`` is not given, a DenseLinalgFactory is created by
           default.

           The filenames may also contain checkpoint files and open h5.File
           objects of checkpoint files. The last such checkpoint file will
           automatically be used as a checkpoint file for this class. If you
           want to override this behavior, provide the ``chk`` keyword argument
           (may be None).
        """
        constructor_args = {}
        lf = kwargs.get('lf')
        if lf is None:
            lf = DenseLinalgFactory()
        for fn in args:
            fn_args = load_system_args(fn, lf)
            constructor_args.update(fn_args)
        constructor_args.update(kwargs)

        # If the basis comes from an external code and some operators are
        # loaded, rows and columns may need to be reordered. Similar for the
        # orbital coefficients and the density matrices.
        permutation = constructor_args.get('permutation')
        if permutation is not None:
            cache = constructor_args.get('cache')
            if cache is not None:
                for value, tags in cache.itervalues():
                    if isinstance(value, LinalgObject):
                        value.apply_basis_permutation(permutation)
            wfn = constructor_args.get('wfn')
            if wfn is not None:
                wfn.apply_basis_permutation(permutation)
            del constructor_args['permutation']

        # After the permutation, correct for different sign conventions of the
        # orbitals
        signs = constructor_args.get('signs')
        if signs is not None:
            cache = constructor_args.get('cache')
            if cache is not None:
                for value, tags in cache.itervalues():
                    if isinstance(value, LinalgObject):
                        value.apply_basis_signs(signs)
            wfn = constructor_args.get('wfn')
            if wfn is not None:
                wfn.apply_basis_signs(signs)
            del constructor_args['signs']

        return cls(**constructor_args)

    def _log_init(self):
        '''Write some basic information about the system to the screen logger.'''
        if log.do_medium:
            log('Initialized: %s' % self)
            log.deflist(
                [('Number of atoms', self.natom)] +
                [('Number of %s' % periodic[n].symbol, (self.numbers==n).sum()) for n in sorted(np.unique(self.numbers))] + [
                ('Linalg Factory', self._lf),
                ('Orbital basis', self._obasis),
                ('Wavefunction', self._wfn),
                ('Checkpoint file', self._chk),
            ])
            if len(self._cache) > 0:
                log('The following cached items are present: %s' % (', '.join(self._cache.iterkeys())))
            if len(self._extra) > 0:
                log('The following extra attributes are present: %s' % (', '.join(self._extra.iterkeys())))
            log.blank()

    def assign_chk(self, chk):
        if self.chk is not None and self._close_chk:
            self.chk.close()

        if isinstance(chk, basestring):
            # Suppose a filename is given. Create or open an HDF5 file.
            self._chk = h5.File(chk)
            self._close_chk = True
        elif isinstance(chk, h5.Group) or chk is None:
            self._chk = chk
            self._close_chk = False
        else:
            raise TypeError('The chk argument, when not None, must be a filename or an open h5.Group object.')
        self.update_chk()


    def update_chk(self, field_name=None):
        """Write (a part of) the system to the checkpoint file.

           **Optional Argument:**

           field
                A field string that specifies which part must be written to the
                checkpoint file. When not given, all possible fields are
                written. The latter is only useful in specific cases, e.g. upon
                initialization of the system. The available field names are
                specified in the attribute register dictionary in the
                module ``horton.checkpoint``.
        """
        if self._chk is not None:
            from horton.checkpoint import attribute_register
            if field_name is None:
                for field_name, field in attribute_register.iteritems():
                    field.write(self._chk, self)
            else:
                field = attribute_register[field_name]
                field.write(self._chk, self)

    def to_file(self, filename):
        '''Write the system to a file

           **Arguments:**

           filename
                The name of the file to write to. The extension of the file
                is used to determine the file format.
        '''
        dump_system(filename, self)

    def _get_charge(self):
        return self.pseudo_numbers.sum() - self.wfn.nel

    charge = property(_get_charge)

    def update_coordinates(self, coordinates=None):
        '''Update all attributes that depend on coodinates and clear related parts of cache

           **Optional arguments:**

           coordinates
                The new atomic coordinates

           When one wants to set new coordintes, one may also edit the
           system.coordinates array in-place and then call this method without
           any arguments.
        '''
        if coordinates is not None:
            self._coordinates[:] = coordinates
        if self._obasis is not None:
            self._obasis.centers[:] = self._coordinates
        if self._grid is not None:
            self._grid.update_centers(self)
        self.cache.clear(tags='cog')
        self._extra = {}

    def update_grid(self, grid=None):
        '''Define a new integration grid and clear related parts of the cache

           **Optional arguments:**

           grid
                The new integration grid. When not given, it is assumed that
                the grid was modified in-place and that only derived results in
                the cache need to be pruned.
        '''
        if grid is not None:
            self._grid = grid
        self.cache.clear(tags='g')

    def update_obasis(self, obasis=None):
        '''Regenerate the orbital basis and clear all attributes that depend on it.

           **Optional arguments:**

           obasis
                The new basis. This may be a string or an instance of GOBasis or
                GOBasisDesc. When not given, the orbital basis description
                stored in the system object (_obasis_desc attribute) will be
                used.
        '''
        # Get the orbital basis and if possible the orbital basis description.
        from horton.gbasis import GOBasisDesc, GOBasis
        if isinstance(obasis, str):
            obasis_desc = GOBasisDesc(obasis)
        elif isinstance(obasis, GOBasisDesc):
            obasis_desc = obasis
        elif isinstance(obasis, GOBasis):
            obasis_desc = None
        elif obasis is None:
            if self.obasis_desc is None:
                raise TypeError('No orbital basis description (obasis_desc) available to update obasis.')
            obasis_desc = self.obasis_desc
        else:
            raise TypeError('Could not interpret the obasis argument.')
        if obasis_desc is not None:
            obasis = obasis_desc.apply_to(self)

        # Discard or reset results that depend on orbital basis
        if self.obasis is not None:
            self._cache.clear(tags='o')
            # Ideally, the user of the system object does some sort of
            # projection of the wavefunction on the new basis. This should be
            # done outside the system class as their are too many different ways
            # to handle this. Here, we set the wfn to None, just to force the
            # user to do something.
            self._wfn = None
            self._extra = {}

        # Assign new obasis
        self._lf.set_default_nbasis(obasis.nbasis)
        self._obasis = obasis
        self._obasis_desc = obasis_desc

        # Some consistency checks. These are needed when the initial value of
        # obasis was None. This may occur when the system object is initialized.
        if self._wfn is not None and self._obasis.nbasis != self._wfn.nbasis:
            raise TypeError('The nbasis attribute of obasis and wfn are inconsistent.')
        for key, value in self._cache.iteritems():
            if isinstance(value, LinalgObject) and value.nbasis != self._obasis.nbasis:
                raise TypeError('The nbasis attribute of the cached object \'%s\' and obasis are inconsistent.' % key)

    @timer.with_section('OLP integrals')
    def get_overlap(self):
        overlap, new = self.cache.load('olp', alloc=self.lf.create_one_body, tags='o')
        if new:
            self.obasis.compute_overlap(overlap)
            self.update_chk('cache.olp')
        return overlap

    @timer.with_section('KIN integrals')
    def get_kinetic(self):
        kinetic, new = self.cache.load('kin', alloc=self.lf.create_one_body, tags='o')
        if new:
            self.obasis.compute_kinetic(kinetic)
            self.update_chk('cache.kin')
        return kinetic

    @timer.with_section('NAI integrals')
    def get_nuclear_attraction(self):
        nuclear_attraction, new = self.cache.load('na', alloc=self.lf.create_one_body, tags='o')
        if new:
            # TODO: ghost atoms and extra charges
            self.obasis.compute_nuclear_attraction(self.numbers.astype(float), self.coordinates, nuclear_attraction)
            self.update_chk('cache.na')
        return nuclear_attraction

    @timer.with_section('ER integrals')
    def get_electron_repulsion(self):
        electron_repulsion, new = self.cache.load('er', alloc=self.lf.create_two_body, tags='o')
        if new:
            self.obasis.compute_electron_repulsion(electron_repulsion)
            # ER integrals are not checkpointed by default because they are too heavy.
            # Can be done manually by user if needed: ``system.update_chk('cache.er')``
            #self.update_chk('cache.er')
        return electron_repulsion

    @timer.with_section('Orbitals grid')
    def compute_grid_orbitals(self, points, iorbs=None, orbs=None, select='alpha'):
        '''Compute the electron density on a grid using self.wfn as input

           **Arguments:**

           points
                A Numpy array with grid points, shape (npoint,3)

           **Optional arguments:**

           iorbs
                The indexes of the orbitals to be computed. If not given, the
                orbitals with a non-zero occupation number are computed

           orbs
                An output array, shape (npoint, len(iorbs)). The results are
                added to this array.

           select
                'alpha', 'beta'

           **Returns:**

           orbs
                The array with the result. This is the same as the output
                argument, in case it was provided.
        '''
        exp = self.wfn.get_exp(select)
        if iorbs is None:
            iorbs = (exp.occupations > 0).nonzero()[0]
        shape = (len(points), len(iorbs))
        if orbs is None:
            orbs = np.zeros(shape, float)
        elif orbs.shape != shape:
            raise TypeError('The shape of the output array is wrong')
        self.obasis.compute_grid_orbitals_exp(exp, points, iorbs, orbs)
        return orbs

    @timer.with_section('Density grid')
    def compute_grid_density(self, points, rhos=None, select='full', epsilon=0):
        '''Compute the electron density on a grid using self.wfn as input

           **Arguments:**

           points
                A Numpy array with grid points, shape (npoint,3)

           **Optional arguments:**

           rhos
                An output array, shape (npoint,). The results are added to this
                array.

           select
                'alpha', 'beta', 'full' or 'spin'. ('full' is the default.)

           epsilon
                Allow errors on the density of this magnitude for the sake of
                efficiency.

           **Returns:**

           rhos
                The array with the result. This is the same as the output
                argument, in case it was provided.
        '''
        if rhos is None:
            rhos = np.zeros(len(points), float)
        elif rhos.shape != (points.shape[0],):
            raise TypeError('The shape of the output array is wrong')
        dm = self.wfn.get_dm(select)
        self.obasis.compute_grid_density_dm(dm, points, rhos, epsilon)
        return rhos

    @timer.with_section('Gradient grid')
    def compute_grid_gradient(self, points, gradrhos=None, select='full'):
        '''Compute the electron density on a grid using self.wfn as input

           **Arguments:**

           points
                A Numpy array with grid points, shape (npoint,3)

           **Optional arguments:**

           gradrhos
                An output array, shape (npoint, 3). The results are added to
                this array.

           select
                'alpha', 'beta', 'full' or 'spin'. ('full' is the default.)

           **Returns:**

           gradrhos
                The array with the result. This is the same as the output
                argument, in case it was provided.
        '''
        if gradrhos is None:
            gradrhos = np.zeros((len(points), 3), float)
        elif gradrhos.shape != (points.shape[0],3):
            raise TypeError('The shape of the output array is wrong')
        dm = self.wfn.get_dm(select)
        self.obasis.compute_grid_gradient_dm(dm, points, gradrhos)
        return gradrhos

    @timer.with_section('Hartree grid')
    def compute_grid_hartree(self, points, hartree=None, select='full'):
        '''Compute the hartree potential on a grid using self.wfn as input

           **Arguments:**

           points
                A Numpy array with grid points, shape (npoint,3)

           **Optional arguments:**

           hartree
                An output array, shape (npoint,). The results are added to this
                array.

           select
                'alpha', 'beta', 'full' or 'spin'. ('full' is the default.)

           **Returns:**

           hartree
                The array with the result. This is the same as the output
                argument, in case it was provided.
        '''
        if hartree is None:
            hartree = np.zeros(len(points), float)
        elif hartree.shape != (points.shape[0],):
            raise TypeError('The shape of the output array is wrong')
        dm = self.wfn.get_dm(select)
        self.obasis.compute_grid_hartree_dm(dm, points, hartree)
        return hartree

    @timer.with_section('ESP grid')
    def compute_grid_esp(self, points, esp=None, select='full'):
        '''Compute the esp on a grid using self.wfn as input

           **Arguments:**

           points
                A Numpy array with grid points, shape (npoint,3)

           **Optional arguments:**

           esp
                An output array, shape (npoint,). The results are added to this
                array.

           select
                'alpha', 'beta', 'full' or 'spin'. ('full' is the default.)

           **Returns:**

           esp
                The array with the result. This is the same as the output
                argument, in case it was provided.
        '''
        if esp is None:
            esp = np.zeros(len(points), float)
        elif esp.shape != (points.shape[0],):
            raise TypeError('The shape of the output array is wrong')
        dm = self.wfn.get_dm(select)
        self.obasis.compute_grid_hartree_dm(dm, points, esp)
        esp *= -1
        compute_grid_nucpot(self.numbers, self.coordinates, points, esp)
        return esp

    @timer.with_section('Fock grid dens')
    def compute_grid_density_fock(self, points, weights, pots, fock):
        '''See documentation self.obasis.compute_grid_density_fock'''
        self.obasis.compute_grid_density_fock(points, weights, pots, fock)

    @timer.with_section('Fock grid grad')
    def compute_grid_gradient_fock(self, points, weights, pots, fock):
        '''See documentation self.obasis.compute_grid_gradient_fock'''
        self.obasis.compute_grid_gradient_fock(points, weights, pots, fock)

    def compute_nucnuc(self):
        '''Compute interaction energy of the nuclei'''
        # TODO: move this to low-level code one day.
        result = 0.0
        for i in xrange(self.natom):
            for j in xrange(i):
                distance = np.linalg.norm(self.coordinates[i]-self.coordinates[j])
                result += self.numbers[i]*self.numbers[j]/distance
        self._extra['energy_nn'] = result
        return result
