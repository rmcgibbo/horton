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
'''Periodic table of elements

   This module contains an object ``periodic`` that can be used as a Pythonic
   periodic table. It can be used as follows::

       >>> from horton import periodic
       >>> periodic['si'].number
       14
       >>> periodic['He'].number
       2
       >>> periodic['h'].symbol
       'H'
       >>> periodic[3].symbol
       'Li'
       >>> periodic['5'].symbol
       'B'
'''
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import


from horton.context import context
from horton.units import angstrom


__all__ = ['periodic', 'Element', 'Periodic']



class Element(object):
    '''Represents an element from the periodic table.

       The following attributes are supported for all elements:

       number
            The atomic number

       symbol
            A string with the symbol of the element.

       The following attributes are present for some elements. When a parameter
       is not known for a given element, the attribute is set to None.

       cov_radius_cordero
            Covalent radius. B. Cordero, V. Gomez, A. E. Platero-Prats, M.
            Reves, J. Echeverria, E. Cremades, F. Barragan, and S. Alvarez,
            Dalton Trans. pp. 2832--2838 (2008), URL
            http://dx.doi.org/10.1039/b801115j

       cov_radius_bragg
            Covalent radius. W. L. Bragg, Phil. Mag. 40, 169 (1920), URL
            http://dx.doi.org/10.1080/14786440808636111

       cov_radius_slater
            Covalent radius. J. C. Slater, J. Chem. Phys. 41, 3199 (1964), URL
            http://dx.doi.org/10.1063/1.1725697

       vdw_radius_bondi
            van der Waals radius. A. Bondi, J. Phys. Chem. 68, 441 (1964), URL
            http://dx.doi.org/10.1021/j100785a001

       vdw_radius_truhlar
            van der Waals radius. M. Mantina A. C. Chamberlin R. Valero C. J.
            Cramer D. G. Truhlar J. Phys. Chem. A 113 5806 (2009), URL
            http://dx.doi.org/10.1021/jp8111556

       vdw_radius_rt
            van der Waals radius. R. S. Rowland and R. Taylor, J. Phys. Chem.
            100, 7384 (1996), URL http://dx.doi.org/10.1021/jp953141+

       vdw_radius_batsanov
            van der Waals radius. S. S. Batsanov Inorganic Materials 37 871
            (2001), URL http://dx.doi.org/10.1023/a%3a1011625728803

       vdw_radius_dreiding
            van der Waals radius. Stephen L. Mayo, Barry D. Olafson, and William
            A. Goddard III J. Phys. Chem. 94 8897 (1990), URL
            http://dx.doi.org/10.1021/j100389a010

       vdw_radius_uff
            van der Waals radius. A. K. Rappi, C. J. Casewit, K. S. Colwell, W.
            A. Goddard III, and W. M. Skid J. Am. Chem. Soc. 114 10024 (1992),
            URL http://dx.doi.org/10.1021/ja00051a040

       vdw_radius_mm3
            van der Waals radius. N. L. Allinger, X. Zhou, and J. Bergsma,
            Journal of Molecular Structure: THEOCHEM 312, 69 (1994),
            http://dx.doi.org/10.1016/s0166-1280(09)80008-0

       wc_radius
            Waber-Cromer radius of the outermost orbital maximum. J. T. Waber
            and D. T. Cromer, J. Chem. Phys. 42, 4116 (1965), URL
            http://dx.doi.org/10.1063/1.1695904

       cr_radius
            Clementi-Raimondi radius. E. Clementi, D. L. Raimondi, W. P.
            Reinhardt, J. Chem. Phys. 47, 1300 (1967), URL
            http://dx.doi.org/10.1063/1.1712084

       The following attribute is derived from the data given above:

       cov_radius:
            equals cov_radius_cordero

       vdw_radius:
            vdw_radius_truhlar if present
            else vdw_radius_bondi if present
            else vdw_radius_batsanov if present
            else vdw_radius_mm3 if present
            else None

       becke_radius:
            cov_radius_slater if present
            else cov_radius_cordero if present
            else None
    '''

    attribute_names = [
        'cov_radius_cordero', 'cov_radius_bragg', 'cov_radius_slater',
        'vdw_radius_bondi', 'vdw_radius_truhlar', 'vdw_radius_rt',
        'vdw_radius_batsanov', 'vdw_radius_dreiding', 'vdw_radius_uff',
        'vdw_radius_mm3', 'wc_radius', 'cr_radius',
    ]

    def __init__(self, number=None, symbol=None, **kwargs):
        self.number = number
        self.symbol = symbol
        for name in self.attribute_names:
            setattr(self, name, kwargs.get(name))

        self.cov_radius = self.cov_radius_cordero

        if self.vdw_radius_truhlar is not None:
            self.vdw_radius = self.vdw_radius_truhlar
        elif self.vdw_radius_bondi is not None:
            self.vdw_radius = self.vdw_radius_bondi
        elif self.vdw_radius_batsanov is not None:
            self.vdw_radius = self.vdw_radius_batsanov
        elif self.vdw_radius_mm3 is not None:
            self.vdw_radius = self.vdw_radius_mm3
        else:
            self.vdw_radius = None

        if self.cov_radius_slater is not None:
            self.becke_radius = self.cov_radius_slater
        elif self.cov_radius_cordero is not None:
            self.becke_radius = self.cov_radius_cordero
        else:
            self.becke_radius = None


class Periodic(object):
    '''A periodic table data structure.'''
    def __init__(self, elements):
        '''**Arguments:**

           elements
                A list of :class:`Element` instances.
        '''
        self.elements = elements
        self._lookup = {}
        for element in elements:
            self._lookup[element.number] = element
            self._lookup[element.symbol.lower()] = element

    def __getitem__(self, index):
        '''Get an element from the table based on a flexible index.

           **Argument:**

           index
                This can be either an integer atomic number, a string with the
                elemental symbol (any case), or a string with the atomic number.

           **Returns:** the corresponding :class:`Element` instance
        '''
        result = self._lookup.get(index)
        if result is None and isinstance(index, basestring):
            index = index.strip()
            result = self._lookup.get(index.lower())
            if result is None and index.isdigit():
                result = self._lookup.get(int(index))
                if result is None:
                    raise KeyError('Could not find element %s.' % index)
        return result

def load_periodic():
    import csv

    convertor_types = {
        'int': (lambda s: int(s)),
        'float': (lambda s : float(s)),
        'str': (lambda s: s.strip()),
        'angstrom': (lambda s: float(s)*angstrom),
        '2angstrom': (lambda s: float(s)*angstrom/2),
    }

    with open(context.get_fn('elements.csv'),'r') as f:
        r = csv.reader(f)
        # go to the actual data
        for row in r:
            if len(row[1]) > 0:
                break
        # parse the first two header rows
        names = row
        convertors = [convertor_types[key] for key in next(r)]

        elements = []
        for row in r:
            if len(row) == 0:
                break
            kwargs = {}
            for i in xrange(len(row)):
                cell = row[i]
                if len(cell) > 0:
                    kwargs[names[i]] = convertors[i](cell)
            elements.append(Element(**kwargs))

    return Periodic(elements)


periodic = load_periodic()
