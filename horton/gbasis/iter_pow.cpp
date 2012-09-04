// Horton is a Density Functional Theory program.
// Copyright (C) 2011-2012 Toon Verstraelen <Toon.Verstraelen@UGent.be>
//
// This file is part of Horton.
//
// Horton is free software; you can redistribute it and/or
// modify it under the terms of the GNU General Public License
// as published by the Free Software Foundation; either version 3
// of the License, or (at your option) any later version.
//
// Horton is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with this program; if not, see <http://www.gnu.org/licenses/>
//
//--


#include "common.h"
#include "iter_pow.h"


int iter_pow1_inc(long* n) {
    // Modify the indexes in place as to move to the next combination of powers
    // withing one angular momentum.
    // Note: shell_type = n[0] + n[1] + n[2];
    if (n[1] == 0) {
      if (n[0] == 0) {
        n[0] = n[2];
        n[2] = 0;
        return 0;
      } else {
        n[1] = n[2] + 1;
        n[2] = 0;
        n[0]--;
      }
    } else {
      n[1]--;
      n[2]++;
    }
    return 1;
}

void IterPow2::reset(long shell_type0, long shell_type1, long max_nbasis) {
    shell_type0 = shell_type0;
    shell_type1 = shell_type1;
    skip = max_nbasis - get_shell_nbasis(shell_type1) + 1;
    n0[0] = shell_type0;
    n0[1] = 0;
    n0[2] = 0;
    n1[0] = shell_type1;
    n1[1] = 0;
    n1[2] = 0;
    ibasis0 = 0;
    ibasis1 = 0;
    offset = 0;
}


int IterPow2::inc() {
    // Increment indexes of shell 1
    int result;
    result = iter_pow1_inc(n1);
    if (result) {
        offset++;
        ibasis1++;
    } else {
        // Increment indexes of shell 0
        result = iter_pow1_inc(n0);
        ibasis1 = 0;
        if (result) {
            offset += 1;
            ibasis0++;
        } else {
            offset = 0;
            ibasis0 = 0;
        }
    }
    return result;
}