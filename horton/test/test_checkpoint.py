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
import os, h5py as h5, numpy as np
from nose.tools import assert_raises

from horton import *
from horton.test.common import get_random_cell, compare_systems, compare_wfns, tmpdir


def test_chk_initialization_filename_cs():
    with tmpdir('horton.test.test_checkpoint.test_chk_initialization_filename_cs') as dn:
        fn_chk = '%s/chk.h5' % dn
        fn_fchk = context.get_fn('test/water_sto3g_hf_g03.fchk')
        fn_log = context.get_fn('test/water_sto3g_hf_g03.log')
        sys1 = System.from_file(fn_fchk, fn_log, chk=fn_chk)
        del sys1
        sys1 = System.from_file(fn_fchk, fn_log)
        sys2 = System.from_file(fn_chk)
        compare_systems(sys1, sys2)


def test_chk_initialization_filename_os():
    with tmpdir('horton.test.test_checkpoint.test_chk_initialization_filename_os') as dn:
        fn_chk = '%s/chk.h5' % dn
        sys1 = System.from_file(context.get_fn('test/li_h_3-21G_hf_g09.fchk'), chk=fn_chk)
        del sys1
        sys1 = System.from_file(context.get_fn('test/li_h_3-21G_hf_g09.fchk'))
        sys2 = System.from_file(fn_chk)
        compare_systems(sys1, sys2)


def test_chk_initialization_file():
    chk = h5.File('horton.test.test_checkpoint.test_chk_initialization_file', driver='core', backing_store=False)
    sys1 = System.from_file(context.get_fn('test/hf_sto3g.fchk'), chk=chk)
    del sys1
    sys1 = System.from_file(context.get_fn('test/hf_sto3g.fchk'))
    sys2 = System.from_file(chk)
    compare_systems(sys1, sys2)
    chk.close()


def test_chk_initialization_override():
    with tmpdir('horton.test.test_checkpoint.test_chk_override') as dn:
        fn_chk1 = '%s/chk1.h5' % dn
        fn_chk2 = '%s/chk2.h5' % dn
        sys1 = System.from_file(context.get_fn('test/hf_sto3g.fchk'), chk=fn_chk1)
        del sys1
        sys1 = System.from_file(context.get_fn('test/hf_sto3g.fchk'))
        sys2 = System.from_file(fn_chk1, chk=fn_chk2)

        compare_systems(sys1, sys2)
        assert os.path.isfile(fn_chk2)

        sys3 = System.from_file(fn_chk2, chk=None)
        compare_systems(sys1, sys3)
        sys3.numbers[:] = 0
        sys3.update_chk('numbers')

        sys4 = System.from_file(fn_chk2, chk=None)
        compare_systems(sys1, sys4)


def test_chk_update1():
    chk = h5.File('horton.test.test_checkpoint.test_chk_update1', driver='core', backing_store=False)
    sys1 = System.from_file(context.get_fn('test/hf_sto3g.fchk'), chk=chk)
    sys1.numbers[:] = [3, 2]
    sys1.coordinates[0,2] = 0.25
    sys1.update_chk()
    del sys1
    sys1 = System.from_file(chk)
    assert (sys1.numbers == [3, 2]).all()
    assert sys1.coordinates[0,2] == 0.25
    chk.close()


def test_chk_update2():
    chk = h5.File('horton.test.test_checkpoint.test_chk_update2', driver='core', backing_store=False)
    sys1 = System.from_file(context.get_fn('test/hf_sto3g.fchk'), chk=chk)
    sys1.numbers[:] = [3, 2]
    sys1.coordinates[0,2] = 0.25
    sys1.update_chk('coordinates')
    del sys1
    sys1 = System.from_file(chk)
    assert (sys1.numbers != [3, 2]).all()
    assert sys1.coordinates[0,2] == 0.25
    chk.close()


def test_chk_update3():
    chk = h5.File('horton.test.test_checkpoint.test_chk_update3', driver='core', backing_store=False)
    sys1 = System.from_file(context.get_fn('test/hf_sto3g.fchk'), chk=chk)
    sys1.numbers[:] = [3, 2]
    sys1.update_chk()
    sys1.coordinates[0,2] = 0.25
    del sys1
    sys1 = System.from_file(chk)
    assert (sys1.numbers == [3, 2]).all()
    assert sys1.coordinates[0,2] != 0.25
    chk.close()


