# -*- coding: utf-8 -*-
# Horton is a Density Functional Theory program.
# Copyright (C) 2011-2012 Toon Verstraelen <Toon.Verstraelen@UGent.be>
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


from horton import *


def test_dm_water_sto3g_hf():
    fn_fchk = context.get_fn('test/water_sto3g_hf_g03.fchk')
    sys = System.from_file(fn_fchk)
    dm = sys.wfn.dm_full
    assert abs(dm.get_element(0, 0) - 2.10503807) < 1e-7
    assert abs(dm.get_element(0, 1) - -0.439115917) < 1e-7
    assert abs(dm.get_element(1, 1) - 1.93312061) < 1e-7


def test_conversion_dm_exp():
    fn_fchk = context.get_fn('test/water_sto3g_hf_g03.fchk')
    sys = System.from_file(fn_fchk)
    oes = sys.wfn.exp_alpha.energies.copy()
    dm = sys.lf.create_one_body()
    dm.assign(sys.wfn.dm_alpha)

    ham = Hamiltonian(sys, [HartreeFock()])
    fock = sys.lf.create_one_body()
    ham.compute_fock(fock, None)
    sys.wfn.invalidate()
    sys.wfn.update_exp(fock, sys.get_overlap(), dm)

    assert abs(sys.wfn.exp_alpha.occupations.sum() - 5) < 1e-8
    assert abs(oes - sys.wfn.exp_alpha.energies).max() < 3e-8
    assert (dm._array == sys.wfn.dm_alpha._array).all()
    # ugly hack
    del sys.wfn._cache._store[('dm_alpha',)]
    assert abs(dm._array - sys.wfn.dm_alpha._array).max() < 1e-9


def test_dm_lih_sto3g_hf():
    fn_fchk = context.get_fn('test/li_h_3-21G_hf_g09.fchk')
    sys = System.from_file(fn_fchk)

    dm = sys.wfn.dm_full
    assert abs(dm.get_element(0, 0) - 1.96589709) < 1e-7
    assert abs(dm.get_element(0, 1) - 0.122114249) < 1e-7
    assert abs(dm.get_element(1, 1) - 0.0133112081) < 1e-7
    assert abs(dm.get_element(10, 10) - 4.23924688E-01) < 1e-7

    dm = sys.wfn.dm_spin
    assert abs(dm.get_element(0, 0) - 1.40210760E-03) < 1e-9
    assert abs(dm.get_element(0, 1) - -2.65370873E-03) < 1e-9
    assert abs(dm.get_element(1, 1) - 5.38701212E-03) < 1e-9
    assert abs(dm.get_element(10, 10) - 4.23889148E-01) < 1e-7


def test_spin_li_h():
    fn_fchk = context.get_fn('test/li_h_3-21G_hf_g09.fchk')
    sys = System.from_file(fn_fchk)
    sz, ssq = sys.wfn.get_spin(sys.get_overlap())
    assert sz == 0.5
    assert abs(ssq - 0.75) < 1e-7

def test_spin_h3_hfs():
    fn_fchk = context.get_fn('test/h3_hfs_321g.fchk')
    sys = System.from_file(fn_fchk)
    sz, ssq = sys.wfn.get_spin(sys.get_overlap())
    assert sz == 0.5
    assert abs(ssq - 0.7530) < 1e-4

def test_spin_h3_pbe():
    fn_fchk = context.get_fn('test/h3_pbe_321g.fchk')
    sys = System.from_file(fn_fchk)
    sz, ssq = sys.wfn.get_spin(sys.get_overlap())
    assert sz == 0.5
    assert abs(ssq - 0.7530) < 1e-4

def test_spin_ch3_hf():
    fn_fchk = context.get_fn('test/ch3_hf_sto3g.fchk')
    sys = System.from_file(fn_fchk)
    sz, ssq = sys.wfn.get_spin(sys.get_overlap())
    assert sz == 0.5
    assert abs(ssq - 0.7632) < 1e-4
