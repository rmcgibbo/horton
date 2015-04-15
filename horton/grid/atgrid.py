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
'''Atomic grids'''
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import


import numpy as np, os


from horton.context import context
from horton.grid.base import IntGrid
from horton.grid.cext import lebedev_laikov_sphere, RTransform, \
    LinearRTransform, ExpRTransform, PowerRTransform
from horton.grid.radial import RadialGrid
from horton.log import log
from horton.units import angstrom


__all__ = [
    'AtomicGrid', 'get_rotation_matrix',
    'get_random_rotation', 'AtomicGridSpec',
]


class AtomicGrid(IntGrid):
    def __init__(self, number, pseudo_number, center, agspec='medium', random_rotate=True, points=None):
        '''
           **Arguments:**

           number
                The element number for which this grid will be used.

           pseudo_number
                The effective core charge for which this grid will be used.

           center
                The center of the radial grid

           **Optional arguments:**

           agspec
                A specifications of the atomic grid. This can either be an
                instance of the AtomicGridSpec object, or the first argument
                of its constructor.

           random_rotate
                When set to False, the random rotation of the grid points is
                disabled. Such random rotation improves the accuracy of the
                integration, but leads to small random changes in the results
                that are not reproducible.

           points
                Array to store the grid points
        '''
        self._number = number
        self._pseudo_number = pseudo_number
        self._center = center
        if not isinstance(agspec, AtomicGridSpec):
            agspec = AtomicGridSpec(agspec)
        self._agspec = agspec
        self._rgrid, self._nlls = self._agspec.get(number, pseudo_number)
        self._random_rotate = random_rotate

        size = self._nlls.sum()
        if points is None:
            points = np.zeros((size, 3), float)
        else:
            assert len(points) == size
        weights = np.zeros(size, float)
        self._av_weights = np.zeros(size, float)

        self._init_low(points, weights)
        IntGrid.__init__(self, points, weights)
        self._log_init()

    def _init_low(self, points, weights):
        offset = 0
        nsphere = len(self._nlls)
        radii = self._rgrid.radii
        rweights = self._rgrid.weights

        for i in xrange(nsphere):
            nll = self._nlls[i]
            my_points = points[offset:offset+nll]
            my_av_weights = self._av_weights[offset:offset+nll]
            my_weights = weights[offset:offset+nll]

            lebedev_laikov_sphere(my_points, my_av_weights)
            my_points *= radii[i]
            if self.random_rotate:
                rotmat = get_random_rotation()
                my_points[:] = np.dot(my_points, rotmat)
            my_weights[:] = my_av_weights
            my_weights *= rweights[i]

            offset += nll

        points[:] += self.center

    def _get_number(self):
        '''The element number of the grid.'''
        return self._number

    number = property(_get_number)

    def _get_center(self):
        '''The center of the grid.'''
        return self._center

    center = property(_get_center)

    def _get_rgrid(self):
        '''The radial integration grid'''
        return self._rgrid

    rgrid = property(_get_rgrid)

    def _get_nlls(self):
        '''The number of Lebedev-Laikov grid points at each sphere.'''
        return self._nlls

    nlls = property(_get_nlls)

    def _get_nsphere(self):
        '''The number of spheres in the grid.'''
        return len(self._nlls)

    nsphere = property(_get_nsphere)

    def _get_random_rotate(self):
        '''The random rotation flag.'''
        return self._random_rotate

    random_rotate = property(_get_random_rotate)

    def _get_av_weights(self):
        '''The weights needed to compute spherical averages.'''
        return self._av_weights

    av_weights = property(_get_av_weights)

    def _log_init(self):
        if log.do_high:
            log('Initialized: %s' % self)
            log.deflist([
                ('Size', self.size),
                ('Number of radii', self.nsphere),
                ('Min LL sphere', self._nlls.min()),
                ('Max LL sphere', self._nlls.max()),
                ('Radial Transform', self._rgrid.rtransform.to_string()),
                ('1D Integrator', self._rgrid.int1d),
            ])
        # Cite reference
        log.cite('lebedev1999', 'the use of Lebedev-Laikov grids (quadrature on a sphere)')

    def get_spherical_average(self, *args, **kwargs):
        '''Returns the spherical average on the radial grid of the product of the given functions'''
        mtype = kwargs.pop('mtype', None)
        lmax = kwargs.pop('lmax', 4)
        if len(kwargs) > 0:
            raise TypeError('Unexpected keyword argument: %s' % kwargs.popitem()[0])
        if mtype is None:
            result = self.integrate(*args, segments=self.nlls)
            result /= self.integrate(segments=self.nlls)
        else:
            result = self.integrate(*args, center=self.center, mtype=mtype, lmax=lmax, segments=self.nlls)
            result /= self.integrate(segments=self.nlls).reshape(-1, 1)
        return result

    def update_center(self, center):
        self._center[:] = center
        self._init_low(self.points, self.weights)