def test_chk_cache():
    chk = h5.File('horton.test.test_checkpoint.test_chk_cache', driver='core', backing_store=False)
    sys1 = System.from_file(context.get_fn('test/hf_sto3g.fchk'), chk=chk)
    ar_olp = sys1.get_overlap()._array
    ar_kin = sys1.get_kinetic()._array
    ar_na = sys1.get_nuclear_attraction()._array
    ar_er = sys1.get_electron_repulsion()._array
    # manually put er integrals in checkpoint, not done by default
    sys1.update_chk('cache.er')
    del sys1
    sys1 = System.from_file(chk)
    assert 'olp' in sys1.cache
    assert 'kin' in sys1.cache
    assert 'na' in sys1.cache
    assert 'er' in sys1.cache
    assert (ar_olp == sys1.get_overlap()._array).all()
    assert (ar_kin == sys1.get_kinetic()._array).all()
    assert (ar_na == sys1.get_nuclear_attraction()._array).all()
    assert (ar_er == sys1.get_electron_repulsion()._array).all()


def test_chk_guess_scf_cs():
    chk = h5.File('horton.test.test_checkpoint.test_chk_guess_scf_cs', driver='core', backing_store=False)
    fn_fchk = context.get_fn('test/hf_sto3g.fchk')
    sys = System.from_file(fn_fchk, chk=chk)

    guess_hamiltonian_core(sys)
    c = sys.wfn.exp_alpha._coeffs
    e = sys.wfn.exp_alpha._energies
    dma = sys.wfn.dm_alpha._array
    del sys
    sys = System.from_file(chk)
    assert (sys.wfn.exp_alpha._coeffs == c).all()
    assert (sys.wfn.exp_alpha._energies == e).all()
    assert (sys.wfn.dm_alpha._array == dma).all()

    ham = Hamiltonian(sys, [HartreeFockExchange()])
    with assert_raises(NoSCFConvergence):
        converge_scf(ham, 5)
    c = sys.wfn.exp_alpha._coeffs
    e = sys.wfn.exp_alpha._energies
    dma = sys.wfn.dm_alpha._array
    ham.compute()
    energy = sys.extra['energy']
    energy_kin = sys.extra['energy_kin']
    energy_hartree = sys.extra['energy_hartree']
    energy_exchange_hartree_fock = sys.extra['energy_exchange_hartree_fock']
    energy_ne = sys.extra['energy_ne']
    energy_nn = sys.extra['energy_nn']
    del sys
    del ham
    sys = System.from_file(chk)
    assert (sys.wfn.exp_alpha._coeffs == c).all()
    assert (sys.wfn.exp_alpha._energies == e).all()
    assert (sys.wfn.dm_alpha._array == dma).all()
    assert sys.extra['energy'] == energy
    assert sys.extra['energy_kin'] == energy_kin
    assert sys.extra['energy_hartree'] == energy_hartree
    assert sys.extra['energy_exchange_hartree_fock'] == energy_exchange_hartree_fock
    assert sys.extra['energy_ne'] == energy_ne
    assert sys.extra['energy_nn'] == energy_nn


