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
'''Code used by ESP fitting scripts'''
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import


import numpy as np

from horton import System, angstrom, ESPCost, LockedH5File
from horton.scripts.common import reduce_data, parse_h5
from horton.part.proatomdb import ProAtomDB


__all__ = [
    'parse_wdens', 'parse_wnear', 'parse_wfar',
    'load_rho', 'load_cost', 'load_charges',
    'save_weights', 'max_at_edge',
]


def parse_wdens(arg):
    '''Parse the argument to the --wdens option of horton-espfit.py'''
    if arg is None:
        return
    words = arg.split(':')
    lnrho0 = -9
    sigma = 0.8
    if len(words) == 0:
        fn_cube = None
    elif len(words) == 1:
        fn_cube = words[0]
    elif len(words) == 2:
        fn_cube = words[0]
        lnrho0 = float(words[1])
    elif len(words) == 3:
        fn_cube = words[0]
        lnrho0 = float(words[1])
        sigma = float(words[2])
    else:
        raise ValueError('The argument to --wdens may at most contain three fields separated by a colon.')
    if len(fn_cube) == 0:
        fn_cube = None
    return fn_cube, lnrho0, sigma


def parse_wnear(args):
    '''Parse the arguments for the --wnear option of horton-espfit.py'''
    if args is None:
        return
    result = {}
    if isinstance(args, basestring):
        args = [args]
    for arg in args:
        words = arg.split(':')
        if len(words) < 2:
            raise ValueError('At least two fields separated by a colon are required for an argument to --wnear.')
        elif len(words) == 2:
            number = int(words[0])
            r0 = float(words[1])*angstrom
            gamma = r0*0.5
        elif len(words) == 3:
            number = int(words[0])
            r0 = float(words[1])*angstrom
            gamma = float(words[2])*angstrom
        else:
            raise ValueError('An argument to --wnear may at most contain three fields separated by a colon.')
        result[number] = r0, gamma
    return result


def parse_wfar(arg):
    '''Parse the argument for the --wfar option of horton-espfit.py'''
    if arg is None:
        return
    words = arg.split(':')
    if len(words) == 0:
        raise ValueError('No argument is given to the --wfar option')
    elif len(words) == 1:
        r0 = float(words[0])*angstrom
        gamma = 1.0*angstrom
    elif len(words) == 2:
        r0 = float(words[0])*angstrom
        gamma = float(words[1])*angstrom
    else:
        raise ValueError('The argument to --wfar may at most contain two fields separated by a colon.')
    return r0, gamma


def load_rho(system, fn_cube, ref_ugrid, stride, chop):
    '''Load densities from a file, reduce by stride, chop and check ugrid

       **Arguments:**

       system
            A Horton system object for the current system. This is only used
            to construct the pro-density.

       fn_cube
            The cube file with the electron density.

       ref_ugrid
            A reference ugrid that must match the one from the density cube
            file (after reduction).

       stride
            The reduction factor.

       chop
            The number of slices to chop of the grid in each direction.
    '''
    if fn_cube is None:
        # Load the built-in database of proatoms
        numbers = np.unique(system.numbers)
        proatomdb = ProAtomDB.from_refatoms(numbers, max_kation=0, max_anion=0, agspec='fine')
        # Construct the pro-density
        rho = np.zeros(ref_ugrid.shape)
        for i in xrange(system.natom):
            spline = proatomdb.get_spline(system.numbers[i])
            ref_ugrid.eval_spline(spline, system.coordinates[i], rho)
    else:
        # Load cube
        sys = System.from_file(fn_cube)
        rho = sys.extra['cube_data']
        ugrid = sys.grid
        # Reduce grid size
        if stride > 1:
            rho, ugrid = reduce_data(rho, ugrid, stride, chop)
        # Compare with ref_ugrid (only shape)
        if (ugrid.shape != ref_ugrid.shape).any():
            raise ValueError('The densities file does not contain the same amount if information as the potential file.')
    return rho


def load_cost(arg_cost):
    '''Load an ESP cost function given at the command line'''
    fn_h5_in, grp_name_in = parse_h5(arg_cost, 'cost')
    with LockedH5File(fn_h5_in, 'r') as f:
        return ESPCost.from_hdf5(f[grp_name_in]['cost'], None), f[grp_name_in]['used_volume'][()]


def load_charges(arg_charges):
    '''Load a charges given at the command line'''
    fn_h5, ds_name = parse_h5(arg_charges, 'charges', path_optional=False)
    with LockedH5File(fn_h5, 'r') as f:
        return f[ds_name][:]


def save_weights(fn_cube, sys, ugrid, weights):
    '''Save the weights used for the ESP cost function to a cube file

       **Arguments:**

       fn_cube
            The name of the cube file.

       sys
            A System instance.

       ugrid
            The uniform integration grid.

       weights
            The weights array to be saved.
    '''
    # construct a new system that contains all info for the cube file
    my_sys = System(sys.coordinates, sys.numbers, pseudo_numbers=sys.pseudo_numbers, grid=ugrid)
    my_sys.extra['cube_data'] = weights
    # save to file
    my_sys.to_file(fn_cube)


def max_at_edge(weights, pbc):
    '''Compute the maximum value of the weight function at the non-periodic
       edges of the grid.

       **Arguments:**

       weights
            A 3D array with ESP fitting weights

       pbc
            A vector of length three with periodicity flags.
    '''
    result = 0.0
    if pbc[0] == 0:
        result = max(result, weights[0,:,:].max())
        result = max(result, weights[-1,:,:].max())
    if pbc[1] == 0:
        result = max(result, weights[:,0,:].max())
        result = max(result, weights[:,-1,:].max())
    if pbc[2] == 0:
        result = max(result, weights[:,:,0].max())
        result = max(result, weights[:,:,-1].max())
    return result