def get_rotation_matrix(axis, angle):
    '''Rodrigues' rotation formula'''
    x, y, z = axis/np.linalg.norm(axis)
    c = np.cos(angle)
    s = np.sin(angle)
    return np.array([
        [x*x*(1-c)+c  , x*y*(1-c)-z*s, x*z*(1-c)+y*s],
        [x*y*(1-c)+z*s, y*y*(1-c)+c  , y*z*(1-c)-x*s],
        [x*z*(1-c)-y*s, y*z*(1-c)+x*s, z*z*(1-c)+c  ],
    ])


def get_random_rotation():
    '''Return a random rotation matrix'''
    # Get a random unit vector for the axis
    while True:
        axis = np.random.uniform(-1, 1, 3)
        norm = np.linalg.norm(axis)
        if norm < 1.0 and norm > 0.1:
            break

    # Get a random rotation angle
    angle = np.random.uniform(0, 2*np.pi)

    return get_rotation_matrix(axis, angle)


def _normalize_nlls(nlls, size):
    '''Make sure nlls is an array of the proper size'''
    if hasattr(nlls, '__iter__'):
        if len(nlls) == 1:
            nlls = np.array(list(nlls)*size, dtype=int)
        else:
            nlls = np.array(nlls, dtype=int)
            if len(nlls) != size:
                raise ValueError('The size of the radial grid must match the number of elements in nlls')
    else:
        nlls = np.array([nlls]*size, dtype=int)
    return nlls


