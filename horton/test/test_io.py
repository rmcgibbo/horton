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


import numpy as np

from horton import *


def test_load_operators_water_sto3g_hf_g03():
    lf = DenseLinalgFactory()
    eps = 1e-5
    fn = context.get_fn('test/water_sto3g_hf_g03.log')
    overlap, kinetic, nuclear_attraction, electronic_repulsion = load_operators_g09(fn, lf)

    for op in overlap, kinetic, nuclear_attraction, electronic_repulsion:
        assert op is not None
        assert op.nbasis == 7
        op.check_symmetry()

    assert abs(overlap.get_element(0,0) - 1.0) < eps
    assert abs(overlap.get_element(0,1) - 0.236704) < eps
    assert abs(overlap.get_element(0,2) - 0.0) < eps
    assert abs(overlap.get_element(-1,-3) - (-0.13198)) < eps

    assert abs(kinetic.get_element(2,0) - 0.0) < eps
    assert abs(kinetic.get_element(4,4) - 2.52873) < eps
    assert abs(kinetic.get_element(-1,5) - 0.00563279) < eps
    assert abs(kinetic.get_element(-1,-3) - (-0.0966161)) < eps

    assert abs(nuclear_attraction.get_element(3,3) - 9.99259) < eps
    assert abs(nuclear_attraction.get_element(-2,-1) - 1.55014) < eps
    assert abs(nuclear_attraction.get_element(2,6) - 2.76941) < eps
    assert abs(nuclear_attraction.get_element(0,3) - 0.0) < eps

    assert abs(electronic_repulsion.get_element(0,0,0,0) - 4.78506575204) < eps
    assert abs(electronic_repulsion.get_element(6,6,6,6) - 0.774605944194) < eps
    assert abs(electronic_repulsion.get_element(6,5,0,5) - 0.0289424337101) < eps
    assert abs(electronic_repulsion.get_element(5,4,0,1) - 0.00274145291476) < eps


def test_load_operators_water_ccpvdz_pure_hf_g03():
    lf = DenseLinalgFactory()
    eps = 1e-5
    fn = context.get_fn('test/water_ccpvdz_pure_hf_g03.log')
    overlap, kinetic, nuclear_attraction, electronic_repulsion = load_operators_g09(fn, lf)

    for op in overlap, kinetic, nuclear_attraction, electronic_repulsion:
        assert op is not None
        assert op.nbasis == 24
        op.check_symmetry()

    assert abs(overlap.get_element(0,0) - 1.0) < eps
    assert abs(overlap.get_element(0,1) - 0.214476) < eps
    assert abs(overlap.get_element(0,2) - 0.183817) < eps
    assert abs(overlap.get_element(10,16) - 0.380024) < eps
    assert abs(overlap.get_element(-1,-3) - 0.000000) < eps

    assert abs(kinetic.get_element(2,0) - 0.160648) < eps
    assert abs(kinetic.get_element(11,11) - 4.14750) < eps
    assert abs(kinetic.get_element(-1,5) - (-0.0244025)) < eps
    assert abs(kinetic.get_element(-1,-6) - (-0.0614899)) < eps

    assert abs(nuclear_attraction.get_element(3,3) - 12.8806) < eps
    assert abs(nuclear_attraction.get_element(-2,-1) - 0.0533113) < eps
    assert abs(nuclear_attraction.get_element(2,6) - 0.173282) < eps
    assert abs(nuclear_attraction.get_element(-1,0) - 1.24131) < eps

    assert abs(electronic_repulsion.get_element(0,0,0,0) - 4.77005841522) < eps
    assert abs(electronic_repulsion.get_element(23,23,23,23) - 0.785718708997) < eps
    assert abs(electronic_repulsion.get_element(23,8,23,2) - (-0.0400337571969)) < eps
    assert abs(electronic_repulsion.get_element(15,2,12,0) - (-0.0000308196281033)) < eps


def test_load_fchk_hf_sto3g_num():
    lf = DenseLinalgFactory()
    coordinates, numbers, obasis, wfn, permutation = load_fchk(context.get_fn('test/hf_sto3g.fchk'), lf)
    assert obasis.nshell == 4
    assert obasis.nbasis == 6
    assert (obasis.nprims == 3).all()
    assert len(coordinates) == len(numbers)
    assert coordinates.shape[1] == 3
    assert len(numbers) == 2


def test_load_fchk_h_sto3g_num():
    lf = DenseLinalgFactory()
    coordinates, numbers, obasis, wfn, permutation = load_fchk(context.get_fn('test/h_sto3g.fchk'), lf)
    assert obasis.nshell == 1
    assert obasis.nbasis == 1
    assert (obasis.nprims == 3).all()
    assert len(coordinates) == len(numbers)
    assert coordinates.shape[1] == 3
    assert len(numbers) == 1


def test_load_fchk_o2_cc_pvtz_pure_num():
    lf = DenseLinalgFactory()
    coordinates, numbers, obasis, wfn, permutation = load_fchk(context.get_fn('test/o2_cc_pvtz_pure.fchk'), lf)
    assert obasis.nshell == 20
    assert obasis.nbasis == 60
    assert len(coordinates) == len(numbers)
    assert coordinates.shape[1] == 3
    assert len(numbers) == 2