def test_chk_guess_scf_os():
    chk = h5.File('horton.test.test_checkpoint.test_chk_guess_scf_os', driver='core', backing_store=False)
    fn_fchk = context.get_fn('test/li_h_3-21G_hf_g09.fchk')
    sys = System.from_file(fn_fchk, chk=chk)

    guess_hamiltonian_core(sys)
    ac = sys.wfn.exp_alpha._coeffs
    bc = sys.wfn.exp_beta._coeffs
    ae = sys.wfn.exp_alpha._energies
    be = sys.wfn.exp_beta._energies
    dma = sys.wfn.dm_alpha._array
    dmb = sys.wfn.dm_beta._array
    del sys
    sys = System.from_file(chk)
    assert (sys.wfn.exp_alpha._coeffs == ac).all()
    assert (sys.wfn.exp_beta._coeffs == bc).all()
    assert (sys.wfn.exp_alpha._energies == ae).all()
    assert (sys.wfn.exp_beta._energies == be).all()
    assert (sys.wfn.dm_alpha._array == dma).all()
    assert (sys.wfn.dm_beta._array == dmb).all()

    ham = Hamiltonian(sys, [HartreeFockExchange()])
    with assert_raises(NoSCFConvergence):
        converge_scf(ham, 5)
    ac = sys.wfn.exp_alpha._coeffs
    bc = sys.wfn.exp_beta._coeffs
    ae = sys.wfn.exp_alpha._energies
    be = sys.wfn.exp_beta._energies
    dma = sys.wfn.dm_alpha._array
    dmb = sys.wfn.dm_beta._array
    ham.compute()
    energy = sys.extra['energy']
    energy_kin = sys.extra['energy_kin']
    energy_hartree = sys.extra['energy_hartree']
    energy_exchange_hartree_fock = sys.extra['energy_exchange_hartree_fock']
    energy_ne = sys.extra['energy_ne']
    energy_nn = sys.extra['energy_nn']
    del sys
    del ham
    sys = System.from_file(chk)
    assert (sys.wfn.exp_alpha._coeffs == ac).all()
    assert (sys.wfn.exp_beta._coeffs == bc).all()
    assert (sys.wfn.exp_alpha._energies == ae).all()
    assert (sys.wfn.exp_beta._energies == be).all()
    assert (sys.wfn.dm_alpha._array == dma).all()
    assert (sys.wfn.dm_beta._array == dmb).all()
    assert sys.extra['energy'] == energy
    assert sys.extra['energy_kin'] == energy_kin
    assert sys.extra['energy_hartree'] == energy_hartree
    assert sys.extra['energy_exchange_hartree_fock'] == energy_exchange_hartree_fock
    assert sys.extra['energy_ne'] == energy_ne
    assert sys.extra['energy_nn'] == energy_nn


def test_hdf5_low():
    chk = h5.File('horton.test.test_checkpoint.test_hdf5_low', driver='core', backing_store=False)

    fn_fchk = context.get_fn('test/li_h_3-21G_hf_g09.fchk')
    sys = System.from_file(fn_fchk, chk=chk)

    data1 = {'a': {'b': np.zeros(5), 'c': 5}, 'd': sys.wfn}
    dump_hdf5_low(chk, 'data', data1)
    data2 = load_hdf5_low(chk['data'], lf=sys.lf)

    assert 'a' in data2
    assert 'd' in data2
    compare_wfns(sys.wfn, data2['d'])
    assert 'b' in data2['a']
    assert 'c' in data2['a']
    assert data2['a']['b'].shape == (5,)
    assert (data2['a']['b'] == 0.0).all()
    assert data2['a']['c'] == 5


def test_cell():
    for i in xrange(12):
        chk = h5.File('horton.test.test_checkpoint.test_cell_%i' % i, driver='core', backing_store=False)
        cell1 = get_random_cell(1.0, i%4)
        coordinates = np.random.uniform(-1, 1, (5, 3))
        numbers = np.random.randint(1, 11, 5)
        sys1 = System(coordinates, numbers, cell=cell1, chk=chk)
        del sys1
        sys2 = System.from_file(chk)
        assert (sys2.cell.rvecs == cell1.rvecs).all()
        chk.close()


def test_cube():
    chk = h5.File('horton.test.test_checkpoint.test_cube', driver='core', backing_store=False)

    fn_cube = context.get_fn('test/aelta.cube')
    sys = System.from_file(fn_cube)
    del sys
    sys1 = System.from_file(fn_cube, chk=chk)
    sys2 = System.from_file(chk)

    g1 = sys1.grid
    g2 = sys2.grid
    assert (g1.origin == g2.origin).all()
    assert (g1.grid_rvecs == g2.grid_rvecs).all()
    assert (g1.shape == g2.shape).all()
    assert (g1.pbc == g2.pbc).all()

    assert (sys1.extra['cube_data'] == sys2.extra['cube_data']).all()
    assert (sys1.pseudo_numbers == sys2.pseudo_numbers).all()