class AtomicGridSpec(object):
    '''A specification of atomic integration grids for multiple elements.'''
    def __init__(self, definition='medium'):
        '''
           **Optional argument:**

           definition
                A definition of the grid.

                This can be a string that can be interpreted in several ways to
                define the grids. Attempts to interpret the string are done in
                the following order:

                1. A local file that has the same format as the files in
                   ${HORTONDATA}/grids.
                2. It can be any of 'coarse', 'medium', 'fine', 'veryfine',
                   'ultrafine', 'insane'. These have a straightforward
                   one-to-one mapping with the files in ${HORTONDATA}/grids.
                3. It can be the name of a file in ${HORTONDATA}/grids (without
                   the extension ``.txt``
                4. A string of the format: ``rname:rmin:rmax:nrad:nll``, with
                   the following meaning for the keywords. ``rname`` specifies
                   the type of radial grid. It can be ``linear``, ``exp`` or
                   ``power``. ``rmin`` and ``rmax`` specify the first and the
                   last radial grid point in angstroms. ``nrad`` is the number
                   of radial grid points. ``nll`` is the number of points for
                   the angular Lebedev-Laikov grid.

                Instead of a string, a Pythonic grid specification is also
                supported:

                * A tuple ``(rgrid, nll)``, where ``rgrid`` is an instance of
                  ``RadialGrid`` and ``nll`` is an integer or a list of
                  integers. The same grid is then used for each element.
                * A list where each element is a tuple of the form ``(number,
                  pseudo_number, rgrid, nll)``, where ``number`` is the element
                  number, ``pseudo_number`` is the effective core charge,
                  ``rgrid`` is an instance of ``RadialGrid`` and ``nll`` is an
                  integer or a list of integers. In this case, each element has
                  its own grid specification. When using pseudo potentials,
                  the most appropriate grid can be selected, depending on the
                  effective core charge.
        '''
        if isinstance(definition, basestring):
            self.name = definition
            self._init_members_from_string(definition)
        elif isinstance(definition, tuple):
            self.name = 'custom'
            self._init_members_from_tuple(definition)
        elif isinstance(definition, list):
            self.name = 'custom'
            self._init_members_from_list(definition)
        else:
            raise ValueError('Could not parse the definition of the atomic grid specification.')

    @classmethod
    def from_hdf5(cls, grp, lf):
        records = []
        for ds in grp.itervalues():
            rtransform = RTransform.from_string(ds.attrs['rtransform'])
            records.append((
                ds.attrs['number'], ds.attrs['pseudo_number'],
                RadialGrid(rtransform), ds[:]
            ))
        return AtomicGridSpec(records)

    def to_hdf5(self, grp, selection=None):
        if selection is not None:
            selection = set(zip(*selection))
        for number in self.members:
            for pseudo_number, rgrid, nlls in self.members.get(number):
                if selection is None or (number, pseudo_number) in selection:
                    ds = grp.create_dataset('%03i_%03i' % (number, pseudo_number), data=nlls)
                    ds.attrs['number'] = number
                    ds.attrs['pseudo_number'] = pseudo_number
                    ds.attrs['rtransform'] = rgrid.rtransform.to_string()

    def get(self, number, pseudo_number):
        for pn, rgrid, nlls in self.members.get(number, []):
            if pn >= pseudo_number:
                return rgrid, nlls
        raise ValueError('The atomic grid specification "%s" does not support element %i with effective core %i' % (self.name, number, pseudo_number))

    def get_size(self, number, pseudo_number):
        '''Get the size of an atomic grid for a given element

           **Arguments:**

           number
                The element number

           pseudo_number
                The effective core charge
        '''
        rgrid, nlls = self.get(number, pseudo_number)
        return nlls.sum()

    def _init_members_from_tuple(self, members):
        assert len(members) == 2
        rgrid, nlls = members
        nlls = _normalize_nlls(nlls, rgrid.size)
        # Assign this grid specification or each element
        self.members = dict((number, [(number, rgrid, nlls)]) for number in xrange(1, 119))

    def _init_members_from_list(self, members):
        self.members = {}
        for number, pseudo_number, rgrid, nlls in members:
            nlls = _normalize_nlls(nlls, rgrid.size)
            l = self.members.setdefault(number, [])
            l.append((pseudo_number, rgrid, nlls))
        for l in self.members.itervalues():
            l.sort()

    _simple_names = {
        'coarse':    'tv-13.7-3',
        'medium':    'tv-13.7-4',
        'fine':      'tv-13.7-5',
        'veryfine':  'tv-13.7-6',
        'ultrafine': 'tv-13.7-7',
        'insane':    'tv-13.7-8',
    }

    _simple_rtfs = {
        'linear': LinearRTransform,
        'exp': ExpRTransform,
        'power': PowerRTransform,
    }

    def _init_members_from_string(self, definition):
        if os.path.isfile(definition):
            self._load(definition)
            return
        filename = context.get_fn('grids/%s.txt' % definition)
        if os.path.isfile(filename):
            self._load(filename)
            return
        name = self._simple_names.get(definition)
        if name is not None:
            filename = context.get_fn('grids/%s.txt' % name)
            self._load(filename)
            return
        if definition.count(':') == 4:
            words = self.name.split(':')
            RTransformClass = self._simple_rtfs.get(words[0])
            if RTransformClass is None:
                raise ValueError('Unknown radial grid type: %s' % words[0])
            rmin = float(words[1])*angstrom
            rmax = float(words[2])*angstrom
            nrad = int(words[3])
            rgrid = RadialGrid(RTransformClass(rmin, rmax, nrad))
            nll = int(words[4])
            self._init_members_from_tuple((rgrid, nll))

    def _load(self, filename):
        fn = context.get_fn(filename)
        members = []
        with open(fn) as f:
            state = 0
            for line in f:
                line = line[:line.find('#')].strip()
                if len(line) > 0:
                    if state == 0:
                        # read element number
                        words = line.split()
                        number = int(words[0])
                        if len(words) > 1:
                            pseudo_number = int(words[1])
                        else:
                            pseudo_number = number
                        state = 1
                    elif state == 1:
                        # read rtf string
                        rtf = RTransform.from_string(line)
                        state = 2
                    elif state == 2:
                        nlls = np.array([int(w) for w in line.split()])
                        state = 0
                        members.append((number, pseudo_number, RadialGrid(rtf), nlls))

        self._init_members_from_list(members)