def test_load_fchk_o2_cc_pvtz_cart_num():
    lf = DenseLinalgFactory()
    coordinates, numbers, obasis, wfn, permutation = load_fchk(context.get_fn('test/o2_cc_pvtz_cart.fchk'), lf)
    assert obasis.nshell == 20
    assert obasis.nbasis == 70
    assert len(coordinates) == len(numbers)
    assert coordinates.shape[1] == 3
    assert len(numbers) == 2


def test_load_fchk_water_sto3g_hf():
    lf = DenseLinalgFactory()
    coordinates, numbers, obasis, wfn, permutation = load_fchk(context.get_fn('test/water_sto3g_hf_g03.fchk'), lf)
    assert obasis.nshell == 5
    assert obasis.nbasis == 7
    assert len(coordinates) == len(numbers)
    assert coordinates.shape[1] == 3
    assert len(numbers) == 3
    assert wfn.nbasis == 7
    assert wfn.nep == 5
    assert abs(wfn.expansion.energies[0] - (-2.02333942E+01)) < 1e-7
    assert abs(wfn.expansion.energies[-1] - 7.66134805E-01) < 1e-7
    assert abs(wfn.expansion.coeffs[0,0] - 0.99410) < 1e-4
    assert abs(wfn.expansion.coeffs[1,0] - 0.02678) < 1e-4
    assert abs(wfn.expansion.coeffs[-1,2] - (-0.44154)) < 1e-4
    assert abs(wfn.expansion.coeffs[3,-1]) < 1e-4
    assert abs(wfn.expansion.coeffs[4,-1] - (-0.82381)) < 1e-4


def test_load_fchk_lih_321g_hf():
    lf = DenseLinalgFactory()
    fn_fchk = context.get_fn('test/li_h_3-21G_hf_g09.fchk')
    coordinates, numbers, obasis, wfn, permutation = load_fchk(fn_fchk, lf)
    assert obasis.nshell == 7
    assert obasis.nbasis == 11
    assert len(coordinates) == len(numbers)
    assert coordinates.shape[1] == 3
    assert len(numbers) == 2
    assert wfn.nbasis == 11
    assert wfn.nalpha == 2
    assert wfn.nbeta == 1
    assert abs(wfn.alpha_expansion.energies[0] - (-2.76117)) < 1e-4
    assert abs(wfn.alpha_expansion.energies[-1] - 0.97089) < 1e-4
    assert abs(wfn.alpha_expansion.coeffs[0,0] - 0.99105) < 1e-4
    assert abs(wfn.alpha_expansion.coeffs[1,0] - 0.06311) < 1e-4
    assert abs(wfn.alpha_expansion.coeffs[3,2]) < 1e-4
    assert abs(wfn.alpha_expansion.coeffs[-1,9] - 0.13666) < 1e-4
    assert abs(wfn.alpha_expansion.coeffs[4,-1] - 0.17828) < 1e-4
    assert abs(wfn.beta_expansion.energies[0] - (-2.76031)) < 1e-4
    assert abs(wfn.beta_expansion.energies[-1] - 1.13197) < 1e-4
    assert abs(wfn.beta_expansion.coeffs[0,0] - 0.99108) < 1e-4
    assert abs(wfn.beta_expansion.coeffs[1,0] - 0.06295) < 1e-4
    assert abs(wfn.beta_expansion.coeffs[3,2]) < 1e-4
    assert abs(wfn.beta_expansion.coeffs[-1,9] - 0.80875) < 1e-4
    assert abs(wfn.beta_expansion.coeffs[4,-1] - (-0.15503)) < 1e-4

    dm = lf.create_one_body(wfn.nbasis)
    dms = lf.create_one_body(wfn.nbasis)
    dma = lf.create_one_body(wfn.nbasis)
    dmb = lf.create_one_body(wfn.nbasis)

    wfn.compute_density_matrix(dm)
    wfn.compute_spin_density_matrix(dms)
    wfn.compute_alpha_density_matrix(dma)
    wfn.compute_beta_density_matrix(dmb)

    assert abs(dm._array - (dma._array + dmb._array)).max() < 1e-10
    assert abs(dms._array - (dma._array - dmb._array)).max() < 1e-10

    # Load some additional matrices from the fchk file and compare
    fchk = FCHKFile(fn_fchk, ['Total SCF Density', 'Spin SCF Density'])
    def to_dens(longrow, size):
        result = np.zeros((size, size), float)
        i0 = 0
        i1 = 0
        for i in xrange(len(longrow)):
            result[i0, i1] = longrow[i]
            result[i1, i0] = longrow[i]
            if i0==i1:
                i1 += 1
                i0 = 0
            else:
                i0 += 1
        return result
    assert abs(dm._array - to_dens(fchk.fields['Total SCF Density'], 11)).max() < 1e-7
    assert abs(dms._array - to_dens(fchk.fields['Spin SCF Density'], 11)).max() < 1e-7